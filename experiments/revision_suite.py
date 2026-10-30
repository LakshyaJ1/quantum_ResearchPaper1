"""Reproducible camera-ready experiments; historical results are never overwritten.

python experiments/revision_suite.py --phase main --workers 6 --seeds 12
python experiments/revision_suite.py --phase sensitivity --workers 6 --seeds 8
"""
from __future__ import annotations

import os
for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_name] = '1'

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from revision.scenarios import Case, build_topology, attack_order, make_simulator
from revision.metrics import summarize
from qkdsim.config import ReservoirConfig

OUT = ROOT / 'results' / 'revision'


def fingerprint():
    paths = sorted((ROOT/'qkdsim').glob('*.py')) + [
        ROOT/'revision/scenarios.py', ROOT/'revision/metrics.py', Path(__file__)]
    h = hashlib.sha256()
    for path in paths:
        h.update(path.relative_to(ROOT).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def case_key(case):
    return hashlib.sha256(json.dumps(asdict(case), sort_keys=True).encode()).hexdigest()[:16]


def cut_budget(name, fibre=10):
    topo = build_topology(name, ReservoirConfig())
    _, costs, cut = attack_order(topo, 'weighted_cut', fibre)
    return sum(costs[k] for k in cut)


def cases_for(phase):
    records = []
    def add(tag, case):
        for mode in ('FAIL_CLOSED','FAIL_DEGRADED'):
            records.append((tag, replace(case, fail_mode=mode)))
    if phase == 'main':
        for topology in ('formation','ring','grid','parallel3','parallel4'):
            for budget in (0,1,cut_budget(topology)):
                add('topology', Case(topology=topology, attack_budget=budget))
    elif phase == 'sensitivity':
        for topology in ('formation','parallel3'):
            cut = cut_budget(topology)
            for budget in (0,cut):
                base = Case(topology=topology,attack_budget=budget)
                for scale in (.03,.1,1.):
                    add('workload',replace(base,isr_scale=scale))
                for initial in (.02,.1,1.):
                    add('initial_reserve',replace(base,initial_spendable_fraction=initial))
                for n_auth in (2,7,40):
                    add('authentication',replace(base,n_auth=n_auth))
                for model in ('independent','correlated'):
                    add('correlation',replace(base,outage_model=model,
                                             mean_uptime_s=900,mean_outage_s=600))
                for policy in ('retain','purge'):
                    add('buffer_policy',replace(base,buffer_policy=policy))
                for surface in ('generation','transport'):
                    for fallback in ('online_kem','preplaced_symmetric'):
                        add('fallback_transport',replace(base,attack_surface=surface,
                                                        fallback=fallback))
                for duration in (3600,21600,86400):
                    add('duration',replace(base,attack_duration_s=duration))
        for budget in (0,2):
            for scale in (.1,1.):
                for route in ('SP','KAR'):
                    add('routing',Case(attack_budget=budget,isr_scale=scale,routing=route))
        for fibre in (1,10,100):
            for method in ('weighted_cut','static_betweenness','adaptive_betweenness'):
                add('attack_cost',Case(attack_budget=2,fibre_attack_cost=fibre,
                                      attack_method=method))
    elif phase == 'threshold':
        for topology in ('parallel3','parallel4'):
            cut = cut_budget(topology)
            for budget in (1,cut,cut+1):
                for delta in (.03,.045,.05):
                    add('capability_budget',Case(topology=topology,attack_budget=budget,
                                               delta_e=delta,outage_model='none'))
        for gamma in (1.,3.4):
            for abort in (.075,.11):
                for delta in (.04,.06,.07,.08):
                    add('rate_threshold',Case(topology='parallel3',attack_budget=3,
                                              gamma=gamma,e_abort=abort,delta_e=delta,
                                              outage_model='none'))
    else:
        raise ValueError(phase)
    unique = {}
    for tag, case in records:
        key = case_key(case)
        if key not in unique:
            unique[key] = {'case_id':key,'tags':[],'case':asdict(case)}
        if tag not in unique[key]['tags']:
            unique[key]['tags'].append(tag)
    return list(unique.values())


def run_job(job):
    record, seed, source_hash = job
    case = Case(**record['case'])
    case_id = record['case_id']
    path = OUT/'runs'/f'{case_id}_seed{seed}.json'
    if path.exists():
        stored = json.loads(path.read_text())
        if stored.get('source_hash') == source_hash:
            return {'cached':True,'case_id':case_id,'seed':seed,'wall_s':0}
        raise RuntimeError(f'Stale run requires explicit archival before rerun: {path}')
    started = time.perf_counter()
    sim = make_simulator(case,seed)
    initial = {str(k):v.level for k,v in sim.topo.stores.items()}
    result = sim.run()
    summary = {name:summarize(result,None if name=='all' else name)
               for name in ('all','C2','ISR','LOG')}
    hourly = [dict(hour=hour,**summarize(result,start=hour*3600,end=(hour+1)*3600))
              for hour in range((case.horizon_s+3599)//3600)]
    arrivals = sorted((s.sid,s.cls,s.arrival_t,s.payload_bits,s.src,s.dst,
                       s.authorised_floor,s.deadline_s) for s in result.sessions)
    record_out = {
        'schema_version':1,'case_id':case_id,'seed':seed,'case':asdict(case),
        'source_hash':source_hash,'summary':summary,'hourly':hourly,
        'arrival_sha256':hashlib.sha256(json.dumps(arrivals).encode()).hexdigest(),
        'topology':{'nodes':list(sim.topo.graph.nodes),
                    'links':[list(k) for k in sim.topo.all_link_keys()],
                    'all_terminal_cut':[list(k) for k in sim.exact_cut],
                    'all_terminal_cut_cost':sum(sim.attack_costs[k] for k in sim.exact_cut),
                    'attacked_edges':[list(k) for k in sim._chosen_attack],
                    'spent_attack_budget':sum(sim.attack_costs[k] for k in sim._chosen_attack)},
        'accounting':{'initial_stored_bits':initial,
                      'final_stored_bits':{str(k):v.level for k,v in sim.topo.stores.items()},
                      'generated_bits_full':result.full_generated_bits,
                      'consumed_bits_full':result.full_consumed_bits,
                      'discarded_bits_full':result.full_discarded_bits,
                      'purged_bits_full':sim.purged_bits},
        'wall_s':time.perf_counter()-started,
    }
    residual = (sum(initial.values())+result.full_generated_bits-result.full_consumed_bits
                -result.full_discarded_bits-sum(v.level for v in sim.topo.stores.values()))
    record_out['accounting']['conservation_residual_bits'] = residual
    if abs(residual) > 1e-2:
        raise RuntimeError(f'Key conservation failed {residual}')
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(record_out,indent=2,allow_nan=True),encoding='utf-8')
    temp.replace(path)
    return {'cached':False,'case_id':case_id,'seed':seed,
            'wall_s':record_out['wall_s']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['main','sensitivity','threshold'],default='main')
    parser.add_argument('--seeds',type=int,default=12)
    parser.add_argument('--seed-start',type=int,default=3000)
    parser.add_argument('--workers',type=int,default=6)
    parser.add_argument('--limit',type=int,default=0)
    parser.add_argument('--shards',type=int,default=1)
    parser.add_argument('--shard',type=int,default=0)
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        parser.error('Use1 to8 workers')
    if not 0 <= args.shard < args.shards:
        parser.error('Require 0 <= shard < shards')
    (OUT/'runs').mkdir(parents=True,exist_ok=True)
    records = cases_for(args.phase)
    if args.limit:
        records = records[:args.limit]
    source_hash = fingerprint()
    manifest = {'phase':args.phase,'source_hash':source_hash,
                'seed_ids':list(range(args.seed_start,args.seed_start+args.seeds)),
                'cases':records,'python':sys.version,
                'platform':{'os_name':os.name,'sys_platform':sys.platform,
                            'windows_version':list(sys.getwindowsversion()) if os.name=='nt' else None},
                'workers':args.workers,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    suffix=f'_shard{args.shard}of{args.shards}' if args.shards>1 else ''
    manifest_path=OUT/f'manifest_{args.phase}{suffix}.json'
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    jobs = [(record,seed,source_hash) for record in records for seed in manifest['seed_ids']]
    jobs = [job for i,job in enumerate(jobs) if i%args.shards==args.shard]
    manifest['shard'],manifest['shards']=args.shard,args.shards
    start=time.perf_counter()
    print(f'{args.phase}: {len(records)} cases x {args.seeds} seeds = {len(jobs)} runs; workers={args.workers}',flush=True)
    cached=0
    def receive(outcomes):
        nonlocal cached
        for i,outcome in enumerate(outcomes,1):
            cached += outcome['cached']
            if i%10 == 0 or i == len(jobs):
                print(f'{i}/{len(jobs)} complete; {cached} reused; elapsed {time.perf_counter()-start:.1f}s',flush=True)
    if args.workers==1:
        receive(map(run_job,jobs))
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures={pool.submit(run_job,job):job for job in jobs}
            receive(future.result() for future in as_completed(futures))
    manifest['completed_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    manifest['wall_s']=time.perf_counter()-start
    manifest['completed_runs']=len(jobs)
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
