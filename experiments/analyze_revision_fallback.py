"""Verify and summarize the completed six-condition, eight-seed fallback grid."""
from __future__ import annotations

import os
for _option in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_option] = '1'

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from revision.metrics import mean_interval, paired_interval


METRICS = ('availability', 'qualified_availability', 'degraded_arrival_fraction',
           'blocked_arrival_fraction', 'forced_entitled_fraction',
           'entitled_blocked_fraction', 'entitled_its_fraction',
           'degraded_payload_fraction', 'forced_payload_fraction')
CLASSES = ('all', 'C2', 'ISR', 'LOG')
ONLINE_UP = 'generation_online_kem_control_up'
ONLINE_DOWN = 'generation_online_kem_control_down'
PREPLACED_UP = 'generation_preplaced_symmetric_control_up'
PREPLACED_DOWN = 'generation_preplaced_symmetric_control_down'
TRANSPORT_ONLINE = 'transport_online_kem_control_up'
TRANSPORT_PREPLACED = 'transport_preplaced_symmetric_control_up'
COMPARISONS = (
    ('online_control_down_minus_up', ONLINE_DOWN, ONLINE_UP),
    ('preplaced_control_down_minus_up', PREPLACED_DOWN, PREPLACED_UP),
    ('preplaced_minus_online_control_down', PREPLACED_DOWN, ONLINE_DOWN),
    ('preplaced_minus_online_control_up', PREPLACED_UP, ONLINE_UP),
    ('transport_preplaced_minus_online', TRANSPORT_PREPLACED, TRANSPORT_ONLINE),
    ('transport_minus_generation_online', TRANSPORT_ONLINE, ONLINE_UP),
    ('transport_minus_generation_preplaced', TRANSPORT_PREPLACED, PREPLACED_UP),
)
LABELS = {
    ONLINE_UP: 'Generation cut; online KEM; control up',
    ONLINE_DOWN: 'Generation cut; online KEM; control down',
    PREPLACED_UP: 'Generation cut; pre-positioned key; control up',
    PREPLACED_DOWN: 'Generation cut; pre-positioned key; control down',
    TRANSPORT_ONLINE: 'Transport cut; online KEM',
    TRANSPORT_PREPLACED: 'Transport cut; pre-positioned key',
}


def _finite(value):
    return value is not None and math.isfinite(value)


def _metrics(row, cls):
    return row['overall'] if cls == 'all' else row['per_class'][cls]


def _check_counts(metrics):
    n, served = metrics['n_arrivals'], metrics['n_served']
    if (min(n, served, metrics['n_qualified'], metrics['n_degraded'], metrics['n_blocked']) < 0
            or served + metrics['n_blocked'] != n
            or metrics['n_qualified'] + metrics['n_degraded'] != served
            or not 0 <= metrics['n_forced'] <= metrics['n_entitled'] <= n):
        raise ValueError('Delivery, authorization, or entitlement counts do not partition the cohort')
    if n:
        expected = {'availability': served/n,
                    'qualified_availability': metrics['n_qualified']/n,
                    'degraded_arrival_fraction': metrics['n_degraded']/n,
                    'blocked_arrival_fraction': metrics['n_blocked']/n}
        for key, value in expected.items():
            if not _finite(metrics[key]) or not math.isclose(metrics[key], value, abs_tol=1e-12):
                raise ValueError(f'Inconsistent denominator for {key}')


