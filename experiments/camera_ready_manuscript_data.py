"""Tables and cited values of the camera-ready manuscript, from raw run files only.

python experiments/camera_ready_manuscript_data.py

Reads results/revision/ (main, sensitivity, threshold, fallback, online, learning)
and results/camera_ready/ (envelope, threshold, floors, chain). Writes
results/camera_ready/manuscript/{head_table,envelope_table,learning_table}.tex and
claims.json, which records every tabulated or cited value with its cases and seeds.
Intervals: 95% percentile bootstrap over seeds, 20000 resamples (revision.metrics).
"""
from __future__ import annotations

import os
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')

from dataclasses import asdict
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from revision.camera_ready import CRCase
from revision.metrics import mean_interval, paired_interval

REV = ROOT / 'results' / 'revision'
CR = ROOT / 'results' / 'camera_ready'
OUTDIR = CR / 'manuscript'
CLAIMS = {}


def claim(name, value, **provenance):
    CLAIMS[name] = dict(value=value, **provenance)
    return value


# -- run loading --------------------------------------------------------------
def load_manifest(path):
    m = json.loads(Path(path).read_text(encoding='utf-8'))
    return m['cases'], m['seed_ids']


def find_case(cases, tag=None, **want):
    """Unique case whose fields equal CRCase defaults overridden by `want`.

    The revision suite hashes each case's JSON, so equal settings written as 86400 and
    86400.0 in different experiments get different ids (identical runs under common
    random numbers); `tag` selects the experiment a value is quoted from."""
    base = asdict(CRCase(**want))
    hits = []
    for record in cases:
        if tag is not None and tag not in record.get('tags', []):
            continue
        c = record['case']
        if all(c.get(k, base[k]) == v for k, v in base.items()):
            hits.append(record['case_id'])
    hits = sorted(set(hits))        # a case can appear under several manifest tags
    if len(hits) != 1:
        raise LookupError(f'{len(hits)} cases match {want}')
    return hits[0]


def runs(rundir, case_id, seeds):
    out = []
    for seed in seeds:
        path = Path(rundir) / f'{case_id}_seed{seed}.json'
        out.append(json.loads(path.read_text(encoding='utf-8')))
    return out


def metric(rs, name, cls='all'):
    return np.array([r['summary'][cls][name] for r in rs], float)


def g4_share(rs):
    vals = []
    for r in rs:
        counts = r['served_grade_counts']
        total = sum(sum(v.values()) for v in counts.values())
        vals.append(sum(v.get('G4', 0) for v in counts.values()) / total)
    return np.array(vals)


def ci(values):
    mean, lo, hi = mean_interval(values)
    return dict(mean=mean, lo=lo, hi=hi, sd=float(np.std(values, ddof=1)), n=len(values))


def signed(x, digits):
    """Signed fixed-point text; a value that rounds to zero is printed unsigned."""
    r = round(x, digits)
    return f'{0:.{digits}f}' if r == 0 else f'{r:+.{digits}f}'


def pct(x, digits=1):
    if x == 0:
        return '0'
    if abs(x * 100) < 0.05:
        return '$<$0.1'
    return f'{100 * x:.{digits}f}'


