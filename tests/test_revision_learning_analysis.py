"""Independent paired-statistics fixtures, not empirical learning results."""
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def module():
    assert importlib.util.find_spec('experiments.revision_learning_analysis') is not None, (
        'Independent learning analysis is missing')
    return importlib.import_module('experiments.revision_learning_analysis')


def rows(value, condition='nominal'):
    return [{'seed':5000+i,'condition':condition,'arrival_sha256':f'{condition}-{i}',
             'summary':{'all':{'utility':value(i) if callable(value) else value}}}
            for i in range(12)]


class LearningAnalysisTests(unittest.TestCase):
    def test_paired_difference_preserves_a_negative_or_zero_result(self):
        m=module()
        negative=m.paired_difference(rows(0.25),rows(0.5),'utility')
        self.assertEqual((negative['mean'],negative['ci_low'],negative['ci_high']),(-0.25,-0.25,-0.25))
        zero=m.paired_difference(rows(0.5),rows(0.5),'utility')
        self.assertEqual((zero['mean'],zero['ci_low'],zero['ci_high']),(0.0,0.0,0.0))

    def test_seed_order_is_joined_rather_than_zipped(self):
        m=module()
        result=m.paired_difference(rows(lambda i:i+1),list(reversed(rows(lambda i:i))),'utility')
        self.assertEqual((result['mean'],result['ci_low'],result['ci_high']),(1.0,1.0,1.0))

    def test_missing_duplicate_or_foreign_seeds_are_rejected(self):
        m=module()
        for invalid in (rows(0)[:-1],rows(0)+rows(0)[:1]):
            with self.assertRaises(ValueError):
                m.paired_difference(rows(1),invalid,'utility')
        changed=rows(0)
        changed[0]['seed']=1000
        with self.assertRaises(ValueError):
            m.paired_difference(rows(1),changed,'utility')

    def test_different_arrival_realizations_cannot_be_called_paired(self):
        m=module()
        changed=rows(0)
        changed[3]['arrival_sha256']='different-stream'
        with self.assertRaises(ValueError):
            m.paired_difference(rows(1),changed,'utility')

    def test_undefined_denominator_does_not_silently_drop_a_seed(self):
        m=module()
        changed=rows(1)
        changed[2]['summary']['all']['utility']=None
        result=m.paired_difference(changed,rows(0),'utility')
        self.assertEqual(result['n_seeds'],12)
        self.assertEqual(result['n_defined'],11)
        self.assertIsNone(result['mean'])
        self.assertIsNone(result['ci_low'])
        self.assertEqual(result['status'],'undefined_denominator')

    def test_seven_condition_mean_bootstraps_twelve_seed_clusters_not_eighty_four_rows(self):
        m=module()
        conditions=[f'c{i}' for i in range(7)]
        treatment=[r for c in conditions for r in rows(lambda i:int(i>=6),c)]
        control=[r for c in conditions for r in rows(0,c)]
        a=m.average_conditions(treatment,conditions,('utility',),('all',))
        b=m.average_conditions(control,conditions,('utility',),('all',))
        self.assertEqual(len(a),12)
        result=m.paired_difference(a,b,'utility')
        # Each seed is perfectly correlated across its seven conditions. The
        # 12-unit Bernoulli bootstrap has central quantiles 3/12 and 9/12.
        self.assertEqual(result['mean'],0.5)
        self.assertEqual((result['ci_low'],result['ci_high']),(0.25,0.75))

    def test_condition_average_rejects_an_incomplete_fixed_benchmark(self):
        m=module()
        with self.assertRaises(ValueError):
            m.average_conditions(rows(0,'c0'),['c0','c1'],('utility',),('all',))

    def test_pretest_freeze_timestamps_are_required_in_order(self):
        m=module()
        result=m.verify_time_order('2026-09-26T10:00:00+00:00',
            '2026-09-26T10:01:00+00:00','2026-09-26T10:05:00+00:00')
        self.assertTrue(result['freeze_precedes_test'])
        with self.assertRaises(ValueError):
            m.verify_time_order('2026-09-26T10:02:00+00:00',
                '2026-09-26T10:01:00+00:00','2026-09-26T10:05:00+00:00')

    def test_integrity_and_strict_json_are_checked(self):
        m=module()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.json'
            payload={'value':1}
            payload['report_sha256']=m.digest(payload)
            path.write_text(json.dumps(payload))
            self.assertEqual(m.read_verified(path,'report_sha256')['value'],1)
            payload['value']=2
            path.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                m.read_verified(path,'report_sha256')
            path.write_text('{"value": NaN}')
            with self.assertRaises(ValueError):
                m.load_json(path)

    def test_no_results_document_or_directory_before_completion(self):
        m=module()
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            with self.assertRaises(FileNotFoundError):
                m.analyze_and_export(base/'learning',base/'freeze.json',base/'analysis',base/'results.md')
            self.assertFalse((base/'results.md').exists())
            self.assertFalse((base/'analysis').exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