def analyze_rows(manifest, rows):
    seeds = manifest['seed_ids']
    cases = {case['name']: case for case in manifest['cases']}
    if len(seeds) != 8 or len(set(seeds)) != 8 or set(cases) != set(LABELS):
        raise ValueError('Expected the six declared conditions and eight distinct seeds')
    expected = {(name, seed) for name in cases for seed in seeds}
    by_key = {}
    for row in rows:
        key = (row['name'], row['seed'])
        if key not in expected or key in by_key:
            raise ValueError('Unexpected or duplicate case/seed record')
        identity = cases[row['name']]
        if (row['source_sha256'] != manifest['source_sha256']
                or row['case'] != identity['case']
                or row['key_establishment_available'] != identity['key_establishment_available']):
            raise ValueError('Mixed source versions or mismatched scenario identity')
        for cls in CLASSES:
            _check_counts(_metrics(row, cls))
        if sum(row['per_class'][cls]['n_arrivals'] for cls in CLASSES[1:]) != row['overall']['n_arrivals']:
            raise ValueError('Per-class arrivals do not sum to the whole cohort')
        by_key[key] = row
    if set(by_key) != expected:
        raise ValueError(f'Incomplete grid: {len(by_key)} of {len(expected)} records')
    for seed in seeds:
        for trace in ('arrivals_sha256', 'environment_sha256'):
            if len({by_key[(name, seed)][trace] for name in cases}) != 1:
                raise ValueError(f'{trace} differs between compared conditions at seed {seed}')

    summary = []
    for name in cases:
        for cls in CLASSES:
            selected = [_metrics(by_key[(name, seed)], cls) for seed in seeds]
            for metric in METRICS:
                values = [row[metric] for row in selected]
                defined = sum(_finite(value) for value in values)
                mean, lo, hi = mean_interval(values) if defined == len(seeds) else (None, None, None)
                summary.append(dict(name=name, traffic_class=cls, n_seeds=len(seeds),
                                    n_arrivals_total=sum(row['n_arrivals'] for row in selected),
                                    metric=metric, defined_seeds=defined, mean=mean, lo=lo, hi=hi,
                                    sample_sd=float(np.std(values, ddof=1)) if defined == len(seeds) else None))
    comparisons = []
    for label, treatment, control in COMPARISONS:
        for cls in CLASSES:
            for metric in METRICS:
                a = [_metrics(by_key[(treatment, seed)], cls)[metric] for seed in seeds]
                b = [_metrics(by_key[(control, seed)], cls)[metric] for seed in seeds]
                defined = sum(_finite(x) and _finite(y) for x, y in zip(a, b))
                delta, lo, hi = paired_interval(a, b) if defined == len(seeds) else (None, None, None)
                comparisons.append(dict(comparison=label, treatment=treatment, control=control,
                                        traffic_class=cls, n_pairs=len(seeds), defined_pairs=defined,
                                        metric=metric, difference=delta, lo=lo, hi=hi))
    return dict(runs_checked=len(rows), seed_ids=seeds,
                arrival_and_environment_traces_identical=True,
                bootstrap_resamples=20000, bootstrap_seed=71,
                interval='marginal percentile bootstrap 95%; independent seed unit; no dropped undefined pairs',
                summary=summary, comparisons=comparisons)


