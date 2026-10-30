"""Two scenario options the submitted paper used and the revision Case lacks.

Class-aware reservation floors and depth-d relay chains. The corrected simulator
(qkdsim 0.2.0 + revision.scenarios) is otherwise used unchanged; make_cr_simulator
mirrors revision.scenarios.make_simulator line for line apart from those options.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from qkdsim.config import (AccountingConfig, AdversaryConfig, OutageConfig,
                           PhysicsConfig, ReservoirConfig, SimConfig, TRAFFIC_CLASSES)
from qkdsim.network import chain_topology
from revision.scenarios import Case, RevisionSimulator, build_topology

FLOOR_FRACTIONS = {1: 0.0, 2: 0.20, 3: 0.40}   # qkdsim/sim.py _reservation_floors


@dataclass(frozen=True)
class CRCase(Case):
    reservation_floors: bool = False
    floor_scale: float = 1.0


def build_cr_topology(name: str, res: ReservoirConfig):
    if name.startswith('chain'):
        return chain_topology(int(name[5:]), res)
    return build_topology(name, res)


class CRSimulator(RevisionSimulator):
    def _reservation_floors(self, priority):
        if not self.case.reservation_floors:
            return None
        frac = min(1.0, FLOOR_FRACTIONS.get(priority, 0.40) * self.case.floor_scale)
        if frac <= 0.0:
            return None
        return {k: self.topo.stores[k].m_min
                + frac * (self.topo.stores[k].m_max - self.topo.stores[k].m_min)
                for k in self.topo.all_link_keys()}


def make_cr_simulator(case: CRCase, seed: int) -> CRSimulator:
    if not 0 <= case.initial_spendable_fraction <= 1:
        raise ValueError('Initial spendable fraction must be in [0,1]')
    if case.fallback not in ('online_kem', 'preplaced_symmetric'):
        raise ValueError(case.fallback)
    if case.buffer_policy not in ('retain', 'purge'):
        raise ValueError(case.buffer_policy)
    base = ReservoirConfig()
    scale = case.reservoir_scale
    minimum, maximum = round(base.m_min * scale), round(base.m_max * scale)
    initial = minimum + case.initial_spendable_fraction * (maximum - minimum)
    reservoir = replace(base, m_min=minimum, m_max=maximum,
                        m_thr=round(base.m_thr * scale), m_initial_frac=initial / maximum)
    cfg = SimConfig(horizon_s=case.horizon_s, warmup_s=case.warmup_s, seed=seed,
                    reservoir=reservoir, accounting=AccountingConfig(n_auth=case.n_auth),
                    physics=PhysicsConfig(e_abort=case.e_abort, gamma=case.gamma),
                    adversary=AdversaryConfig(budget_links=0),
                    outage=OutageConfig(), routing=case.routing,
                    reservation_floors=case.reservation_floors,
                    fail_mode=case.fail_mode,
                    pqc_setup_s=0.35 if case.fallback == 'online_kem' else 0.0)
    topo = build_cr_topology(case.topology, reservoir)
    for link in topo.links.values():
        link.nominal_rate_bps *= case.rate_scale
    traffic = tuple(replace(tc, arrival_rate=tc.arrival_rate * case.isr_scale)
                    if tc.name == 'ISR' else tc for tc in TRAFFIC_CLASSES)
    return CRSimulator(topo, cfg, case, traffic)
