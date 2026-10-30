"""Regression tests for scientifically consequential simulator semantics.

Expected quantities in the small fixtures are hand-derived, not calculated by
the same production helpers. Run with python -m unittest discover -s tests -v.
"""
import unittest
from dataclasses import replace

from qkdsim.config import OutageConfig, ReservoirConfig, SimConfig
from qkdsim.network import candidate_paths, chain_topology, formation_9node
from qkdsim.physics import LinkState
from qkdsim.rl import Shield, TablePolicy
from qkdsim.sim import Outcome, Results, Session, Simulator


def request(sid=0, cls="C2", floor="G2", arrival=0, deadline=5, payload=2048):
    return Session(sid, cls, arrival, payload, "N0", "N1", floor, deadline, 1)


def setup_sim(**overrides):
    opts = dict(horizon_s=3, warmup_s=0,
                outage=OutageConfig(mean_uptime_s=1e12, mean_outage_s=1))
    opts.update(overrides)
    cfg = SimConfig(**opts)
    return Simulator(chain_topology(1, cfg.reservoir), cfg, traffic=())


class BufferedRelayTests(unittest.TestCase):
    def test_abort_suspends_generation_but_relay_spends_existing_stock(self):
        # Removing the distinction between production and transport breaks this.
        for routing in ("SP", "KAR"):
            with self.subTest(routing=routing):
                sim = setup_sim(routing=routing)
                link = sim.topo.link("N0", "N1")
                store = sim.topo.store("N0", "N1")
                link.excess_qber = 0.05
                self.assertEqual(link.state(sim.cfg.physics), LinkState.ABORT)
                sim._tick_generate()
                self.assertEqual(store.generated_bits, 0)
                self.assertTrue(sim._try_grade(request(), "G2", 0))
                self.assertEqual(store.level, 52_428_050)
                self.assertEqual(store.consumed_bits, 750)

    def test_zero_rate_only_blocks_when_stored_key_is_insufficient(self):
        sim = setup_sim(reservoir=ReservoirConfig(m_min=10, m_thr=500, m_max=1510))
        store = sim.topo.store("N0", "N1")
        sim.topo.link("N0", "N1").nominal_rate_bps = 0
        self.assertTrue(sim._try_grade(request(0), "G2", 0))
        self.assertTrue(sim._try_grade(request(1), "G2", 0))
        self.assertFalse(sim._try_grade(request(2), "G2", 0))
        self.assertEqual(store.level, 10)

    def test_outage_blocks_all_transport_and_retains_keys(self):
        sim = setup_sim()
        sim.topo.link("N0", "N1").outage = True
        for grade in ("G1", "G2", "G3", "G4"):
            self.assertFalse(sim._try_grade(request(), grade, 0))
        self.assertEqual(sim.topo.store("N0", "N1").level, 52_428_800)

    def test_aborted_short_path_can_be_used_but_not_refilled(self):
        cfg = SimConfig(horizon_s=3, warmup_s=0)
        sim = Simulator(chain_topology(2, cfg.reservoir), cfg, traffic=())
        for k in sim.topo.all_link_keys():
            sim.topo.links[k].excess_qber = 0.05
        req = replace(request(), dst="N2")
        self.assertTrue(sim._try_grade(req, "G2", 0))
        self.assertEqual(req.hops, 2)
        self.assertEqual(req.key_bits, 1500)


class DeadlineAndPolicyTests(unittest.TestCase):
    def test_session_is_not_served_after_its_deadline(self):
        sim = setup_sim()
        req = request(deadline=1)
        sim.pending = [req]
        sim._tick_serve(2)
        self.assertEqual(req.outcome, Outcome.BLOCKED)
        self.assertEqual(req.key_bits, 0)

    def test_pqc_and_hybrid_setup_must_fit_deadline_before_spending(self):
        for grade in ("G3", "G4"):
            with self.subTest(grade=grade):
                sim = setup_sim()
                short = request(deadline=0.2)
                self.assertFalse(sim._try_grade(short, grade, 0))
                self.assertEqual(sim.topo.store("N0", "N1").consumed_bits, 0)
                enough = request(deadline=0.35)
                self.assertTrue(sim._try_grade(enough, grade, 0))
                self.assertEqual(enough.ttk, 0.35)

    def test_fail_closed_applies_to_external_grade_policies(self):
        sim = setup_sim(fail_mode="FAIL_CLOSED")
        sim.grade_policy = lambda req, env: "G4"
        req = request()
        sim._serve_or_wait(req, 0)
        self.assertEqual(req.outcome, Outcome.PENDING)
        self.assertFalse(sim._try_grade(req, "G4", 0))

    def test_forbidden_shield_action_projects_to_floor_without_overprovision(self):
        sim = setup_sim()
        policy = TablePolicy([3] * 12, Shield())
        self.assertEqual(policy(request(), sim), "G2")

    def test_all_class_shield_uses_each_requests_authorized_floor(self):
        self.assertIn("all_class_floors", Shield.__dataclass_fields__)
        policy = TablePolicy([3] * 12, Shield(all_class_floors=True))
        sim = setup_sim()
        self.assertEqual(policy(request(cls="ISR", floor="G1"), sim), "G1")
        self.assertEqual(policy(request(cls="LOG", floor="G3"), sim), "G3")

    def test_arrival_cohort_gets_its_deadline_after_arrivals_stop(self):
        sim = setup_sim(horizon_s=1, fail_mode="FAIL_CLOSED",
                        reservoir=ReservoirConfig(m_min=0, m_thr=400, m_max=2000,
                                                  m_initial_frac=0))
        # 240 bit/s; request needs 750. Arrivals stop at t=1, but the cohort
        # may wait to t=3, where accumulated stock is 960 and service is timely.
        req = request(deadline=5)
        sim.pending = [req]
        result = sim.run()
        self.assertEqual(req.outcome, Outcome.SERVED)
        self.assertEqual(req.ttk, 3)
        self.assertEqual(result.served_fraction(), 1)


