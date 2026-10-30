from dataclasses import replace

import networkx as nx
import pytest

from qkdsim.config import ReservoirConfig
from revision.scenarios import Case, build_topology, attack_order, make_simulator


@pytest.mark.parametrize('name,cut', [('ring', 2), ('grid', 2), ('parallel3', 3), ('parallel4', 4)])
def test_declared_terminal_connectivity(name, cut):
    topo = build_topology(name, ReservoirConfig())
    rear = next(n for n, r in topo.node_roles.items() if r == 'rear')
    terminal = next(n for n, r in topo.node_roles.items() if r == 'forward')
    assert nx.edge_connectivity(topo.graph, rear, terminal) == cut


def test_weighted_cut_avoids_costly_backbone_when_cheaper_complete_cut_exists():
    topo = build_topology('formation', ReservoirConfig())
    order, costs, cut = attack_order(topo, 'weighted_cut', 10.0)
    assert sum(costs[k] for k in cut) == 2
    assert all(topo.links[k].link_class != 'FIBRE' for k in cut)
    assert set(order[:len(cut)]) == set(cut)


def test_quantum_denial_is_not_classical_denial():
    base = Case(horizon_s=20, outage_model='none', attack_budget=2,
                topology='ring', attack_start_s=0, attack_duration_s=20)
    quantum = make_simulator(base, 11)
    classical = make_simulator(replace(base, attack_surface='transport'), 11)
    quantum._tick_outages()
    classical._tick_outages()
    assert all(not quantum.topo.links[k].outage for k in quantum._adv_links)
    assert all(classical.topo.links[k].outage for k in classical._adv_links)
    assert all(quantum.topo.links[k].current_rate_bps(quantum.cfg.physics) == 0
               for k in quantum._adv_links)


def test_environment_and_arrivals_match_attack_counterfactual():
    base = Case(horizon_s=200, outage_model='correlated', mean_uptime_s=10,
                mean_outage_s=5, attack_budget=0, topology='ring')
    clean = make_simulator(base, 21)
    attacked = make_simulator(replace(base, attack_budget=2), 21)
    for tick in range(40):
        clean._tick_outages()
        attacked._tick_outages()
        assert clean.environment_transport == attacked.environment_transport
        assert clean.environment_generation == attacked.environment_generation
        clean._tick_arrivals(float(tick))
        attacked._tick_arrivals(float(tick))
    assert [(s.sid, s.cls, s.src, s.dst, s.arrival_t) for s in clean.pending] == [
        (s.sid, s.cls, s.src, s.dst, s.arrival_t) for s in attacked.pending]


def test_attack_release_restores_generation_without_erasing_stock():
    case = Case(horizon_s=20, outage_model='none', attack_budget=2,
                topology='ring', attack_duration_s=2)
    sim = make_simulator(case, 31)
    before = {k: s.level for k, s in sim.topo.stores.items()}
    sim._tick_outages()
    sim._tick_outages()
    sim._tick_outages()
    assert not sim._adv_links
    assert all(l.current_rate_bps(sim.cfg.physics) > 0 for l in sim.topo.links.values())
    assert before == {k: s.level for k, s in sim.topo.stores.items()}


def test_explicit_purge_policy_discards_spendable_stock_once():
    case = Case(horizon_s=20, outage_model='none', attack_budget=2,
                topology='ring', buffer_policy='purge')
    sim = make_simulator(case, 31)
    sim._tick_outages()
    purged = sim.purged_bits
    assert purged > 0
    assert all(sim.topo.stores[k].available() == 0 for k in sim._adv_links)
    sim._tick_outages()
    assert sim.purged_bits == purged