# -- Table II: fail-mode exchange rate ------------------------------------------
def head_table():
    cases, seeds = load_manifest(CR / 'manifest_floors.json')
    main_cases, main_seeds = load_manifest(REV / 'manifest_main.json')
    assert seeds == main_seeds, 'headline replay must use the main-grid seeds'
    rows, spread = [], {}
    cols = [('availability', 'all'), ('qualified_availability', 'all'),
            ('qualified_availability', 'C2'), ('qualified_availability', 'ISR'),
            ('qualified_availability', 'LOG'), ('forced_entitled_fraction', 'all')]
    specs = [('--', 0, 'weighted_cut'), ('cut', 1, 'weighted_cut'),
             ('cut', 2, 'weighted_cut'), ('betw.', 1, 'static_betweenness'),
             ('betw.', 2, 'static_betweenness')]
    for mode, label in (('FAIL_CLOSED', r'\textsc{closed}'), ('FAIL_DEGRADED', r'\textsc{degr.}')):
        for target, budget, method in specs:
            cid = find_case(cases, fail_mode=mode, attack_budget=budget, attack_method=method)
            rs = runs(CR / 'runs', cid, seeds)
            if method == 'weighted_cut':
                # Replay must equal the frozen main grid seed by seed.
                rid = next(r['case_id'] for r in main_cases
                           if r['case']['topology'] == 'formation'
                           and r['case']['attack_budget'] == budget
                           and r['case']['fail_mode'] == mode)
                ref = runs(REV / 'runs', rid, seeds)
                for name, cls in cols:
                    assert np.array_equal(metric(rs, name, cls), metric(ref, name, cls)), (cid, name)
            cells, key = [], f'head_{mode}_{method}_b{budget}'
            for name, cls in cols:
                s = ci(metric(rs, name, cls))
                claim(f'{key}_{name}_{cls}', s, case_id=cid, seeds=seeds)
                tag = 'isr' if cls == 'ISR' else 'other'
                spread[f'half_{tag}'] = max(spread.get(f'half_{tag}', 0.0),
                                            s['hi'] - s['mean'], s['mean'] - s['lo'])
                spread[f'sd_{tag}'] = max(spread.get(f'sd_{tag}', 0.0), s['sd'])
                cells.append(pct(s['mean']))
            g = ci(g4_share(rs))
            claim(f'{key}_g4_share', g, case_id=cid, seeds=seeds)
            spread['half_other'] = max(spread['half_other'], g['hi'] - g['mean'], g['mean'] - g['lo'])
            spread['sd_other'] = max(spread['sd_other'], g['sd'])
            cells.append(pct(g['mean']))
            rows.append(f'{label} & {target} & {budget} & ' + ' & '.join(cells) + r'\\')
        if mode == 'FAIL_CLOSED':
            rows.append(r'\addlinespace[2pt]')
    for k, v in spread.items():
        claim(f'head_max_{k}', v)
    body = '\n'.join([
        r'\begin{tabular}{@{}llrrrrrrrr@{}}', r'\toprule',
        r'Mode & Target & $b$ & $A$ & $Q$ & $Q_{\mathrm{C2}}$ & $Q_{\mathrm{ISR}}$ & '
        r'$Q_{\mathrm{LOG}}$ & $F$ & \GIV\\', r'\midrule', *rows, r'\bottomrule',
        r'\end{tabular}'])
    (OUTDIR / 'head_table.tex').write_text(body + '\n', encoding='utf-8')
    return spread


