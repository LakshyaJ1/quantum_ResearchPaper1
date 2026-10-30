"""Behavioral tests for arrival-budgeted grade selection.

The tiny real simulations have hand-counted costs and no random arrivals.
"""
import importlib
import importlib.util
import pickle
from dataclasses import replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from qkdsim.config import ReservoirConfig, SimConfig
from qkdsim.network import chain_topology
from qkdsim.sim import Outcome, Session, Simulator


def policies():
    assert importlib.util.find_spec('revision.policies') is not None, (
        'arrival-budgeted policy implementation is missing')
    return importlib.import_module('revision.policies')


def request(sid=0, cls='ISR', floor='G1', deadline=100, arrival=0):
    return Session(sid, cls, arrival, 144000, 'N0', 'N1', floor, deadline, 1)


def simulation(spendable=0, rate=0, routing='KAR'):
    reservoir = ReservoirConfig(m_min=10, m_thr=1010, m_max=200010,
                                m_initial_frac=(spendable + 10) / 200010)
    cfg = SimConfig(horizon_s=3, warmup_s=0, reservoir=reservoir, routing=routing)
    sim = Simulator(chain_topology(1, reservoir), cfg, traffic=())
    sim.now_s = 0.0
    sim.topo.link('N0', 'N1').nominal_rate_bps = rate
    return sim


@pytest.mark.parametrize('cls,floor,expected', [
    ('C2', 'G2', 0), ('ISR', 'G1', 5), ('LOG', 'G3', 5)])
