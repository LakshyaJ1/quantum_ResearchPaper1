"""Independent completed-learning analysis; never trains or reruns a rollout.

Default outputs are results/revision/learning_analysis/ and
docs/revision/LEARNING_RESULTS.md. Incomplete or mismatched evidence is rejected
before any output is written. --self-test uses synthetic paired-statistics tests.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SEEDS=tuple(range(5000,5012))
REGIMES=('short_nominal','full_nominal','full_robust')
POLICIES=('strict_floor','budget_greedy',*REGIMES)
GROUPS=('all','C2','ISR','LOG')
RESAMPLES, BOOTSTRAP_SEED=20000,71
AGGREGATE='fixed_seven_condition_average'
ACTION_LABELS=('floor','affordable_fallback','defer','G4','G2')
METRICS={
    'utility':'Timely served / arrivals - 0.75 * below-floor timely served / arrivals',
    'availability':'Timely served requests / all class arrivals',
    'qualified_availability':'Timely served at authorized floor or higher / all class arrivals',
    'degraded_arrival_fraction':'Timely served below authorized floor / all class arrivals',
    'blocked_arrival_fraction':'Requests not served on time / all class arrivals',
    'forced_entitled_fraction':'Eligible G1/G2 requests served at G3/G4 / all eligible arrivals',
    'conditional_forced_fraction':'Eligible requests served at G3/G4 / timely served eligible requests',
    'forced_payload_fraction':'Payload bits of eligible requests served at G3/G4 / all eligible arrival payload bits',
    'degraded_payload_fraction':'Payload bits served below floor / all arrival payload bits',
    'qualified_payload_fraction':'Payload bits served on time at floor or higher / all arrival payload bits',
    'latency_p95':'Within-run 95th percentile among timely served requests, seconds',
    'mean_hops':'Mean hop count among timely served requests',
}
_INDICES=np.random.default_rng(BOOTSTRAP_SEED).integers(0,12,size=(RESAMPLES,12))


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
                                     allow_nan=False).encode()).hexdigest()


def load_json(path):
    def reject_constant(value):
        raise ValueError(f'Nonstandard JSON numeric value {value} in {path}')
    return json.loads(Path(path).read_text(encoding='utf-8'),parse_constant=reject_constant)


def read_verified(path, hash_field):
    data=load_json(path)
    saved=data.pop(hash_field,None)
    if saved!=digest(data):
        raise ValueError(f'Integrity mismatch: {path}')
    data[hash_field]=saved
    return data


def finite(value):
    return value is not None and isinstance(value,(int,float)) and math.isfinite(value)


def mean_interval(values):
    if len(values)!=12:
        raise ValueError('The independent bootstrap unit is exactly 12 registered seeds')
    defined=sum(finite(v) for v in values)
    if defined!=12:
        return {'mean':None,'ci_low':None,'ci_high':None,'n_seeds':12,
                'n_defined':defined,'status':'undefined_denominator'}
    array=np.asarray(values,dtype=float)
    means=array[_INDICES].mean(axis=1)
    low,high=np.quantile(means,[0.025,0.975])
    return {'mean':float(array.mean()),'ci_low':float(low),'ci_high':float(high),
            'n_seeds':12,'n_defined':12,'status':'defined'}


def index_seeds(rows):
    mapping={}
    for row in rows:
        if row['seed'] in mapping:
            raise ValueError('Duplicate seed in a policy/condition comparison')
        mapping[row['seed']]=row
    if set(mapping)!=set(SEEDS):
        raise ValueError('Missing or foreign final-test seeds')
    if len({r['condition'] for r in rows})!=1:
        raise ValueError('A per-condition comparison mixed conditions')
    return mapping


def paired_difference(treatment, control, metric, group='all'):
    a,b=index_seeds(treatment),index_seeds(control)
    differences=[]
    for seed in SEEDS:
        if (a[seed]['condition'],a[seed]['arrival_sha256']) != (
                b[seed]['condition'],b[seed]['arrival_sha256']):
            raise ValueError('A paired comparison requires identical arrival trace hashes')
        x,y=a[seed]['summary'][group][metric],b[seed]['summary'][group][metric]
        differences.append(x-y if finite(x) and finite(y) else None)
    return mean_interval(differences)


def average_conditions(rows, conditions, metrics=tuple(METRICS), groups=GROUPS):
    indexed={}
    for row in rows:
        key=(row['condition'],row['seed'])
        if key in indexed:
            raise ValueError('Duplicate policy/condition/seed row')
        indexed[key]=row
    expected={(condition,seed) for condition in conditions for seed in SEEDS}
    if set(indexed)!=expected:
        raise ValueError('Incomplete or altered fixed-condition benchmark')
    output=[]
    for seed in SEEDS:
        subset=[indexed[condition,seed] for condition in conditions]
        summary={}
        for group in groups:
            summary[group]={}
            for metric in metrics:
                values=[r['summary'][group][metric] for r in subset]
                summary[group][metric]=(float(np.mean(values)) if all(finite(v) for v in values) else None)
        output.append({'seed':seed,'condition':AGGREGATE,'condition_count':len(conditions),
            'arrival_sha256':digest([(r['condition'],r['arrival_sha256']) for r in subset]),
            'summary':summary})
    return output


def verify_time_order(frozen, started, completed):
    times=[datetime.fromisoformat(value.replace('Z','+00:00')) for value in (frozen,started,completed)]
    if any(t.tzinfo is None for t in times) or not times[0]<=times[1]<=times[2]:
        raise ValueError('Freeze must precede test start, which must precede completion')
    return {'freeze_precedes_test':True,'freeze_created_utc':frozen,
            'test_started_utc':started,'test_completed_utc':completed,
            'logged_test_elapsed_s':(times[2]-times[1]).total_seconds()}


def verify_splits(protocol):
    train={s['seed'] for regime in REGIMES for s in protocol['train'][regime]}
    validation={s['seed'] for s in protocol['validation']}
    test={s['seed'] for s in protocol['test']}
    if train!=set(range(1000,1006)) or validation!=set(range(2000,2004)) or test!=set(SEEDS):
        raise ValueError('Realization identifiers differ from the registered learning protocol')
    if train & validation or train & test or validation & test:
        raise ValueError('Training/validation/test realization leakage')
    return {'train':sorted(train),'validation':sorted(validation),'test':sorted(test),'disjoint':True}


def close(actual, expected, name):
    if expected is None:
        if actual is not None:
            raise ValueError(f'{name}: zero denominator must remain null')
    elif not finite(actual) or not math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-12):
        raise ValueError(f'{name}: inconsistent numerator/denominator')


def verify_budget_and_counts(row, budgets):
    snapshot,prefix=row['budget_snapshot'],row['prefix_audit']
    if prefix['maximum_excess']!=0 or any(prefix['maximum_excess_by_class'].values()):
        raise ValueError('Nonzero observed prefix-budget violation')
    if snapshot['budgets']!=budgets:
        raise ValueError('Different runtime exception budgets were compared')
    for group in GROUPS:
        s=row['summary'][group]
        for key in ('n_arrivals','n_served','n_qualified','n_degraded','n_blocked','n_entitled','n_forced'):
            if not isinstance(s[key],int) or isinstance(s[key],bool) or s[key]<0:
                raise ValueError('Counts must be nonnegative integers')
        n=s['n_arrivals']
        if s['n_qualified']+s['n_degraded']!=s['n_served'] or s['n_served']+s['n_blocked']!=n:
            raise ValueError('Timely qualified/degraded/blocked outcomes do not partition arrivals')
        for metric,numerator in (('availability',s['n_served']),
            ('qualified_availability',s['n_qualified']),('degraded_arrival_fraction',s['n_degraded']),
            ('blocked_arrival_fraction',s['n_blocked'])):
            close(s[metric],numerator/n if n else None,metric)
        close(s['utility'],(s['n_served']-0.75*s['n_degraded'])/n if n else None,'utility')
        close(s['forced_entitled_fraction'],s['n_forced']/s['n_entitled'] if s['n_entitled'] else None,'forced_entitled_fraction')
        if row['counters'][group]['n_arrivals']!=n:
            raise ValueError('Raw count and summary cohorts disagree')
        if group!='all':
            cap=math.floor(Fraction(str(budgets[group]))*n)
            if (snapshot['arrivals'][group]!=n or snapshot['caps'][group]!=cap
                or snapshot['violations'][group]!=s['n_degraded'] or s['n_degraded']>cap):
                raise ValueError('Final exception-budget accounting mismatch')
            if prefix['arrivals'][group]!=n or prefix['violations'][group]!=s['n_degraded']:
                raise ValueError('Independent prefix reconstruction disagrees with outcomes')
    if row['summary']['all']['n_arrivals']!=sum(row['summary'][c]['n_arrivals'] for c in GROUPS[1:]):
        raise ValueError('Class counts do not sum to all arrivals')


def spec_pair(spec):
    return (spec['condition'],digest(spec['case']),spec['seed'])


def load_bundle(learning, freeze_path):
    learning=Path(learning)
    # Fail before output construction if the final report is absent/incomplete.
    report=read_verified(learning/'test_results.json','report_sha256')
    freeze=read_verified(freeze_path,'freeze_sha256')
    manifest=load_json(learning/'train_manifest.json')
    started=load_json(learning/'test_started.json')
    if not manifest.get('completed_utc') or not report.get('completed_utc'):
        raise ValueError('Learning or final evaluation is incomplete')
    if report['freeze_sha256']!=freeze['freeze_sha256'] or started['freeze_sha256']!=freeze['freeze_sha256']:
        raise ValueError('Final evaluation does not reference this freeze')
    if len({d['source_hash'] for d in (report,freeze,manifest,started)})!=1:
        raise ValueError('Source/runtime fingerprint changed between experiment phases')
    protocol=freeze['protocol']
    if digest(protocol)!=freeze['protocol_sha256'] or manifest['protocol']!=protocol:
        raise ValueError('Training and frozen protocols disagree')
    if protocol['test']!=freeze['test_plan'] or digest({'files':freeze['files'],'runtime':freeze['runtime']})!=freeze['source_hash']:
        raise ValueError('Frozen provenance integrity mismatch')
    splits=verify_splits(protocol)
    timing=verify_time_order(freeze['created_utc'],started['started_utc'],report['completed_utc'])
    expected_specs={(s['condition'],s['seed']):s for s in freeze['test_plan']}
    conditions=sorted({s['condition'] for s in freeze['test_plan']})
    if len(conditions)!=7 or len(expected_specs)!=84:
        raise ValueError('Expected seven fixed conditions on twelve paired seeds')
    expected_policies={'strict_floor':{'kind':'strict_floor'},'budget_greedy':{'kind':'budget_greedy'}}
    for regime in REGIMES:
        selected=freeze['selected'][regime]
        table=selected['table']
        if len(table)!=18 or any(type(a) is not int or not 0<=a<5 for a in table) or digest(table)!=selected['table_sha256']:
            raise ValueError('Invalid frozen table')
        expected_policies[regime]={'kind':'table','table':table}
    if report['policies']!=expected_policies:
        raise ValueError('Evaluated policies differ from frozen selections and named baselines')
    rows={}
    cache={}
    def get(key):
        if key not in cache:
            value=read_verified(learning/'cache'/f'{key}.json','record_sha256')
            if value['job_key']!=key or digest(value['job'])!=key or value['job']['source_hash']!=freeze['source_hash']:
                raise ValueError('Rollout key or source mismatch')
            verify_budget_and_counts(value,protocol['exception_budgets'])
            cache[key]=value
        return cache[key]
    for row in report['rows']:
        key=(row['policy_name'],row['condition'],row['seed'])
        if key in rows or row['policy_name'] not in expected_policies:
            raise ValueError('Duplicate or unexpected final-test policy row')
        if (row['condition'],row['seed']) not in expected_specs:
            raise ValueError('Final evaluation has an unregistered condition or seed')
        policy=expected_policies[row['policy_name']]
        raw=get(row['rollout_key'])
        spec=expected_specs[row['condition'],row['seed']]
        if raw['job']!={**spec,'stage':'test','policy':policy,'source_hash':freeze['source_hash']}:
            raise ValueError('Final raw rollout does not match frozen test cell')
        if row['policy_sha256']!=digest(policy):
            raise ValueError('Final policy label/hash mismatch')
        for field in ('summary','counters','budget_snapshot','prefix_audit','arrival_sha256','wall_s'):
            if row[field]!=raw[field]:
                raise ValueError(f'Report differs from verified raw rollout: {field}')
        rows[key]=row
    expected={(p,c,s) for p in POLICIES for c,s in expected_specs}
    if set(rows)!=expected or len(rows)!=420:
        raise ValueError('The final report is not the complete 420-cell registered evaluation')
    for condition in conditions:
        for seed in SEEDS:
            if len({rows[p,condition,seed]['arrival_sha256'] for p in POLICIES})!=1:
                raise ValueError('Final policy comparisons lack matched arrival traces')
    earliest_test_write=min((learning/'cache'/f'{r["rollout_key"]}.json').stat().st_mtime
                            for r in report['rows'])
    frozen_time=datetime.fromisoformat(freeze['created_utc'].replace('Z','+00:00')).timestamp()
    if earliest_test_write<frozen_time-2.0:
        raise ValueError('A final-test cache file predates the policy freeze')
    timing['earliest_test_cache_file_mtime_utc']=datetime.fromtimestamp(earliest_test_write,timezone.utc).isoformat()
    requested={'train':[],'validation':[],'test':[r['rollout_key'] for r in report['rows']]}
    search_audits=[]
    for regime in REGIMES:
        allowed={spec_pair(s) for s in protocol['train'][regime]}
        finalists={}
        for restart in range(2):
            path=learning/'search'/f'{regime}_restart{restart}.json'
            search=load_json(path)
            if search['source_hash']!=freeze['source_hash'] or search['completed_iterations']!=4 or len(search['history'])!=4:
                raise ValueError('Incomplete or foreign CEM search history')
            if search['optimizer_seed']!=protocol['optimizer_seeds'][restart]:
                raise ValueError('Optimizer restart seed differs from the registered protocol')
            incumbent=tuple([1]*18)
            for generation in search['history']:
                candidates=generation['population']
                tables={tuple(c['table']) for c in candidates}
                if len(candidates)!=10 or len(tables)!=10 or not {tuple([0]*18),tuple([1]*18),incumbent}<=tables:
                    raise ValueError('CEM population omitted an incumbent/baseline or changed its budget')
                for candidate in candidates:
                    records=[get(k) for k in candidate['rollout_keys']]
                    pairs=[spec_pair(r['job']) for r in records]
                    if len(records)!=6 or set(pairs)!=allowed:
                        raise ValueError('Training candidate has unmatched realization budget')
                    if digest(candidate['table'])!=candidate['table_sha256']:
                        raise ValueError('Search table hash mismatch')
                    for raw in records:
                        if raw['job']['stage']!='train' or raw['job']['policy']!={'kind':'table','table':candidate['table']}:
                            raise ValueError('Search score contains another stage or policy')
                    score=float(np.mean([r['summary']['all']['utility'] for r in records]))
                    close(candidate['training_score']['mean']['utility'],score,'candidate score')
                    requested['train'].extend(candidate['rollout_keys'])
                incumbent=tuple(generation['incumbent_table'])
                best=min(candidates,key=lambda c:(-c['training_score']['mean']['utility'],
                    sum(a!=b for a,b in zip(c['table'],c['table'][1:])),tuple(c['table'])))
                if incumbent!=tuple(best['table']):
                    raise ValueError('Search incumbent is not the registered best observed candidate')
            finalists[restart]=list(incumbent)
            search_audits.append({'regime':regime,'restart':restart,
                'optimizer_seed':search['optimizer_seed'],'history_sha256':digest(search),
                'execution_stats':search['execution_stats']})
        scored=[]
        validation_allowed={spec_pair(s) for s in protocol['validation']}
        if {c['restart'] for c in freeze['validation_candidates'][regime]}!={0,1}:
            raise ValueError('Missing validation restart')
        for candidate in freeze['validation_candidates'][regime]:
            records=[get(k) for k in candidate['validation_rollout_keys']]
            if candidate['table']!=finalists[candidate['restart']] or len(records)!=12:
                raise ValueError('Validation did not evaluate the trained finalist')
            if {spec_pair(r['job']) for r in records}!=validation_allowed:
                raise ValueError('Validation pairs differ from the registered grid')
            for raw in records:
                if raw['job']['stage']!='validation' or raw['job']['policy']!={'kind':'table','table':candidate['table']}:
                    raise ValueError('Selection contains non-validation policy data')
            score=float(np.mean([r['summary']['all']['utility'] for r in records]))
            close(candidate['validation_score']['mean']['utility'],score,'validation score')
            complexity=sum(a!=b for a,b in zip(candidate['table'],candidate['table'][1:]))
            scored.append((-score,complexity,tuple(candidate['table']),candidate['restart']))
            requested['validation'].extend(candidate['validation_rollout_keys'])
        winner=min(scored)
        selected=freeze['selected'][regime]
        if (tuple(selected['table']),selected['restart'])!=(winner[2],winner[3]):
            raise ValueError('Frozen restart does not obey the registered validation selection rule')
    expected_requests={'train':1440,'validation':72,'test':420}
    # Account for completed same-source cache work even if an interrupted or
    # exploratory request is absent from the final search references.
    completed_by_stage={stage:set() for stage in requested}
    foreign_cache_files=0
    for path in sorted((learning/'cache').glob('*.json')):
        raw=cache.get(path.stem)
        if raw is None:
            raw=read_verified(path,'record_sha256')
            if raw['job']['source_hash']!=freeze['source_hash']:
                foreign_cache_files+=1
                continue
            raw=get(path.stem)
        if raw['job']['stage'] not in completed_by_stage:
            raise ValueError('Unexpected stage in same-source experiment cache')
        completed_by_stage[raw['job']['stage']].add(path.stem)
    compute={}
    for stage,keys in requested.items():
        if len(keys)!=expected_requests[stage]:
            raise ValueError('Requested search/evaluation budget changed')
        unique=set(keys)
        records=[get(k) for k in completed_by_stage[stage]]
        compute[stage]={'requested_rollouts':len(keys),'unique_completed_rollouts':len(records),
            'referenced_unique_rollouts':len(unique),
            'unreferenced_completed_rollouts':len(completed_by_stage[stage]-unique),
            'reused_requests':len(keys)-len(unique),
            'requested_arrival_horizon_hours':sum(get(k)['job']['case']['horizon_s']/3600 for k in keys),
            'unique_arrival_horizon_hours':sum(r['job']['case']['horizon_s']/3600 for r in records),
            'sum_unique_rollout_wall_s':sum(r['wall_s'] for r in records)}
    compute['training_coordinator']={'wall_s':manifest['wall_s'],'workers':manifest['workers'],
        'logged_execution_stats':manifest['execution_stats'],
        'note':'Coordinator wall is the completed invocation; unique rollout walls overlap under parallel execution.'}
    compute['test_coordinator']={'wall_s':report['wall_s'],'workers':started['workers'],
        'logged_execution_stats':report['execution_stats']}
    compute['foreign_source_cache_files_excluded']=foreign_cache_files
    return {'freeze':freeze,'report':report,'rows':list(rows.values()),'conditions':conditions,
            'splits':splits,'timing':timing,'compute':compute,'search_audits':search_audits,
            'integrity':{'freeze_sha256':freeze['freeze_sha256'],'report_sha256':report['report_sha256'],
                         'source_hash':freeze['source_hash'],'verified_unique_cache_records':len(cache),
                         'all_observed_prefix_excess_zero':True,'all_arrival_pairs_match':True}}


def statistics(rows, conditions):
    grouped={policy:[r for r in rows if r['policy_name']==policy] for policy in POLICIES}
    estimates=[]
    comparisons=[]
    aggregates=[]
    all_sets={}
    for policy,policy_rows in grouped.items():
        per_condition={condition:[r for r in policy_rows if r['condition']==condition]
                       for condition in conditions}
        averaged=average_conditions(policy_rows,conditions)
        per_condition[AGGREGATE]=averaged
        aggregates.extend({'policy_name':policy,**r} for r in averaged)
        all_sets[policy]=per_condition
        for condition,cells in per_condition.items():
            indexed=index_seeds(cells)
            for group in GROUPS:
                for metric,denominator in METRICS.items():
                    result=mean_interval([indexed[s]['summary'][group][metric] for s in SEEDS])
                    estimates.append({'policy':policy,'condition':condition,'class':group,
                        'metric':metric,'denominator':denominator,
                        'condition_count':7 if condition==AGGREGATE else 1,**result})
    pairs=[(regime,baseline) for regime in REGIMES for baseline in ('budget_greedy','strict_floor')]
    pairs.append(('strict_floor','budget_greedy'))
    for treatment,control in pairs:
        for condition in [*conditions,AGGREGATE]:
            for group in GROUPS:
                for metric,denominator in METRICS.items():
                    result=paired_difference(all_sets[treatment][condition],all_sets[control][condition],metric,group)
                    comparisons.append({'treatment':treatment,'control':control,'condition':condition,
                        'class':group,'metric':metric,'denominator':denominator,
                        'condition_count':7 if condition==AGGREGATE else 1,
                        'difference':'treatment minus control',**result})
    return estimates,comparisons,aggregates


def labelled_tables(freeze):
    output=[]
    for regime in REGIMES:
        selected=freeze['selected'][regime]
        for state,action in enumerate(selected['table']):
            cls,rest=divmod(state,6)
            feasibility,urgent=divmod(rest,2)
            label=f'{GROUPS[cls+1]} | {("affordable","refill_within_deadline","unfundable_now")[feasibility]} | {"urgent" if urgent else "not_urgent"}'
            output.append({'regime':regime,'selected_restart':selected['restart'],
                'optimizer_seed':selected['optimizer_seed'],'state_index':state,'state_label':label,
                'action_index':action,'action_label':ACTION_LABELS[action],
                'table_sha256':selected['table_sha256']})
    return output


def flattened_outcomes(rows):
    output=[]
    for row in sorted(rows,key=lambda r:(r['policy_name'],r['condition'],r['seed'])):
        for group in GROUPS:
            flat={'policy':row['policy_name'],'condition':row['condition'],'seed':row['seed'],
                  'class':group,'arrival_sha256':row['arrival_sha256'],'rollout_key':row['rollout_key'],
                  **row['summary'][group],
                  **{f'raw_{k}':v for k,v in row['counters'][group].items()},
                  'prefix_maximum_excess':row['prefix_audit']['maximum_excess'],
                  'exception_budget_fraction':row['budget_snapshot']['budgets'].get(group),
                  'exception_cap':row['budget_snapshot']['caps'].get(group),
                  'confirmed_exceptions':row['budget_snapshot']['violations'].get(group),
                  'rollout_wall_s':row['wall_s']}
            output.append(flat)
    return output


def write_csv(path, rows):
    if not rows:
        raise ValueError('Refusing to export an empty result table')
    fields=list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def interval_text(row):
    if row['status']!='defined':
        return 'undefined (zero denominator)'
    return f'{row["mean"]:+.4f} [{row["ci_low"]:+.4f}, {row["ci_high"]:+.4f}]'


def markdown_report(analysis):
    comparisons=analysis['comparisons']
    def find(regime,metric,condition=AGGREGATE,group='all',control='budget_greedy'):
        return next(r for r in comparisons if r['treatment']==regime and r['control']==control
                    and r['condition']==condition and r['class']==group and r['metric']==metric)
    lines=['# Learning results from the completed registered experiment','',
        'This report retains every registered policy, condition and seed, including negative differences and intervals that include zero. '
        'The policy tables were selected using validation outcomes and frozen before final-test evaluation. '
        'The tables below report treatment-minus-BudgetGreedy differences; positive service/utility differences favor the treatment, '
        'while positive loss differences indicate more service below the requested assurance.','',
        'The benchmark contains seven fixed test conditions and twelve realization seeds (5000–5011). '
        'For the overall comparison, each condition first receives equal weight within a seed; the bootstrap then resamples those twelve seed-level averages. '
        'The 84 condition/seed cells are not treated as independent draws. Intervals use 20,000 paired percentile resamples at seed 71. '
        'They quantify realization uncertainty for this fixed benchmark, not uncertainty over an unknown population of deployment conditions. '
        'Multiple comparisons are exploratory and no multiplicity-adjusted significance claim is made.','',
        'Utility is timely-service availability minus 0.75 times the below-floor delivery count divided by all arrivals. '
        'Qualified availability counts timely deliveries at the requested floor or above, divided by all arrivals. '
        'Floor loss uses all arrivals as its denominator. Forced-payload loss uses the payload bits of all G1/G2-entitled arrivals; '
        'it records lower contractual assurance, not demonstrated plaintext disclosure. Conditional metrics retain their explicit denominators in the CSVs. '
        'Undefined conditional values remain null in JSON and empty in CSV; no seed or condition is silently dropped.','',
        '| Learned training regime | Mean utility difference [95% CI] | Qualified availability difference [95% CI] | Floor-loss difference [95% CI] |',
        '|---|---|---|---|']
    for regime in REGIMES:
        lines.append(f'| {regime} | {interval_text(find(regime,"utility"))} | '
                     f'{interval_text(find(regime,"qualified_availability"))} | '
                     f'{interval_text(find(regime,"degraded_arrival_fraction"))} |')
    lines += ['', 'Per-condition utility differences against BudgetGreedy are shown without excluding unfavorable or null outcomes.','',
        '| Condition | Short nominal [95% CI] | Full nominal [95% CI] | Full robust [95% CI] |',
        '|---|---|---|---|']
    for condition in analysis['conditions']:
        cells=' | '.join(interval_text(find(regime,'utility',condition)) for regime in REGIMES)
        lines.append(f'| {condition} | {cells} |')
    lines += ['', 'All per-class estimates, all three learned-versus-StrictFloor comparisons, and the StrictFloor-versus-BudgetGreedy comparison are exported alongside the headline tables. '
        'StrictFloor and BudgetGreedy use the same model and arrival traces; the learned policies share the fixed runtime exception projection. '
        'The independent audit found zero excess over the declared exception cap at every observed arrival prefix in every verified training, validation and test rollout. '
        'This is a simulator accounting result under the declared projection, not certification of a cryptographic implementation.','',
        'The selected controller is the best observed under the limited CEM search and registered validation rule. '
        'The robust-training objective averages three conditions; it does not optimize the worst case. '
        'No superiority, weight robustness, global optimality or deployment safety beyond the tested model is inferred from a mean ranking alone.','',
        '| Stage | Requested rollouts | Unique completed rollouts | Unique simulated arrival-horizon hours | Sum of recorded unique rollout wall seconds |',
        '|---|---:|---:|---:|---:|']
    for stage in ('train','validation','test'):
        c=analysis['compute'][stage]
        lines.append(f'| {stage} | {c["requested_rollouts"]} | {c["unique_completed_rollouts"]} | '
                     f'{c["unique_arrival_horizon_hours"]:.1f} | {c["sum_unique_rollout_wall_s"]:.1f} |')
    lines += ['', 'Repeated deterministic evaluations are counted in the requested budget but execute once through the verified cache. '
        'Simulated hours here count the arrival horizon, excluding the short deadline drain. Summed rollout wall durations overlap under parallel execution and are not elapsed coordinator time. '
        f'The completed training coordinator invocation took {analysis["compute"]["training_coordinator"]["wall_s"]:.1f} seconds; '
        f'final-test coordination took {analysis["compute"]["test_coordinator"]["wall_s"]:.1f} seconds.','',
        f'Freeze timestamp: {analysis["timing"]["freeze_created_utc"]}. '
        f'Test start: {analysis["timing"]["test_started_utc"]}. '
        f'Test completion: {analysis["timing"]["test_completed_utc"]}. '
        'The logged order was checked, and training, validation and test seed sets are disjoint.','',
        f'Freeze SHA-256: `{analysis["integrity"]["freeze_sha256"]}`. '
        f'Test report SHA-256: `{analysis["integrity"]["report_sha256"]}`. '
        'Every referenced rollout record and its duplicated report fields passed integrity and count checks.','',
        'The full selected tables follow. Actions are raw table proposals executed through the common budget projection; an action label alone does not imply that an exception was allowed.','',
        '| Regime | State | Action |', '|---|---|---|']
    for row in analysis['selected_tables']:
        lines.append(f'| {row["regime"]} | {row["state_label"].replace("|","/")} | {row["action_label"]} |')
    lines += ['', 'Machine-readable outputs are in results/revision/learning_analysis/: analysis.json, per_seed.csv, per_class.csv, '
        'fixed_benchmark_per_seed.csv, estimates.csv, paired_differences.csv and selected_policy_tables.csv. '
        'analysis.json includes denominator definitions, search/validation integrity audits and actual compute accounting. '
        'All estimates and intervals remain available even when the headline table is inconclusive.','']
    return '\n'.join(lines)


def analyze_and_export(learning, freeze_path, output, markdown_path):
    bundle=load_bundle(learning,freeze_path)
    estimates,comparisons,aggregates=statistics(bundle['rows'],bundle['conditions'])
    outcomes=flattened_outcomes(bundle['rows'])
    tables=labelled_tables(bundle['freeze'])
    analysis={'schema_version':1,'created_utc':datetime.now(timezone.utc).isoformat(),
        'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'conditions':bundle['conditions'],'policies':list(POLICIES),'seed_ids':list(SEEDS),
        'bootstrap':{'unit':'seed-level average over the fixed conditions','n_units':12,
                     'resamples':RESAMPLES,'seed':BOOTSTRAP_SEED,'confidence':0.95,
                     'condition_population':'the seven fixed registered conditions'},
        'denominators':METRICS,'integrity':bundle['integrity'],'splits':bundle['splits'],
        'timing':bundle['timing'],'compute':bundle['compute'],'search_audits':bundle['search_audits'],
        'estimates':estimates,'comparisons':comparisons,'selected_tables':tables,
        'per_seed_per_class':outcomes,'fixed_benchmark_per_seed':aggregates}
    analysis['analysis_sha256']=digest(analysis)
    text=markdown_report(analysis)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    (output/'analysis.json').write_text(json.dumps(analysis,indent=2,allow_nan=False),encoding='utf-8')
    write_csv(output/'per_seed.csv',[r for r in outcomes if r['class']=='all'])
    write_csv(output/'per_class.csv',[r for r in outcomes if r['class']!='all'])
    write_csv(output/'estimates.csv',estimates)
    write_csv(output/'paired_differences.csv',comparisons)
    write_csv(output/'selected_policy_tables.csv',tables)
    aggregate_flat=[]
    for row in aggregates:
        for group in GROUPS:
            aggregate_flat.append({'policy':row['policy_name'],'seed':row['seed'],'class':group,
                'condition':AGGREGATE,'condition_count':7,**row['summary'][group]})
    write_csv(output/'fixed_benchmark_per_seed.csv',aggregate_flat)
    Path(markdown_path).parent.mkdir(parents=True,exist_ok=True)
    Path(markdown_path).write_text(text,encoding='utf-8')
    return analysis


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--learning-dir',type=Path,default=ROOT/'results/revision/learning')
    parser.add_argument('--freeze',type=Path,default=ROOT/'results/revision/learning_policy_freeze.json')
    parser.add_argument('--output',type=Path,default=ROOT/'results/revision/learning_analysis')
    parser.add_argument('--markdown',type=Path,default=ROOT/'docs/revision/LEARNING_RESULTS.md')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        sys.path.insert(0,str(ROOT))
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_revision_learning_analysis.py')
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    analysis=analyze_and_export(args.learning_dir,args.freeze,args.output,args.markdown)
    print(f'Verified {len(analysis["per_seed_per_class"])} per-class rows; '
          f'{len(analysis["comparisons"])} paired interval records. Results: {args.output}',flush=True)
    print(f'Report: {args.markdown}',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