# -- Table IV: learned controllers ----------------------------------------------
def learning_table():
    d = json.loads((REV / 'learning' / 'test_results.json').read_text(encoding='utf-8'))
    rows = d['rows']
    seeds = sorted({r['seed'] for r in rows})
    conditions = sorted({r['condition'] for r in rows})
    assert len(seeds) == 12 and len(conditions) == 7

    def per_seed(policy, name, cls='all'):
        out = []
        for seed in seeds:
            vals = [r['summary'][cls][name] for r in rows
                    if r['policy_name'] == policy and r['seed'] == seed]
            assert len(vals) == len(conditions)
            out.append(float(np.mean(vals)))
        return np.array(out)

    def utility(policy):
        return (per_seed(policy, 'availability')
                - 0.75 * per_seed(policy, 'degraded_arrival_fraction'))

    metrics = [('J', lambda p: utility(p), 1e3), ('Q', lambda p: per_seed(p, 'qualified_availability'), 100),
               ('QISR', lambda p: per_seed(p, 'qualified_availability', 'ISR'), 100),
               ('FB', lambda p: per_seed(p, 'forced_payload_fraction'), 100)]
    # The 24 h nominal search returned the strict-floor table; its rollouts equal
    # strict_floor exactly (asserted here), so the two share one row.
    for name in ('availability', 'qualified_availability', 'forced_payload_fraction'):
        assert np.array_equal(per_seed('full_nominal', name), per_seed('strict_floor', name))
    labels = [('strict_floor', 'Strict floor$^\\ast$'), ('short_nominal', '6\\,h nominal'),
              ('full_robust', 'Multi-condition')]
    names = {'J': r'$\Delta J$ ($10^{-3}$)', 'Q': r'$\Delta Q$', 'QISR': r'$\Delta Q_{\mathrm{ISR}}$',
             'FB': r'$\Delta F_B$'}
    lines = []
    for key, fn, scale in metrics:
        cells = []
        for policy, _ in labels:
            diff, lo, hi = paired_interval(fn(policy), fn('budget_greedy'))
            claim(f'learn_{policy}_minus_greedy_{key}', dict(mean=diff, lo=lo, hi=hi),
                  seeds=seeds, conditions=conditions, scale=scale)
            digits = 1 if key == 'J' else 2
            cells.append(f'${signed(scale * diff, digits)}$ '
                         f'{{\\tiny$[{signed(scale * lo, digits)},{signed(scale * hi, digits)}]$}}')
        lines.append(f'{names[key]} & ' + ' & '.join(cells) + r'\\')
    greedy_j = float(np.mean(utility('budget_greedy')))
    robust_j = float(np.mean(utility('full_robust')))
    claim('learn_greedy_over_robust_J', greedy_j / robust_j)

    # Reversal prices: lambda* = dA/dL (strict floor vs heuristic) and
    # mu* = dJ/dF (learned vs heuristic), ratio of seed means, same bootstrap draws.
    idx = np.random.default_rng(71).integers(len(seeds), size=(20000, len(seeds)))

    def ratio(num, den):
        point = float(num.mean() / den.mean())
        boot = num[idx].mean(axis=1) / den[idx].mean(axis=1)
        return dict(mean=point, lo=float(np.quantile(boot, .025)),
                    hi=float(np.quantile(boot, .975)))

    dA = per_seed('strict_floor', 'availability') - per_seed('budget_greedy', 'availability')
    dL = (per_seed('strict_floor', 'degraded_arrival_fraction')
          - per_seed('budget_greedy', 'degraded_arrival_fraction'))
    claim('learn_lambda_star_strict_vs_greedy', ratio(dA, dL), seeds=seeds)
    dJ = utility('full_robust') - utility('budget_greedy')
    dF = (per_seed('full_robust', 'forced_entitled_fraction')
          - per_seed('budget_greedy', 'forced_entitled_fraction'))
    claim('learn_mu_star_robust_vs_greedy', ratio(dJ, dF), seeds=seeds)
    d, lo, hi = paired_interval(per_seed('full_robust', 'forced_entitled_fraction'),
                                per_seed('budget_greedy', 'forced_entitled_fraction'))
    claim('learn_full_robust_minus_greedy_F', dict(mean=d, lo=lo, hi=hi), seeds=seeds)
    d, lo, hi = paired_interval(per_seed('full_robust', 'degraded_arrival_fraction'),
                                per_seed('budget_greedy', 'degraded_arrival_fraction'))
    claim('learn_full_robust_minus_greedy_L', dict(mean=d, lo=lo, hi=hi), seeds=seeds)
    body = '\n'.join([r'\begin{tabular}{@{}lccc@{}}', r'\toprule',
                      ' & ' + ' & '.join(label for _, label in labels) + r'\\',
                      r'\midrule', *lines, r'\bottomrule', r'\end{tabular}'])
    (OUTDIR / 'learning_table.tex').write_text(body + '\n', encoding='utf-8')