def _write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_report(report, manifest):
    stats = {(r['name'], r['traffic_class'], r['metric']): r for r in report['summary']}
    pairs = {(r['comparison'], r['traffic_class'], r['metric']): r for r in report['comparisons']}
    def pct(row, key='mean'):
        if row[key] is None:
            return 'undefined'
        return f"{100*row[key]:.3f} [{100*row['lo']:.3f}, {100*row['hi']:.3f}]"
    def mean(name, metric):
        return pct(stats[(name, 'all', metric)])
    def difference(label, metric):
        return pct(pairs[(label, 'all', metric)], 'difference')
    case = manifest['cases'][0]['case']
    lines = [
        '# Fallback results: key establishment and data transport', '',
        f"All {report['runs_checked']} scheduled runs completed: six conditions over seeds "
        f"{min(report['seed_ids'])} through {max(report['seed_ids'])}. Every compared condition "
        'has identical arrival and exogenous environment digests for each matched seed. '
        'Duplicate/missing records, mixed source hashes, scenario mismatches, or incompatible '
        'service/assurance counts cause the analysis to fail rather than produce this report.', '',
        f"The scenario is the eight-node formation, {case['horizon_s']/3600:g} simulated hours, "
        f"{case['initial_spendable_fraction']*100:g}% initially spendable stock, retained-key policy, "
        f"ISR arrival scale {case['isr_scale']:g}, authentication count {case['n_auth']}, "
        'independent environmental interruptions, and a weighted all-terminal cut of relative cost two. '
        'Generation suppression and transport denial use the same selected cut. The global online '
        'key-establishment service flag is an additional controlled dimension; no physical attack '
        'cost is assigned to making that service unavailable.', '',
        'Service here means timely key-supply or modeled session-admission service. No payload '
        'cipher, bandwidth/serialization, packet delivery, or application throughput is simulated. '
        'Payload-weighted loss is an associated-payload exposure proxy, not observed transmitted '
        'or compromised data. The 0.35-second online setup time is an assumption, not a KEM benchmark.', '',
        'Reported values are means of eight seed-level fractions, with marginal 95% percentile '
        'bootstrap intervals in brackets (20,000 resamples, bootstrap seed 71). They are not '
        'simultaneous intervals and do not include model uncertainty. Percentages describe the '
        'stated denominator; comparison differences are percentage points.', '',
        '## Joint delivery and assurance outcomes', '',
        '| Condition | Timely key service % | Authorized key service % | Below-floor service / arrivals % | '
        'Below-ITS service / entitled arrivals % | Entitled arrivals blocked % |',
        '|---|---|---|---|---|---|',
    ]
    for name in LABELS:
        cells = [mean(name, metric) for metric in (
            'availability', 'qualified_availability', 'degraded_arrival_fraction',
            'forced_entitled_fraction', 'entitled_blocked_fraction')]
        lines.append('| ' + ' | '.join([LABELS[name], *cells]) + ' |')
    lines += ['',
        'Authorized service, below-floor service, and blocking partition all arrivals. '
        'ITS-key service, below-ITS service, and entitled blocking partition all G1/G2-entitled '
        'arrivals. These are separate decompositions: G2 can violate an ISR G1 floor while still '
        'meeting the ITS-key classification. A smaller below-ITS fraction after blocking more '
        'requests is not an assurance improvement for the denied population.', '',
        '## Paired contrasts', '',
        '| Treatment minus control | Timely-service difference, pp | Authorized-service difference, pp | '
        'Below-ITS difference on entitled arrivals, pp | Entitled-blocking difference, pp |',
        '|---|---|---|---|---|',
    ]
    for label, treatment, control in COMPARISONS:
        cells = [difference(label, metric) for metric in (
            'availability', 'qualified_availability', 'forced_entitled_fraction', 'entitled_blocked_fraction')]
        lines.append('| ' + ' | '.join([f'{LABELS[treatment]} minus {LABELS[control]}', *cells]) + ' |')
    lines += ['',
        f"With generation suppressed and the online key-establishment service unavailable, "
        f"timely service is {mean(ONLINE_DOWN, 'availability')}%. Ideal pre-positioned shared "
        f"keys yield {mean(PREPLACED_DOWN, 'availability')}%, a paired increase of "
        f"{difference('preplaced_minus_online_control_down', 'availability')} percentage points. "
        f"Authorized service changes by {difference('preplaced_minus_online_control_down', 'qualified_availability')} "
        'percentage points. The recovered delivery must therefore be read together with its '
        'reported below-floor and below-ITS composition; it is not restored QKD-grade service.', '',
        f"Under transport denial, online KEM and pre-positioned fallback provide "
        f"{mean(TRANSPORT_ONLINE, 'availability')}% and {mean(TRANSPORT_PREPLACED, 'availability')}% "
        'timely service respectively. The full cut removes every data path during the attack. '
        'The attack ends at the arrival horizon, after which the simulator lets the last arrivals '
        'reach their deadlines. Any residual service in this transport-cut cohort is therefore '
        'post-release service, not delivery through an unavailable path. This reporting convention '
        'must not be mistaken for a permanent transport-cut experiment.', '',
        'Changing the key-establishment flag has no operational effect on the ideal pre-positioned '
        'mode by construction. Its exact paired equality checks that separation; it is not physical '
        'evidence that a deployed pre-positioned-key system is unaffected by all control failures.', '',
        '## Limits and artifacts', '',
        'Pre-positioned symmetric fallback assumes sufficient, valid, unexpired already-shared '
        'key material and zero online setup. Finite stock, expiry, refresh, key-distribution '
        'authentication, and KEM computation are not modeled. G3/G4 are assurance-policy labels '
        'in this simulation; no KEM or cryptographic combiner is executed. The result separates '
        'availability dependencies and does not establish a cryptographic security guarantee.', '',
        'The complete [summary](../../results/revision/fallback/analysis/summary.csv), '
        '[paired comparisons](../../results/revision/fallback/analysis/paired_comparisons.csv), '
        '[verification record](../../results/revision/fallback/analysis/verification.json), and '
        '[raw per-seed files](../../results/revision/fallback/runs/) retain per-class and '
        'payload-weighted metrics in addition to the aggregate values above. An undefined metric '
        'is left undefined; it is never replaced with zero or summarized after silently dropping seeds.', '',
        'Reproduce the analysis without rerunning simulations:', '',
        '```powershell',
        'python -X faulthandler -u -c "from experiments.analyze_revision_fallback import main; raise SystemExit(main())"',
        '```', '',
        'The analysis uses [revision/metrics.py](../../revision/metrics.py) and the separate '
        '[analysis script](../../experiments/analyze_revision_fallback.py). Its input guards and '
        'hand-derived paired-difference checks are in '
        '[tests/test_fallback_analysis.py](../../tests/test_fallback_analysis.py).', '',
    ]
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'results/revision/fallback')
    parser.add_argument('--doc', type=Path, default=ROOT / 'docs/revision/FALLBACK_RESULTS.md')
    args = parser.parse_args(argv)
    manifest_path = args.input / 'manifest_shard0of1.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    paths = sorted((args.input / 'runs').glob('*.json'))
    rows = [json.loads(path.read_text(encoding='utf-8')) for path in paths]
    report = analyze_rows(manifest, rows)
    output = args.input / 'analysis'
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / 'summary.csv', report['summary'])
    _write_csv(output / 'paired_comparisons.csv', report['comparisons'])
    verification = {key: value for key, value in report.items() if key not in ('summary', 'comparisons')}
    verification.update(analyzed_utc=datetime.now(timezone.utc).isoformat(),
                        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                        analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        raw_file_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                         for path in paths})
    (output / 'verification.json').write_text(json.dumps(verification, indent=2, allow_nan=False)
                                            + '\n', encoding='utf-8')
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(markdown_report(report, manifest), encoding='utf-8')
    print(json.dumps({'runs_verified': report['runs_checked'], 'paired_trace_identity': True,
                      'summary_rows': len(report['summary']),
                      'comparison_rows': len(report['comparisons']), 'doc': str(args.doc)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
