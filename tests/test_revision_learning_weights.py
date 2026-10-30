"""Hand-derived weighted-count identities; no simulation or policy selection."""
import importlib
import importlib.util
import unittest


def module():
    assert importlib.util.find_spec('experiments.revision_learning_weights') is not None
    return importlib.import_module('experiments.revision_learning_weights')


COUNTS={'C2':{'N':2,'S':2,'D':0},'ISR':{'N':1,'S':1,'D':1},'LOG':{'N':1,'S':0,'D':0}}


class WeightSensitivityTests(unittest.TestCase):
    def test_equal_weights_reproduce_the_exact_unweighted_count_ratio(self):
        m=module()
        result=m.weighted_utility(COUNTS,(1,1,1))
        self.assertEqual(result['numerator_quarters'],9)
        self.assertEqual(result['denominator_quarters'],16)
        self.assertEqual(result['utility'],0.5625)

    def test_declared_importance_weights_change_both_numerator_and_denominator(self):
        m=module()
        result=m.weighted_utility(COUNTS,(5,2,1))
        self.assertEqual(result['weighted_arrivals'],13)
        self.assertEqual(result['weighted_served'],12)
        self.assertEqual(result['weighted_degraded'],2)
        self.assertEqual((result['numerator_quarters'],result['denominator_quarters']),(42,52))
        self.assertEqual(result['utility'],21/26)
        strongest=m.weighted_utility(COUNTS,(10,3,1))
        self.assertEqual((strongest['numerator_quarters'],strongest['denominator_quarters']),(83,96))

    def test_unregistered_weights_and_impossible_counts_are_rejected(self):
        m=module()
        with self.assertRaises(ValueError):
            m.weighted_utility(COUNTS,(2,1,1))
        invalid={**COUNTS,'ISR':{'N':1,'S':1,'D':2}}
        with self.assertRaises(ValueError):
            m.weighted_utility(invalid,(1,1,1))

    def test_zero_denominator_is_undefined_not_perfect_service(self):
        m=module()
        result=m.weighted_utility({c:{'N':0,'S':0,'D':0} for c in COUNTS},(1,1,1))
        self.assertIsNone(result['utility'])
        self.assertEqual(result['denominator_quarters'],0)


if __name__=='__main__':
    unittest.main(verbosity=2)