def envelope_table():
    """Table III: forced loss against injection and budget, three graphs, outage-free."""
    env_cases, env_seeds = load_manifest(CR / 'manifest_envelope.json')
    thr_cases, thr_seeds = load_manifest(CR / 'manifest_threshold.json')
    assert env_seeds == thr_seeds
    columns = [(1.0, 0.03), (1.0, 0.04), (1.0, 0.045), (1.0, 0.05), (3.4, 0.03), (3.4, 0.04)]
    graphs = [('formation', 'Formation', 2, env_cases), ('parallel3', '3-path', 3, thr_cases),
              ('parallel4', '4-path', 4, thr_cases)]
    lines = []
    for topology, label, cut, cases in graphs:
        for budget in (cut - 1, cut, cut + 1):
            cells = []
            for gamma, delta in columns:
                values = {}
                for mode in ('FAIL_CLOSED', 'FAIL_DEGRADED'):
                    cid = find_case(cases, topology=topology, attack_budget=budget,
                                    delta_e=delta, gamma=gamma, outage_model='none',
                                    fail_mode=mode)
                    values[mode] = runs(CR / 'runs', cid, env_seeds)
                f = ci(metric(values['FAIL_DEGRADED'], 'forced_entitled_fraction'))
                a = ci(metric(values['FAIL_CLOSED'], 'availability'))
                claim(f'envelope_{topology}_b{budget}_g{gamma}_d{delta}',
                      dict(F=f, closed_A=a), seeds=env_seeds)
                half = max(f['hi'] - f['mean'], f['mean'] - f['lo'])
                if f['mean'] == 0 and half == 0:
                    cells.append('0')
                elif f['mean'] < 0.0005:
                    cells.append('$<$0.1')
                else:
                    digits = 2 if f['mean'] < 0.01 else 1
                    cells.append(f"{100 * f['mean']:.{digits}f}$\\pm${100 * half:.{digits}f}")
            name = label if budget == cut - 1 else ''
            lines.append(f'{name} & {budget} & ' + ' & '.join(cells) + r'\\')
        lines.append(r'\addlinespace[1pt]')
    body = '\n'.join([
        r'\begin{tabular}{@{}lrrrrrrr@{}}', r'\toprule',
        r' & & \multicolumn{4}{c}{$\gamma=1$, $\Delta e=$} & \multicolumn{2}{c}{$\gamma=3.4$, $\Delta e=$}\\',
        r'\cmidrule(lr){3-6}\cmidrule(l){7-8}',
        r'Graph & $b$ & 0.03 & 0.04 & 0.045 & 0.05 & 0.03 & 0.04\\', r'\midrule',
        *lines[:-1], r'\bottomrule', r'\end{tabular}'])
    (OUTDIR / 'envelope_table.tex').write_text(body + '\n', encoding='utf-8')


