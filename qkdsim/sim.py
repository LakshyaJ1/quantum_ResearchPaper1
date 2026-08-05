"""Discrete-event simulator: control plane, key economy, fail-mode comparison.

The object of study is the CONTROL POLICY, not the photonics. Per-link secret
key rates are parameterised inputs (see config.py provenance), which is why a
single CPU core suffices and why the physical layer is not simulated.

Why a purpose-built simulator rather than an existing tool (dossier 2.6):
  SeQUeNCe  -- sequence/qkd/ is point-to-point BB84 + cascade; no trusted
               relay, no key pools.
  NetSquid  -- no relay/pools; package and docs behind registration with no
               OSI licence, which is an artifact-availability problem.
  QuISP     -- no key pools; inherits OMNeT++ Academic Public License.
  QKDNetSim -- the only on-target tool, and we adopt its QKDBuffer semantics
               verbatim for citability. But routing there is self-described as
               "an early version of routing table", QCenController implements
               exactly one policy, and ADMISSION CONTROL DOES NOT EXIST --
               precisely the two things this study compares. QKDNetSim+
               (arXiv:2402.10822) additionally found that nodes did not
               adequately process received key material and the crypto handler
               malfunctioned, in exactly this layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np

from .config import (GRADE_ORDER, G1_OTP, G2_QKD_SYM, G3_HYBRID, G4_PQC, SimConfig,
                     TRAFFIC_CLASSES, TrafficClass, grade_rank, is_at_least,
                     quantum_key_demand)
from .network import Topology, candidate_paths, select_path_kar, select_path_sp
from .physics import LinkState


class Outcome(str, Enum):
    PENDING = "PENDING"
    SERVED = "SERVED"
    BLOCKED = "BLOCKED"


@dataclass
class Session:
    sid: int
    cls: str
    arrival_t: float
    payload_bits: int
    src: str
    dst: str
    authorised_floor: str
    deadline_s: float
    priority: int
    outcome: Outcome = Outcome.PENDING
    grade: Optional[str] = None
    served_t: Optional[float] = None
    hops: int = 0
    key_bits: float = 0.0
    floor_violation: bool = False

    @property
    def ttk(self) -> Optional[float]:
        if self.served_t is None:
            return None
        return self.served_t - self.arrival_t


@dataclass
class Results:
    cfg_summary: Dict
    sessions: List[Session] = field(default_factory=list)
    generated_bits: float = 0.0
    consumed_bits: float = 0.0
    discarded_bits: float = 0.0
    link_state_ticks: Dict[str, int] = field(default_factory=dict)
    warmup_s: float = 0.0
    """Sessions arriving before this are excluded from every metric below."""

    # ---- aggregate views -------------------------------------------------
    def _sel(self, cls: Optional[str] = None,
             include_warmup: bool = False) -> List[Session]:
        return [s for s in self.sessions
                if (cls is None or s.cls == cls)
                and (include_warmup or s.arrival_t >= self.warmup_s)]

    def n_sessions(self, cls: Optional[str] = None) -> int:
        return len(self._sel(cls))

    def transient_report(self) -> Dict[str, float]:
        """The warm-up is a finding, not a discard. Quantifies how long a
        formation deploying with topped-up reservoirs runs before the key
        economy binds."""
        warm = [s for s in self.sessions if s.arrival_t < self.warmup_s
                and s.outcome is Outcome.SERVED]
        steady = [s for s in self._sel() if s.outcome is Outcome.SERVED]
        def below(xs):
            return (sum(not is_at_least(s.grade, G2_QKD_SYM) for s in xs)
                    / len(xs)) if xs else float("nan")
        return {"warmup_below_its": below(warm),
                "steady_below_its": below(steady),
                "n_warmup": len(warm), "n_steady": len(steady)}

    def served_fraction(self, cls: Optional[str] = None) -> float:
        xs = self._sel(cls)
        if not xs:
            return float("nan")
        return sum(s.outcome is Outcome.SERVED for s in xs) / len(xs)

    def blocked_fraction(self, cls: Optional[str] = None) -> float:
        xs = self._sel(cls)
        if not xs:
            return float("nan")
        return sum(s.outcome is Outcome.BLOCKED for s in xs) / len(xs)

    def grade_composition(self, cls: Optional[str] = None) -> Dict[str, float]:
        """Fraction of SERVED sessions delivered at each assurance grade.

        This is the operator-facing indicator absent from current QKD
        resilience standards (ITU-T Y.3815/Y.3821 restore *QKD* key supply and
        have no vocabulary for having served traffic at a lower assurance
        class). Zhu arXiv:2510.15248 defines an antecedent quantity (rho_k,t);
        we report it against swept adversarial pressure, which they do not.
        """
        xs = [s for s in self._sel(cls) if s.outcome is Outcome.SERVED]
        if not xs:
            return {g: float("nan") for g in GRADE_ORDER}
        return {g: sum(s.grade == g for s in xs) / len(xs) for g in GRADE_ORDER}

    def below_its_fraction(self, cls: Optional[str] = None) -> float:
        """Fraction of SERVED sessions delivered below G2, i.e. WITHOUT an
        information-theoretically-delivered key. The quantity the adversary is
        trying to maximise; the denominator of the downgrade-forcing cost."""
        xs = [s for s in self._sel(cls) if s.outcome is Outcome.SERVED]
        if not xs:
            return float("nan")
        return sum(not is_at_least(s.grade, G2_QKD_SYM) for s in xs) / len(xs)

    def forced_below_its_fraction(self, cls: Optional[str] = None) -> float:
        """Fraction of served sessions that were ENTITLED to an
        information-theoretically delivered key (authorised floor at or above
        G2) but were served below it.

        This is the quantity the downgrade-forcing cost is defined on.
        `below_its_fraction` is NOT suitable: it counts LOG traffic whose
        authorised floor is G3, i.e. traffic the policy already permits to run
        on computational security. Conflating authorised with forced
        degradation would make the adversary appear to have already won before
        it acted.
        """
        xs = [s for s in self._sel(cls) if s.outcome is Outcome.SERVED
              and is_at_least(s.authorised_floor, G2_QKD_SYM)]
        if not xs:
            return float("nan")
        return sum(not is_at_least(s.grade, G2_QKD_SYM) for s in xs) / len(xs)

    def floor_violation_fraction(self, cls: Optional[str] = None) -> float:
        xs = [s for s in self._sel(cls) if s.outcome is Outcome.SERVED]
        if not xs:
            return float("nan")
        return sum(s.floor_violation for s in xs) / len(xs)

    def ttk_stats(self, cls: Optional[str] = None) -> Tuple[float, float]:
        vals = [s.ttk for s in self._sel(cls)
                if s.outcome is Outcome.SERVED and s.ttk is not None]
        if not vals:
            return float("nan"), float("nan")
        a = np.asarray(vals, dtype=float)
        return float(a.mean()), float(np.percentile(a, 95))

    def mean_hops(self) -> float:
        vals = [s.hops for s in self.sessions if s.outcome is Outcome.SERVED]
        return float(np.mean(vals)) if vals else float("nan")


class Simulator:
    def __init__(self, topo: Topology, cfg: SimConfig,
                 traffic: Sequence[TrafficClass] = TRAFFIC_CLASSES,
                 grade_policy=None):
        """`grade_policy(session, sim) -> Optional[str]`

        Extension point for the policy-space audit (PHASE2_DESIGN section 12).
        When supplied, it chooses which assurance grade to ATTEMPT for a pending
        session, or returns None to defer to a later tick. When absent, the
        hand-designed heuristic runs: target the authorised floor, then degrade
        or block according to fail_mode.

        The learned policy can only pick among grades -- it cannot alter the key
        economy, the per-hop accounting, or the shield. That containment is what
        makes the audit a statement about our design's headroom rather than an
        unfalsifiable performance claim.
        """
        self.topo = topo
        self.cfg = cfg
        self.traffic = list(traffic)
        self.grade_policy = grade_policy

        # Common random numbers: independent streams so that changing the
        # POLICY does not change the arrival sequence or the channel
        # realisation. Without this, a 3-4 point service delta between policies
        # is partly noise rather than signal.
        ss = np.random.SeedSequence(cfg.seed)
        s_arr, s_out, s_pair = ss.spawn(3)
        self.rng_arrivals = np.random.default_rng(s_arr)
        self.rng_outage = np.random.default_rng(s_out)
        self.rng_pairs = np.random.default_rng(s_pair)

        self._endpoints = self._pick_endpoints()
        self._adv_links: set = set()
        self._apply_adversary()

        self.pending: List[Session] = []
        self.results = Results(warmup_s=cfg.warmup_s, cfg_summary={
            "horizon_s": cfg.horizon_s,
            "warmup_s": cfg.warmup_s,
            "routing": cfg.routing,
            "fail_mode": cfg.fail_mode,
            "reservation_floors": cfg.reservation_floors,
            "auth_on": cfg.accounting.auth_on,
            "gamma": cfg.physics.gamma,
            "e_abort": cfg.physics.e_abort,
            "adv_budget_links": cfg.adversary.budget_links,
            "adv_delta_e": cfg.adversary.delta_e,
            "seed": cfg.seed,
        })
        self._next_sid = 0

    # -- setup ------------------------------------------------------------
    def _pick_endpoints(self) -> List[Tuple[str, str]]:
        """Rear-area node to each forward post. Traffic always traverses the
        relay chain, which is where the hop multiplier bites."""
        rear = [n for n, r in self.topo.node_roles.items() if r == "rear"]
        fwd = [n for n, r in self.topo.node_roles.items() if r == "forward"]
        if not rear or not fwd:
            nodes = sorted(self.topo.graph.nodes())
            return [(nodes[0], nodes[-1])]
        return [(rear[0], f) for f in sorted(fwd)]

    def _apply_adversary(self) -> None:
        """Worst-case adversary: suppress the k most path-critical links.

        Selection is by edge betweenness centrality, so it is deterministic
        given the topology and therefore reproducible. Pressure is expressed in
        ABSOLUTE QBER units, which can be checked against a measured error rate;
        a dimensionless multiplier cannot.
        """
        adv = self.cfg.adversary
        if adv.budget_links <= 0:
            return
        if adv.targeting == "mincut":
            ranked = self._mincut_order()
        elif adv.targeting == "betweenness":
            eb = nx.edge_betweenness_centrality(self.topo.graph)
            ranked = [e for e, _ in
                      sorted(eb.items(), key=lambda kv: (-kv[1], kv[0]))]
        else:
            raise ValueError(f"unknown targeting {adv.targeting!r}")
        for (u, v) in ranked[:adv.budget_links]:
            self._adv_links.add(Topology.key(u, v))
            lk = self.topo.link(u, v)
            if adv.deny_classical:
                # Quantum channel pristine, key rate zero. Invisible to any
                # QBER-driven model -- Mehic et al. arXiv:1810.03857.
                lk.outage = True
            else:
                lk.excess_qber = adv.delta_e

    def _mincut_order(self) -> List[Tuple[str, str]]:
        """Edges ordered so that the smallest prefix severs the most traffic.

        Takes the minimum edge cut isolating each forward post from the rear
        node, ordered by cut size (cheapest target first), then any remaining
        edges. With two edge-disjoint paths to a post, this needs 2 edges no
        matter how deep the relay chain is -- the honest worst case against
        which the betweenness adversary's d+1 figure must be read.
        """
        g = self.topo.graph
        rear = [n for n, r in self.topo.node_roles.items() if r == "rear"]
        fwd = [n for n, r in self.topo.node_roles.items() if r == "forward"]
        order: List[Tuple[str, str]] = []
        cuts: List[Tuple[int, List[Tuple[str, str]]]] = []
        if rear and fwd:
            for f in sorted(fwd):
                try:
                    cut = nx.minimum_edge_cut(g, rear[0], f)
                except Exception:
                    continue
                cuts.append((len(cut), [Topology.key(u, v) for u, v in cut]))
        for _, edges in sorted(cuts, key=lambda t: t[0]):
            for e in edges:
                if e not in order:
                    order.append(e)
        for e in self.topo.all_link_keys():
            if e not in order:
                order.append(e)
        return order

    # -- per-tick ---------------------------------------------------------
    def _tick_outages(self) -> None:
        dt = self.cfg.tick_s
        oc = self.cfg.outage
        for k in self.topo.all_link_keys():
            lk = self.topo.links[k]
            if k in self._adv_links and self.cfg.adversary.deny_classical:
                continue
                # Adversary-held: stays down. Must test membership in the
                # adversary set, NOT `lk.outage` -- keying off the outage flag
                # made every STOCHASTIC outage permanent too, so the whole
                # network died over a long horizon and availability collapsed
                # to zero for both fail modes. Caught by E6b returning an
                # impossible 0.0000 when a reachable forward post remained.
            if lk.outage:
                if self.rng_outage.random() < dt / oc.mean_outage_s:
                    lk.outage = False
            else:
                if self.rng_outage.random() < dt / oc.mean_uptime_s:
                    lk.outage = True

    def _tick_generate(self) -> None:
        dt = self.cfg.tick_s
        for k in self.topo.all_link_keys():
            rate = self.topo.links[k].current_rate_bps(self.cfg.physics)
            st = self.topo.links[k].state(self.cfg.physics)
            self.results.link_state_ticks[st.value] = (
                self.results.link_state_ticks.get(st.value, 0) + 1)
            if rate > 0.0:
                self.topo.stores[k].accumulate(rate * dt)

    def _tick_arrivals(self, t: float) -> None:
        for tc in self.traffic:
            n = self.rng_arrivals.poisson(tc.arrival_rate * self.cfg.tick_s)
            for _ in range(int(n)):
                src, dst = self._endpoints[
                    self.rng_pairs.integers(0, len(self._endpoints))]
                self.pending.append(Session(
                    sid=self._next_sid, cls=tc.name, arrival_t=t,
                    payload_bits=tc.payload_bits, src=src, dst=dst,
                    authorised_floor=tc.authorised_floor,
                    deadline_s=tc.deadline_s, priority=tc.priority))
                self._next_sid += 1

    # -- grade / path selection ------------------------------------------
    def _reservation_floors(self, priority: int) -> Optional[Dict]:
        """Per-class reservation floors above m_min.

        CITED, NOT CLAIMED: Mehic et al. IEEE/ACM ToN 28 (2020) define exactly
        this -- a per-link key store with M_min that only premium-class traffic
        may draw below; and Cheng/Sun/Ji (AIAI 2011) reserve key on intermediate
        relay nodes for their key-guaranteed class (QKRA).
        """
        if not self.cfg.reservation_floors:
            return None
        frac = {1: 0.0, 2: 0.20, 3: 0.40}.get(priority, 0.40)
        if frac <= 0.0:
            return None
        return {k: self.topo.stores[k].m_min
                + frac * (self.topo.stores[k].m_max
                          - self.topo.stores[k].m_min)
                for k in self.topo.all_link_keys()}

    def _path_ok_classical(self, path: Sequence[str]) -> bool:
        """G4 needs only the classical channel. A link in ABORT has a pristine
        classical channel -- only its quantum channel is unusable -- so PQC
        still traverses it. This is precisely why fallback buys availability."""
        return all(self.topo.links[lk].state(self.cfg.physics)
                   is not LinkState.OUTAGE
                   for lk in self.topo.path_links(path))

    def _try_grade(self, s: Session, grade: str, t: float) -> bool:
        """Attempt to serve `s` at `grade`. Returns True on success."""
        demand = quantum_key_demand(grade, s.payload_bits)
        floors = self._reservation_floors(s.priority)

        if demand == 0:  # G4: no quantum key at all
            paths = candidate_paths(self.topo, s.src, s.dst)
            for p in paths:
                if self._path_ok_classical(p):
                    s.outcome = Outcome.SERVED
                    s.grade = grade
                    s.served_t = t + self.cfg.pqc_setup_s
                    s.hops = len(p) - 1
                    s.key_bits = 0.0
                    return True
            return False

        if self.cfg.routing == "SP":
            paths = candidate_paths(self.topo, s.src, s.dst)
            path = select_path_sp(self.topo, paths, demand, self.cfg)
        else:
            paths = candidate_paths(self.topo, s.src, s.dst)
            path = select_path_kar(self.topo, paths, demand, self.cfg, floors)
        if path is None:
            return False

        lks = self.topo.path_links(path)
        per_hop = self.cfg.accounting.cost_per_hop(demand)

        # All-or-nothing check first. A relay that fails at hop k has already
        # spent pads on hops 1..k-1 (ETSI GS QKD 020 ack_status: failed / key
        # not present), so we check before committing to avoid modelling a
        # partial debit we do not then account for.
        for lk in lks:
            floor = None if floors is None else floors.get(lk)
            if not self.topo.stores[lk].can_take(per_hop, floor):
                return False

        for lk in lks:
            floor = None if floors is None else floors.get(lk)
            ok = self.topo.stores[lk].take(per_hop, floor)
            assert ok, "affordability check passed but debit failed"

        s.outcome = Outcome.SERVED
        s.grade = grade
        s.served_t = t
        s.hops = len(lks)
        s.key_bits = per_hop * len(lks)
        return True

    def _serve_or_wait(self, s: Session, t: float) -> None:
        """Serve at the cheapest grade policy allows; degrade or block below it.

        Policy: target the authorised floor. Grades stronger than the floor
        cost strictly more key and buy the flow nothing it is authorised to
        need, so over-provisioning is not attempted.
        """
        floor_idx = grade_rank(s.authorised_floor)

        # Learned policy, if present, replaces ONLY the grade choice.
        if self.grade_policy is not None:
            want = self.grade_policy(s, self)
            if want is None:
                return  # defer to a later tick
            if self._try_grade(s, want, t):
                if not is_at_least(want, s.authorised_floor):
                    s.floor_violation = True
                return
            return

        # 1. try the authorised floor exactly.
        if self._try_grade(s, s.authorised_floor, t):
            return

        # 2. below the floor. This is the fail-mode fork.
        if self.cfg.fail_mode == "FAIL_CLOSED":
            # Spooren et al. IEEE QCNC 2026: "a fail-safe mechanism prevents
            # downgrade attacks, where the data tunnel is interrupted after a
            # defined time." We do not serve; the session waits and blocks on
            # deadline expiry.
            return

        if self.cfg.fail_mode != "FAIL_DEGRADED":
            raise ValueError(f"unknown fail_mode {self.cfg.fail_mode!r}")

        # ITU-T Y.3803 cl. 8.2.3 / Req_KM 7: "If the necessary number of keys
        # for OTP-encrypted key relay is not available, a backup method with
        # symmetric key cipher such as AES can be used for key relay." The
        # method is recorded in KMA metadata -- so the grade is knowable at the
        # key store, and we surface it as a first-class auditable event.
        for weaker in GRADE_ORDER[floor_idx + 1:]:
            if self._try_grade(s, weaker, t):
                s.floor_violation = True
                return

    def _tick_serve(self, t: float) -> None:
        # strict priority, then FIFO within a class
        self.pending.sort(key=lambda s: (s.priority, s.arrival_t, s.sid))
        still: List[Session] = []
        for s in self.pending:
            self._serve_or_wait(s, t)
            if s.outcome is Outcome.SERVED:
                self.results.sessions.append(s)
                continue
            if t - s.arrival_t >= s.deadline_s:
                s.outcome = Outcome.BLOCKED
                self.results.sessions.append(s)
                continue
            still.append(s)
        self.pending = still

    # -- run --------------------------------------------------------------
    def run(self) -> Results:
        t = 0.0
        while t < self.cfg.horizon_s:
            self._tick_outages()
            self._tick_generate()
            self._tick_arrivals(t)
            self._tick_serve(t)
            t += self.cfg.tick_s

        # flush anything still pending as blocked
        for s in self.pending:
            s.outcome = Outcome.BLOCKED
            self.results.sessions.append(s)
        self.pending = []

        r = self.results
        for k in self.topo.all_link_keys():
            st = self.topo.stores[k]
            r.generated_bits += st.generated_bits
            r.consumed_bits += st.consumed_bits
            r.discarded_bits += st.discarded_bits
        return r


def run_once(topo_factory, cfg: SimConfig) -> Results:
    topo = topo_factory(cfg.reservoir)
    return Simulator(topo, cfg).run()
