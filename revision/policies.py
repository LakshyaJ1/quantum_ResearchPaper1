"""Interpretable policies with deterministic per-class exception budgets.

The guarantee is provided by the common runtime projection, not by policy search.
At every sequential service decision, confirmed below-floor deliveries cannot
exceed floor(epsilon[class] * all arrivals of that class so far). Pending and
blocked requests remain in the arrival count. Failed attempts spend no allowance.

This module predicts feasibility without consuming key or finalizing sessions.
The simulator alone attempts the returned grade. Refill estimates assume current
rates persist and ignore future competing consumption; they are state features,
not a promise that a deadline will be met.
"""
from __future__ import annotations

import math
import operator
from fractions import Fraction
from typing import Mapping, Optional, Sequence

from qkdsim.config import (GRADE_ORDER, G2_QKD_SYM, G3_HYBRID, G4_PQC,
                          grade_rank, is_at_least, quantum_key_demand)
from qkdsim.network import candidate_paths, select_path
from qkdsim.sim import Outcome


CLASSES = ('C2', 'ISR', 'LOG')
N_STATES = 18
ACTION_NAMES = ('floor', 'affordable_fallback', 'defer', 'G4', 'G2')
N_ACTIONS = len(ACTION_NAMES)
DEFAULT_BUDGETS = {'C2': 0.0, 'ISR': 0.1, 'LOG': 0.1}


def _grade_timing(session, sim, grade: str):
    """Return (affordable now, estimated refill-plus-setup time).

    Positive-QKD grades use the exact SP/KAR selector used by _try_grade().
    Classical-only service uses the same ordered candidate-path search.
    """
    remaining = session.arrival_t + session.deadline_s - sim.now_s
    setup = sim.cfg.pqc_setup_s if grade in (G3_HYBRID, G4_PQC) else 0.0
    if remaining + 1e-9 < setup:
        return False, math.inf
    demand = quantum_key_demand(grade, session.payload_bits)
    if demand == 0:
        paths = candidate_paths(sim.topo, session.src, session.dst)
        connected = any(all(not sim.topo.links[k].outage
                            for k in sim.topo.path_links(path)) for path in paths)
        return connected, setup if connected else math.inf

    floors = sim._reservation_floors(session.priority)
    path = select_path(sim.topo, session.src, session.dst, demand, sim.cfg, floors)
    if path is None:
        return False, math.inf
    cost = sim.cfg.accounting.cost_per_hop(demand)
    delay = 0.0
    affordable = True
    for edge in sim.topo.path_links(path):
        link, store = sim.topo.links[edge], sim.topo.stores[edge]
        if link.outage:
            return False, math.inf
        floor = None if floors is None else floors.get(edge)
        if store.can_take(cost, floor):
            continue
        affordable = False
        rate = link.current_rate_bps(sim.cfg.physics)
        if rate <= 0:
            return False, math.inf
        delay = max(delay, (cost - store.available(floor)) / rate)
    return affordable, delay + setup


def state_index(session, sim) -> int:
    """3 classes x 3 floor-feasibility states x 2 urgency states.

    Feasibility: 0 affordable now, 1 refill estimate within remaining deadline,
    2 otherwise. Urgent: at most 20% of the original deadline remains.
    """
    try:
        cls = CLASSES.index(session.cls)
    except ValueError as exc:
        raise ValueError(f'Unknown traffic class {session.cls!r}') from exc
    remaining = session.arrival_t + session.deadline_s - sim.now_s
    affordable, refill = _grade_timing(session, sim, session.authorised_floor)
    status = 0 if affordable else (1 if refill <= remaining + 1e-9 else 2)
    urgent = int(remaining <= 0.2 * session.deadline_s + 1e-9)
    return (cls * 3 + status) * 2 + urgent


def state_label(index: int) -> str:
    if not 0 <= index < N_STATES:
        raise ValueError(f'State index must be in [0, {N_STATES})')
    cls, rest = divmod(index, 6)
    status, urgency = divmod(rest, 2)
    name = ('affordable', 'refill_within_deadline', 'unfundable_now')[status]
    return f'{CLASSES[cls]} | {name} | {"urgent" if urgency else "not_urgent"}'