def floors_summary(verbose=False):
    """Submitted routing result (3): class-aware reservation floors, paired by seed."""
    cases, seeds = load_manifest(CR / 'manifest_floors.json')
    out = []
    cells = [dict(initial_spendable_fraction=f, isr_scale=i, attack_budget=b)
             for f in (0.02, 1.0) for i in (0.1, 1.0) for b in (0, 2)]
    cells += [dict(attack_budget=b, floor_scale=s) for s in (0.05, 0.25) for b in (0, 2)]
    for cell in cells:
        for mode in ('FAIL_CLOSED', 'FAIL_DEGRADED'):
            on = runs(CR / 'runs', find_case(cases, fail_mode=mode, reservation_floors=True,
                                             **cell), seeds)
            base = dict(cell)
            base.pop('floor_scale', None)
            off = runs(CR / 'runs', find_case(cases, fail_mode=mode, reservation_floors=False,
                                              **base), seeds)
            row = dict(cell, mode=mode)
            for name, cls in (('availability', 'all'), ('qualified_availability', 'all'),
                              ('availability', 'C2'), ('availability', 'ISR'),
                              ('availability', 'LOG'), ('forced_entitled_fraction', 'all'),
                              ('key_Mbit', 'all')):
                a, b = metric(on, name, cls), metric(off, name, cls)
                d, lo, hi = paired_interval(a, b)
                row[f'{name}_{cls}'] = dict(floors=float(a.mean()), none=float(b.mean()),
                                            diff=d, lo=lo, hi=hi)
            label = '_'.join(f'{k}{v}' for k, v in sorted(cell.items()))
            claim(f'floors_{mode}_{label}', row, seeds=seeds)
            out.append(row)
            if verbose:
                A, Q, L = (row['availability_all'], row['qualified_availability_all'],
                           row['availability_LOG'])
                print(f"{mode[5:]:9s} {label:60s} A {100*A['none']:5.1f}->{100*A['floors']:5.1f}"
                      f"  Q {100*Q['none']:5.1f}->{100*Q['floors']:5.1f}"
                      f"  LOG A {100*L['none']:5.1f}->{100*L['floors']:5.1f}"
                      f"  F {100*row['forced_entitled_fraction_all']['none']:5.1f}->"
                      f"{100*row['forced_entitled_fraction_all']['floors']:5.1f}")
    return out


def endurance_summary(verbose=False):
    """Cut-condition endurance T* against first forcing, and weather-only service (8 seeds)."""
    cases, seeds = load_manifest(REV / 'manifest_sensitivity.json')
    usable_capacity = 52_428_800 - 1_048_576
    demand = 0.05 * 1385 + 0.002 * 145_129 + 0.03 * 1257      # bit/s at floor debits, n_auth=7
    out = {}
    for fill in (0.02, 0.1, 1.0):
        deg = runs(REV / 'runs', find_case(cases, 'initial_reserve', initial_spendable_fraction=fill,
                                           attack_budget=2, fail_mode='FAIL_DEGRADED'), seeds)
        clo = runs(REV / 'runs', find_case(cases, 'initial_reserve', initial_spendable_fraction=fill,
                                           attack_budget=2, fail_mode='FAIL_CLOSED'), seeds)
        first = [r['summary']['all']['first_forced_s'] for r in deg]
        first = [x for x in first if x is not None and not (isinstance(x, float) and math.isnan(x))]
        t_star = 2 * fill * usable_capacity / demand
        row = dict(t_star_h=t_star / 3600,
                   first_forced_median_h=float(np.median(first)) / 3600 if first else None,
                   runs_with_forcing=len(first), runs=len(deg),
                   closed_A=float(metric(clo, 'availability').mean()),
                   predicted_closed_A=min(1.0, t_star / 86400))
        out[f'endurance_fill{fill}'] = row
        claim(f'endurance_fill{fill}', row, seeds=seeds)
    for model in ('independent', 'correlated'):
        rs = runs(REV / 'runs', find_case(cases, 'correlation', attack_budget=0, fail_mode='FAIL_CLOSED',
                                          outage_model=model, mean_uptime_s=900.0,
                                          mean_outage_s=600.0), seeds)
        value = ci(metric(rs, 'availability'))
        out[f'weather_{model}_closed_A'] = value
        claim(f'weather_900_600_{model}_unattacked_closed_A', value, seeds=seeds)
    if verbose:
        for k, v in out.items():
            print(k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})
    return out


