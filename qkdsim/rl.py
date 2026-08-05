"""Policy-space audit: is the hand-designed heuristic near-optimal in-model?


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
