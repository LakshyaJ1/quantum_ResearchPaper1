"""Submitted configuration on the submitted (0d1e2fa) and corrected simulators.

python experiments/camera_ready_bridge.py --workers 4

Both codes receive the same SimConfig, so arrival, outage and endpoint streams are
identical and every difference is paired by seed. Variants:
  orig      qkdsim at git commit 0d1e2fa (extracted to a temporary directory)
  current   working-tree qkdsim
  ablation  working-tree qkdsim with only the stored-key rule reverted
            (a link is usable only while generating), isolating that correction
Cells: the submitted Table II (KAR, k = 0, 1, 2, 5, both modes, n_auth = 2) and the
routing comparison at k = 0 (SP and KAR, fail-closed) at n_auth = 2 and 7.
Output: results/camera_ready/bridge/rows.jsonl (one row per run).
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'camera_ready' / 'bridge'
ORIG_COMMIT = '0d1e2fa'


def extract_original(dest: Path) -> Path:
    archive = subprocess.run(['git', '-C', str(ROOT), 'archive', ORIG_COMMIT, 'qkdsim'],
                             check=True, capture_output=True).stdout
    tar = dest / 'orig.tar'
    tar.write_bytes(archive)
    subprocess.run(['tar', '-xf', str(tar), '-C', str(dest)], check=True)
    return dest


def metrics(sim, r):
    from qkdsim.config import G2_QKD_SYM, is_at_least
    xs = [s for s in r.sessions if r.warmup_s <= s.arrival_t < 86400.0]
    timely = [s for s in xs if s.outcome.value == 'SERVED'
              and s.served_t <= s.arrival_t + s.deadline_s + 1e-9]
    below = [s for s in timely if not is_at_least(s.grade, s.authorised_floor)]
    entitled = [s for s in xs if is_at_least(s.authorised_floor, G2_QKD_SYM)]
    served_any = [s for s in xs if s.outcome.value == 'SERVED']
    ent_any = [s for s in served_any if is_at_least(s.authorised_floor, G2_QKD_SYM)]
    forced = [s for s in timely if is_at_least(s.authorised_floor, G2_QKD_SYM)
              and not is_at_least(s.grade, G2_QKD_SYM)]
    forced_any = [s for s in ent_any if not is_at_least(s.grade, G2_QKD_SYM)]
    ratio = lambda a, b: a / b if b else float('nan')
    out = dict(n=len(xs), A=ratio(len(timely), len(xs)),
               A_submitted=ratio(len(served_any), len(xs)),
               Q=ratio(len(timely) - len(below), len(xs)), L=ratio(len(below), len(xs)),
               F=ratio(len(forced), len(entitled)),
               F_submitted=ratio(len(forced_any), len(ent_any)),
               mean_hops=(sum(s.hops for s in served_any) / len(served_any)
                          if served_any else float('nan')))
    for c in ('C2', 'ISR', 'LOG'):
        xc = [s for s in xs if s.cls == c]
        out[f'A_{c}'] = ratio(sum(s in timely for s in xc), len(xc))
    return out


def run_one(spec):
    root = spec['root']
    sys.path.insert(0, root)
    from qkdsim.config import (AccountingConfig, AdversaryConfig, PhysicsConfig,
                               ReservoirConfig, SimConfig)
    import qkdsim.network as network
    from qkdsim.sim import Simulator
    if spec['variant'] == 'ablation':
        network._usable = lambda topo, lk, phys: topo.links[lk].current_rate_bps(phys) > 0.0
    cfg = SimConfig(horizon_s=86400.0, warmup_s=43200.0, seed=spec['seed'],
                    routing=spec['routing'], fail_mode=spec['mode'],
                    physics=PhysicsConfig(), accounting=AccountingConfig(n_auth=spec['n_auth']),
                    reservoir=ReservoirConfig(),
                    adversary=AdversaryConfig(budget_links=spec['k'], delta_e=0.05))
    sim = Simulator(network.formation_9node(cfg.reservoir), cfg)
    attacked = sorted(sim._adv_links)
    started = time.time()
    row = dict(spec, attacked=[list(e) for e in attacked])
    row.pop('root')
    row.update(metrics(sim, sim.run()))
    row['wall_s'] = time.time() - started
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--seeds', type=int, default=12)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        orig_root = str(extract_original(Path(tmp)))
        roots = {'orig': orig_root, 'current': str(ROOT), 'ablation': str(ROOT)}
        specs = []
        for variant in ('orig', 'current', 'ablation'):
            for mode in ('FAIL_CLOSED', 'FAIL_DEGRADED'):
                for k in (0, 1, 2, 5):
                    if variant == 'ablation' and k == 0:
                        continue
                    specs += [dict(cell='headline', variant=variant, mode=mode, k=k,
                                   routing='KAR', n_auth=2, seed=s) for s in range(args.seeds)]
        for variant in ('orig', 'current'):
            for n_auth in (2, 7):
                if variant == 'orig' and n_auth == 7:
                    continue
                for routing in ('SP', 'KAR'):
                    if n_auth == 2 and routing == 'KAR':
                        continue          # identical to the headline k = 0 closed cell
                    specs += [dict(cell='routing', variant=variant, mode='FAIL_CLOSED', k=0,
                                   routing=routing, n_auth=n_auth, seed=s)
                              for s in range(args.seeds)]
        for spec in specs:
            spec['root'] = roots[spec['variant']]
        started = time.time()
        # One interpreter per task: the two qkdsim versions must never share a process.
        with ProcessPoolExecutor(max_workers=args.workers, max_tasks_per_child=1) as pool, \
                open(OUT / 'rows.jsonl', 'w', encoding='utf-8') as fh:
            for row in pool.map(run_one, specs):
                fh.write(json.dumps(row) + '\n')
    meta = dict(commit=ORIG_COMMIT, runs=len(specs), wall_s=time.time() - started,
                python=sys.version)
    (OUT / 'meta.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print(f"{len(specs)} runs in {meta['wall_s']:.0f}s")


if __name__ == '__main__':
    raise SystemExit(main())
