"""Figure 3 of the camera-ready paper: downgrade-forcing cost against relay depth.

PYTHONDONTWRITEBYTECODE=1 python experiments/make_fig_forcing_cost_cr.py

k*(F >= 0.5) is the smallest budget whose mean forced assurance loss over seeds
reaches one half after a 24 h attack (fail-degraded, 2% usable fill, n_auth = 7).
Offline adversaries come from results/camera_ready (depths 1-6, budgets 1..d+2);
the online route-observing adversary from results/revision/online_adversary and
online_persistence (depths 2, 4, 6; budgets 1, 2; budget 2 is the cut).
Writes figures/camera_ready/fig3_forcing_cost.pdf/.png and a provenance JSON.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from revision.camera_ready import CRCase  # noqa: E402
from dataclasses import asdict  # noqa: E402

OUT = ROOT / 'figures' / 'camera_ready'
STEM = 'fig3_forcing_cost'
W, H = 3.45, 1.32
FS = 7.0
BLUE, VERM, GREEN, ORANGE, PURPLE = '#0072B2', '#D55E00', '#009E73', '#E69F00', '#CC79A7'


def serif_font():
    have = {f.name for f in fontManager.ttflist}
    return next((n for n in ('Times New Roman', 'STIXGeneral') if n in have), 'serif')


mpl.rcParams.update({'font.family': 'serif', 'font.serif': [serif_font(), 'STIXGeneral'],
                     'mathtext.fontset': 'stix', 'font.size': FS, 'pdf.fonttype': 42,
                     'ps.fonttype': 42, 'savefig.dpi': 300, 'axes.linewidth': 0.6,
                     'xtick.major.width': 0.6, 'ytick.major.width': 0.6})


def offline_curves():
    manifest = json.loads((ROOT / 'results/camera_ready/manifest_chain.json').read_text())
    seeds = manifest['seed_ids']
    index = {}
    for record in manifest['cases']:
        c = record['case']
        key = (c['topology'], c['attack_method'], c['attack_budget'], c['fail_mode'])
        assert key not in index, key
        index[key] = record['case_id']
    base = asdict(CRCase())
    for record in manifest['cases']:
        c = record['case']
        for k, v in base.items():
            if k not in ('topology', 'attack_method', 'attack_budget', 'fail_mode'):
                assert c[k] == v, (k, c[k], v)
    curves, detail = {}, {}
    for method in ('static_betweenness', 'adaptive_betweenness', 'weighted_cut'):
        ks = []
        for depth in range(1, 7):
            k_star, f_by_budget = None, {}
            for budget in range(1, depth + 3):
                cid = index[(f'chain{depth}', method, budget, 'FAIL_DEGRADED')]
                f = []
                for seed in seeds:
                    run = json.loads((ROOT / 'results/camera_ready/runs'
                                      / f'{cid}_seed{seed}.json').read_text())
                    assert run['case']['fail_mode'] == 'FAIL_DEGRADED'
                    f.append(run['summary']['all']['forced_entitled_fraction'])
                f_by_budget[budget] = float(np.mean(f))
                if k_star is None and f_by_budget[budget] >= 0.5:
                    k_star = budget
            ks.append(k_star)
            detail[f'{method}_d{depth}'] = dict(k_star=k_star, F_by_budget=f_by_budget)
        curves[method] = ks
    return curves, detail, seeds


def online_points():
    points, detail = {}, {}
    sources = {'release_on_unusable': 'online_persistence', 'persistent_slots': 'online_persistence'}
    for variant, folder in sources.items():
        ks = {}
        for path in sorted((ROOT / 'results/revision' / folder / 'runs').glob('*.json')):
            run = json.loads(path.read_text())
            if run['variant'] != variant:
                continue
            ks.setdefault(run['depth'], {}).setdefault(run['budget'], []).append(
                run['summary']['all']['forced_entitled_fraction'])
        out = {}
        for depth, by_budget in sorted(ks.items()):
            means = {b: float(np.mean(v)) for b, v in sorted(by_budget.items())}
            k_star = next((b for b, m in means.items() if m >= 0.5), None)
            out[depth] = k_star
            detail[f'{variant}_d{depth}'] = dict(k_star=k_star, F_by_budget=means,
                                                 seeds=len(next(iter(by_budget.values()))))
        points[variant] = out
    return points, detail


def main():
    curves, detail, seeds = offline_curves()
    online, online_detail = online_points()
    depths = np.arange(1, 7)
    fig, ax = plt.subplots(figsize=(W, H))
    fig.subplots_adjust(left=0.13, right=0.99, bottom=0.285, top=0.975)
    style = {'static_betweenness': (BLUE, 'o', '-', 'static betweenness'),
             'adaptive_betweenness': (GREEN, 's', '--', 'residual betweenness'),
             'weighted_cut': (VERM, 'D', ':', 'minimum cut')}
    for method, (color, marker, ls, label) in style.items():
        ks = np.array([np.nan if k is None else k for k in curves[method]], float)
        ax.plot(depths, ks, color=color, marker=marker, ls=ls, lw=1.1, ms=3.6, label=label,
                zorder=3 if method != 'weighted_cut' else 4)
    for variant, (color, marker, label) in {
            'persistent_slots': (PURPLE, 'v', 'online, persistent'),
            'release_on_unusable': (ORANGE, '^', 'online, releasing')}.items():
        xs, ys, censored = [], [], []
        for depth, k in online[variant].items():
            if k is None:
                censored.append(depth)
            else:
                xs.append(depth + (0.12 if variant == 'persistent_slots' else -0.12))
                ys.append(k)
        ax.plot(xs, ys, ls='none', marker=marker, color=color, ms=4.2, mfc='white',
                mew=1.0, label=label, zorder=5)
        for depth in censored:
            ax.annotate('', xy=(depth - 0.12, 4.1), xytext=(depth - 0.12, 2.15),
                        arrowprops=dict(arrowstyle='-|>', color=color, lw=1.2,
                                        mutation_scale=8))
            ax.text(depth - 0.2, 4.15, '$>2$', color=color, fontsize=FS,
                    ha='right', va='bottom')
    ax.set_xlabel('Relay-chain depth $d$ (hops)')
    ax.set_ylabel(r'$k^\ast(F\geq0.5)$')
    ax.set_xticks(depths)
    ax.set_yticks(range(1, 9))
    ax.set_ylim(0.6, 10.9)
    ax.set_xlim(0.7, 6.3)
    ax.grid(axis='y', color='#dddddd', lw=0.5)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.legend(loc='upper left', frameon=False, fontsize=FS, handlelength=2.2,
              borderaxespad=0.05, labelspacing=0.18, ncol=1)
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(OUT / f'{STEM}.{ext}')
    plt.close(fig)
    prov = dict(offline=detail, online=online_detail, seeds_offline=seeds,
                offline_k_star=curves, online_k_star=online)
    (OUT / f'{STEM}.provenance.json').write_text(json.dumps(prov, indent=1))
    print('k* offline', curves)
    print('k* online', online)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
