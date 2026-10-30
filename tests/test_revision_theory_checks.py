"""Small deterministic checks of finite-key bounds and structural attacks."""
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def theory_module():
    assert importlib.util.find_spec('experiments.revision_theory_checks') is not None, (
        'the independent finite-reservoir check implementation is missing')
    return importlib.import_module('experiments.revision_theory_checks')


class ReservoirTheoryChecks(unittest.TestCase):
    def test_divisible_stocks_reach_the_cut_count_bound(self):
        # Each of three two-hop branches can relay two 750-bit deliveries.
        row = theory_module().run_reservoir_case(branches=3, spendable_bits=1500)
        self.assertEqual(row['served'], 6)
        self.assertEqual(row['branch_service_counts'], {'B0': 2, 'B1': 2, 'B2': 2})
        self.assertEqual(row['pooled_cut_bound'], 6)
        self.assertEqual(row['cut_consumed_bits'], 4500)
        self.assertEqual(row['full_consumed_bits'], 9000)
        self.assertEqual(row['first_unserved_arrival_s'], 30)
        self.assertEqual(row['retained_fluid_reference_s'], 30)
        self.assertEqual(row['full_conservation_residual_bits'], 0)
        self.assertTrue(row['all_checks_passed'])

    def test_separate_reservoir_fragments_do_not_form_an_extra_session(self):
        # 3 * 1900 / 750 permits seven sessions in a pooled relaxation.
        # Actual separate branches each leave 400 bits, so only six fit.
        row = theory_module().run_reservoir_case(branches=3, spendable_bits=1900)
        self.assertEqual(row['served'], 6)
        self.assertEqual(row['pooled_cut_bound'], 7)
        self.assertEqual(row['retained_exact_branch_capacity'], 6)
        self.assertEqual(row['cut_remaining_spendable_bits'], 1200)
        self.assertEqual(row['first_unserved_arrival_s'], 30)
        self.assertEqual(row['retained_fluid_reference_s'], 38)
        self.assertTrue(all(event['cut_bound_holds'] for event in row['events']))

    def test_purging_is_recorded_as_lost_stock_not_delivered_key(self):
        row = theory_module().run_reservoir_case(
            branches=3, spendable_bits=1900, buffer_policy='purge')
        self.assertEqual(row['served'], 0)
        self.assertEqual(row['first_unserved_arrival_s'], 0)
        self.assertEqual(row['cut_discarded_bits'], 5700)
        self.assertEqual(row['full_purged_bits'], 11400)
        self.assertEqual(row['full_consumed_bits'], 0)
        self.assertEqual(row['post_discard_cut_bound'], 0)
        self.assertEqual(row['full_conservation_residual_bits'], 0)
        self.assertTrue(row['transport_available'])
        self.assertTrue(row['generation_stopped'])

    def test_positive_aggregate_stock_cannot_fund_one_unaffordable_hop(self):
        row = theory_module().run_reservoir_case(branches=4, spendable_bits=749)
        self.assertEqual(row['pooled_cut_bound'], 3)
        self.assertEqual(row['served'], 0)
        self.assertEqual(row['first_unserved_arrival_s'], 0)

    def test_arrival_spacing_changes_failure_time_without_changing_capacity(self):
        row = theory_module().run_reservoir_case(
            branches=2, spendable_bits=1500, interval_s=7)
        self.assertEqual(row['served'], 4)
        self.assertEqual(row['first_unserved_arrival_s'], 28)
        self.assertEqual(row['full_generated_bits'], 0)

    def test_unsupported_fixture_inputs_fail_before_simulation(self):
        module = theory_module()
        for kwargs in ({'branches': 5}, {'spendable_bits': -1},
                       {'interval_s': 0}, {'buffer_policy': 'silent_reset'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                module.run_reservoir_case(**kwargs)


class StructuralAttackChecks(unittest.TestCase):
    def test_adaptive_and_cut_methods_isolate_the_two_path_chain_in_two_edges(self):
        rows = theory_module().structural_depth_checks()
        for depth in range(1, 7):
            for method in ('adaptive_betweenness', 'weighted_cut'):
                row = next(r for r in rows if r['depth'] == depth and r['method'] == method)
                self.assertEqual(row['isolation_edge_count'], 1 if depth == 1 else 2)
                self.assertEqual(row['isolation_relative_cost'], 1 if depth == 1 else 2)
                self.assertTrue(row['connected_before_last_removal'])
                self.assertFalse(row['connected_after_prefix'])

    def test_static_tie_conventions_are_reported_separately(self):
        rows = theory_module().structural_depth_checks()
        at_six = {r['method']: r for r in rows if r['depth'] == 6}
        self.assertEqual(at_six['historical_static_betweenness']['isolation_edge_count'], 7)
        self.assertEqual(at_six['static_betweenness']['isolation_edge_count'], 8)
        self.assertEqual(at_six['adaptive_betweenness']['isolation_edge_count'], 2)

    def test_report_serializes_exact_results_and_source_identity(self):
        module = theory_module()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'theory.json'
            module.write_report(path)
            report = json.loads(path.read_text(encoding='utf-8'))
        self.assertTrue(report['all_checks_passed'])
        self.assertGreaterEqual(len(report['reservoir_checks']), 6)
        self.assertEqual(len(report['structural_depth_checks']), 24)
        self.assertIn('qkdsim/sim.py', report['source_sha256'])
        self.assertEqual(len(report['source_sha256']['qkdsim/sim.py']), 64)
        self.assertEqual(report['scope']['structural_test'], 'offline edge removal; no key inventory feedback')


if __name__ == '__main__':
    unittest.main(verbosity=2)
