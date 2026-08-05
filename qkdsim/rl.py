"""Policy-space audit: is the hand-designed heuristic near-optimal in-model?

FRAMING (PHASE2_DESIGN section 12). Learned ROUTING for key-scarce QKD networks
is saturated -- Johann et al. Photonics 13:198 (2026) already do DRL with graph
attention and cross-topology generalisation; Hao et al. Photonics 12:969 (2025),
Xie et al. Opt. Express (2025), Sharma et al. IET QC 4(3) (2023), Seok et al.
JNSM 33:30 (2025) and Zuo et al. ACP 2020 fill in the rest. Learned ADMISSION
control is saturated in classical networking (survey: Khani et al., Int. J.
Commun. Syst., 2024). We therefore do not claim a better router.

What is NOT occupied: a learned policy over the ASSURANCE GRADE, driven by
information-theoretic key-reservoir exhaustion, per traffic class, under a hard
safety constraint. The closest prior art is Premakumari et al., Sensors
25:2056 (2025), whose action is an encryption level -- but driven by a threat
classifier, with no QKD, no trusted relay and no traffic classes.

The claim is deliberately narrow and falsifiable:

    Within model M, the hand-designed heuristic attains X% of the best policy
    discoverable in M under a hard constraint on command traffic.

That is a statement about our design's HEADROOM, not about the world. It has
the same epistemic status as every other simulation result in the paper, and
that parity is the argument against the circularity objection.

METHOD CHOICE. We use direct policy search (cross-entropy method) over a small
tabular policy, evaluated by the actual simulator, rather than a DQN. Three
reasons, all of which strengthen the paper:
  1. No credit-assignment hand-waving. Serving a session now depletes key for
     later; a myopic learner would need an invented opportunity-cost term. Here
     every candidate policy is scored by a FULL simulation rollout, so the
     sequential key economy is evaluated exactly.
  2. The searched policy class is auditable BY CONSTRUCTION -- a 12-cell lookup
     table an operator can read. We therefore do not need VIPER/CART policy
     distillation to obtain interpretability, which is a stronger position than
     distilling an opaque network and reporting fidelity loss.
  3. It runs on CPU in minutes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .config import (GRADE_ORDER, G1_OTP, G2_QKD_SYM, G3_HYBRID, G4_PQC,
                     SimConfig, grade_rank, is_at_least, quantum_key_demand)
from .network import candidate_paths
from .sim import Outcome, Results, Session, Simulator

DEFER = 4
ACTIONS: Tuple[str, ...] = (G1_OTP, G2_QKD_SYM, G3_HYBRID, G4_PQC)
ACTION_NAMES: Tuple[str, ...] = ACTIONS + ("DEFER",)

CLASSES: Tuple[str, ...] = ("C2", "ISR", "LOG")
N_OCC = 4
N_STATES = len(CLASSES) * N_OCC


# ---------------------------------------------------------------------------
# state
# ---------------------------------------------------------------------------
def occupancy_bucket(sim: Simulator, s: Session) -> int:
    """Bottleneck reservoir occupancy on the shortest path, bucketed 0..3.

    Deliberately POLICY-INDEPENDENT: computed on the shortest path at fixed
    granularity so that the state does not depend on the grade the policy is
    about to choose (which would make the encoding circular).

    0 : at or below the authentication reserve (m_min)  -- starved
    1 : below the refill threshold (m_thr)              -- WARNING/CHARGING
    2 : above threshold, below 60% of capacity
    3 : above 60% of capacity                           -- comfortable
    """
    paths = candidate_paths(sim.topo, s.src, s.dst)
    if not paths:
        return 0
    lks = sim.topo.path_links(paths[0])
    worst = 1.0
    for lk in lks:
        st = sim.topo.stores[lk]
        worst = min(worst, st.available() / max(st.m_max - st.m_min, 1.0))
    store0 = sim.topo.stores[lks[0]]
    thr_frac = (store0.m_thr - store0.m_min) / max(store0.m_max - store0.m_min, 1.0)
    if worst <= 0.0:
        return 0
    if worst < thr_frac:
        return 1
    return 2 if worst < 0.60 else 3


def state_index(s: Session, sim: Simulator) -> int:
    ci = CLASSES.index(s.cls) if s.cls in CLASSES else 0
    return ci * N_OCC + occupancy_bucket(sim, s)


def state_label(idx: int) -> str:
    ci, occ = divmod(idx, N_OCC)
    names = ["starved(<=m_min)", "warning(<m_thr)", "mid(<60%)", "ample(>=60%)"]
    return f"{CLASSES[ci]:<4} | {names[occ]}"


# ---------------------------------------------------------------------------
# shield
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Shield:
    """Hard, deterministic action mask -- NOT a reward penalty.

    We concede up front that the guarantee comes from the shield, which is
    verifiable by inspection; learning only searches inside it. Conceding this
    pre-empts the "your shield is the policy" objection instead of inviting it.

    Constraint: command (C2) traffic may never be assigned below G2, i.e. never
    without an information-theoretically delivered key. The reservoir's m_min
    authentication reserve is enforced independently inside KeyStore.take(), so
    the shield does not need to restate it.
    """

    enabled: bool = True
    c2_floor: str = G2_QKD_SYM

    def allowed(self, s: Session) -> Tuple[int, ...]:
        acts = tuple(range(len(ACTION_NAMES)))
        if not self.enabled or s.cls != "C2":
            return acts
        return tuple(a for a in acts
                     if a == DEFER or is_at_least(ACTIONS[a], self.c2_floor))


# ---------------------------------------------------------------------------
# policy
# ---------------------------------------------------------------------------
class TablePolicy:
    """State -> action lookup table. Picklable as a plain tuple of ints."""

    __slots__ = ("table", "shield")

    def __init__(self, table: Sequence[int], shield: Shield = Shield()):
        self.table = tuple(int(x) for x in table)
        self.shield = shield

    def __call__(self, s: Session, sim: Simulator) -> Optional[str]:
        a = self.table[state_index(s, sim)]
        ok = self.shield.allowed(s)
        if a not in ok:
            # project onto the shield: strongest permitted grade, else defer
            grades = [x for x in ok if x != DEFER]
            a = min(grades, key=lambda x: grade_rank(ACTIONS[x])) if grades else DEFER
        return None if a == DEFER else ACTIONS[a]

    def as_rows(self) -> List[Tuple[str, str]]:
        return [(state_label(i), ACTION_NAMES[a]) for i, a in enumerate(self.table)]


def heuristic_table() -> Tuple[int, ...]:
    """The hand-designed heuristic expressed in the SAME policy class, so the
    comparison is apples-to-apples: serve at the authorised floor, degrade one
    step when the reservoir is starved."""
    floors = {"C2": G2_QKD_SYM, "ISR": G1_OTP, "LOG": G3_HYBRID}
    tab: List[int] = []
    for c in CLASSES:
        fl = floors[c]
        for occ in range(N_OCC):
            if occ == 0:                     # starved -> degrade one step
                idx = min(grade_rank(fl) + 1, len(ACTIONS) - 1)
            else:
                idx = grade_rank(fl)
            tab.append(idx)
    return tuple(tab)


# ---------------------------------------------------------------------------
# objective
# ---------------------------------------------------------------------------
def objective(r: Results, lam_viol: float = 0.5, w_its: float = 0.5) -> float:
    """J = availability - lam*floor_violations + w*ITS-delivered share.

    Stated explicitly because a learned policy's score is meaningless without
    it. Components are always reported alongside J so a reader can reweight.
    """
    av = r.served_fraction()
    fv = r.floor_violation_fraction()
    its = 1.0 - r.below_its_fraction()
    if av != av:
        return -1e9
    fv = 0.0 if fv != fv else fv
    its = 0.0 if its != its else its
    return av - lam_viol * fv + w_its * its


def score_components(r: Results) -> Dict[str, float]:
    return {"J": objective(r), "avail": r.served_fraction(),
            "viol": r.floor_violation_fraction(),
            "its_share": 1.0 - r.below_its_fraction(),
            "c2_below_its": r.below_its_fraction("C2"),
            "key_Mbit": r.consumed_bits / 1e6}