def routing_summary(verbose=False):
    """Key-aware minus shortest-path routing by initial fill and warm-up (ISR x1)."""
    cases, seeds = load_manifest(CR / 'manifest_routing.json')
    out = {}
    for fill in (1.0, 0.02):
        for warmup in (43200, 0):
            sel = {r: runs(CR / 'runs', find_case(cases, isr_scale=1.0, routing=r,
                                                  initial_spendable_fraction=fill,
                                                  warmup_s=warmup, fail_mode='FAIL_CLOSED'),
                           seeds) for r in ('SP', 'KAR')}
            d, lo, hi = paired_interval(metric(sel['KAR'], 'availability'),
                                        metric(sel['SP'], 'availability'))
            row = dict(diff=d, lo=lo, hi=hi,
                       sp=float(metric(sel['SP'], 'availability').mean()),
                       kar=float(metric(sel['KAR'], 'availability').mean()),
                       isr_sp=float(metric(sel['SP'], 'availability', 'ISR').mean()),
                       isr_kar=float(metric(sel['KAR'], 'availability', 'ISR').mean()))
            out[f'routing_fill{fill}_warmup{warmup}'] = row
            claim(f'routing_fill{fill}_warmup{warmup}_KAR_minus_SP', row, seeds=seeds)
            if verbose:
                print(fill, warmup, {k: round(100 * v, 2) for k, v in row.items()})
    return out


def bridge_summary(verbose=False):
    """Submitted configuration on the submitted and corrected code, paired by seed."""
    rows = [json.loads(line) for line in
            (CR / 'bridge' / 'rows.jsonl').read_text(encoding='utf-8').splitlines()]

    def pick(**want):
        sel = sorted((r for r in rows if all(r[k] == v for k, v in want.items())),
                     key=lambda r: r['seed'])
        assert sel and len({r['seed'] for r in sel}) == len(sel), want
        return sel

    def vec(sel, name):
        return np.array([r[name] for r in sel], float)

    out = {}
    for mode in ('FAIL_CLOSED', 'FAIL_DEGRADED'):
        for k in (0, 1, 2, 5):
            orig = pick(cell='headline', variant='orig', mode=mode, k=k)
            cur = pick(cell='headline', variant='current', mode=mode, k=k)
            assert [r['seed'] for r in orig] == [r['seed'] for r in cur]
            for name in ('A', 'Q', 'F', 'F_submitted', 'A_submitted'):
                a, b = vec(cur, name), vec(orig, name)
                if np.all(np.isfinite(a - b)):
                    d, lo, hi = paired_interval(a, b)
                    out[f'bridge_{mode}_k{k}_{name}'] = dict(
                        orig=float(b.mean()), current=float(a.mean()), diff=d, lo=lo, hi=hi)
            if k:
                abl = pick(cell='headline', variant='ablation', mode=mode, k=k)
                out[f'bridge_{mode}_k{k}_ablation_maxdiff'] = max(
                    float(np.max(np.abs(vec(abl, name) - vec(orig, name))))
                    for name in ('A', 'F'))
    for variant, n_auth in (('orig', 2), ('current', 2), ('current', 7)):
        sp = pick(cell='routing', variant=variant, n_auth=n_auth, routing='SP')
        kar = (pick(cell='headline', variant=variant, mode='FAIL_CLOSED', k=0)
               if n_auth == 2 else pick(cell='routing', variant=variant, n_auth=7, routing='KAR'))
        d, lo, hi = paired_interval(vec(kar, 'A'), vec(sp, 'A'))
        out[f'bridge_routing_{variant}_n{n_auth}_KAR_minus_SP'] = dict(
            kar=float(vec(kar, 'A').mean()), sp=float(vec(sp, 'A').mean()), diff=d, lo=lo, hi=hi)
    for key, value in out.items():
        claim(key, value, source='results/camera_ready/bridge/rows.jsonl')
        if verbose:
            print(key, {k: round(v, 4) for k, v in value.items()} if isinstance(value, dict)
                  else value)
    return out


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    head_table()
    learning_table()
    envelope_table()
    floors_summary()
    routing_summary()
    endurance_summary()
    bridge_summary()
    (OUTDIR / 'claims.json').write_text(json.dumps(CLAIMS, indent=1, default=float),
                                        encoding='utf-8')
    print(f'{len(CLAIMS)} claims written to {OUTDIR}')


if __name__ == '__main__':
    main()
