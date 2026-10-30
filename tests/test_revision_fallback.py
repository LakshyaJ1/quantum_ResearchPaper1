"""Deterministic tests of key-establishment-only failure versus data outage."""
import importlib
import importlib.util
import json
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qkdsim.sim import Outcome, Session
from revision.scenarios import Case, make_simulator


def fallback_module():
    assert importlib.util.find_spec('experiments.revision_fallback') is not None, (
        'the independent fallback control-plane experiment is missing')
    return importlib.import_module('experiments.revision_fallback')


def depleted_case(**changes):
    base = Case(topology='ring', horizon_s=30, outage_model='none',
                attack_budget=2, attack_surface='generation',
                initial_spendable_fraction=0, fallback='online_kem')
    return replace(base, **changes)


def session(sim, sid=0, floor='G2'):
    src, dst = sim._endpoints[0]
    return Session(sid, 'C2', 0, 2048, src, dst, floor, 5, 1)


class FallbackControlTests(unittest.TestCase):
    def test_online_kem_can_supply_fallback_with_control_and_data_available(self):
        sim = fallback_module().make_control_simulator(depleted_case(), 7, True)
        sim._tick_outages()
        req = session(sim)
        sim._serve_or_wait(req, 0)
        self.assertEqual(req.outcome, Outcome.SERVED)
        self.assertEqual(req.grade, 'G4')
        self.assertEqual(req.served_t, 0.35)

    def test_online_kem_fails_when_only_key_establishment_is_unavailable(self):
        sim = fallback_module().make_control_simulator(depleted_case(), 7, False)
        sim._tick_outages()
        req = session(sim)
        sim._serve_or_wait(req, 0)
        self.assertTrue(all(not link.outage for link in sim.topo.links.values()))
        self.assertEqual(req.outcome, Outcome.PENDING)
        self.assertEqual(req.key_bits, 0)

    def test_preplaced_secret_bypasses_online_control_with_up_data_path(self):
        sim = fallback_module().make_control_simulator(
            depleted_case(fallback='preplaced_symmetric'), 7, False)
        sim._tick_outages()
        req = session(sim)
        sim._serve_or_wait(req, 0)
        self.assertEqual(req.outcome, Outcome.SERVED)
        self.assertEqual(req.grade, 'G4')
        self.assertEqual(req.served_t, 0)

    def test_both_fallbacks_fail_when_transport_is_cut(self):
        for mode in ('online_kem', 'preplaced_symmetric'):
            with self.subTest(mode=mode):
                sim = fallback_module().make_control_simulator(
                    depleted_case(fallback=mode, attack_surface='transport'), 7, True)
                sim._tick_outages()
                req = session(sim)
                sim._serve_or_wait(req, 0)
                self.assertEqual(req.outcome, Outcome.PENDING)
                self.assertEqual(req.key_bits, 0)

    def test_control_failure_does_not_disable_g1_or_g2_with_valid_stock(self):
        for grade in ('G1', 'G2'):
            with self.subTest(grade=grade):
                sim = fallback_module().make_control_simulator(
                    depleted_case(initial_spendable_fraction=1), 7, False)
                sim._tick_outages()
                self.assertTrue(sim._try_grade(session(sim, floor='G1'), grade, 0))

    def test_online_hybrid_and_pqc_attempts_fail_before_consuming_any_key(self):
        for grade in ('G3', 'G4'):
            with self.subTest(grade=grade):
                sim = fallback_module().make_control_simulator(
                    depleted_case(initial_spendable_fraction=1), 7, False)
                sim._tick_outages()
                before = {k: s.level for k, s in sim.topo.stores.items()}
                self.assertFalse(sim._try_grade(session(sim), grade, 0))
                self.assertEqual(before, {k: s.level for k, s in sim.topo.stores.items()})

    def test_restoring_control_allows_retry_without_resetting_link_inventory(self):
        sim = fallback_module().make_control_simulator(depleted_case(), 7, False)
        sim._tick_outages()
        req = session(sim)
        self.assertFalse(sim._try_grade(req, 'G4', 0))
        sim.key_establishment_outage = False
        self.assertTrue(sim._try_grade(req, 'G4', 0))

    def test_new_dimension_preserves_the_base_exogenous_trace(self):
        case = depleted_case(outage_model='correlated', mean_uptime_s=10,
                             mean_outage_s=4)
        controlled = fallback_module().make_control_simulator(case, 17, False)
        base = make_simulator(case, 17)
        for tick in range(12):
            controlled._tick_outages()
            base._tick_outages()
            controlled._tick_arrivals(tick)
            base._tick_arrivals(tick)
            self.assertEqual(controlled.environment_transport, base.environment_transport)
            self.assertEqual(controlled.environment_generation, base.environment_generation)
        self.assertEqual([(s.sid, s.cls, s.src, s.dst) for s in controlled.pending],
                         [(s.sid, s.cls, s.src, s.dst) for s in base.pending])

    def test_grid_has_four_generation_conditions_and_two_transport_controls(self):
        rows = fallback_module().control_cases()
        self.assertEqual(len(rows), 6)
        generation = [r for r in rows if r['case'].attack_surface == 'generation']
        transport = [r for r in rows if r['case'].attack_surface == 'transport']
        self.assertEqual({(r['case'].fallback, r['key_establishment_available'])
                          for r in generation},
                         {('online_kem', True), ('online_kem', False),
                          ('preplaced_symmetric', True), ('preplaced_symmetric', False)})
        self.assertEqual({r['case'].fallback for r in transport},
                         {'online_kem', 'preplaced_symmetric'})
        self.assertTrue(all(r['case'].attack_budget == 2 for r in rows))

    def test_result_writer_rejects_a_one_bit_conservation_error(self):
        # The guard must reject a single unaccounted bit, even with large stores.
        # Only the exported result is corrupted; the simulator itself is real.
        module = fallback_module()
        case = depleted_case(initial_spendable_fraction=1)
        sim = module.make_control_simulator(case, 17, True)
        real_run = sim.run
        def corrupted_result():
            result = real_run()
            result.final_stored_bits += 1
            return result
        sim.run = corrupted_result
        record = dict(name='accounting_guard', case=case, key_establishment_available=True)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(module, 'make_control_simulator', return_value=sim):
                with self.assertRaises(AssertionError):
                    module.run_case(record, 17, directory)

    def test_short_run_artifacts_preserve_pairing_and_portable_json(self):
        module = fallback_module()
        case = depleted_case(horizon_s=300, outage_model='correlated',
                             mean_uptime_s=10, mean_outage_s=4)
        with tempfile.TemporaryDirectory() as directory:
            common = dict(name='short_pair', case=case)
            up = module.run_case(dict(common, key_establishment_available=True), 17, directory)
            down = module.run_case(dict(common, key_establishment_available=False), 17, directory)
            self.assertEqual(up['arrivals_sha256'], down['arrivals_sha256'])
            self.assertEqual(up['environment_sha256'], down['environment_sha256'])
            self.assertNotEqual(up['case_id'], down['case_id'])
            paths = list((Path(directory) / 'runs').glob('*.json'))
            self.assertEqual(len(paths), 2)
            def nonportable_constant(value):
                raise AssertionError(f'Nonportable JSON constant: {value}')
            for path in paths:
                raw = json.loads(path.read_text(encoding='utf-8'), parse_constant=nonportable_constant)
                self.assertIn('n_arrivals', raw['per_class']['ISR'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
