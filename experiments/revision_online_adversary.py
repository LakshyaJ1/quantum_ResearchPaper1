"""Route-feedback generation suppression on finite-reserve relay chains.

Standalone study: no frozen simulator/controller modules are edited. The online
adversary sees committed route use and current classical reachability, not key
values, inventory levels, future arrivals, or future environmental transitions.
"""
from __future__ import annotations

import os
for _thread_variable in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[_thread_variable]='1'

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict,replace
from datetime import datetime,timezone
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import networkx as nx
import numpy as np
from qkdsim.config import (AccountingConfig,AdversaryConfig,OutageConfig,PhysicsConfig,
                          ReservoirConfig,SimConfig,TRAFFIC_CLASSES)
from qkdsim.network import candidate_paths,chain_topology
from revision.metrics import summarize
from revision.scenarios import Case,RevisionSimulator

METHODS=('static_betweenness','weighted_cut','online_route_feedback')
CONTROL_METHOD='no_attack'
DEPTHS=(2,4,6)
BUDGETS=(1,2)
SEEDS=tuple(range(3000,3006))
UPDATE_SECONDS=60
UNOBSERVED_WEIGHT=0.01
OUT=ROOT/'results/revision/online_adversary'
REPORT=ROOT/'docs/revision/ONLINE_ATTACK_RESULTS.md'