class MeasurementTests(unittest.TestCase):
    def test_mean_hops_uses_same_arrival_cohort_as_availability(self):
        warm = replace(request(arrival=0), outcome=Outcome.SERVED, grade="G2", hops=9)
        measured = replace(request(1, arrival=5), outcome=Outcome.SERVED, grade="G2", hops=2)
        result = Results({}, sessions=[warm, measured], warmup_s=5)
        self.assertEqual(result.mean_hops(), 2)

    def test_outcome_metrics_keep_violations_and_blocking_on_arrival_denominator(self):
        warm = replace(request(arrival=0), outcome=Outcome.SERVED, grade="G4",
                       floor_violation=True, served_t=0.35)
        good = replace(request(1, arrival=5), outcome=Outcome.SERVED, grade="G2", served_t=5)
        forced = replace(request(2, arrival=6, payload=4096), outcome=Outcome.SERVED,
                         grade="G4", floor_violation=True, served_t=6.35)
        blocked = replace(request(3, arrival=7), outcome=Outcome.BLOCKED)
        result = Results({}, sessions=[warm, good, forced, blocked], warmup_s=5)
        self.assertTrue(hasattr(result, "outcome_metrics"))
        m = result.outcome_metrics("C2")
        self.assertEqual(m["n_arrivals"], 3)
        self.assertEqual(m["n_served"], 2)
        self.assertEqual(m["n_blocked"], 1)
        self.assertEqual(m["n_authorized_served"], 1)
        self.assertEqual(m["n_floor_violations"], 1)
        self.assertEqual(m["n_forced_below_its"], 1)
        self.assertAlmostEqual(m["floor_violation_arrival_fraction"], 1/3)
        self.assertAlmostEqual(m["forced_below_its_arrival_fraction"], 1/3)
        self.assertEqual(m["floor_violation_payload_bits"], 4096)
        self.assertEqual(m["forced_below_its_payload_bits"], 4096)

    def test_metric_counters_distinguish_cohort_spend_from_window_supply(self):
        sim = setup_sim(horizon_s=3, warmup_s=1)
        # Existing pending request is warm-up traffic; no stochastic arrivals.
        sim.pending = [request(arrival=0)]
        result = sim.run()
        self.assertEqual(result.consumed_bits, 0)
        self.assertEqual(result.generated_bits, 480)
        self.assertTrue(hasattr(result, "full_consumed_bits"))
        self.assertEqual(result.full_consumed_bits, 750)
        self.assertEqual(result.full_generated_bits, 720)
        self.assertEqual(result.initial_stored_bits + result.full_generated_bits
                         - result.full_consumed_bits - result.full_discarded_bits,
                         result.final_stored_bits)

    def test_full_balance_excludes_inventory_operations_before_run_start(self):
        sim = setup_sim()
        sim.topo.store("N0", "N1").take(750)
        result = sim.run()
        self.assertEqual(result.full_consumed_bits, 0)
        self.assertEqual(result.initial_stored_bits + result.full_generated_bits
                         - result.full_consumed_bits - result.full_discarded_bits,
                         result.final_stored_bits)


class RoutingTests(unittest.TestCase):
    def test_path_cache_does_not_reuse_a_different_candidate_limit(self):
        topo = formation_9node(ReservoirConfig())
        one = candidate_paths(topo, "BASE", "FWD1", max_paths=1)
        four = candidate_paths(topo, "BASE", "FWD1", max_paths=4)
        self.assertEqual(len(one), 1)
        self.assertGreater(len(four), 1)


if __name__ == "__main__":
    unittest.main()
