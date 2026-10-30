"""Lightweight protocol tests; never execute the registered training/test grid."""
import importlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np


def module():
    assert importlib.util.find_spec('experiments.revision_learning') is not None, (
        'The registered learning pipeline is not implemented')
    return importlib.import_module('experiments.revision_learning')


class LearningProtocolTests(unittest.TestCase):
    def test_training_validation_and_test_realizations_are_disjoint(self):
        m = module()
        train = {s['seed'] for name in m.REGIMES for s in m.training_specs(name)}
        validation = {s['seed'] for s in m.validation_specs()}
        test = {s['seed'] for s in m.test_specs()}
        self.assertEqual(train, set(range(1000,1006)))
        self.assertEqual(validation, set(range(2000,2004)))
        self.assertEqual(test, set(range(5000,5012)))
        self.assertFalse(train & validation or train & test or validation & test)

    def test_three_regimes_have_matched_six_rollout_candidate_budgets(self):
        m = module()
        for name in m.REGIMES:
            specs = m.training_specs(name)
            self.assertEqual(len(specs), 6)
            self.assertEqual(len({(s['seed'],m.digest(s['case'])) for s in specs}), 6)
            self.assertTrue(all(s['case']['warmup_s'] == 0 for s in specs))
        self.assertEqual({s['case']['horizon_s'] for s in m.training_specs('short_nominal')}, {21600})
        self.assertEqual({s['case']['horizon_s'] for s in m.training_specs('full_nominal')}, {86400})
        self.assertEqual(len({s['condition'] for s in m.training_specs('full_robust')}), 3)
        self.assertEqual(m.POPULATION*m.ITERATIONS*m.RESTARTS*6*len(m.REGIMES),1440)

    def test_population_reproducibility_and_both_baselines_survive(self):
        m=module()
        incumbent=tuple([4]*18)
        probabilities=np.full((18,5),0.2)
        a=m.population(probabilities,10,incumbent,np.random.default_rng(77))
        b=m.population(probabilities,10,incumbent,np.random.default_rng(77))
        self.assertEqual(a,b)
        self.assertEqual(len(set(a)),10)
        for required in (tuple([0]*18),tuple([1]*18),incumbent):
            self.assertIn(required,a)

    def test_cross_entropy_update_favors_actions_of_the_elites(self):
        m=module()
        probabilities=m.elite_probabilities([tuple([4]*18)]*3)
        self.assertEqual(probabilities.shape,(18,5))
        self.assertTrue(np.allclose(probabilities.sum(axis=1),1))
        self.assertTrue(np.all(probabilities[:,4] > probabilities[:,0]))

    def validation_candidate(self, restart, table, score):
        m=module()
        return {'restart':restart,'table':list(table), 'rollouts':[
            {'job':{**spec,'stage':'validation'},
             'summary':{'all':{'utility':score,'availability':score,
                               'qualified_availability':score,'degraded_arrival_fraction':0.0}}}
            for spec in m.validation_specs()]}

    def test_restart_selection_uses_validation_and_deterministic_ties(self):
        m=module()
        constant=self.validation_candidate(1,[1]*18,0.8)
        complex_table=self.validation_candidate(0,[i%2 for i in range(18)],0.8)
        self.assertEqual(m.select_restart([complex_table,constant])['restart'],1)
        better=self.validation_candidate(0,[i%2 for i in range(18)],0.81)
        self.assertEqual(m.select_restart([better,constant])['restart'],0)

    def test_selection_rejects_a_final_test_seed_and_missing_validation_pair(self):
        m=module()
        candidate=self.validation_candidate(0,[1]*18,0.8)
        candidate['rollouts'][0]['job']['seed']=5000
        with self.assertRaises(ValueError):
            m.select_restart([candidate])
        candidate=self.validation_candidate(0,[1]*18,0.8)
        candidate['rollouts'].pop()
        with self.assertRaises(ValueError):
            m.select_restart([candidate])

    def test_nonfinite_scoring_is_rejected_and_json_undefined_values_are_null(self):
        m=module()
        candidate=self.validation_candidate(0,[1]*18,float('nan'))
        with self.assertRaises(ValueError):
            m.select_restart([candidate])
        cleaned=m.json_safe({'x':float('nan'),'y':[float('inf'),2.0]})
        self.assertEqual(json.loads(json.dumps(cleaned,allow_nan=False)),{'x':None,'y':[None,2.0]})

    def test_duplicate_jobs_are_deduplicated_before_any_executor_dispatch(self):
        m=module()
        job={'case':m.training_specs('full_nominal')[0]['case'],'seed':1000,
             'condition':'nominal','stage':'train','policy':{'kind':'table','table':[1]*18},
             'source_hash':'fixture','cache_dir':'unused'}
        unique=m.unique_jobs([job,dict(job)])
        self.assertEqual(len(unique),1)
        changed=dict(job,seed=1001)
        self.assertEqual(len(m.unique_jobs([job,changed])),2)

    def test_freeze_integrity_rejects_policy_or_source_changes(self):
        m=module()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'freeze.json'
            data={'schema_version':1,'source_hash':'source-a',
                  'selected':{'full_nominal':{'table':[1]*18}},'test_plan':m.test_specs()}
            m.write_freeze(path,data)
            self.assertEqual(m.read_freeze(path,'source-a')['selected'],data['selected'])
            with self.assertRaises(RuntimeError):
                m.read_freeze(path,'source-b')
            altered=json.loads(path.read_text())
            altered['selected']['full_nominal']['table'][0]=4
            path.write_text(json.dumps(altered))
            with self.assertRaises(RuntimeError):
                m.read_freeze(path,'source-a')

    def test_short_real_rollout_cache_retains_budget_and_arrival_evidence(self):
        m=module()
        from dataclasses import asdict
        from revision.scenarios import Case
        with tempfile.TemporaryDirectory() as directory:
            case=asdict(Case(horizon_s=240,outage_model='none',isr_scale=1.0,
                             initial_spendable_fraction=0.0,rate_scale=0.0))
            job={'case':case,'seed':1000,'condition':'unit_fixture','stage':'fixture',
                 'policy':{'kind':'table','table':[3]*18},
                 'source_hash':'fixture','cache_dir':directory}
            a=m.run_rollout(job)
            b=m.run_rollout(job)
            self.assertFalse(a['cached'])
            self.assertTrue(b['cached'])
            self.assertEqual(a['record'],b['record'])
            record=a['record']
            self.assertEqual(record['prefix_audit']['maximum_excess'],0)
            self.assertEqual(record['budget_snapshot']['violations']['C2'],0)
            self.assertEqual(len(record['arrival_sha256']),64)
            self.assertGreater(record['summary']['all']['n_arrivals'],0)

    def test_real_constant_tables_match_named_baselines_on_the_same_trace(self):
        m=module()
        from dataclasses import asdict
        from revision.scenarios import Case
        with tempfile.TemporaryDirectory() as directory:
            case=asdict(Case(horizon_s=240,outage_model='none',isr_scale=1.0,
                             initial_spendable_fraction=0.0,rate_scale=0.0))
            base={'case':case,'seed':1001,'condition':'unit_fixture','stage':'fixture',
                  'source_hash':'fixture','cache_dir':directory}
            for action,kind in ((0,'strict_floor'),(1,'budget_greedy')):
                table=m.run_rollout(dict(base,policy={'kind':'table','table':[action]*18}))['record']
                named=m.run_rollout(dict(base,policy={'kind':kind}))['record']
                self.assertEqual(table['summary'],named['summary'])
                self.assertEqual(table['arrival_sha256'],named['arrival_sha256'])

    def test_evaluator_dispatches_duplicate_rollout_once_and_checks_trace_pairing(self):
        m=module()
        self.assertTrue(hasattr(m,'Evaluator'))
        from dataclasses import asdict
        from revision.scenarios import Case
        with tempfile.TemporaryDirectory() as directory:
            evaluator=m.Evaluator('fixture',Path(directory),None)
            spec={'case':asdict(Case(horizon_s=240,outage_model='none')),
                  'seed':1000,'condition':'unit_fixture'}
            policy={'kind':'table','table':[1]*18}
            records=evaluator.evaluate([policy,policy],[spec],'fixture')
            self.assertEqual(len(records[m.policy_key(policy)]),1)
            self.assertEqual(evaluator.stats['requested'],2)
            self.assertEqual(evaluator.stats['executed'],1)
            self.assertEqual(evaluator.stats['unique_jobs_dispatched'],1)

    def test_final_evaluation_refuses_to_start_without_a_freeze(self):
        m=module()
        self.assertTrue(hasattr(m,'run_test'))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                m.run_test(1,Path(directory)/'learning',Path(directory)/'missing-freeze.json')
            self.assertFalse((Path(directory)/'learning/cache').exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
