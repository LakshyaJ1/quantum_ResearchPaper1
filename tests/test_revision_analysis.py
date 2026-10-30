import unittest
import pandas as pd

from experiments.revision_analyze import METRICS, paired_rows


class PairedAnalysisTests(unittest.TestCase):
    def fixtures(self):
        cases=[{'case_id':'base','case':{'fail_mode':'FAIL_CLOSED','attack_budget':0.0}},
               {'case_id':'attack','case':{'fail_mode':'FAIL_CLOSED','attack_budget':1.0}}]
        rows=[]
        for cid in ('base','attack'):
            for cls in ('all','C2','ISR','LOG'):
                for seed in (1,2,3):
                    rows.append({'case_id':cid,'traffic_class':cls,'seed':seed,
                                 'arrival_sha256':f'trace{seed}',
                                 **{m:float(cid=='attack') for m in METRICS}})
        return {'cases':cases},pd.DataFrame(rows)

    def test_numeric_zero_serialization_does_not_drop_counterfactual(self):
        manifest,rows=self.fixtures()
        result=paired_rows(manifest,rows)
        self.assertEqual(len(result),4*len(METRICS))
        self.assertTrue((result.difference==1).all())
        self.assertTrue((result.lo==1).all())

    def test_changed_arrivals_cannot_be_called_paired(self):
        manifest,rows=self.fixtures()
        rows.loc[(rows.case_id=='attack')&(rows.seed==2),'arrival_sha256']='different'
        with self.assertRaisesRegex(RuntimeError,'arrivals changed'):
            paired_rows(manifest,rows)

    def duplicate_fixture(self):
        manifest={'cases':[
            {'case_id':'a','case':{'attack_budget':2},'tags':['first']},
            {'case_id':'b','case':{'attack_budget':2.0},'tags':['second']}],
            'seed_ids':[1,2]}
        runs=[]
        for case in manifest['cases']:
            for seed in manifest['seed_ids']:
                runs.append({'case_id':case['case_id'],'seed':seed,'case':case['case'],
                             'summary':{'all':{'availability':.5}},'hourly':[],
                             'topology':{},'accounting':{},'arrival_sha256':f'trace{seed}'})
        return manifest,runs

    def test_configuration_aliases_are_not_extra_replicates(self):
        from experiments import revision_analyze as module
        self.assertTrue(hasattr(module,'canonicalize_records'),'Canonical reporting is missing')
        manifest,runs=self.duplicate_fixture()
        canonical,selected,aliases=module.canonicalize_records(manifest,runs)
        self.assertEqual(len(canonical['cases']),1)
        self.assertEqual(len(selected),2)
        self.assertEqual(set(canonical['cases'][0]['tags']),{'first','second'})
        self.assertEqual(aliases['b'],'a')

    def test_disagreeing_alias_results_are_rejected(self):
        from experiments import revision_analyze as module
        self.assertTrue(hasattr(module,'canonicalize_records'),'Canonical reporting is missing')
        manifest,runs=self.duplicate_fixture()
        runs[-1]['summary']['all']['availability']=.4
        with self.assertRaisesRegex(RuntimeError,'Equivalent configurations disagree'):
            module.canonicalize_records(manifest,runs)


if __name__=='__main__':
    unittest.main()
