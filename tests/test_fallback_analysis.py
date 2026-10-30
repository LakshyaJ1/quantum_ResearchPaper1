"""Analysis guards use explicit synthetic records, never research output."""
import copy
import importlib
import importlib.util
from dataclasses import asdict
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.revision_fallback import control_cases


def analysis_module():
    assert importlib.util.find_spec('experiments.analyze_revision_fallback') is not None, (
        'paired fallback analysis implementation is missing')
    return importlib.import_module('experiments.analyze_revision_fallback')


def synthetic_records():
    records = []
    sources = {'synthetic_fixture': 'a' * 64}
    manifest = dict(seed_ids=list(range(3000, 3008)), source_sha256=sources,
                    cases=[dict(name=r['name'], case=asdict(r['case']),
                                key_establishment_available=r['key_establishment_available'])
                           for r in control_cases()])
    for record in manifest['cases']:
        name = record['name']
        served = 0 if name.startswith('transport') else (
            10 if name == 'generation_online_kem_control_down' else 90)
        qualified = min(10, served)
        degraded = served - qualified
        metrics = dict(n_arrivals=100, n_served=served, n_qualified=qualified,
                       n_degraded=degraded, n_blocked=100-served,
                       n_entitled=100, n_forced=degraded,
                       availability=served/100, qualified_availability=qualified/100,
                       degraded_arrival_fraction=degraded/100,
                       blocked_arrival_fraction=(100-served)/100,
                       forced_entitled_fraction=degraded/100,
                       entitled_blocked_fraction=(100-served)/100,
                       entitled_its_fraction=qualified/100,
                       degraded_payload_fraction=degraded/100,
                       forced_payload_fraction=degraded/100)
        empty = {key: (0 if key.startswith('n_') else None) for key in metrics}
        for seed in manifest['seed_ids']:
            records.append(dict(record, seed=seed, source_sha256=sources,
                                arrivals_sha256=f'arrival-{seed}',
                                environment_sha256=f'environment-{seed}',
                                overall=dict(metrics),
                                per_class={'C2': dict(metrics), 'ISR': dict(empty), 'LOG': dict(empty)}))
    return manifest, records


class FallbackAnalysisTests(unittest.TestCase):
    def test_eight_paired_seeds_produce_the_hand_derived_difference(self):
        manifest, records = synthetic_records()
        report = analysis_module().analyze_rows(manifest, records)
        row = next(r for r in report['comparisons'] if
                   r['comparison'] == 'preplaced_minus_online_control_down'
                   and r['traffic_class'] == 'all' and r['metric'] == 'availability')
        self.assertEqual(row['n_pairs'], 8)
        self.assertAlmostEqual(row['difference'], 0.8)
        self.assertAlmostEqual(row['lo'], 0.8)
        self.assertAlmostEqual(row['hi'], 0.8)

    def test_incomplete_grid_is_rejected_instead_of_aggregated_early(self):
        manifest, records = synthetic_records()
        with self.assertRaises(ValueError):
            analysis_module().analyze_rows(manifest, records[:-1])

    def test_pairing_checks_both_arrival_and_environment_identity(self):
        for field in ('arrivals_sha256', 'environment_sha256'):
            manifest, records = synthetic_records()
            records[-1][field] = 'mismatched-trace'
            with self.subTest(field=field), self.assertRaises(ValueError):
                analysis_module().analyze_rows(manifest, records)

    def test_mixed_code_versions_are_rejected(self):
        manifest, records = synthetic_records()
        records[-1]['source_sha256'] = {'synthetic_fixture': 'b' * 64}
        with self.assertRaises(ValueError):
            analysis_module().analyze_rows(manifest, records)

    def test_delivery_and_assurance_counts_must_partition_arrivals(self):
        manifest, records = synthetic_records()
        records[0]['overall']['n_degraded'] += 1
        with self.assertRaises(ValueError):
            analysis_module().analyze_rows(manifest, records)

    def test_undefined_class_metric_is_not_replaced_with_zero_or_dropped_pairs(self):
        manifest, records = synthetic_records()
        report = analysis_module().analyze_rows(manifest, records)
        row = next(r for r in report['comparisons'] if
                   r['comparison'] == 'preplaced_minus_online_control_down'
                   and r['traffic_class'] == 'ISR' and r['metric'] == 'availability')
        self.assertEqual(row['n_pairs'], 8)
        self.assertEqual(row['defined_pairs'], 0)
        self.assertIsNone(row['difference'])
        self.assertIsNone(row['lo'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