def test_every_arrival_prefix_obeys_its_class_exception_budget(cls, floor, expected):
    # Removing projection or counting served requests as arrivals breaks this.
    module = policies()
    policy = module.BudgetedTablePolicy([3] * 18)
    sim = simulation()
    sim.grade_policy = policy
    for n in range(1, 51):
        sim.now_s = float(n - 1)
        sim.pending.append(request(n, cls, floor, arrival=sim.now_s))
        sim._tick_serve(sim.now_s)
        violations = sum(s.floor_violation for s in sim.results.sessions)
        assert violations <= (0 if cls == 'C2' else n // 10)
    assert sum(s.floor_violation for s in sim.results.sessions) == expected


def test_pending_arrivals_authorize_only_their_fixed_budget():
    module = policies()
    policy = module.BudgetedTablePolicy([3] * 18)
    sim = simulation()
    sim.grade_policy = policy
    sim.pending = [request(i) for i in range(20)]
    sim._tick_serve(0)
    assert len(sim.results.sessions) == 2
    assert len(sim.pending) == 18
    assert policy.snapshot(sim)['arrivals']['ISR'] == 20
    assert policy.snapshot(sim)['violations']['ISR'] == 2


def test_unsuccessful_grade_attempts_do_not_spend_exceptions():
    module = policies()
    policy = module.BudgetedTablePolicy([3] * 18)
    sim = simulation()
    sim.grade_policy = policy
    sim.pending = [request(i) for i in range(10)]
    sim.topo.link('N0', 'N1').outage = True
    sim._tick_serve(0)
    assert policy.snapshot(sim)['violations']['ISR'] == 0
    sim.topo.link('N0', 'N1').outage = False
    sim.now_s = 1
    sim._tick_serve(1)
    assert len(sim.results.sessions) == 1
    assert policy.snapshot(sim)['violations']['ISR'] == 1


@pytest.mark.parametrize('policy_name', ['StrictFloorPolicy', 'BudgetGreedyPolicy'])
def test_baselines_enforce_the_same_c2_floor(policy_name):
    module = policies()
    sim = simulation()
    sim.grade_policy = getattr(module, policy_name)()
    sim.pending = [request(i, 'C2', 'G2') for i in range(20)]
    sim._tick_serve(0)
    assert not sim.results.sessions
    assert all(s.outcome is Outcome.PENDING for s in sim.pending)


def test_greedy_uses_strongest_affordable_fallback_without_mutating_store():
    module = policies()
    sim = simulation(spendable=750)
    sim.pending = [request(i) for i in range(10)]
    policy = module.BudgetGreedyPolicy()
    assert policy(sim.pending[0], sim) == 'G2'
    assert sim.topo.store('N0', 'N1').level == 760


def test_direct_g2_is_projected_when_no_exception_is_available():
    module = policies()
    sim = simulation(spendable=750)
    policy = module.BudgetedTablePolicy([4] * 18)
    sim.pending = [request()]
    assert policy(sim.pending[0], sim) == 'G1'


def test_defer_never_changes_the_session_or_store():
    module = policies()
    sim = simulation(spendable=150000)
    policy = module.BudgetedTablePolicy([2] * 18)
    s = request()
    assert policy(s, sim) is None
    assert s.outcome is Outcome.PENDING
    assert sim.topo.store('N0', 'N1').level == 150010


@pytest.mark.parametrize('spendable,rate,now,expected', [
    (144494, 0, 0, 6), (144494, 0, 80, 7),
    (0, 2000, 0, 8), (0, 10000, 80, 9),
    (0, 0, 0, 10), (0, 0, 80, 11)])
def test_state_distinguishes_affordability_refill_and_deadline_urgency(
        spendable, rate, now, expected):
    # ISR is class 1. Its 144494-bit floor can refill in 72.247 seconds
    # at 2000 bit/s, or 14.4494 seconds at 10000 bit/s.
    module = policies()
    sim = simulation(spendable=spendable, rate=rate)
    sim.now_s = now
    assert module.state_index(request(), sim) == expected


def test_transport_loss_cannot_be_mistaken_for_refill_feasibility():
    module = policies()
    sim = simulation(spendable=150000, rate=1e6)
    sim.topo.link('N0', 'N1').outage = True
    assert module.state_index(request(), sim) == 10


def test_grade_that_finishes_after_deadline_is_not_affordable():
    module = policies()
    sim = simulation(spendable=622)
    s = request(cls='LOG', floor='G3', deadline=0.2)
    assert module.state_index(s, sim) == 16


def test_policy_can_be_pickled_for_worker_processes_and_reused_on_a_new_run():
    module = policies()
    policy = pickle.loads(pickle.dumps(module.BudgetedTablePolicy([3] * 18)))
    first = simulation()
    first.grade_policy = policy
    first.pending = [request(i) for i in range(10)]
    first._tick_serve(0)
    assert policy.snapshot(first)['violations']['ISR'] == 1
    second = simulation()
    second.pending = [request(0)]
    assert policy(second.pending[0], second) == 'G1'
    assert policy.snapshot(second)['arrivals']['ISR'] == 1


@pytest.mark.parametrize('table,budgets', [
    ([0] * 17, None), ([5] * 18, None), ([0] * 18, {'ISR': -0.1}),
    ([0] * 18, {'LOG': 1.1}), ([0] * 18, {'C2': 0.1})])
def test_invalid_policy_contract_is_rejected_before_simulation(table, budgets):
    module = policies()
    with pytest.raises(ValueError):
        module.BudgetedTablePolicy(table, budgets=budgets)


if __name__ == '__main__':
    # The local pytest launcher intermittently terminates with a Windows native
    # exception. Exercise these same functions through unittest as a fallback.
    import unittest

    class DirectPolicyTests(unittest.TestCase):
        pass

    for name, function in list(globals().items()):
        if not name.startswith('test_') or not callable(function):
            continue
        marks = [m for m in getattr(function, 'pytestmark', [])
                 if m.name == 'parametrize']
        cases = marks[0].args[1] if marks else [()]
        for number, args in enumerate(cases):
            arguments = args if isinstance(args, tuple) else (args,)
            def run(self, fn=function, values=arguments):
                fn(*values)
            setattr(DirectPolicyTests, f'{name}_{number}', run)
    del function
    unittest.main(verbosity=2)
