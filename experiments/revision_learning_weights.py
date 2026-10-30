"""Exploratory class-importance reweighting of completed frozen outcomes.

No simulation, training, model selection or extra weight search occurs here.
The only vectors are (1,1,1), (5,2,1) and (10,3,1) in C2/ISR/LOG order.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments import revision_learning_analysis as analysis

CLASSES=('C2','ISR','LOG')
WEIGHTS=((1,1,1),(5,2,1),(10,3,1))
OUTPUT=ROOT/'results/revision/learning_analysis'
REPORT=ROOT/'docs/revision/LEARNING_WEIGHT_SENSITIVITY.md'


def weighted_utility(counts,weights):
    weights=tuple(weights)
    if weights not in WEIGHTS or set(counts)!=set(CLASSES):
        raise ValueError('Only the three declared class vectors and complete class counts are permitted')
    n=s=d=0
    for cls,weight in zip(CLASSES,weights):
        values=counts[cls]
        if any(type(values[k]) is not int or values[k]<0 for k in ('N','S','D')):
            raise ValueError('Counts must be nonnegative integers')
        if not values['D']<=values['S']<=values['N']:
            raise ValueError('Degraded, timely served and arrival counts are inconsistent')
        n+=weight*values['N']
        s+=weight*values['S']
        d+=weight*values['D']
    numerator,denominator=4*s-3*d,4*n
    return {'weighted_arrivals':n,'weighted_served':s,'weighted_degraded':d,
        'numerator_quarters':numerator,'denominator_quarters':denominator,
        'utility':float(Fraction(numerator,denominator)) if denominator else None}


def raw_counts(row):
    result={}
    for cls in CLASSES:
        raw=row['counters'][cls]
        count={'N':raw['n_arrivals'],'S':raw['n_timely_served'],'D':raw['n_floor_violations']}
        s=row['summary'][cls]
        if (count['N'],count['S'],count['D'])!=(s['n_arrivals'],s['n_served'],s['n_degraded']):
            raise ValueError('Raw counter and timely outcome summaries disagree')
        result[cls]=count
    return result


def render(result):
    rows=result['intervals']
    def find(weights,policy):
        return next(r for r in rows if r['weights']==list(weights) and r['policy']==policy
                    and r['condition']==analysis.AGGREGATE)
    def show(row):
        if row['paired_status']!='defined':
            return 'undefined'
        return f'{row["paired_mean"]:+.6f} [{row["paired_ci_low"]:+.6f}, {row["paired_ci_high"]:+.6f}]'
    lines=['# Exploratory class-importance sensitivity of frozen policies','',
        'This is post-hoc reweighting of already-completed outcomes from the same five frozen policies. '
        'No controller was retrained, reselected or optimized for these weights. Only the three previously declared vectors '
        '(C2, ISR, LOG) = (1,1,1), (5,2,1) and (10,3,1) are evaluated. They are illustrative preferences, not calibrated harm costs.','',
        'For each condition and seed, weighted utility is sum_c w_c(S_c - 0.75 D_c) / sum_c w_c N_c, '
        'where N_c counts all arrivals of class c, S_c counts timely served arrivals, and D_c counts timely below-floor deliveries. '
        'Both numerator and denominator change with the weights. Raw counts and integer quarter-unit numerators/denominators are exported. '
        'The seven fixed conditions are averaged equally within each seed, then the twelve seed-level averages are paired with BudgetGreedy. '
        'Intervals are 95% percentile intervals from 20,000 bootstrap resamples with seed 71. The 84 condition/seed cells are not treated as independent observations.','',
        'Every declared vector and every frozen policy is retained, including null or unfavorable differences. '
        'This sensitivity is conditional on the fixed benchmark; it does not establish robustness over unknown deployments or weight-robust optimality. '
        'Request-class weighting also does not by itself calibrate the harm of losing entitlement to OTP-protected payload.','',
        '| C2 / ISR / LOG weights | Strict floor minus greedy [95% CI] | Short nominal minus greedy [95% CI] | Full nominal minus greedy [95% CI] | Multi-condition minus greedy [95% CI] |',
        '|---|---|---|---|---|']
    for weights in WEIGHTS:
        cells=' | '.join(show(find(weights,p)) for p in ('strict_floor',*analysis.REGIMES))
        lines.append(f'| {weights[0]} / {weights[1]} / {weights[2]} | {cells} |')
    lines += ['', f'Equal weights reproduce the original aggregate count numerator and denominator exactly for all {result["equal_weight_check"]["checked_policy_condition_seed_rows"]} frozen rows. '
        f'The largest difference from the previously stored floating-point utility is {result["equal_weight_check"]["maximum_floating_point_difference"]:.3g}, '
        'consistent with the different order of floating-point arithmetic. No stored experiment outcome is changed.','',
        f'Frozen policy manifest hash: `{result["freeze_sha256"]}`. '
        f'Completed test-report hash: `{result["report_sha256"]}`. '
        'The existing analysis gate revalidated policy selection provenance, matched arrival traces, raw counts, exception caps and disjoint train/validation/test seeds before reweighting.','',
        'The complete JSON and CSV files retain absolute weighted-utility intervals, all per-condition and fixed-benchmark paired intervals, '
        'per-seed averages and all condition/seed weighted numerators and denominators. '
        'They are results/revision/learning_analysis/weight_sensitivity.json, weight_sensitivity.csv, '
        'weight_sensitivity.per_seed.csv and weight_sensitivity.per_condition.csv. No additional weights are proposed from these outcomes.','']
    return '\n'.join(lines)


def run(output=OUTPUT,report_path=REPORT):
    bundle=analysis.load_bundle(ROOT/'results/revision/learning',ROOT/'results/revision/learning_policy_freeze.json')
    raw=[]
    seed_rows=[]
    intervals=[]
    maximum_difference=0.0
    exact_count_checks=0
    for weights in WEIGHTS:
        converted=[]
        for row in bundle['rows']:
            counts=raw_counts(row)
            score=weighted_utility(counts,weights)
            if weights==(1,1,1):
                s=row['summary']['all']
                if score['numerator_quarters']!=4*s['n_served']-3*s['n_degraded'] or score['denominator_quarters']!=4*s['n_arrivals']:
                    raise ValueError('Equal-weight exact count identity failed')
                difference=abs(score['utility']-s['utility'])
                if difference>1e-12:
                    raise ValueError('Equal weights do not reproduce stored utility')
                maximum_difference=max(maximum_difference,difference)
                exact_count_checks+=1
            item={'weights':list(weights),'policy':row['policy_name'],'condition':row['condition'],'seed':row['seed'],
                'arrival_sha256':row['arrival_sha256'],**score,
                **{f'{cls}_{field}':value for cls,values in counts.items() for field,value in values.items()}}
            raw.append(item)
            converted.append({'policy_name':row['policy_name'],'condition':row['condition'],'seed':row['seed'],
                'arrival_sha256':row['arrival_sha256'],'summary':{'all':{'utility':score['utility']}}})
        by_policy={}
        for policy in analysis.POLICIES:
            policy_rows=[r for r in converted if r['policy_name']==policy]
            by_condition={c:[r for r in policy_rows if r['condition']==c] for c in bundle['conditions']}
            averaged=analysis.average_conditions(policy_rows,bundle['conditions'],('utility',),('all',))
            by_condition[analysis.AGGREGATE]=averaged
            by_policy[policy]=by_condition
            seed_rows.extend({'weights':list(weights),'policy':policy,'seed':r['seed'],
                'condition_count':7,'utility':r['summary']['all']['utility']} for r in averaged)
        for policy in analysis.POLICIES:
            for condition in (*bundle['conditions'],analysis.AGGREGATE):
                target=by_policy[policy][condition]
                control=by_policy['budget_greedy'][condition]
                estimate=analysis.mean_interval([r['summary']['all']['utility'] for r in target])
                paired=analysis.paired_difference(target,control,'utility')
                intervals.append({'weights':list(weights),'policy':policy,'control':'budget_greedy',
                    'condition':condition,'condition_count':7 if condition==analysis.AGGREGATE else 1,
                    **{f'absolute_{k}':v for k,v in estimate.items()},
                    **{f'paired_{k}':v for k,v in paired.items()},
                    'denominator':'sum of class importance times all class arrivals, calculated separately per condition/seed'})
    result={'schema_version':1,'classification':'exploratory reweighting of frozen outcomes, not a calibrated harm model',
        'weights':[list(w) for w in WEIGHTS],'class_order':list(CLASSES),
        'policies':list(analysis.POLICIES),'conditions':bundle['conditions'],'seed_ids':list(analysis.SEEDS),
        'source_hash':bundle['integrity']['source_hash'],'freeze_sha256':bundle['integrity']['freeze_sha256'],
        'report_sha256':bundle['integrity']['report_sha256'],
        'weight_analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'formula':'sum_c w_c(S_c - 0.75 D_c) / sum_c w_c N_c',
        'count_definitions':{'N':'all arrivals','S':'timely served arrivals','D':'timely served below authorized floor'},
        'bootstrap':{'resamples':20000,'seed':71,'units':12,'confidence':0.95,
            'aggregate':'equally average the seven fixed conditions within seed before resampling seeds'},
        'equal_weight_check':{'exact_integer_count_identity':True,'checked_policy_condition_seed_rows':exact_count_checks,
                              'maximum_floating_point_difference':maximum_difference},
        'intervals':intervals,'per_seed':seed_rows,'per_condition':raw,
        'no_training_or_selection_performed':True,'created_utc':datetime.now(timezone.utc).isoformat()}
    result['analysis_sha256']=analysis.digest(result)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    (output/'weight_sensitivity.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    def csv_rows(rows):
        return [{**r,'weights':','.join(str(v) for v in r['weights'])} for r in rows]
    analysis.write_csv(output/'weight_sensitivity.csv',csv_rows(intervals))
    analysis.write_csv(output/'weight_sensitivity.per_seed.csv',csv_rows(seed_rows))
    analysis.write_csv(output/'weight_sensitivity.per_condition.csv',csv_rows(raw))
    Path(report_path).parent.mkdir(parents=True,exist_ok=True)
    Path(report_path).write_text(render(result),encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        tests=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_revision_learning_weights.py')
        return 0 if unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful() else 1
    result=run()
    print(f'Weighted frozen-outcome sensitivity complete: {len(result["per_condition"])} raw weighted cells; '
          f'{len(result["intervals"])} interval records. Report: {REPORT}')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
