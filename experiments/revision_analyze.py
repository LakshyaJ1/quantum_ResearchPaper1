"""Build auditable summary tables from completed revision run manifests.

No manuscript number is hand-entered by this program. Undefined denominators
remain undefined; censored event times are not silently averaged as zeros.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from revision.metrics import mean_interval, paired_interval
from revision.scenarios import Case

OUT=ROOT/'results/revision'
METRICS=('availability','qualified_availability','degraded_arrival_fraction',
         'blocked_arrival_fraction','forced_entitled_fraction',
         'entitled_blocked_fraction','entitled_its_fraction',
         'conditional_forced_fraction','degraded_payload_fraction',
         'forced_payload_fraction','qualified_payload_fraction','key_Mbit',
         'mean_hops','latency_p95','utility')


def strict_json(value):
    if isinstance(value,dict):
        return {k:strict_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [strict_json(v) for v in value]
    if isinstance(value,(np.floating,float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value,np.integer):
        return int(value)
    return value


def load_phase(phase):
    path=OUT/f'manifest_{phase}.json'
    manifest=json.loads(path.read_text(encoding='utf-8'))
    expected=len(manifest['cases'])*len(manifest['seed_ids'])
    if manifest.get('completed_runs')!=expected:
        raise RuntimeError(f'{phase} is incomplete; expected {expected} completed runs')
    records=[]
    for case in manifest['cases']:
        for seed in manifest['seed_ids']:
            run_path=OUT/'runs'/f"{case['case_id']}_seed{seed}.json"
            run=json.loads(run_path.read_text(encoding='utf-8'))
            if run['source_hash']!=manifest['source_hash']:
                raise RuntimeError(f'Stale source hash in {run_path}')
            if abs(run['accounting']['conservation_residual_bits'])>1e-2:
                raise RuntimeError(f'Conservation failure in {run_path}')
            if run['case']!=case['case'] or run['seed']!=seed:
                raise RuntimeError(f'Run identity mismatch in {run_path}')
            records.append(run)
    return manifest,records


def canonicalize_records(manifest,records):
    """Collapse numeric serialization aliases after checking repeated results.

    Case identifiers deliberately retain the execution's original JSON. Reporting
    must nevertheless treat2 and2.0 as the same setting and never pool them as
    independent realizations. The selected identifier is the lexical first alias.
    """
    def normalize(value):
        if isinstance(value,dict):
            return {key:normalize(item) for key,item in value.items()}
        if isinstance(value,list):
            return [normalize(item) for item in value]
        if isinstance(value,float) and np.isfinite(value) and value.is_integer():
            return int(value)
        return value
    groups=defaultdict(list)
    for item in manifest['cases']:
        groups[json.dumps(normalize(item['case']),sort_keys=True)].append(item)
    lookup={(run['case_id'],run['seed']):run for run in records}
    if len(lookup)!=len(records):
        raise RuntimeError('Repeated execution identity in recorded data')
    selected=[]
    cases=[]
    aliases={}
    scientific_fields=('summary','hourly','topology','accounting','arrival_sha256')
    for group in groups.values():
        group=sorted(group,key=lambda item:item['case_id'])
        chosen=group[0]
        combined=dict(chosen)
        combined['tags']=sorted({tag for item in group for tag in item.get('tags',[])})
        combined['equivalent_recorded_case_ids']=[item['case_id'] for item in group]
        cases.append(combined)
        for item in group:
            aliases[item['case_id']]=chosen['case_id']
        for seed in manifest['seed_ids']:
            reference=lookup[(chosen['case_id'],seed)]
            reference_values={key:strict_json(reference[key]) for key in scientific_fields}
            for item in group[1:]:
                other=lookup[(item['case_id'],seed)]
                values={key:strict_json(other[key]) for key in scientific_fields}
                if values!=reference_values:
                    raise RuntimeError('Equivalent configurations disagree: '
                                       f"{chosen['case_id']} / {item['case_id']}, seed{seed}")
            selected.append(reference)
    canonical=dict(manifest)
    canonical['cases']=cases
    canonical['completed_runs']=len(selected)
    canonical['canonical_reporting']=True
    canonical['recorded_runs']=len(records)
    return canonical,selected,aliases


def rows_for(records):
    rows=[]
    for run in records:
        common={'case_id':run['case_id'],'seed':run['seed'],**run['case'],
                'arrival_sha256':run['arrival_sha256'],
                'node_count':len(run['topology']['nodes']),
                'edge_count':len(run['topology']['links']),
                'cut_cost':run['topology']['all_terminal_cut_cost'],
                'spent_attack_budget':run['topology']['spent_attack_budget']}
        for cls,metrics in run['summary'].items():
            rows.append({**common,'traffic_class':cls,**metrics})
    return pd.DataFrame(rows)


def summarize_rows(raw):
    rows=[]
    for (cid,cls),group in raw.groupby(['case_id','traffic_class'],sort=True):
        group=group.sort_values('seed')
        identifiers=['case_id','traffic_class']+[f.name for f in fields(Case)]
        identifiers+=['cut_cost','node_count','edge_count','spent_attack_budget']
        row={k:group.iloc[0][k] for k in identifiers}
        row['n_seeds']=len(group)
        row['n_arrivals_total']=int(group.n_arrivals.sum())
        for metric in METRICS:
            a=group[metric].to_numpy(float)
            finite=np.isfinite(a)
            row[f'{metric}_defined_seeds']=int(finite.sum())
            if finite.all() and len(a)>=2:
                mean,lo,hi=mean_interval(a)
            else:
                # No implicit available-case inference or n=1 pseudo-CI.
                mean=float(a.mean()) if finite.all() else float('nan')
                lo=hi=float('nan')
            row[metric],row[f'{metric}_lo'],row[f'{metric}_hi']=mean,lo,hi
            row[f'{metric}_sd']=float(a.std(ddof=1)) if finite.all() and len(a)>1 else float('nan')
        times=group.first_forced_s.to_numpy(float)
        observed=np.isfinite(times)
        row['forced_event_observed_seeds']=int(observed.sum())
        row['forced_event_observed_fraction']=float(observed.mean())
        row['first_forced_median_if_observed_s']=float(np.median(times[observed])) if observed.any() else float('nan')
        rows.append(row)
    return pd.DataFrame(rows)


def paired_rows(manifest,raw):
    cases={r['case_id']:r['case'] for r in manifest['cases']}
    comparisons=[]
    for cid,case in cases.items():
        controls=[]
        if case['fail_mode']=='FAIL_DEGRADED':
            controls.append(('degraded_minus_closed',{**case,'fail_mode':'FAIL_CLOSED'}))
        if case['attack_budget']>0:
            controls.append(('attack_minus_no_attack',{**case,'attack_budget':0}))
        for label,config in controls:
            # Dataclass JSON can contain0 or0.0 depending on construction;
            # equal numeric settings must identify the same counterfactual.
            other=next((candidate for candidate,cfg in cases.items() if cfg==config),None)
            if other is None:
                # Some factorial grids compare capability/budget cells without
                # claiming a separately run no-attack attribution estimate.
                continue
            for cls in ('all','C2','ISR','LOG'):
                treatment=raw[(raw.case_id==cid)&(raw.traffic_class==cls)].sort_values('seed')
                control=raw[(raw.case_id==other)&(raw.traffic_class==cls)].sort_values('seed')
                if treatment.seed.tolist()!=control.seed.tolist():
                    raise RuntimeError('Unmatched seed identifiers')
                if treatment.arrival_sha256.tolist()!=control.arrival_sha256.tolist():
                    raise RuntimeError('Counterfactual arrivals changed')
                common=dict(comparison=label,treatment_case=cid,control_case=other,
                            traffic_class=cls,n_seeds=len(treatment),**case)
                for metric in METRICS:
                    a,b=treatment[metric].to_numpy(float),control[metric].to_numpy(float)
                    if not np.isfinite(a-b).all():
                        mean=lo=hi=float('nan')
                    else:
                        mean,lo,hi=paired_interval(a,b)
                    comparisons.append({**common,'metric':metric,'difference':mean,'lo':lo,'hi':hi})
    return pd.DataFrame(comparisons)


def weighted_exposure(raw):
    rows=[]
    weights={'equal':(1,1,1),'priority_5_2_1':(5,2,1),'priority_10_3_1':(10,3,1)}
    for (cid,seed),group in raw[raw.traffic_class!='all'].groupby(['case_id','seed']):
        g=group.set_index('traffic_class')
        for label,values in weights.items():
            weighted_n=sum(w*g.loc[c,'n_arrivals'] for c,w in zip(('C2','ISR','LOG'),values))
            weighted_bad=sum(w*g.loc[c,'n_degraded'] for c,w in zip(('C2','ISR','LOG'),values))
            weighted_qualified=sum(w*g.loc[c,'n_qualified'] for c,w in zip(('C2','ISR','LOG'),values))
            rows.append(dict(case_id=cid,seed=seed,weight_scenario=label,
                             weighted_degraded_fraction=weighted_bad/weighted_n,
                             weighted_qualified_availability=weighted_qualified/weighted_n))
    return pd.DataFrame(rows)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['main','sensitivity','threshold'],default='main')
    args=parser.parse_args()
    manifest,records=load_phase(args.phase)
    raw=rows_for(records)
    canonical,selected,aliases=canonicalize_records(manifest,records)
    analysis_raw=rows_for(selected)
    destination=OUT/'analysis'
    destination.mkdir(exist_ok=True)
    raw.to_csv(destination/f'{args.phase}_raw_metrics.csv',index=False)
    analysis_raw.to_csv(destination/f'{args.phase}_canonical_raw_metrics.csv',index=False)
    summary=summarize_rows(analysis_raw)
    summary.to_csv(destination/f'{args.phase}_summary.csv',index=False)
    pairs=paired_rows(canonical,analysis_raw)
    pairs.to_csv(destination/f'{args.phase}_paired_comparisons.csv',index=False)
    weighted_exposure(analysis_raw).to_csv(destination/f'{args.phase}_importance_sensitivity.csv',index=False)
    (destination/f'{args.phase}_case_aliases.json').write_text(json.dumps({
        'aliases':aliases,'canonical_cases':canonical['cases'],
        'duplicate_recorded_runs':len(records)-len(selected),
        'check':'All duplicate scientific outcomes and traces agree exactly per seed'},indent=2),encoding='utf-8')
    evidence={'phase':args.phase,'source_hash':manifest['source_hash'],
              'manifest_sha256':hashlib.sha256((OUT/f'manifest_{args.phase}.json').read_bytes()).hexdigest(),
              'runs_checked':len(records),'canonical_cases':len(canonical['cases']),
              'canonical_runs':len(selected),'duplicate_recorded_runs':len(records)-len(selected),
              'summary_rows':len(summary),
              'paired_comparison_rows':len(pairs),'bootstrap_resamples':20000,
              'bootstrap_seed':71,'bootstrap_unit':'independent simulator seed',
              'interval':'marginal percentile bootstrap95percent; not simultaneous',
              'weight_scenarios':'declared relative priorities, not calibrated harm',
              'analysis_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (destination/f'{args.phase}_verification.json').write_text(
        json.dumps(strict_json(evidence),indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(evidence,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
