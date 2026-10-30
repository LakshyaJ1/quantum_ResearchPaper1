"""Camera-ready re-runs of submitted-paper items that the revision grid did not cover.

The corrected simulator (qkdsim 0.2.0 + revision/) is used unchanged; the two
scenario options the revision Case lacks -- class-aware reservation floors and
depth-d relay chains -- live in revision/camera_ready.py. Output goes to
results/camera_ready/, so the revision evidence under results/revision/ is never
touched.

python experiments/camera_ready_runs.py --phase envelope --workers 6
python experiments/camera_ready_runs.py --phase threshold --workers 6
python experiments/camera_ready_runs.py --phase floors   --workers 6   (also betweenness)
python experiments/camera_ready_runs.py --phase chain    --workers 6
"""
from __future__ import annotations

import os
for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_name] = '1'

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from revision.camera_ready import CRCase, make_cr_simulator
from revision.metrics import summarize

OUT = ROOT / 'results' / 'camera_ready'


def fingerprint():
    # Simulator code only: editing the case grid below must not invalidate runs.
    paths = sorted((ROOT / 'qkdsim').glob('*.py')) + [
        ROOT / 'revision/scenarios.py', ROOT / 'revision/metrics.py',
        ROOT / 'revision/camera_ready.py']
    h = hashlib.sha256()
    for path in paths:
        h.update(path.relative_to(ROOT).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def case_key(case):
    return hashlib.sha256(json.dumps(asdict(case), sort_keys=True).encode()).hexdigest()[:16]


def cases_for(phase):
    records = []

    def add(tag, case, modes=('FAIL_CLOSED', 'FAIL_DEGRADED')):
        for mode in modes:
            records.append((tag, replace(case, fail_mode=mode)))

    if phase == 'envelope':
        # Submitted Table III (sub-threshold injection x budget), formation, with
        # both response shapes; outage-free like the revision threshold batch.
        for gamma in (1.0, 3.4):
            for delta in (0.01, 0.02, 0.03, 0.04, 0.045, 0.05):
                for budget in (1, 2, 3, 4, 5):
                    add('envelope', CRCase(attack_budget=budget, delta_e=delta,
                                           gamma=gamma, outage_model='none'))
    elif phase == 'threshold':
        # Same capability x budget grid on the three- and four-link cuts (reviewer
        # question 2), so Table III compares all graphs on identical cells.
        for topology, cut in (('parallel3', 3), ('parallel4', 4)):
            for gamma in (1.0, 3.4):
                for delta in (0.03, 0.04, 0.045, 0.05):
                    for budget in (1, cut - 1, cut, cut + 1):
                        add('threshold', CRCase(topology=topology, attack_budget=budget,
                                                delta_e=delta, gamma=gamma,
                                                outage_model='none'))
    elif phase == 'routing':
        # Attribute the submitted key-aware routing penalty: initial fill and warm-up
        # at the submitted ISR rate and the calibrated n_auth, unattacked, fail-closed.
        for fill in (1.0, 0.02):
            for warmup in (43200, 0):
                for routing in ('SP', 'KAR'):
                    add('routing', CRCase(isr_scale=1.0, initial_spendable_fraction=fill,
                                          warmup_s=warmup, routing=routing),
                        modes=('FAIL_CLOSED',))
    elif phase == 'floors':
        # Submitted routing result (3): class-aware reservation floors.
        for fill in (0.02, 1.0):
            for isr in (0.1, 1.0):
                for budget in (0, 2):
                    for floors in (False, True):
                        add('floors', CRCase(initial_spendable_fraction=fill, isr_scale=isr,
                                             attack_budget=budget, reservation_floors=floors))
        for scale in (0.05, 0.25):
            for budget in (0, 2):
                add('floor_scale', CRCase(attack_budget=budget, reservation_floors=True,
                                          floor_scale=scale))
        # The submitted headline adversary (static betweenness) at the main settings,
        # on the twelve main seeds, so Table II can show it beside the cut.
        for budget in (1, 2):
            add('betweenness', CRCase(attack_budget=budget,
                                      attack_method='static_betweenness'))
        # Deterministic replay of the main-grid formation cells, now recording the
        # served-grade counts that the revision run files do not store.
        for budget in (0, 1, 2):
            add('headline', CRCase(attack_budget=budget))
    elif phase == 'chain':
        # Submitted Fig. 3: forcing cost versus relay-chain depth.
        for depth in range(1, 7):
            topo = f'chain{depth}'
            add('chain', CRCase(topology=topo, attack_budget=0))
            for method in ('static_betweenness', 'adaptive_betweenness', 'weighted_cut'):
                for budget in range(1, depth + 3):
                    add('chain', CRCase(topology=topo, attack_budget=budget,
                                        attack_method=method))
    else:
        raise ValueError(phase)
    unique = {}
    for tag, case in records:
        key = case_key(case)
        if key not in unique:
            unique[key] = {'case_id': key, 'tags': [], 'case': asdict(case)}
        if tag not in unique[key]['tags']:
            unique[key]['tags'].append(tag)
    return list(unique.values())


def run_job(job):
    record, seed, source_hash = job
    case = CRCase(**record['case'])
    case_id = record['case_id']
    path = OUT / 'runs' / f'{case_id}_seed{seed}.json'
    if path.exists():
        stored = json.loads(path.read_text())
        if stored.get('source_hash') == source_hash:
            return {'cached': True, 'case_id': case_id, 'seed': seed, 'wall_s': 0}
        raise RuntimeError(f'Stale run requires explicit archival before rerun: {path}')
    started = time.perf_counter()
    sim = make_cr_simulator(case, seed)
    initial = {str(k): v.level for k, v in sim.topo.stores.items()}
    result = sim.run()
    summary = {name: summarize(result, None if name == 'all' else name)
               for name in ('all', 'C2', 'ISR', 'LOG')}
    hourly = [dict(hour=hour, **summarize(result, start=hour * 3600, end=(hour + 1) * 3600))
              for hour in range((int(case.horizon_s) + 3599) // 3600)]
    grades = {}
    for s in result.sessions:
        if s.grade is not None and s.arrival_t >= result.warmup_s:
            grades.setdefault(s.cls, {}).setdefault(s.grade, 0)
            grades[s.cls][s.grade] += 1
    arrivals = sorted((s.sid, s.cls, s.arrival_t, s.payload_bits, s.src, s.dst,
                       s.authorised_floor, s.deadline_s) for s in result.sessions)
    out = {
        'schema_version': 1, 'case_id': case_id, 'seed': seed, 'case': asdict(case),
        'source_hash': source_hash, 'summary': summary, 'hourly': hourly,
        'served_grade_counts': grades,
        'arrival_sha256': hashlib.sha256(json.dumps(arrivals).encode()).hexdigest(),
        'topology': {'nodes': list(sim.topo.graph.nodes),
                     'links': [list(k) for k in sim.topo.all_link_keys()],
                     'all_terminal_cut': [list(k) for k in sim.exact_cut],
                     'all_terminal_cut_cost': sum(sim.attack_costs[k] for k in sim.exact_cut),
                     'attacked_edges': [list(k) for k in sim._chosen_attack],
                     'spent_attack_budget': sum(sim.attack_costs[k] for k in sim._chosen_attack)},
        'accounting': {'initial_stored_bits': initial,
                       'final_stored_bits': {str(k): v.level for k, v in sim.topo.stores.items()},
                       'generated_bits_full': result.full_generated_bits,
                       'consumed_bits_full': result.full_consumed_bits,
                       'discarded_bits_full': result.full_discarded_bits,
                       'purged_bits_full': sim.purged_bits},
        'wall_s': time.perf_counter() - started,
    }
    residual = (sum(initial.values()) + result.full_generated_bits - result.full_consumed_bits
                - result.full_discarded_bits - sum(v.level for v in sim.topo.stores.values()))
    out['accounting']['conservation_residual_bits'] = residual
    if abs(residual) > 1e-2:
        raise RuntimeError(f'Key conservation failed {residual}')
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(out, allow_nan=True), encoding='utf-8')
    temp.replace(path)
    return {'cached': False, 'case_id': case_id, 'seed': seed, 'wall_s': out['wall_s']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['envelope', 'threshold', 'routing', 'floors', 'chain'], required=True)
    parser.add_argument('--seeds', type=int, default=0)
    parser.add_argument('--seed-start', type=int, default=3000)
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        parser.error('Use 1 to 8 workers')
    seeds = args.seeds or {'envelope': 8, 'threshold': 8, 'routing': 12, 'floors': 12, 'chain': 8}[args.phase]
    (OUT / 'runs').mkdir(parents=True, exist_ok=True)
    records = cases_for(args.phase)
    source_hash = fingerprint()
    manifest = {'phase': args.phase, 'source_hash': source_hash,
                'seed_ids': list(range(args.seed_start, args.seed_start + seeds)),
                'cases': records, 'python': sys.version, 'workers': args.workers,
                'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    manifest_path = OUT / f'manifest_{args.phase}.json'
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    jobs = [(record, seed, source_hash) for record in records for seed in manifest['seed_ids']]
    start = time.perf_counter()
    print(f'{args.phase}: {len(records)} cases x {seeds} seeds = {len(jobs)} runs', flush=True)
    done = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run_job, job) for job in jobs]):
            future.result()
            done += 1
            if done % 25 == 0 or done == len(jobs):
                print(f'{done}/{len(jobs)} elapsed {time.perf_counter() - start:.0f}s', flush=True)
    manifest['completed_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    manifest['wall_s'] = time.perf_counter() - start
    manifest['completed_runs'] = len(jobs)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
