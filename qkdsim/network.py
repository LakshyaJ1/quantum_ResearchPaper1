"""Topologies and routing policies.

SP and KAR are REPRODUCED BASELINES, cited not claimed. Key-availability-aware
routing in trusted-relay QKD networks is an established literature:
  van Duijn et al., ONDM 2024      -- SPF/SPF+/ADA-KGR/ADA-KEYS/OSKAR compared
  Johann et al., JOCN 16(3), 2024  -- five routing methods compared
  Hao et al., Photonics 12:969     -- Q-learning vs SPF and max-residual-key
  Yang et al., China Commun. 2018  -- OSKAR secret-key-aware routing
  Cao et al., Opt. Express 25:26453 (2017) -- KoD, key pools with MAX/MIN/WARN
  Cvitic et al., arXiv:2511.15465  -- survey of 26 strategies

The published field-level headline is that key-aware dynamic routing reduces
service rejection by 25-40% versus static shortest path. We must not appear to
rediscover it.

CRITICAL NULL RESULT TO REPRODUCE: van Duijn et al. found differences AMONG
resource-aware strategies to be statistically insignificant (Welch's t-test)
under centralised routing, and recommended the cheap SPF+ variant. A reviewer
who knows that paper will ask why our policies should separate at all. E2
answers it pre-emptively.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import networkx as nx

from .config import LINK_CLASSES, PhysicsConfig, ReservoirConfig, SimConfig
from .physics import KeyStore, Link


@dataclass
class Topology:
    graph: nx.Graph
    links: Dict[Tuple[str, str], Link]
    stores: Dict[Tuple[str, str], KeyStore]
    node_roles: Dict[str, str]
    path_cache: Dict[Tuple[str, str], List[List[str]]] = field(default_factory=dict)
    """Candidate paths are a function of the graph only, and the graph is static
    (link *state* varies, topology does not). Enumerating simple paths per
    pending session per tick dominated runtime, so it is cached once."""
    _link_cache: Dict[Tuple[str, ...], List[Tuple[str, str]]] = field(default_factory=dict)

    @staticmethod
    def key(u: str, v: str) -> Tuple[str, str]:
        """Canonical undirected link key. One shared pad per link -- both
        endpoints mark the SAME bits consumed, so there is exactly one debit
        per link per relay, never one per endpoint."""
        return (u, v) if u <= v else (v, u)

    def link(self, u: str, v: str) -> Link:
        return self.links[self.key(u, v)]

    def store(self, u: str, v: str) -> KeyStore:
        return self.stores[self.key(u, v)]

    def path_links(self, path: Sequence[str]) -> List[Tuple[str, str]]:
        tp = tuple(path)
        got = self._link_cache.get(tp)
        if got is None:
            got = [self.key(path[i], path[i + 1]) for i in range(len(path) - 1)]
            self._link_cache[tp] = got
        return got

    def all_link_keys(self) -> List[Tuple[str, str]]:
        return sorted(self.links.keys())


def _build(edges: Sequence[Tuple[str, str, str]],
           roles: Dict[str, str],
           res: ReservoirConfig) -> Topology:
    g = nx.Graph()
    links: Dict[Tuple[str, str], Link] = {}
    stores: Dict[Tuple[str, str], KeyStore] = {}
    for u, v, cls in edges:
        k = Topology.key(u, v)
        lc = LINK_CLASSES[cls]
        g.add_edge(u, v, link_class=cls, rate=lc.rate_bps)
        links[k] = Link(name=f"{k[0]}-{k[1]}", endpoints=k,
                        nominal_rate_bps=lc.rate_bps, link_class=cls)
        stores[k] = KeyStore(res)
    return Topology(graph=g, links=links, stores=stores, node_roles=dict(roles))


def formation_9node(res: ReservoirConfig) -> Topology:
    """T1: nine-node tactical formation. Main policy comparison.

    BASE (rear area) - REL1/REL2 (relays) - BDE1/BDE2 (brigade) -
    FWD1..FWD3 (forward posts). One fibre backbone segment, the rest free-space
    optical hops of three grades. Path diversity is deliberate: without it, a
    key-aware policy has nothing to choose between and the comparison is void.
    """
    edges = [
        ("BASE", "REL1", "FIBRE"),
        ("BASE", "REL2", "FSO_NOMINAL"),
        ("REL1", "REL2", "FSO_LATERAL"),
        ("REL1", "BDE1", "FSO_NOMINAL"),
        ("REL2", "BDE2", "FSO_NOMINAL"),
        ("BDE1", "BDE2", "FSO_LATERAL"),
        ("BDE1", "FWD1", "FSO_SHORT"),
        ("BDE1", "FWD2", "FSO_NOMINAL"),
        ("BDE2", "FWD3", "FSO_SHORT"),
    ]
    roles = {"BASE": "rear", "REL1": "relay", "REL2": "relay",
             "BDE1": "brigade", "BDE2": "brigade",
             "FWD1": "forward", "FWD2": "forward", "FWD3": "forward"}
    return _build(edges, roles, res)


def chain_topology(depth: int, res: ReservoirConfig) -> Topology:
    """T2: parametric relay chain of `depth` hops, plus one lateral alternate.

    Isolates the interaction between the hop multiplier and adversarial
    pressure, which is the axis for the downgrade-forcing-cost experiment.
    """
    if depth < 1:
        raise ValueError("depth must be >= 1")
    edges: List[Tuple[str, str, str]] = []
    roles: Dict[str, str] = {"N0": "rear"}
    for i in range(depth):
        edges.append((f"N{i}", f"N{i+1}", "FSO_NOMINAL"))
        roles[f"N{i+1}"] = "forward" if i == depth - 1 else "relay"
    # one alternate path of depth+1 hops via A-nodes, so a key-aware policy has
    # a real choice; longer, so choosing it costs more key on every hop.
    if depth >= 2:
        edges.append(("N0", "A1", "FSO_LATERAL"))
        roles["A1"] = "relay"
        prev = "A1"
        for i in range(1, depth):
            nxt = f"A{i+1}"
            edges.append((prev, nxt, "FSO_LATERAL"))
            roles[nxt] = "relay"
            prev = nxt
        edges.append((prev, f"N{depth}", "FSO_LATERAL"))
    return _build(edges, roles, res)


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def candidate_paths(topo: Topology, src: str, dst: str,
                    max_paths: int = 4, max_extra_hops: int = 2
                    ) -> List[List[str]]:
    """Simple paths from src to dst, shortest first, bounded.

    Bounded because every extra hop consumes key on an ADDITIONAL link -- path
    length is a key-budget decision, not merely a latency one.
    """
    ck = (src, dst)
    hit = topo.path_cache.get(ck)
    if hit is not None:
        return hit
    try:
        shortest = nx.shortest_path_length(topo.graph, src, dst)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        topo.path_cache[ck] = []
        return []
    out: List[List[str]] = []
    for p in nx.shortest_simple_paths(topo.graph, src, dst):
        if len(p) - 1 > shortest + max_extra_hops:
            break
        out.append(p)
        if len(out) >= max_paths:
            break
    topo.path_cache[ck] = out
    return out


def _usable(topo: Topology, lk: Tuple[str, str], phys: PhysicsConfig) -> bool:
    """A link in OUTAGE or ABORT carries no traffic and generates no key."""
    return topo.links[lk].current_rate_bps(phys) > 0.0


def select_path_sp(topo: Topology, paths: Sequence[Sequence[str]],
                   demand_bits: int, cfg: SimConfig) -> Sequence[str] | None:
    """Minimum-hop path. The baseline every prior work compares against."""
    for p in paths:
        lks = topo.path_links(p)
        if all(_usable(topo, lk, cfg.physics) for lk in lks):
            return p
    return None


def select_path_kar(topo: Topology, paths: Sequence[Sequence[str]],
                    demand_bits: int, cfg: SimConfig,
                    floors: Dict[Tuple[str, str], float] | None = None
                    ) -> Sequence[str] | None:
    """Key-availability-aware: minimise bottleneck expected time-to-key.

    For each hop the shortfall is (cost_per_hop(demand) - available)+, and the
    time to cover it is shortfall / current_rate. The path cost is the worst
    hop plus a per-hop penalty, because the hop multiplier makes every extra
    hop a real key expenditure.

    This is the OSKAR/ADA-KEYS family (Yang 2018; van Duijn 2024), reproduced.
    """
    best: Sequence[str] | None = None
    best_cost = float("inf")
    for p in paths:
        lks = topo.path_links(p)
        if not all(_usable(topo, lk, cfg.physics) for lk in lks):
            continue
        need = cfg.accounting.cost_per_hop(demand_bits)
        worst_ttk = 0.0
        feasible = True
        for lk in lks:
            store = topo.stores[lk]
            floor = None if floors is None else floors.get(lk)
            avail = store.available(floor)
            shortfall = max(0.0, need - avail)
            if shortfall <= 0.0:
                continue
            rate = topo.links[lk].current_rate_bps(cfg.physics)
            if rate <= 0.0:
                feasible = False
                break
            worst_ttk = max(worst_ttk, shortfall / rate)
        if not feasible:
            continue
        cost = worst_ttk + cfg.hop_penalty * len(lks)
        if cost < best_cost:
            best_cost, best = cost, p
    return best


def select_path(topo: Topology, src: str, dst: str, demand_bits: int,
                cfg: SimConfig,
                floors: Dict[Tuple[str, str], float] | None = None
                ) -> Sequence[str] | None:
    paths = candidate_paths(topo, src, dst)
    if not paths:
        return None
    if cfg.routing == "SP":
        return select_path_sp(topo, paths, demand_bits, cfg)
    if cfg.routing == "KAR":
        return select_path_kar(topo, paths, demand_bits, cfg, floors)
    raise ValueError(f"unknown routing policy {cfg.routing!r}")
