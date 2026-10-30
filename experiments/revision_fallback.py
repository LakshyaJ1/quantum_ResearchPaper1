"""Separate online key-establishment failure from application data transport.

This is an additional controlled scenario, not a retrofit of the main grid.
Preplaced symmetric fallback means ideal sufficient, unexpired already-shared
secret material. No finite PSK stock, expiry, refresh, KEM computation, or delivery
authentication overhead is implemented or measured here.

The six-case / eight-seed grid is deliberately serial by default. Run only when
CPU capacity has been allocated; --shards allows independent serial processes.
"""
from __future__ import annotations

import os
for _thread_option in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_thread_option] = '1'

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qkdsim.config import G3_HYBRID, G4_PQC
from revision.metrics import summarize
from revision.scenarios import Case, RevisionSimulator, make_simulator


class FallbackControlSimulator(RevisionSimulator):
    """A modeled KEM-service outage is separate from physical link outages."""

    def __init__(self, topo, cfg, case, traffic, grade_policy=None,
                 key_establishment_available=True):
        self.key_establishment_outage = not key_establishment_available
        self._environment_digest = hashlib.sha256()
        self._environment_edge_order = topo.all_link_keys()
        super().__init__(topo, cfg, case, traffic, grade_policy=grade_policy)

    def _try_grade(self, session, grade, t):
        if (self.case.fallback == 'online_kem' and self.key_establishment_outage
                and grade in (G3_HYBRID, G4_PQC)):
            return False
        return super()._try_grade(session, grade, t)

    def _tick_outages(self):
        super()._tick_outages()
        # Hash only the common observation window: different policies can have
        # different deadline-drain lengths after arrivals stop.
        if self.now_s < self.cfg.horizon_s:
            self._environment_digest.update(bytes(
                value for edge in self._environment_edge_order
                for value in (self.environment_generation[edge],
                              self.environment_transport[edge])))


def make_control_simulator(case: Case, seed: int, key_establishment_available: bool,
                           policy=None) -> FallbackControlSimulator:
    if type(key_establishment_available) is not bool:
        raise ValueError('Key-establishment availability must be explicitly true or false')
    # Reuse the frozen constructor's exact topology/config/traffic preparation.
    # It does not advance the clock or consume inventory before run().
    prepared = make_simulator(case, seed, policy)
    return FallbackControlSimulator(
        prepared.topo, prepared.cfg, case, prepared.traffic, grade_policy=policy,
        key_establishment_available=key_establishment_available)


def control_cases():
    base = Case(attack_budget=2, attack_surface='generation')
    records = []
    for fallback in ('online_kem', 'preplaced_symmetric'):
        for available in (True, False):
            records.append(dict(
                name=f'generation_{fallback}_control_{"up" if available else "down"}',
                case=replace(base, fallback=fallback),
                key_establishment_available=available))
    for fallback in ('online_kem', 'preplaced_symmetric'):
        records.append(dict(name=f'transport_{fallback}_control_up',
                            case=replace(base, fallback=fallback, attack_surface='transport'),
                            key_establishment_available=True))
    return records


def source_hashes():
    paths = sorted((ROOT / 'qkdsim').glob('*.py')) + [
        ROOT / 'revision/scenarios.py', ROOT / 'revision/metrics.py', Path(__file__)]
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def _identity(record):
    return dict(case=asdict(record['case']),
                key_establishment_available=record['key_establishment_available'])


def _finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _finite_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_finite_json(item) for item in value]
    return value


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(_finite_json(payload), indent=2, allow_nan=False)
                         + '\n', encoding='utf-8')
    temporary.replace(path)


