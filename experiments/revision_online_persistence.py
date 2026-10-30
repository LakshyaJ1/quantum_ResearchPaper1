"""Post-hoc persistence diagnostic on disjoint confirmation seeds.

The completed online study and preregistered learning code are imported/read,
never edited. Only unused-slot retention is changed in the new online variant.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments import revision_online_adversary as original
import numpy as np

RELEASE='release_on_unusable'
PERSIST='persistent_slots'
CUT='weighted_cut'
CONTROL='no_attack'
VARIANTS=(RELEASE,PERSIST,CUT)
DEPTHS=(2,4,6)
BUDGETS=(1,2)
SEEDS=tuple(range(3100,3106))
OUT=ROOT/'results/revision/online_persistence'
REPORT=ROOT/'docs/revision/ONLINE_PERSISTENCE_RESULTS.md'


class PersistentSlotSimulator(original.RouteFeedbackSimulator):
    def __init__(self,*args,**kwargs):
        self.retention_log=[]
        self.retained_slot_fills=0
        self.initialized_slot_fills=0
        super().__init__(*args,**kwargs)

    def select_online_targets(self):
        selected=super().select_online_targets()
        feedback_selected=list(selected)
        remaining=self.case.attack_budget-sum(self.attack_costs[e] for e in selected)
        retained=[]
        initialized=[]
        # First preserve previous target order; do not change any covered-path
        # weights, observations, or tie breaking in the original selector.
        for edge in self._chosen_attack:
            if edge not in selected and self.attack_costs[edge]<=remaining+1e-10:
                selected.append(edge)
                retained.append(edge)
                remaining-=self.attack_costs[edge]
        # At initialization there may be no previous target. The frozen
        # weighted-cut order supplies missing slots, then its canonical tail.
        for edge in self._order:
            if edge not in selected and self.attack_costs[edge]<=remaining+1e-10:
                selected.append(edge)
                initialized.append(edge)
                remaining-=self.attack_costs[edge]
        if retained or initialized:
            self.retained_slot_fills+=len(retained)
            self.initialized_slot_fills+=len(initialized)
            self.retention_log.append({'time_s':self.now_s,
                'original_route_feedback_targets':[list(e) for e in feedback_selected],
                'retained_previous_targets':[list(e) for e in retained],
                'initialization_order_fills':[list(e) for e in initialized],
                'final_targets':[list(e) for e in selected]})
        return selected

    def attack_audit(self):
        return {**super().attack_audit(),'retained_slot_fills':self.retained_slot_fills,
                'initialized_slot_fills':self.initialized_slot_fills,'retention_log':self.retention_log}


def make_simulator(depth,variant,budget,seed,case=None):
    if variant not in (*VARIANTS,CONTROL):
        raise ValueError('Unknown persistence-study variant')
    method='online_route_feedback' if variant in (RELEASE,PERSIST) else variant
    prototype=original.make_chain_simulator(depth,method,budget,seed,case)
    if variant!=PERSIST:
        return prototype
    return PersistentSlotSimulator(prototype.topo,prototype.cfg,prototype.case,prototype.traffic,method)


def protected_hashes():
    paths=[ROOT/'experiments/revision_online_adversary.py',
           ROOT/'results/revision/online_adversary/manifest.json',
           ROOT/'results/revision/online_adversary/analysis.json']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def protocol():
    return {'classification':'post-hoc mechanism diagnostic with disjoint confirmation seeds',
        'exploratory_seeds':list(range(3000,3006)),'confirmation_seeds':list(SEEDS),
        'variants':list(VARIANTS),'depths':list(DEPTHS),'budgets':list(BUDGETS),
        'requested_runs':126,'shared_no_attack_controls':18,'horizon_s':86400,
        'initial_spendable_fraction':0.02,'isr_scale':0.1,'n_auth':7,
        'update_period_s':original.UPDATE_SECONDS,'unobserved_path_weight':original.UNOBSERVED_WEIGHT,
        'persistence_rule':'original feedback choices first, fill unused slots with previous targets in prior order',
        'initialization_rule':'fill any remaining slots from frozen weighted-cut order and canonical tail',
        'unchanged':'path weights, committed-route observations, lexical coverage ties, 60-second update period, environment',
        'target_cost':'concurrent relative-cost cap; actual integral and campaign footprint reported separately',
        'retarget_overhead_modelled':False,'optimal_attacker_claim':False}


def source_metadata():
    metadata=original.source_metadata()
    metadata['files']['experiments/revision_online_persistence.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    metadata['source_hash']=original.digest({'files':metadata['files'],'runtime':metadata['runtime']})
    return metadata


def prior_mechanism_audit():
    path=ROOT/'results/revision/online_adversary'
    manifest=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('completed_runs')!=126:
        raise ValueError('The exploratory online study must be complete')
    records=[original.load_run(path/'runs'/f'{r["key"]}.json') for r in manifest['runs']]
    output=[]
    for depth in DEPTHS:
        online=sorted([r for r in records if r['depth']==depth and r['method']=='online_route_feedback' and r['budget']==2],key=lambda r:r['seed'])
        cut=sorted([r for r in records if r['depth']==depth and r['method']=='weighted_cut' and r['budget']==2],key=lambda r:r['seed'])
        control={r['seed']:r for r in records if r['depth']==depth and r['method']=='no_attack'}
        counts={0:0,1:0,2:0}
        for row in online:
            updates=row['attack']['feedback_updates']
            recovered_hours=0.0
            for update in updates:
                n=len(update['selected_edges'])
                counts[n]+=1
                recovered_hours+=n*min(original.UPDATE_SECONDS,86400-update['time_s'])/3600
            if not math.isclose(recovered_hours,row['attack']['relative_cost_link_seconds']/3600,abs_tol=1e-7):
                raise ValueError('Exploratory feedback logs do not reconstruct realized link-hours')
        excess=[r['summary']['all']['forced_entitled_fraction']-control[r['seed']]['summary']['all']['forced_entitled_fraction'] for r in online]
        output.append({'depth':depth,'online_excess_fal':float(np.mean(excess)),
            'online_link_hours':float(np.mean([r['attack']['relative_cost_link_seconds']/3600 for r in online])),
            'cut_link_hours':float(np.mean([r['attack']['relative_cost_link_seconds']/3600 for r in cut])),
            'online_update_slot_count_histogram':counts,
            'fraction_updates_below_two_slots':(counts[0]+counts[1])/sum(counts.values()),
            'online_minus_cut_generated_Mbit':float(np.mean([(a['accounting']['generated_bits_full']-b['accounting']['generated_bits_full'])/1e6 for a,b in zip(online,cut)]))})
    return {'exploratory_source_hash':manifest['source_hash'],'logs_reconstruct_exposure':True,
        'findings':output,'interpretation':'Exposure loss is verified; its effect on forcing is tested prospectively on disjoint seeds.'}


def value(row,metric,group='all'):
    if metric=='realized_link_hours':
        return row['attack']['relative_cost_link_seconds']/3600
    if metric in ('retarget_count','distinct_links_touched_count','retained_slot_fills','initialized_slot_fills'):
        return row['attack'].get(metric,0)
    return row['summary'][group][metric]


def paired(treatment,control,metric,group='all'):
    def index(rows):
        result={r['seed']:r for r in rows}
        if len(result)!=len(rows) or set(result)!=set(SEEDS):
            raise ValueError('Six disjoint confirmation-seed pairs are required')
        return result
    a,b=index(treatment),index(control)
    differences=[]
    for seed in SEEDS:
        if a[seed]['arrival_sha256']!=b[seed]['arrival_sha256'] or a[seed]['attack']['environment_trace_sha256']!=b[seed]['attack']['environment_trace_sha256']:
            raise ValueError('Confirmation counterfactual traces differ')
        x,y=value(a[seed],metric,group),value(b[seed],metric,group)
        differences.append(x-y if x is not None and y is not None else None)
    return original.interval(differences)


def run_job(job):
    key=original.digest({k:job[k] for k in ('depth','variant','budget','seed','source_hash')})
    path=Path(job['output'])/'runs'/f'{key}.json'
    if path.exists():
        row=original.load_run(path)
        if row['source_hash']!=job['source_hash'] or row['run_key']!=key:
            raise ValueError('Confirmation cache mismatch')
        return {'key':key,'cached':True,'wall_s':row['wall_s']}
    start=time.perf_counter()
    sim=make_simulator(job['depth'],job['variant'],job['budget'],job['seed'])
    result=sim.run()
    summary={g:original.summarize(result,None if g=='all' else g) for g in ('all','C2','ISR','LOG')}
    arrivals=sorted((s.sid,s.cls,s.arrival_t,s.payload_bits,s.src,s.dst,s.authorised_floor,s.deadline_s)
                    for s in result.sessions)
    residual=result.initial_stored_bits+result.full_generated_bits-result.full_consumed_bits-result.full_discarded_bits-result.final_stored_bits
    if abs(residual)>1e-2 or sim.purged_bits!=0:
        raise RuntimeError('Key accounting or retained-buffer rule failed')
    audit=sim.attack_audit()
    if audit['maximum_concurrent_relative_cost']>job['budget']+1e-10:
        raise RuntimeError('Concurrent cap exceeded')
    if job['variant']==PERSIST and not math.isclose(audit['relative_cost_link_seconds'],job['budget']*86400,abs_tol=1e-6):
        raise RuntimeError('Persistent slots did not retain full registered exposure')
    row=original.safe({'schema_version':1,**{k:job[k] for k in ('depth','variant','budget','seed','source_hash')},
        'run_key':key,'case':asdict(sim.case),'summary':summary,
        'counters':{g:result.outcome_metrics(None if g=='all' else g) for g in ('all','C2','ISR','LOG')},
        'arrival_sha256':original.digest(arrivals),'attack':audit,
        'accounting':{'initial_stored_bits':result.initial_stored_bits,'final_stored_bits':result.final_stored_bits,
            'generated_bits_full':result.full_generated_bits,'consumed_bits_full':result.full_consumed_bits,
            'discarded_bits_full':result.full_discarded_bits,'purged_bits':sim.purged_bits,
            'conservation_residual_bits':residual},'wall_s':time.perf_counter()-start})
    row['record_sha256']=original.digest(row)
    original.write_json(path,row)
    return {'key':key,'cached':False,'wall_s':row['wall_s']}


def run_study(workers=3,output=OUT):
    output=Path(output)
    if output.resolve()==original.OUT.resolve():
        raise ValueError('Never write diagnostic records into the completed exploratory dataset')
    meta=source_metadata()
    before=protected_hashes()
    path=output/'manifest.json'
    if path.exists():
        previous=json.loads(path.read_text(encoding='utf-8'))
        if previous['source_hash']!=meta['source_hash'] or previous['protocol_sha256']!=original.digest(protocol()):
            raise ValueError('Archive a previous confirmation explicitly after changing this diagnostic')
    manifest={'schema_version':1,**meta,'protocol':protocol(),'protocol_sha256':original.digest(protocol()),
        'protected_previous_artifact_hashes':before,'prior_mechanism_audit':prior_mechanism_audit(),
        'started_utc':datetime.now(timezone.utc).isoformat(),'workers':workers}
    original.write_json(path,manifest)
    jobs=[dict(depth=d,variant=v,budget=b,seed=s,source_hash=meta['source_hash'],output=str(output))
          for d in DEPTHS for v in VARIANTS for b in BUDGETS for s in SEEDS]
    jobs += [dict(depth=d,variant=CONTROL,budget=0,seed=s,source_hash=meta['source_hash'],output=str(output))
             for d in DEPTHS for s in SEEDS]
    started=time.perf_counter()
    completed=[]
    def collect(iterator):
        for index,item in enumerate(iterator,1):
            completed.append(item)
            if index%6==0 or index==126:
                print(f'{index}/126 confirmations complete; {time.perf_counter()-started:.1f}s elapsed',flush=True)
    print(f'Post-hoc persistence confirmation: 126 runs, {workers} workers, seeds 3100â€“3105',flush=True)
    if workers==1:
        collect(map(run_job,jobs))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            collect(pool.map(run_job,jobs))
    if protected_hashes()!=before:
        raise RuntimeError('A protected prior artifact changed during this diagnostic')
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),completed_runs=len(completed),
                    wall_s=time.perf_counter()-started,runs=completed,previous_artifacts_unchanged=True)
    original.write_json(path,manifest)
    return manifest


def report_text(result):
    def contrast(depth,budget,treatment,control,metric='forced_entitled_fraction'):
        return next(r for r in result['contrasts'] if (r['depth'],r['budget'],r['treatment'],r['control'],r['metric'],r['class'])==
                    (depth,budget,treatment,control,metric,'all'))
    lines=['# Persistence diagnostic on disjoint confirmation seeds','',
        'This is a post-hoc mechanism diagnostic motivated by the completed online-adversary study. '
        'It is separate from the preregistered learning experiment and uses new seeds 3100â€“3105 rather than the exploratory 3000â€“3005. '
        'All three chain depths (2, 4, 6), concurrent budgets (1, 2), 24-hour horizon, 2% spendable initial stock, ISR scale 0.1, n_auth = 7, '
        'retained keys, independent environment and fail-degraded operation remain fixed. There are 108 attacked runs and 18 shared no-attack controls.','',
        'Saved exploratory feedback logs exactly reconstruct the lower realized online link-hours as paths become temporarily transport-unusable. '
        'At budget two, original online exposure falls from 43.89 link-hours at depth two to 38.95 at depth six, while the fixed cut spends 48. '
        'The model permits fresh generation on a released target when its own channel is up. These observations identify the exposure confound; '
        'the new experiment tests the effect of the persistence intervention instead of treating adaptivity as intrinsically stronger or weaker.','',
        'The release variant is the unchanged original route-feedback selector. The persistent variant first takes exactly the same weighted route-coverage choices, '
        'then fills unused slots from the previous target set in its prior order. If previous targets are insufficient, the frozen weighted-cut ordering '
        'and its canonical tail initialize the remaining slots. Committed-route observations, path weights, tie breaking and 60-second update times are unchanged. '
        'Selection and subsequent route feedback can respond endogenously to the changed persistence. This is not a new optimal-attacker claim.','',
        'FAL counts G1/G2-entitled requests delivered at G3/G4 over all G1/G2-entitled arrivals, including blocked requests. '
        'Excess FAL subtracts the matched no-attack value within each seed. The 95% percentile intervals use 20,000 paired bootstrap resamples, seed 71, '
        'over six confirmation seeds. Null and negative differences are retained. These are exploratory simulation-model statements, with no multiplicity-adjusted significance claim.','',
        '| Depth | Budget | Persistent minus release FAL [95% CI] | Persistent minus fixed cut FAL [95% CI] |',
        '|---|---:|---|---|']
    for depth in DEPTHS:
        for budget in BUDGETS:
            lines.append(f'| {depth} | {budget} | {original.show(contrast(depth,budget,PERSIST,RELEASE))} | '
                         f'{original.show(contrast(depth,budget,PERSIST,CUT))} |')
    lines += ['', '| Depth | Budget | Release excess FAL [95% CI] | Persistent excess FAL [95% CI] | Fixed-cut excess FAL [95% CI] |',
              '|---|---:|---|---|---|']
    for depth in DEPTHS:
        for budget in BUDGETS:
            cells=' | '.join(original.show(contrast(depth,budget,v,CONTROL)) for v in VARIANTS)
            lines.append(f'| {depth} | {budget} | {cells} |')
    lines += ['', '| Depth | Variant | Budget | Realized relative-cost link-hours [95% CI] | Distinct links [95% CI] |',
              '|---|---|---:|---|---|']
    for row in result['estimates']:
        if row['class']=='all' and row['metric']=='realized_link_hours' and row['variant']!=CONTROL:
            footprint=next(r for r in result['estimates'] if (r['depth'],r['variant'],r['budget'],r['metric'],r['class'])==
                           (row['depth'],row['variant'],row['budget'],'distinct_links_touched_count','all'))
            lines.append(f'| {row["depth"]} | {row["variant"]} | {row["budget"]} | {original.show(row)} | {original.show(footprint)} |')
    lines += ['', 'The comparison changes realized persistence/exposure through an unused-slot rule. Retargeting overhead, mobility, coordination and sensing cost remain unmodeled. '
        'Distinct-link campaign footprint is not the same quantity as simultaneous budget. Full exposure can differ from the strong route-feedback policy that releases '
        'targets during transport interruptions; the results must not be paraphrased as a universal ranking of adaptive and fixed attackers.','',
        'All methods and controls matched exact arrival and fixed-arrival-horizon environmental digests. Concurrent caps, full-exposure retention for the persistent '
        'variant and key conservation were checked for every run. Protected previous source, manifest and analysis hashes remained unchanged. '
        'Raw baseline/FAL/excess values, per-class counts, cost integrals, retention decisions and changed target sets are preserved.','',
        f'Confirmation source/runtime hash: `{result["source_hash"]}`. '
        f'Completed runs: 126. Coordinator wall time: {result["wall_s"]:.1f}s. '
        f'Sum of recorded per-run wall durations: {result["sum_rollout_wall_s"]:.1f}s, overlapping when workers run concurrently.','',
        'Outputs: results/revision/online_persistence/analysis.json, per_seed_per_class.csv, estimates.csv, paired_contrasts.csv and runs/*.json. '
        'The manifest includes the original exposure-log audit and the post-hoc protocol. No further empirical study is implied by these results.','']
    return '\n'.join(lines)


def analyze(output=OUT,report=REPORT):
    output=Path(output)
    manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('completed_runs')!=126 or not manifest.get('previous_artifacts_unchanged'):
        raise ValueError('The confirmation is not complete')
    if manifest['protocol_sha256']!=original.digest(protocol()):
        raise ValueError('Confirmation protocol mismatch')
    records=[original.load_run(output/'runs'/f'{item["key"]}.json') for item in manifest['runs']]
    indexed={}
    for row in records:
        key=(row['depth'],row['variant'],row['budget'],row['seed'])
        if key in indexed or row['source_hash']!=manifest['source_hash']:
            raise ValueError('Duplicate run or source mismatch')
        indexed[key]=row
    expected={(d,v,b,s) for d in DEPTHS for v in VARIANTS for b in BUDGETS for s in SEEDS}
    expected|={(d,CONTROL,0,s) for d in DEPTHS for s in SEEDS}
    if set(indexed)!=expected:
        raise ValueError('Incomplete confirmation grid')
    def select(d,v,b):
        return [indexed[d,v,b,s] for s in SEEDS]
    estimates=[]
    contrasts=[]
    metrics=('forced_entitled_fraction','availability','qualified_availability','degraded_arrival_fraction','forced_payload_fraction')
    costs=('realized_link_hours','distinct_links_touched_count','retarget_count','retained_slot_fills','initialized_slot_fills')
    for depth in DEPTHS:
        control=select(depth,CONTROL,0)
        for variant,budget in [(CONTROL,0)]+[(v,b) for v in VARIANTS for b in BUDGETS]:
            rows=select(depth,variant,budget)
            paired(rows,control,'availability')
            for group in ('all','C2','ISR','LOG'):
                for metric in metrics:
                    estimates.append({'depth':depth,'variant':variant,'budget':budget,'class':group,'metric':metric,
                                      **original.interval([value(r,metric,group) for r in rows])})
                    if variant!=CONTROL:
                        contrasts.append({'depth':depth,'budget':budget,'treatment':variant,'control':CONTROL,
                            'class':group,'metric':metric,**paired(rows,control,metric,group)})
            for metric in costs:
                estimates.append({'depth':depth,'variant':variant,'budget':budget,'class':'all','metric':metric,
                                  **original.interval([value(r,metric) for r in rows])})
        for budget in BUDGETS:
            for baseline in (RELEASE,CUT):
                a,b=select(depth,PERSIST,budget),select(depth,baseline,budget)
                for group in ('all','C2','ISR','LOG'):
                    for metric in metrics:
                        contrasts.append({'depth':depth,'budget':budget,'treatment':PERSIST,'control':baseline,
                            'class':group,'metric':metric,**paired(a,b,metric,group)})
                for metric in costs:
                    contrasts.append({'depth':depth,'budget':budget,'treatment':PERSIST,'control':baseline,
                        'class':'all','metric':metric,**paired(a,b,metric)})
    flat=[]
    for row in records:
        control=indexed[row['depth'],CONTROL,0,row['seed']]
        for group in ('all','C2','ISR','LOG'):
            raw=row['summary'][group]['forced_entitled_fraction']
            baseline=control['summary'][group]['forced_entitled_fraction']
            flat.append({k:row[k] for k in ('depth','variant','budget','seed','source_hash','run_key')}|
                {'class':group,**row['summary'][group],
                 'baseline_fal':baseline,'excess_fal':raw-baseline if raw is not None and baseline is not None else None,
                 'realized_link_hours':value(row,'realized_link_hours'),
                 'distinct_links_touched':value(row,'distinct_links_touched_count'),
                 'retarget_count':value(row,'retarget_count'),
                 'maximum_concurrent_relative_cost':row['attack']['maximum_concurrent_relative_cost'],
                 'arrival_sha256':row['arrival_sha256'],'environment_trace_sha256':row['attack']['environment_trace_sha256']})
    result={'schema_version':1,'classification':protocol()['classification'],'source_hash':manifest['source_hash'],
        'protocol':manifest['protocol'],'prior_mechanism_audit':manifest['prior_mechanism_audit'],
        'completed_runs':126,'wall_s':manifest['wall_s'],'sum_rollout_wall_s':sum(r['wall_s'] for r in records),
        'estimates':estimates,'contrasts':contrasts,'per_seed_per_class':flat,
        'bootstrap':{'resamples':20000,'seed':71,'units':6,'confidence':0.95},
        'previous_artifacts_unchanged':True,'completed_utc':datetime.now(timezone.utc).isoformat()}
    result['analysis_sha256']=original.digest(result)
    original.write_json(output/'analysis.json',result)
    original.write_csv(output/'per_seed_per_class.csv',flat)
    original.write_csv(output/'estimates.csv',estimates)
    original.write_csv(output/'paired_contrasts.csv',contrasts)
    Path(report).parent.mkdir(parents=True,exist_ok=True)
    Path(report).write_text(report_text(result),encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('run','analyze','all'),default='all')
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--describe',action='store_true')
    args=parser.parse_args()
    if not 1<=args.workers<=3:
        parser.error('This bounded confirmation permits one to three workers')
    if args.self_test:
        tests=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_revision_online_persistence.py')
        return 0 if unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful() else 1
    if args.describe:
        print(json.dumps(original.safe({'protocol':protocol(),'source':source_metadata(),
            'prior_mechanism_audit':prior_mechanism_audit()}),indent=2))
        return 0
    if args.phase in ('run','all'):
        run_study(args.workers)
    if args.phase in ('analyze','all'):
        result=analyze()
        print(f'Completed 126-run persistence diagnostic: {REPORT}',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