class _BudgetProjection:
    def __init__(self, budgets: Optional[Mapping[str, float]] = None):
        self.budgets = dict(DEFAULT_BUDGETS)
        if budgets is not None:
            if set(budgets) - set(CLASSES):
                raise ValueError('Budgets may only name C2, ISR, and LOG')
            self.budgets.update(budgets)
        if any(not math.isfinite(float(v)) or not 0 <= float(v) <= 1
               for v in self.budgets.values()):
            raise ValueError('Budgets must be finite fractions in [0, 1]')
        if self.budgets['C2'] != 0:
            raise ValueError('C2 has a strict zero-exception floor')
        self._fractions = {c: Fraction(str(v)) for c, v in self.budgets.items()}
        self._sim_id = None
        self._reset()

    def _reset(self):
        self.arrivals = {c: 0 for c in CLASSES}
        self.violations = {c: 0 for c in CLASSES}
        self._seen_arrivals = set()
        self._finalized_cursor = 0
        self._pending_stamp = None

    def _arrived(self, session):
        if session.cls not in self.arrivals:
            raise ValueError(f'Unknown traffic class {session.cls!r}')
        if session.sid not in self._seen_arrivals:
            self._seen_arrivals.add(session.sid)
            self.arrivals[session.cls] += 1

    def _observe(self, sim, session=None):
        if id(sim) != self._sim_id:
            self._reset()
            self._sim_id = id(sim)
        finalized = sim.results.sessions
        for i in range(self._finalized_cursor, len(finalized)):
            s = finalized[i]
            self._arrived(s)
            if s.outcome is Outcome.SERVED and not is_at_least(s.grade, s.authorised_floor):
                self.violations[s.cls] += 1
        self._finalized_cursor = len(finalized)
        # At most one pending-list scan per tick/list change/new arrival. This
        # avoids rescanning the full historical result list on every decision.
        stamp = (id(sim.pending), sim.now_s, sim._next_sid, len(sim.pending))
        if stamp != self._pending_stamp:
            for pending in sim.pending:
                if pending.arrival_t <= sim.now_s + 1e-9:
                    self._arrived(pending)
            self._pending_stamp = stamp
        if session is not None:
            self._arrived(session)

    def _cap(self, cls: str) -> int:
        # Rational arithmetic avoids flooring 0.1*30 below its intended value.
        return math.floor(self._fractions[cls] * self.arrivals[cls])

    def _allowed(self, session, sim, grade: str) -> bool:
        if is_at_least(grade, session.authorised_floor):
            return True
        if sim.cfg.fail_mode == 'FAIL_CLOSED':
            return False
        return self.violations[session.cls] < self._cap(session.cls)

    def _project(self, session, sim, grade: Optional[str]) -> Optional[str]:
        if grade is None or self._allowed(session, sim, grade):
            return grade
        return session.authorised_floor

    def _affordable_fallback(self, session, sim) -> Optional[str]:
        for grade in GRADE_ORDER[grade_rank(session.authorised_floor):]:
            if self._allowed(session, sim, grade) and _grade_timing(session, sim, grade)[0]:
                return grade
        return None

    def snapshot(self, sim=None):
        """Counters for reporting; pass sim to include its latest final outcome."""
        if sim is not None:
            self._observe(sim)
        return {'arrivals': dict(self.arrivals), 'violations': dict(self.violations),
                'caps': {c: self._cap(c) for c in CLASSES},
                'budgets': dict(self.budgets)}


class BudgetedTablePolicy(_BudgetProjection):
    """A pickleable 18-cell table projected through the common budget rule."""
    def __init__(self, table: Sequence[int], budgets: Optional[Mapping[str, float]] = None):
        try:
            self.table = tuple(operator.index(a) for a in table)
        except TypeError as exc:
            raise ValueError('Policy actions must be integers') from exc
        if len(self.table) != N_STATES or any(a < 0 or a >= N_ACTIONS for a in self.table):
            raise ValueError(f'Policy requires {N_STATES} actions in [0, {N_ACTIONS})')
        super().__init__(budgets)

    def __call__(self, session, sim) -> Optional[str]:
        self._observe(sim, session)
        action = self.table[state_index(session, sim)]
        if action == 0:
            proposed = session.authorised_floor
        elif action == 1:
            proposed = self._affordable_fallback(session, sim)
        elif action == 2:
            proposed = None
        elif action == 3:
            proposed = G4_PQC
        else:
            proposed = G2_QKD_SYM
        return self._project(session, sim, proposed)


class StrictFloorPolicy(_BudgetProjection):
    """Always attempt the authorized floor; never consume an exception."""
    def __call__(self, session, sim) -> str:
        self._observe(sim, session)
        return self._project(session, sim, session.authorised_floor)


class BudgetGreedyPolicy(_BudgetProjection):
    """Choose the strongest affordable grade within the same exception budget."""
    def __call__(self, session, sim) -> Optional[str]:
        self._observe(sim, session)
        return self._project(session, sim, self._affordable_fallback(session, sim))
