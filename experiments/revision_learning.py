"""Registered finite-budget CEM study; see docs/revision/learning_protocol.md.

No experiment runs at import. Use --describe for the fixed protocol and --phase
train/test/all to run it. Final-test evaluation requires an intact policy freeze.
"""
from __future__ import annotations

import os
for _thread_variable in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[_thread_variable] = '1'

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import networkx as nx
import numpy as np
from qkdsim.config import is_at_least
from qkdsim.sim import Outcome
from revision.metrics import summarize
from revision.policies import (BudgetedTablePolicy, BudgetGreedyPolicy,
    StrictFloorPolicy, CLASSES, DEFAULT_BUDGETS, N_STATES, N_ACTIONS)
from revision.scenarios import Case, make_simulator

OUTPUT = ROOT/'results/revision/learning'
FREEZE = ROOT/'results/revision/learning_policy_freeze.json'
REGIMES = ('short_nominal','full_nominal','full_robust')
POPULATION, ITERATIONS, RESTARTS = 10, 4, 2
OPTIMIZER_SEEDS = (7000,7001)
TRAIN_SEEDS = tuple(range(1000,1006))
VALIDATION_SEEDS = tuple(range(2000,2004))
TEST_SEEDS = tuple(range(5000,5012))
N_ELITES, PSEUDOCOUNT = 3, 0.5


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def json_safe(value):
    if isinstance(value, dict):
        return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value,(float,np.floating)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value,np.integer):
        return int(value)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(json_safe(value),sort_keys=True,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write_json(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(f'.{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp')
    try:
        temp.write_text(json.dumps(json_safe(value),indent=2,allow_nan=False),encoding='utf-8')
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def runtime_metadata():
    # platform.platform() reproducibly terminates this Windows host natively.
    return {'python':sys.version,'numpy':np.__version__,'networkx':nx.__version__,
            'os_name':os.name,'sys_platform':sys.platform,
            'windows_version':list(sys.getwindowsversion()) if os.name=='nt' else None}


def source_metadata():
    paths=sorted((ROOT/'qkdsim').glob('*.py'))+[
        ROOT/'revision/scenarios.py',ROOT/'revision/policies.py',
        ROOT/'revision/metrics.py',Path(__file__)]
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    metadata={'files':files,'runtime':runtime_metadata()}
    return {**metadata,'source_hash':digest(metadata)}


def training_conditions():
    nominal=Case()
    return [('nominal',nominal),('attack2',replace(nominal,attack_budget=2)),
        ('severe',replace(nominal,outage_model='correlated',
                          mean_uptime_s=900,mean_outage_s=600,rate_scale=0.5))]


def specification(condition, case, seed):
    return {'condition':condition,'case':asdict(case),'seed':seed}


def training_specs(regime):
    if regime not in REGIMES:
        raise ValueError(f'Unknown registered regime {regime}')
    if regime!='full_robust':
        case=Case(horizon_s=21600 if regime=='short_nominal' else 86400)
        return [specification('nominal',case,seed) for seed in TRAIN_SEEDS]
    return [specification(name,case,seed)
            for index,(name,case) in enumerate(training_conditions())
            for seed in TRAIN_SEEDS[index*2:index*2+2]]


def validation_specs():
    return [specification(name,case,seed) for name,case in training_conditions()
            for seed in VALIDATION_SEEDS]


def test_specs():
    base=Case()
    conditions=[('nominal',base),('attack2',replace(base,attack_budget=2)),
        ('overload_isr1',replace(base,isr_scale=1.0)),
        ('rate_half',replace(base,rate_scale=0.5)),
        ('correlated_weather',replace(base,outage_model='correlated',
                                      mean_uptime_s=900,mean_outage_s=600)),
        ('unseen_ring',replace(base,topology='ring')),
        ('unseen_parallel3_attack3',replace(base,topology='parallel3',attack_budget=3))]
    return [specification(name,case,seed) for name,case in conditions for seed in TEST_SEEDS]


def registered_protocol():
    return {'schema_version':1,'regimes':list(REGIMES),'states':N_STATES,'actions':N_ACTIONS,
        'population':POPULATION,'iterations':ITERATIONS,'restarts':RESTARTS,
        'optimizer_seeds':list(OPTIMIZER_SEEDS),'elite_count':N_ELITES,'pseudocount':PSEUDOCOUNT,
        'exception_budgets':DEFAULT_BUDGETS,'objective':'mean(A - 0.75 * degraded_arrival_fraction)',
        'tie_rule':'fewest adjacent action changes, then lexicographic table, then restart index',
        'train':{regime:training_specs(regime) for regime in REGIMES},
        'validation':validation_specs(),'test':test_specs(),
        'requested_training_rollouts':1440,'requested_validation_rollouts':72,
        'requested_test_rollouts':420}


def table_complexity(table):
    return sum(a!=b for a,b in zip(table,table[1:]))


def population(probabilities, size, incumbent, rng):
    if size<3 or probabilities.shape!=(N_STATES,N_ACTIONS):
        raise ValueError('Need at least three population slots and an 18x5 probability matrix')
    tables=[]
    for table in (tuple([0]*N_STATES),tuple([1]*N_STATES),tuple(incumbent)):
        if table not in tables:
            tables.append(table)
    while len(tables)<size:
        table=tuple(int(rng.choice(N_ACTIONS,p=probabilities[i])) for i in range(N_STATES))
        if table not in tables:
            tables.append(table)
    return tables


def elite_probabilities(elites):
    counts=np.full((N_STATES,N_ACTIONS),PSEUDOCOUNT)
    for table in elites:
        for index,action in enumerate(table):
            counts[index,action]+=1
    return counts/counts.sum(axis=1,keepdims=True)


def policy_key(policy):
    return digest(policy)


def job_identity(job):
    return {k:job[k] for k in ('case','seed','condition','stage','policy','source_hash')}


def job_key(job):
    return digest(job_identity(job))


def unique_jobs(jobs):
    return list({job_key(job):job for job in jobs}.values())


def make_policy(spec):
    if spec['kind']=='table':
        return BudgetedTablePolicy(spec['table'])
    if spec['kind']=='strict_floor':
        return StrictFloorPolicy()
    if spec['kind']=='budget_greedy':
        return BudgetGreedyPolicy()
    raise ValueError(f'Unknown policy kind {spec["kind"]}')


def audit_prefixes(sessions, budgets):
    fractions={c:Fraction(str(budgets[c])) for c in CLASSES}
    events=[]
    for s in sessions:
        events.append((s.arrival_t,0,s.sid,s.cls))
        if s.outcome is Outcome.SERVED and not is_at_least(s.grade,s.authorised_floor):
            events.append((s.served_t,1,s.sid,s.cls))
    arrivals={c:0 for c in CLASSES}
    violations={c:0 for c in CLASSES}
    maximum={c:0 for c in CLASSES}
    for _,kind,_,cls in sorted(events):
        if kind==0:
            arrivals[cls]+=1
        else:
            violations[cls]+=1
        maximum[cls]=max(maximum[cls],violations[cls]-math.floor(fractions[cls]*arrivals[cls]))
    return {'maximum_excess':max(maximum.values()),'maximum_excess_by_class':maximum,
            'arrivals':arrivals,'violations':violations,
            'caps':{c:math.floor(fractions[c]*arrivals[c]) for c in CLASSES}}


def verified_record(path, expected_key):
    record=json.loads(Path(path).read_text(encoding='utf-8'))
    stored_hash=record.pop('record_sha256',None)
    if record.get('job_key')!=expected_key or stored_hash!=digest(record):
        raise RuntimeError(f'Corrupt or mismatched rollout cache: {path}')
    record['record_sha256']=stored_hash
    return record


def run_rollout(job):
    key=job_key(job)
    path=Path(job['cache_dir'])/f'{key}.json'
    if path.exists():
        return {'cached':True,'record':verified_record(path,key)}
    started=time.perf_counter()
    case=Case(**job['case'])
    policy=make_policy(job['policy'])
    sim=make_simulator(case,job['seed'],policy)
    initial={str(k):s.level for k,s in sim.topo.stores.items()}
    result=sim.run()
    summary={name:summarize(result,None if name=='all' else name)
             for name in ('all',*CLASSES)}
    if not math.isfinite(summary['all']['utility']):
        raise ValueError('Scoring requires a nonempty finite overall arrival cohort')
    snapshot=policy.snapshot(sim)
    prefix=audit_prefixes(result.sessions,snapshot['budgets'])
    if prefix['maximum_excess']>0 or snapshot['arrivals']!=prefix['arrivals']:
        raise RuntimeError('Independent prefix budget audit failed')
    if snapshot['violations']!=prefix['violations']:
        raise RuntimeError('Policy snapshot disagrees with finalized session grades')
    final={str(k):s.level for k,s in sim.topo.stores.items()}
    residual=(sum(initial.values())+result.full_generated_bits-result.full_consumed_bits
              -result.full_discarded_bits-sum(final.values()))
    if abs(residual)>1e-2:
        raise RuntimeError(f'Key conservation failed: {residual}')
    arrivals=sorted((s.sid,s.cls,s.arrival_t,s.payload_bits,s.src,s.dst,
                     s.authorised_floor,s.deadline_s,s.priority) for s in result.sessions)
    record=json_safe({'schema_version':1,'job_key':key,'job':job_identity(job),
        'summary':summary,'counters':{name:result.outcome_metrics(None if name=='all' else name)
                                    for name in ('all',*CLASSES)},
        'arrival_sha256':digest(arrivals),
        'sessions_sha256':digest([asdict(s) for s in result.sessions]),
        'budget_snapshot':snapshot,'prefix_audit':prefix,
        'accounting':{'initial_by_link':initial,'final_by_link':final,
            'generated_bits_full':result.full_generated_bits,
            'consumed_bits_full':result.full_consumed_bits,
            'discarded_bits_full':result.full_discarded_bits,
            'purged_bits_full':sim.purged_bits,'conservation_residual_bits':residual},
        'wall_s':time.perf_counter()-started})
    record['record_sha256']=digest(record)
    write_json(path,record)
    return {'cached':False,'record':record}


def aggregate_rollouts(rows):
    utilities=[r['summary']['all']['utility'] for r in rows]
    if not utilities or any(x is None or not math.isfinite(x) for x in utilities):
        raise ValueError('Cannot score missing or nonfinite overall utility')
    fields=('utility','availability','qualified_availability','degraded_arrival_fraction',
            'blocked_arrival_fraction','forced_entitled_fraction','qualified_payload_fraction')
    def means(group):
        out={}
        for field in fields:
            values=[r['summary']['all'].get(field) for r in group]
            finite=[v for v in values if v is not None and math.isfinite(v)]
            out[field]=float(np.mean(finite)) if finite else None
        return out
    conditions={name:means([r for r in rows if r['job']['condition']==name])
                for name in sorted({r['job']['condition'] for r in rows})}
    worst={}
    for field in fields:
        values=[r[field] for r in conditions.values() if r[field] is not None]
        adverse=max if field in ('degraded_arrival_fraction','blocked_arrival_fraction',
                                  'forced_entitled_fraction') else min
        worst[field]=adverse(values) if values else None
    return {'mean':means(rows),'condition_means':conditions,'worst_condition_components':worst,
            'minimum_condition_utility':min(r['utility'] for r in conditions.values()),
            'n_rollouts':len(rows)}


def select_restart(candidates):
    expected={(s['condition'],digest(s['case']),s['seed']) for s in validation_specs()}
    scored=[]
    for candidate in candidates:
        rows=candidate['rollouts']
        observed=[]
        for row in rows:
            job=row['job']
            if job['stage']!='validation' or job['seed'] not in VALIDATION_SEEDS:
                raise ValueError('Restart selection accepts only registered validation rows')
            observed.append((job['condition'],digest(job['case']),job['seed']))
        if set(observed)!=expected or len(observed)!=len(expected):
            raise ValueError('Restart selection requires each validation pair exactly once')
        score=aggregate_rollouts(rows)
        scored.append({**candidate,'validation_score':score})
    if not scored:
        raise ValueError('No restart candidates')
    return min(scored,key=lambda r:(-r['validation_score']['mean']['utility'],
        table_complexity(r['table']),tuple(r['table']),r['restart']))


def write_freeze(path, value):
    path=Path(path)
    if path.exists():
        raise RuntimeError('Policy freeze already exists; do not overwrite after selection')
    payload=json_safe(value)
    payload['freeze_sha256']=digest(payload)
    write_json(path,payload)
    return payload


def read_freeze(path, source_hash):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    expected=data.pop('freeze_sha256',None)
    if expected!=digest(data):
        raise RuntimeError('Policy freeze integrity check failed')
    if data.get('source_hash')!=source_hash:
        raise RuntimeError('Scientific code/runtime changed after policy freeze')
    if data.get('test_plan')!=test_specs():
        raise RuntimeError('Registered final-test plan changed after policy freeze')
    data['freeze_sha256']=expected
    return data


class Evaluator:
    def __init__(self, source_hash, directory, executor):
        self.source_hash=source_hash
        self.cache_dir=Path(directory)/'cache'
        self.executor=executor
        self.stats={'requested':0,'unique_jobs_dispatched':0,'cache_hits':0,'executed':0}
        self.arrival_hashes={}

    def evaluate(self, policies, specs, stage):
        jobs=[{**spec,'stage':stage,'policy':policy,'source_hash':self.source_hash,
               'cache_dir':str(self.cache_dir)} for policy in policies for spec in specs]
        unique=unique_jobs(jobs)
        self.stats['requested']+=len(jobs)
        self.stats['unique_jobs_dispatched']+=len(unique)
        envelopes=(self.executor.map(run_rollout,unique) if self.executor is not None
                   else map(run_rollout,unique))
        records={}
        for envelope in envelopes:
            self.stats['cache_hits']+=int(envelope['cached'])
            self.stats['executed']+=int(not envelope['cached'])
            row=envelope['record']
            job=row['job']
            trace=(digest(job['case']),job['seed'])
            known=self.arrival_hashes.setdefault(trace,row['arrival_sha256'])
            if known!=row['arrival_sha256']:
                raise RuntimeError('Compared policies did not receive an identical arrival realization')
            records[row['job_key']]=row
        grouped={}
        for policy in policies:
            grouped[policy_key(policy)]=[
                records[job_key({**spec,'stage':stage,'policy':policy,
                                 'source_hash':self.source_hash})] for spec in specs]
        return grouped


def candidate_rank(candidate):
    return (-candidate['training_score']['mean']['utility'],
            table_complexity(candidate['table']),tuple(candidate['table']))


def search_restart(regime, restart, evaluator, output):
    rng=np.random.default_rng(OPTIMIZER_SEEDS[restart])
    probabilities=np.full((N_STATES,N_ACTIONS),1/N_ACTIONS)
    incumbent=tuple([1]*N_STATES)
    history=[]
    best=None
    before_stats=dict(evaluator.stats)
    for iteration in range(ITERATIONS):
        tables=population(probabilities,POPULATION,incumbent,rng)
        policies=[{'kind':'table','table':list(table)} for table in tables]
        evaluated=evaluator.evaluate(policies,training_specs(regime),'train')
        candidates=[]
        for table,policy in zip(tables,policies):
            rows=evaluated[policy_key(policy)]
            candidates.append({'table':list(table),'table_sha256':digest(list(table)),
                'training_score':aggregate_rollouts(rows),
                'rollout_keys':[r['job_key'] for r in rows]})
        ranked=sorted(candidates,key=candidate_rank)
        best=ranked[0]
        incumbent=tuple(best['table'])
        updated=elite_probabilities([tuple(c['table']) for c in ranked[:N_ELITES]])
        history.append({'iteration':iteration,'population':candidates,
            'probabilities_before':probabilities.tolist(),'probabilities_after':updated.tolist(),
            'incumbent_table':list(incumbent),'incumbent_training_utility':best['training_score']['mean']['utility'],
            'optimizer_rng_state':rng.bit_generator.state,
            'requested_candidates':POPULATION,'requested_rollouts':POPULATION*6})
        probabilities=updated
        artifact={'schema_version':1,'source_hash':evaluator.source_hash,'regime':regime,
            'restart':restart,'optimizer_seed':OPTIMIZER_SEEDS[restart],
            'completed_iterations':len(history),'registered_iterations':ITERATIONS,
            'history':history,'best_observed':best,
            'execution_stats':{k:evaluator.stats[k]-before_stats[k] for k in evaluator.stats}}
        write_json(Path(output)/'search'/f'{regime}_restart{restart}.json',artifact)
        print(f'{regime} restart {restart} generation {iteration+1}/{ITERATIONS}: '
              f'mean training utility {best["training_score"]["mean"]["utility"]:.6f}; '
              f'{evaluator.stats["executed"]} new rollouts, {evaluator.stats["cache_hits"]} cached',flush=True)
    return {'restart':restart,'optimizer_seed':OPTIMIZER_SEEDS[restart],
            'table':list(incumbent),'table_sha256':digest(list(incumbent)),
            'training_score':best['training_score'],
            'training_rollout_keys':best['rollout_keys'],
            'search_artifact':f'search/{regime}_restart{restart}.json'}


def _training_with_executor(executor, metadata, output, freeze_path):
    evaluator=Evaluator(metadata['source_hash'],output,executor)
    selected={}
    validations={}
    for regime in REGIMES:
        finalists=[search_restart(regime,restart,evaluator,output) for restart in range(RESTARTS)]
        policies=[{'kind':'table','table':r['table']} for r in finalists]
        evaluated=evaluator.evaluate(policies,validation_specs(),'validation')
        candidates=[{**r,'rollouts':evaluated[policy_key(p)]} for r,p in zip(finalists,policies)]
        winner=select_restart(candidates)
        rows=[]
        for candidate in candidates:
            compact={k:v for k,v in candidate.items() if k!='rollouts'}
            compact['validation_score']=aggregate_rollouts(candidate['rollouts'])
            compact['validation_rollout_keys']=[r['job_key'] for r in candidate['rollouts']]
            rows.append(compact)
        validations[regime]=rows
        selected[regime]=next(r for r in rows if r['restart']==winner['restart'])
        selected[regime]['table_complexity']=table_complexity(winner['table'])
        print(f'{regime}: validation selected restart {winner["restart"]}, '
              f'mean utility {winner["validation_score"]["mean"]["utility"]:.6f}',flush=True)
        write_json(Path(output)/'validation'/f'{regime}.json',{
            'source_hash':metadata['source_hash'],'candidates':rows,'selected_restart':winner['restart']})
    protocol=registered_protocol()
    freeze={'schema_version':1,'created_utc':utc_now(),**metadata,
        'protocol_sha256':digest(protocol),'protocol':protocol,
        'selected':selected,'validation_candidates':validations,
        'test_plan':test_specs(),'execution_stats':dict(evaluator.stats),
        'claim_scope':'best observed under finite search and validation; not globally optimal'}
    return write_freeze(freeze_path,freeze)


def run_training(workers, output=OUTPUT, freeze_path=FREEZE):
    output,freeze_path=Path(output),Path(freeze_path)
    metadata=source_metadata()
    if freeze_path.exists():
        freeze=read_freeze(freeze_path,metadata['source_hash'])
        if freeze.get('protocol_sha256')!=digest(registered_protocol()):
            raise RuntimeError('Protocol changed after policy selection')
        print(f'Using existing verified policy freeze: {freeze_path}',flush=True)
        return freeze
    if (output/'test_started.json').exists():
        raise RuntimeError('Final-test evidence exists without a freeze; cannot select policies now')
    protocol=registered_protocol()
    manifest_path=output/'train_manifest.json'
    manifest={'schema_version':1,**metadata,'protocol':protocol,
              'protocol_sha256':digest(protocol),'started_utc':utc_now(),'workers':workers}
    if manifest_path.exists():
        previous=json.loads(manifest_path.read_text(encoding='utf-8'))
        if (previous.get('source_hash'),previous.get('protocol_sha256')) != (
                metadata['source_hash'],digest(protocol)):
            raise RuntimeError('Training source/protocol changed; archive old output explicitly')
        manifest['started_utc']=previous['started_utc']
    write_json(manifest_path,manifest)
    started=time.perf_counter()
    if workers==1:
        freeze=_training_with_executor(None,metadata,output,freeze_path)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            freeze=_training_with_executor(executor,metadata,output,freeze_path)
    manifest.update(completed_utc=utc_now(),wall_s=time.perf_counter()-started,
                    freeze_sha256=freeze['freeze_sha256'],execution_stats=freeze['execution_stats'])
    write_json(manifest_path,manifest)
    return freeze


def _test_with_executor(executor, metadata, output, freeze):
    evaluator=Evaluator(metadata['source_hash'],output,executor)
    roster=[('strict_floor',{'kind':'strict_floor'}),
            ('budget_greedy',{'kind':'budget_greedy'})]
    roster += [(regime,{'kind':'table','table':freeze['selected'][regime]['table']})
               for regime in REGIMES]
    rows=evaluator.evaluate([p for _,p in roster],freeze['test_plan'],'test')
    report=[]
    for name,policy in roster:
        policy_rows=rows[policy_key(policy)]
        for row in policy_rows:
            report.append({'policy_name':name,'policy_sha256':policy_key(policy),
                'condition':row['job']['condition'],'seed':row['job']['seed'],
                'rollout_key':row['job_key'],'summary':row['summary'],
                'counters':row['counters'],'budget_snapshot':row['budget_snapshot'],
                'prefix_audit':row['prefix_audit'],'arrival_sha256':row['arrival_sha256'],
                'wall_s':row['wall_s']})
    return {'schema_version':1,'source_hash':metadata['source_hash'],
        'freeze_sha256':freeze['freeze_sha256'],'rows':report,
        'execution_stats':dict(evaluator.stats),'requested_rollouts':420,
        'policies':{name:policy for name,policy in roster},'completed_utc':utc_now()}


def run_test(workers, output=OUTPUT, freeze_path=FREEZE):
    output,freeze_path=Path(output),Path(freeze_path)
    metadata=source_metadata()
    # All validation must happen before an evaluator or output cache is created.
    freeze=read_freeze(freeze_path,metadata['source_hash'])
    if freeze.get('protocol_sha256')!=digest(registered_protocol()):
        raise RuntimeError('Registered learning protocol changed after freeze')
    if set(freeze['selected'])!=set(REGIMES):
        raise RuntimeError('Incomplete policy freeze')
    for selected in freeze['selected'].values():
        BudgetedTablePolicy(selected['table'])
        if selected['table_sha256']!=digest(selected['table']):
            raise RuntimeError('Frozen table digest does not match')
    report_path=output/'test_results.json'
    if report_path.exists():
        report=json.loads(report_path.read_text(encoding='utf-8'))
        if report.get('freeze_sha256')!=freeze['freeze_sha256']:
            raise RuntimeError('Existing test report belongs to a different policy freeze')
        stored_hash=report.pop('report_sha256',None)
        if stored_hash!=digest(report):
            raise RuntimeError('Final-test report integrity check failed')
        report['report_sha256']=stored_hash
        for key in {r['rollout_key'] for r in report['rows']}:
            verified_record(output/'cache'/f'{key}.json',key)
        print(f'Using existing verified final-test report: {report_path}',flush=True)
        return report
    write_json(output/'test_started.json',{'source_hash':metadata['source_hash'],
        'freeze_sha256':freeze['freeze_sha256'],'started_utc':utc_now(),'workers':workers})
    started=time.perf_counter()
    if workers==1:
        report=_test_with_executor(None,metadata,output,freeze)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            report=_test_with_executor(executor,metadata,output,freeze)
    report['wall_s']=time.perf_counter()-started
    report['report_sha256']=digest(report)
    write_json(report_path,report)
    print(f'Final test complete: {len(report["rows"])} policy/condition/seed rows',flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('train','test','all'),default='train')
    parser.add_argument('--workers',type=int,default=6)
    parser.add_argument('--describe',action='store_true',help='Print protocol only; do not simulate')
    args=parser.parse_args()
    if not 1<=args.workers<=8:
        parser.error('Use one to eight workers')
    if args.describe:
        protocol=registered_protocol()
        print(json.dumps({'protocol_sha256':digest(protocol),
            'regimes':REGIMES,'optimizer_seeds':OPTIMIZER_SEEDS,
            'requested_training_rollouts':1440,'requested_validation_rollouts':72,
            'requested_test_rollouts':420,'source':source_metadata()},indent=2))
        return 0
    print(f'Learning phase {args.phase}; workers={args.workers}; '
          'fixed protocol and disjoint realization seeds',flush=True)
    if args.phase in ('train','all'):
        run_training(args.workers)
    if args.phase in ('test','all'):
        run_test(args.workers)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