def safe(value):
    if isinstance(value,dict):
        return {str(k):safe(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [safe(v) for v in value]
    if isinstance(value,(float,np.floating)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value,np.integer):
        return int(value)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(safe(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write_json(path,value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(f'.{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp')
    try:
        temp.write_text(json.dumps(safe(value),indent=2,allow_nan=False),encoding='utf-8')
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


class RouteFeedbackSimulator(RevisionSimulator):
    def __init__(self,topo,cfg,case,traffic,method):
        if method not in (*METHODS,CONTROL_METHOD) or case.buffer_policy!='retain' or case.attack_surface!='generation':
            raise ValueError('This registered study only supports retained-buffer generation attacks')
        self.method=method
        self.recent_routes=Counter()
        self.lifetime_routes=Counter()
        self.quantum_route_observations=0
        self._observation_digest=hashlib.sha256()
        self._environment_digest=hashlib.sha256()
        self._route_ids={}
        self.route_registry={}
        self.feedback_updates=[]
        self.attack_changes=[]
        self.retarget_count=0
        self.distinct_links_touched=set()
        self.relative_cost_link_seconds=0.0
        self.maximum_concurrent_cost=0.0
        self._last_attack=None
        self._next_update=case.attack_start_s
        boot=replace(case,attack_method='weighted_cut' if method in ('online_route_feedback',CONTROL_METHOD) else method)
        super().__init__(topo,cfg,boot,traffic)
        self.case=replace(case,attack_method=method)
        if method=='online_route_feedback':
            self._chosen_attack=[]
        for source,target in self._endpoints:
            for path in candidate_paths(topo,source,target):
                self._route_id(tuple(sorted(topo.path_links(path))))

    def _route_id(self,signature):
        if signature not in self._route_ids:
            identifier=f'p{len(self._route_ids)}'
            self._route_ids[signature]=identifier
            self.route_registry[identifier]=[list(edge) for edge in signature]
        return self._route_ids[signature]

    def _try_grade(self,session,grade,t):
        if grade=='G4':
            return super()._try_grade(session,grade,t)
        before={edge:store.consumed_bits for edge,store in self.topo.stores.items()}
        served=super()._try_grade(session,grade,t)
        if served:
            committed=tuple(sorted(edge for edge,store in self.topo.stores.items()
                                   if store.consumed_bits>before[edge]))
            if committed:
                self.recent_routes[committed]+=1
                self.lifetime_routes[committed]+=1
                self.quantum_route_observations+=1
                route=self._route_id(committed)
                self._observation_digest.update(json.dumps((session.sid,t,grade,route),separators=(',',':')).encode())
        return served

    def select_online_targets(self):
        weighted=[]
        for source,target in self._endpoints:
            for path in candidate_paths(self.topo,source,target):
                edges=tuple(sorted(self.topo.path_links(path)))
                # An accepted-key relay requires classical reachability. An
                # empty inventory is not observable to this selector.
                if all(not self.topo.links[edge].outage for edge in edges):
                    weighted.append((set(edges),float(self.recent_routes[edges])
                                     if self.recent_routes[edges] else UNOBSERVED_WEIGHT))
        remaining=float(self.case.attack_budget)
        chosen=[]
        while weighted:
            candidates={edge for edges,_ in weighted for edge in edges
                        if edge not in chosen and self.attack_costs[edge]<=remaining+1e-10}
            if not candidates:
                break
            # Fixed canonical edge order resolves exact coverage/cost ties.
            edge=min(candidates,key=lambda e:(
                -sum(weight for path,weight in weighted if e in path)/self.attack_costs[e],e))
            chosen.append(edge)
            remaining-=self.attack_costs[edge]
            weighted=[(path,weight) for path,weight in weighted if edge not in path]
        return chosen

    def _apply_generation_selection(self,active):
        self._adv_links=set(self._chosen_attack) if active else set()
        for edge,link in self.topo.links.items():
            link.outage=self.environment_transport[edge]
            link.excess_qber=max(self.case.delta_e if edge in self._adv_links else 0.0,
                                 1.0 if self.environment_generation[edge] else 0.0)
        self._previous_generation_failure={edge for edge,link in self.topo.links.items()
                                           if link.current_rate_bps(self.cfg.physics)<=0}

    def _tick_outages(self):
        # Exactly one parent tick: same exogenous random draws for all methods.
        super()._tick_outages()
        active=self.case.attack_start_s<=self.now_s<self.case.attack_start_s+self.case.attack_duration_s
        if self.method=='online_route_feedback' and active and self.now_s>=self._next_update-1e-9:
            observed={self._route_id(route):count for route,count in self.recent_routes.items()}
            self._chosen_attack=self.select_online_targets()
            self.feedback_updates.append({'time_s':self.now_s,'recent_committed_route_counts':observed,
                                          'selected_edges':[list(e) for e in self._chosen_attack]})
            self.recent_routes.clear()
            self._next_update=self.now_s+UPDATE_SECONDS
            self._apply_generation_selection(active)
        current=tuple(sorted(self._adv_links))
        cost=sum(self.attack_costs[edge] for edge in current)
        if cost>self.case.attack_budget+1e-10:
            raise RuntimeError('Concurrent attack budget exceeded')
        self.maximum_concurrent_cost=max(self.maximum_concurrent_cost,cost)
        self.relative_cost_link_seconds+=cost*self.cfg.tick_s
        self.distinct_links_touched.update(current)
        if self._last_attack!=current:
            kind=('initial' if self._last_attack is None else 'retarget' if active else 'release')
            if kind=='retarget':
                self.retarget_count+=1
            self.attack_changes.append({'time_s':self.now_s,'kind':kind,
                'selected_edges':[list(e) for e in current],'concurrent_relative_cost':cost})
            self._last_attack=current
        if self.now_s<self.cfg.horizon_s:
            state=[]
            for edge in self.topo.all_link_keys():
                state.extend((int(self.environment_transport[edge]),int(self.environment_generation[edge])))
            self._environment_digest.update(bytes(state))

    def attack_audit(self):
        return {'method':self.method,'simultaneous_budget':self.case.attack_budget,
            'maximum_concurrent_relative_cost':self.maximum_concurrent_cost,
            'relative_cost_link_seconds':self.relative_cost_link_seconds,
            'distinct_links_touched':[list(e) for e in sorted(self.distinct_links_touched)],
            'distinct_links_touched_count':len(self.distinct_links_touched),
            'retarget_count':self.retarget_count,'attack_changes':self.attack_changes,
            'feedback_update_period_s':UPDATE_SECONDS,'unobserved_path_weight':UNOBSERVED_WEIGHT,
            'feedback_updates':self.feedback_updates,'route_registry':self.route_registry,
            'lifetime_committed_route_counts':{self._route_id(r):n for r,n in self.lifetime_routes.items()},
            'quantum_route_observations':self.quantum_route_observations,
            'observation_sha256':self._observation_digest.hexdigest(),
            'environment_trace_sha256':self._environment_digest.hexdigest(),
            'retarget_overhead_modelled':False}


def make_chain_simulator(depth,method,budget,seed,case=None):
    valid=(method==CONTROL_METHOD and budget==0) or (method in METHODS and budget in BUDGETS)
    if depth not in DEPTHS or not valid:
        raise ValueError('Unregistered depth, method or concurrent budget')
    case=case or Case()
    if case.buffer_policy!='retain' or case.warmup_s!=0 or case.fail_mode!='FAIL_DEGRADED':
        raise ValueError('Study requires retained keys, zero warmup and fail-degraded operation')
    case=replace(case,attack_budget=budget,attack_method=method,attack_surface='generation',
                 attack_start_s=0.0,attack_duration_s=case.horizon_s)
    base=ReservoirConfig()
    minimum=round(base.m_min*case.reservoir_scale)
    maximum=round(base.m_max*case.reservoir_scale)
    initial=minimum+case.initial_spendable_fraction*(maximum-minimum)
    reservoir=replace(base,m_min=minimum,m_max=maximum,m_thr=round(base.m_thr*case.reservoir_scale),
                      m_initial_frac=initial/maximum)
    cfg=SimConfig(horizon_s=case.horizon_s,warmup_s=0,seed=seed,routing=case.routing,
        fail_mode=case.fail_mode,reservoir=reservoir,accounting=AccountingConfig(n_auth=case.n_auth),
        physics=PhysicsConfig(gamma=case.gamma,e_abort=case.e_abort),adversary=AdversaryConfig(),
        outage=OutageConfig(),pqc_setup_s=0.35 if case.fallback=='online_kem' else 0)
    topo=chain_topology(depth,reservoir)
    for link in topo.links.values():
        link.nominal_rate_bps*=case.rate_scale
    traffic=tuple(replace(tc,arrival_rate=tc.arrival_rate*case.isr_scale) if tc.name=='ISR' else tc
                  for tc in TRAFFIC_CLASSES)
    return RouteFeedbackSimulator(topo,cfg,case,traffic,method)


def source_metadata():
    paths=sorted((ROOT/'qkdsim').glob('*.py'))+[
        ROOT/'revision/scenarios.py',ROOT/'revision/metrics.py',Path(__file__)]
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    runtime={'python':sys.version,'numpy':np.__version__,'networkx':nx.__version__,
             'os_name':os.name,'windows':list(sys.getwindowsversion()) if os.name=='nt' else None}
    return {'files':files,'runtime':runtime,'source_hash':digest({'files':files,'runtime':runtime})}


def protocol():
    return {'depths':DEPTHS,'methods':METHODS,'simultaneous_budgets':BUDGETS,'seed_ids':SEEDS,
        'case_defaults':asdict(Case()),'update_period_s':UPDATE_SECONDS,
        'unobserved_path_weight':UNOBSERVED_WEIGHT,'tie_rule':'canonical undirected edge lexicographic order',
        'requested_runs':126,'attacked_runs':108,'shared_control_runs':18,
        'thresholds':[0.1,0.25,0.5],'excess_thresholds':[0.5],
        'FAL_denominator':'all G1/G2-entitled arrivals, including blocked requests',
        'retarget_overhead_modelled':False,'zero_budget_control_included':True,
        'environment_digest_interval':'fixed arrival horizon, excluding deadline drain'}


def load_run(path):
    record=json.loads(Path(path).read_text(encoding='utf-8'))
    expected=record.pop('record_sha256',None)
    if expected!=digest(record):
        raise ValueError(f'Run integrity mismatch: {path}')
    record['record_sha256']=expected
    return record


def run_job(job):
    key=digest({k:job[k] for k in ('depth','method','budget','seed','source_hash')})
    path=Path(job['output'])/'runs'/f'{key}.json'
    if path.exists():
        record=load_run(path)
        if record['source_hash']!=job['source_hash']:
            raise ValueError('Stale source in online study cache')
        return {'cached':True,'key':key,'wall_s':record['wall_s']}
    started=time.perf_counter()
    sim=make_chain_simulator(job['depth'],job['method'],job['budget'],job['seed'])
    result=sim.run()
    summary={group:summarize(result,None if group=='all' else group) for group in ('all','C2','ISR','LOG')}
    counters={group:result.outcome_metrics(None if group=='all' else group) for group in ('all','C2','ISR','LOG')}
    arrivals=sorted((s.sid,s.cls,s.arrival_t,s.payload_bits,s.src,s.dst,s.authorised_floor,s.deadline_s)
                    for s in result.sessions)
    balance=(result.initial_stored_bits+result.full_generated_bits-result.full_consumed_bits
             -result.full_discarded_bits-result.final_stored_bits)
    if abs(balance)>1e-2 or sim.purged_bits!=0:
        raise RuntimeError('Retained-buffer accounting failed')
    record=safe({'schema_version':1,'run_key':key,'source_hash':job['source_hash'],
        'depth':job['depth'],'method':job['method'],'budget':job['budget'],'seed':job['seed'],
        'case':asdict(sim.case),'summary':summary,'counters':counters,
        'arrival_sha256':digest(arrivals),'attack':sim.attack_audit(),
        'accounting':{'initial_stored_bits':result.initial_stored_bits,'final_stored_bits':result.final_stored_bits,
            'generated_bits_full':result.full_generated_bits,'consumed_bits_full':result.full_consumed_bits,
            'discarded_bits_full':result.full_discarded_bits,'purged_bits':sim.purged_bits,
            'conservation_residual_bits':balance},'wall_s':time.perf_counter()-started})
    record['record_sha256']=digest(record)
    write_json(path,record)
    return {'cached':False,'key':key,'wall_s':record['wall_s']}


def run_study(workers=1,output=OUT):
    output=Path(output)
    meta=source_metadata()
    specification=protocol()
    path=output/'manifest.json'
    if path.exists():
        previous=json.loads(path.read_text(encoding='utf-8'))
        if previous['source_hash']!=meta['source_hash'] or previous['protocol_sha256']!=digest(specification):
            raise ValueError('Archive prior study explicitly after source/protocol changes')
    manifest={'schema_version':1,**meta,'protocol':specification,'protocol_sha256':digest(specification),
              'started_utc':datetime.now(timezone.utc).isoformat(),'workers':workers}
    write_json(path,manifest)
    jobs=[dict(depth=depth,method=method,budget=budget,seed=seed,source_hash=meta['source_hash'],output=str(output))
          for depth in DEPTHS for method in METHODS for budget in BUDGETS for seed in SEEDS]
    jobs += [dict(depth=depth,method=CONTROL_METHOD,budget=0,seed=seed,
                  source_hash=meta['source_hash'],output=str(output)) for depth in DEPTHS for seed in SEEDS]
    started=time.perf_counter()
    outcomes=[]
    def collect(iterator):
        for index,result in enumerate(iterator,1):
            outcomes.append(result)
            if index%6==0 or index==len(jobs):
                print(f'{index}/126 complete; {sum(r["cached"] for r in outcomes)} reused; '
                      f'{time.perf_counter()-started:.1f}s elapsed',flush=True)
    if workers==1:
        collect(map(run_job,jobs))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            collect(pool.map(run_job,jobs))
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),
        wall_s=time.perf_counter()-started,completed_runs=len(outcomes),runs=outcomes)
    write_json(path,manifest)
    return manifest


def interval(values):
    if len(values)!=6:
        raise ValueError('Require all six registered seed values')
    if any(v is None or not math.isfinite(v) for v in values):
        return {'mean':None,'ci_low':None,'ci_high':None,'n_seeds':6,'status':'undefined_denominator'}
    array=np.asarray(values,dtype=float)
    indices=np.random.default_rng(71).integers(0,6,size=(20000,6))
    means=array[indices].mean(axis=1)
    low,high=np.quantile(means,[0.025,0.975])
    return {'mean':float(array.mean()),'ci_low':float(low),'ci_high':float(high),
            'n_seeds':6,'status':'defined'}


def threshold_assessment(rows,threshold):
    means=[r['budget'] for r in rows if r['mean'] is not None and r['mean']>=threshold]
    confident=[r['budget'] for r in rows if r['ci_low'] is not None and r['ci_low']>=threshold]
    return {'threshold':threshold,'minimum_tested_budget_crossing_mean':min(means) if means else None,
        'minimum_tested_budget_with_lower_ci_crossing':min(confident) if confident else None,
        'global_minimum_identified':False,'tested_budgets':[1,2],
        'interpretation':'Smallest observed crossing among tested concurrent budgets {1,2}; not a global optimum'}


def value(row,metric,group='all'):
    if metric in ('retarget_count','distinct_links_touched_count','relative_cost_link_seconds'):
        return row['attack'][metric]
    if metric=='forced_all_arrival_fraction':
        return row['counters'][group]['forced_below_its_arrival_fraction']
    return row['summary'][group][metric]


def indexed(rows):
    result={}
    for row in rows:
        if row['seed'] in result:
            raise ValueError('Duplicate paired seed')
        result[row['seed']]=row
    if set(result)!=set(SEEDS):
        raise ValueError('Need all six registered matched seeds')
    return result


def paired(treatment,control,metric,group='all'):
    a,b=indexed(treatment),indexed(control)
    differences=[]
    for seed in SEEDS:
        if a[seed]['arrival_sha256']!=b[seed]['arrival_sha256'] or (
            a[seed]['attack']['environment_trace_sha256']!=b[seed]['attack']['environment_trace_sha256']):
            raise ValueError('Counterfactual arrival/environment trace mismatch')
        x,y=value(a[seed],metric,group),value(b[seed],metric,group)
        differences.append(x-y if x is not None and y is not None else None)
    return interval(differences)


def write_csv(path,rows):
    columns=list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def show(row):
    if row.get('mean') is None:
        return 'undefined'
    return f'{row["mean"]:.4f} [{row["ci_low"]:.4f}, {row["ci_high"]:.4f}]'


def render_report(analysis):
    estimates=analysis['estimates']
    contrasts=analysis['contrasts']
    def absolute(depth,method,budget,metric='forced_entitled_fraction'):
        return next(r for r in estimates if (r['depth'],r['method'],r['budget'],r['metric'],r['class'])==
                    (depth,method,budget,metric,'all'))
    def excess(depth,method,budget):
        return next(r for r in contrasts if (r['depth'],r['treatment'],r['control'],r['budget'],r['metric'],r['class'])==
                    (depth,method,CONTROL_METHOD,budget,'forced_entitled_fraction','all'))
    lines=['# Online route-feedback adversary results','',
        'This standalone study compares fixed all-pairs betweenness, a weighted structural cut, and an online route-feedback selector '
        'on two-path relay chains of depth 2, 4 and 6. Each primary path has a lateral alternative one hop longer. '
        'Concurrent attack budgets are one or two relative-cost units. Six paired seeds are used for every cell. '
        'Eighteen shared no-attack runs supply depth/seed-matched controls, giving 126 completed runs.','',
        'All runs last 24 hours with no warmup exclusion, initial spendable stock at 2% of the reservoir range, ISR arrival scale 0.1, '
        'n_auth = 7, independent environmental generation/transport processes and fail-degraded service. '
        'Generator suppression preserves accepted stored keys. These are explicit model assumptions, not measured attack powers or hardware certification.','',
        'The online selector updates every 60 seconds. It observes only genuinely committed positive-key relay routes in the preceding window '
        'and current classical reachability. Unobserved viable alternatives receive weight 0.01; observed paths receive their count of successful relay events. '
        'At each choice it maximizes uncovered route weight per relative edge cost, with canonical undirected-edge lexicographic ties, '
        'and removes covered paths before spending the next slot. It releases its previous set when installing the new one. '
        'At time zero all viable paths have the same prior weight. It sees neither key contents/inventory levels nor future arrivals or outages. '
        'This is a strong modeled controller-observing adversary, not a proof of optimal interdiction.','',
        'FAL here counts G1/G2-entitled requests delivered at G3/G4 divided by all G1/G2-entitled arrivals, including blocked requests. '
        'The separate all-arrival forced-loss fraction and below-floor fraction are also exported. '
        'Excess FAL subtracts the matched no-attack fraction within each seed. All 95% intervals use 20,000 paired seed bootstrap resamples '
        'with seed 71 and six independent seed-level units. Negative excess and inconclusive intervals are retained. '
        'They quantify simulation-realization uncertainty, not physical-model uncertainty; multiple comparisons are exploratory.','',
        '| Depth | Concurrent budget | Static betweenness raw FAL [95% CI] | Weighted cut raw FAL [95% CI] | Online raw FAL [95% CI] |',
        '|---|---:|---|---|---|']
    for depth in DEPTHS:
        for budget in BUDGETS:
            cells=' | '.join(show(absolute(depth,m,budget)) for m in METHODS)
            lines.append(f'| {depth} | {budget} | {cells} |')
    lines += ['', '| Depth | Concurrent budget | Static excess FAL [95% CI] | Cut excess FAL [95% CI] | Online excess FAL [95% CI] |',
              '|---|---:|---|---|---|']
    for depth in DEPTHS:
        for budget in BUDGETS:
            cells=' | '.join(show(excess(depth,m,budget)) for m in METHODS)
            lines.append(f'| {depth} | {budget} | {cells} |')
    lines += ['', 'Threshold assessments identify only the smallest tested concurrent budget in {1, 2} whose mean excess FAL reaches 0.5. '
        'A separate column requires the lower confidence limit to reach 0.5. An empty crossing means it was not established on this tested grid. '
        'This is not a universal two-link result or a global optimum, and it does not equate the number of distinct links visited during a campaign with concurrent attack capacity.','',
        '| Depth | Method | Smallest tested budget with mean excess FAL >= 0.5 | Smallest tested budget with lower CI >= 0.5 |',
        '|---|---|---|---|']
    for row in analysis['thresholds']:
        if row['basis']=='excess_fal_vs_no_attack':
            first=row['minimum_tested_budget_crossing_mean']
            lower=row['minimum_tested_budget_with_lower_ci_crossing']
            lines.append(f'| {row["depth"]} | {row["method"]} | {first if first is not None else "not established"} | '
                         f'{lower if lower is not None else "not established"} |')
    lines += ['', 'Equal concurrent budget caps are the primary comparison. Actual link-time cost is separately measured as the integral '
        'of selected relative edge cost over time; online control may leave slots unused when no viable uncovered route remains. '
        'Retarget latency, equipment relocation, sensing, coordination and switching overhead are unmodeled. '
        'Distinct links touched is a campaign-footprint count and cannot be interpreted as the same cost as the simultaneous slot budget.','',
        '| Depth | Method | Budget | Mean retarget changes | Mean distinct links touched | Mean relative-cost link-hours |',
        '|---|---|---:|---:|---:|---:|']
    for depth in DEPTHS:
        for method in METHODS:
            for budget in BUDGETS:
                r=absolute(depth,method,budget,'retarget_count')['mean']
                d=absolute(depth,method,budget,'distinct_links_touched_count')['mean']
                c=absolute(depth,method,budget,'relative_cost_link_seconds')['mean']/3600
                lines.append(f'| {depth} | {method} | {budget} | {r:.2f} | {d:.2f} | {c:.2f} |')
    lines += ['', 'Every changed attack set, every online update and recent route-count input, the route registry, total route observations, '
        'arrival digest, fixed-arrival-horizon environment digest, per-class outcomes and key accounting are retained in the per-seed JSON files. '
        'All paired methods and controls passed exact arrival/environment digest checks, no run exceeded its concurrent budget, '
        'and retained-buffer key accounting passed in every run. The fixed digest interval excludes policy-dependent deadline drain lengths.','',
        f'Source/runtime fingerprint: `{analysis["source_hash"]}`. '
        f'Unique recorded runs: {analysis["completed_runs"]}. '
        f'Coordinator elapsed time: {analysis["coordinator_wall_s"]:.1f} seconds. '
        f'Sum of per-run wall durations: {analysis["sum_rollout_wall_s"]:.1f} seconds; these overlap if workers run in parallel.','',
        'Machine-readable results are in results/revision/online_adversary/: analysis.json, per_seed_per_class.csv, estimates.csv, '
        'paired_contrasts.csv, thresholds.csv and runs/*.json. Raw and excess threshold rows for all registered methods are retained without selecting a favorable result.','']
    return '\n'.join(lines)


def analyze_study(output=OUT,report_path=REPORT):
    output=Path(output)
    manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('completed_runs')!=126 or not manifest.get('completed_utc'):
        raise ValueError('The registered 126-run study is not complete')
    if manifest['protocol_sha256']!=digest(protocol()):
        raise ValueError('Study protocol changed')
    records=[]
    for entry in manifest['runs']:
        row=load_run(output/'runs'/f'{entry["key"]}.json')
        if row['source_hash']!=manifest['source_hash'] or row['run_key']!=entry['key']:
            raise ValueError('Run source/key mismatch')
        if row['attack']['maximum_concurrent_relative_cost']>row['budget']+1e-10:
            raise ValueError('Recorded concurrent budget exceeded')
        if row['attack']['relative_cost_link_seconds']>row['budget']*row['case']['horizon_s']+1e-6:
            raise ValueError('Link-time budget exceeded')
        if abs(row['accounting']['conservation_residual_bits'])>1e-2 or row['accounting']['purged_bits']!=0:
            raise ValueError('Retained-key conservation mismatch')
        records.append(row)
    mapping={}
    for row in records:
        key=(row['depth'],row['method'],row['budget'],row['seed'])
        if key in mapping:
            raise ValueError('Duplicate run')
        mapping[key]=row
    expected={(d,m,b,s) for d in DEPTHS for m in METHODS for b in BUDGETS for s in SEEDS}
    expected|={(d,CONTROL_METHOD,0,s) for d in DEPTHS for s in SEEDS}
    if set(mapping)!=expected:
        raise ValueError('Incomplete or altered experiment matrix')
    def select(depth,method,budget):
        return [mapping[depth,method,budget,s] for s in SEEDS]
    metrics=('forced_entitled_fraction','forced_all_arrival_fraction','availability',
             'qualified_availability','degraded_arrival_fraction','forced_payload_fraction')
    cost_metrics=('retarget_count','distinct_links_touched_count','relative_cost_link_seconds')
    estimates=[]
    contrasts=[]
    thresholds=[]
    for depth in DEPTHS:
        control=select(depth,CONTROL_METHOD,0)
        for method,budget in [(CONTROL_METHOD,0)]+[(m,b) for m in METHODS for b in BUDGETS]:
            rows=select(depth,method,budget)
            # Verify counterfactual trace equality even for undefined metrics.
            paired(rows,control,'availability')
            for group in ('all','C2','ISR','LOG'):
                for metric in metrics:
                    estimates.append({'depth':depth,'method':method,'budget':budget,'class':group,'metric':metric,
                                      **interval([value(r,metric,group) for r in rows])})
                    if method!=CONTROL_METHOD:
                        contrasts.append({'depth':depth,'treatment':method,'control':CONTROL_METHOD,
                            'budget':budget,'class':group,'metric':metric,
                            **paired(rows,control,metric,group)})
            for metric in cost_metrics:
                estimates.append({'depth':depth,'method':method,'budget':budget,'class':'all','metric':metric,
                                  **interval([value(r,metric) for r in rows])})
        for budget in BUDGETS:
            for treatment,baseline in (('online_route_feedback','static_betweenness'),
                    ('online_route_feedback','weighted_cut'),('weighted_cut','static_betweenness')):
                a,b=select(depth,treatment,budget),select(depth,baseline,budget)
                for group in ('all','C2','ISR','LOG'):
                    for metric in metrics:
                        contrasts.append({'depth':depth,'treatment':treatment,'control':baseline,'budget':budget,
                            'class':group,'metric':metric,**paired(a,b,metric,group)})
        for method in METHODS:
            raw=[r for r in estimates if r['depth']==depth and r['method']==method and
                 r['class']=='all' and r['metric']=='forced_entitled_fraction']
            excess=[r for r in contrasts if r['depth']==depth and r['treatment']==method and
                    r['control']==CONTROL_METHOD and r['class']=='all' and r['metric']=='forced_entitled_fraction']
            for threshold in (0.1,0.25,0.5):
                thresholds.append({'depth':depth,'method':method,'basis':'raw_fal',**threshold_assessment(raw,threshold)})
            thresholds.append({'depth':depth,'method':method,'basis':'excess_fal_vs_no_attack',
                               **threshold_assessment(excess,0.5)})
    flat=[]
    for row in records:
        for group in ('all','C2','ISR','LOG'):
            flat.append({'depth':row['depth'],'method':row['method'],'budget':row['budget'],'seed':row['seed'],
                'class':group,'source_hash':row['source_hash'],'run_key':row['run_key'],**row['summary'][group],
                'forced_all_arrival_fraction':value(row,'forced_all_arrival_fraction',group),
                'arrival_sha256':row['arrival_sha256'],'environment_trace_sha256':row['attack']['environment_trace_sha256'],
                'retarget_count':row['attack']['retarget_count'],
                'distinct_links_touched_count':row['attack']['distinct_links_touched_count'],
                'relative_cost_link_seconds':row['attack']['relative_cost_link_seconds'],
                'maximum_concurrent_relative_cost':row['attack']['maximum_concurrent_relative_cost']})
    analysis={'schema_version':1,'source_hash':manifest['source_hash'],'protocol':manifest['protocol'],
        'completed_runs':126,'coordinator_wall_s':manifest['wall_s'],
        'sum_rollout_wall_s':sum(r['wall_s'] for r in records),
        'estimates':estimates,'contrasts':contrasts,'thresholds':thresholds,'per_seed_per_class':flat,
        'bootstrap':{'resamples':20000,'seed':71,'units':6,'confidence':0.95},
        'FAL_denominator':'all G1/G2-entitled arrivals including blocked requests',
        'all_arrival_FAL_denominator':'all requests in the selected class/cohort',
        'completed_utc':datetime.now(timezone.utc).isoformat()}
    analysis['analysis_sha256']=digest(analysis)
    text=render_report(analysis)
    write_json(output/'analysis.json',analysis)
    write_csv(output/'per_seed_per_class.csv',flat)
    write_csv(output/'estimates.csv',estimates)
    write_csv(output/'paired_contrasts.csv',contrasts)
    threshold_rows=[{**r,'tested_budgets':'1,2'} for r in thresholds]
    write_csv(output/'thresholds.csv',threshold_rows)
    Path(report_path).parent.mkdir(parents=True,exist_ok=True)
    Path(report_path).write_text(text,encoding='utf-8')
    return analysis


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('run','analyze','all'),default='all')
    parser.add_argument('--workers',type=int,default=1)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--describe',action='store_true')
    args=parser.parse_args()
    if not 1<=args.workers<=8:
        parser.error('Use one to eight workers')
    if args.self_test:
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_revision_online_adversary.py')
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if args.describe:
        print(json.dumps(safe({'protocol':protocol(),'source':source_metadata()}),indent=2,allow_nan=False))
        return 0
    if args.phase in ('run','all'):
        run_study(args.workers)
    if args.phase in ('analyze','all'):
        result=analyze_study()
        print(f'Analyzed {result["completed_runs"]} verified runs; report {REPORT}',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