def run_case(record, seed, output_dir=ROOT / 'results/revision/fallback'):
    identity = _identity(record)
    case_id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:16]
    path = Path(output_dir) / 'runs' / f'{case_id}_seed{seed}.json'
    before = source_hashes()
    if path.exists():
        cached = json.loads(path.read_text(encoding='utf-8'))
        if cached.get('source_sha256') == before:
            return cached
    started = time.perf_counter()
    sim = make_control_simulator(record['case'], seed,
                                 record['key_establishment_available'])
    result = sim.run()
    arrivals = sorted((s.sid, s.cls, s.arrival_t, s.src, s.dst, s.payload_bits,
                       s.authorised_floor, s.deadline_s) for s in result.sessions)
    residual = (result.initial_stored_bits + result.full_generated_bits
                - result.full_consumed_bits - result.full_discarded_bits
                - result.final_stored_bits)
    tolerance = max(1e-5, 1e-12 * result.initial_stored_bits)
    if abs(residual) > tolerance:
        raise AssertionError(f'Key accounting failed: residual {residual}')
    if before != source_hashes():
        raise RuntimeError('Source changed during the run; result is not written')
    payload = dict(
        schema_version=1, name=record['name'], case_id=case_id, seed=seed,
        **identity, source_sha256=before,
        created_utc=datetime.now(timezone.utc).isoformat(),
        python_version=platform.python_version(),
        wall_s=time.perf_counter() - started,
        arrivals_sha256=hashlib.sha256(json.dumps(arrivals).encode()).hexdigest(),
        environment_sha256=sim._environment_digest.hexdigest(),
        overall=summarize(result),
        per_class={cls: summarize(result, cls) for cls in ('C2', 'ISR', 'LOG')},
        topology={
            'node_roles': sim.topo.node_roles,
            'edges': [list(k) for k in sim.topo.all_link_keys()],
            'attacked_edges': [list(k) for k in sim._chosen_attack],
            'spent_relative_attack_budget': sum(sim.attack_costs[k] for k in sim._chosen_attack),
        },
        accounting={
            'initial_stored_bits': result.initial_stored_bits,
            'generated_bits_full': result.full_generated_bits,
            'consumed_bits_full': result.full_consumed_bits,
            'discarded_bits_full': result.full_discarded_bits,
            'final_stored_bits': result.final_stored_bits,
            'conservation_residual_bits': residual,
        },
        interpretation={
            'control_outage': 'global online KEM-service unavailability; data transport unchanged',
            'preplaced_symmetric': 'ideal sufficient unexpired shared secret; zero online setup',
            'not_modeled': ['finite fallback stock', 'key expiry', 'key refresh',
                            'KEM computation', 'fallback delivery authentication'],
            'undefined_fraction': 'null; retained numerator and denominator counts explain eligibility',
        },
    )
    payload = _finite_json(payload)
    _write_json(path, payload)
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/revision/fallback')
    parser.add_argument('--seed-start', type=int, default=3000)
    parser.add_argument('--seeds', type=int, default=8)
    parser.add_argument('--shards', type=int, default=1)
    parser.add_argument('--shard-index', type=int, default=0)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args(argv)
    if args.seeds < 1 or args.shards < 1 or not 0 <= args.shard_index < args.shards:
        parser.error('Positive seed/shard counts and an in-range shard index are required')
    records = control_cases()
    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    jobs = [(record, seed) for record in records for seed in seeds]
    jobs = [job for index, job in enumerate(jobs) if index % args.shards == args.shard_index]
    if args.limit is not None:
        if args.limit < 0:
            parser.error('Limit must be nonnegative')
        jobs = jobs[:args.limit]
    manifest = dict(
        schema_version=1, created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=source_hashes(), seed_ids=seeds,
        cases=[dict(name=r['name'], **_identity(r)) for r in records],
        shard_index=args.shard_index, shards=args.shards, scheduled_runs=len(jobs),
        execution='serial within each independent shard',
        scope='separate key-establishment-only dimension; ideal preplaced shared keys',
    )
    _write_json(args.output / f'manifest_shard{args.shard_index}of{args.shards}.json', manifest)
    print(f'Fallback control: {len(jobs)} serial runs in shard {args.shard_index}/{args.shards}',
          flush=True)
    for index, (record, seed) in enumerate(jobs, 1):
        row = run_case(record, seed, args.output)
        print(f'{index}/{len(jobs)} {record["name"]} seed={seed} '
              f'availability={row["overall"]["availability"]}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
