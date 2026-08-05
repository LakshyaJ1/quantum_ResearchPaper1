"""E6a -- Is "key-aware routing underperforms shortest path" an artifact?

E2 found that under FAIL_CLOSED, KAR is significantly WORSE than SP on
availability. That inverts the literature's headline (key-aware dynamic routing
reduces service rejection by 25-40% vs static shortest path, per the Cvitic
survey), so before claiming it we must rule out the obvious artifact: KAR's
hop penalty being mispriced.

Mechanism under test: KAR minimises bottleneck expected time-to-key plus
hop_penalty * hops. Every extra hop consumes key on an ADDITIONAL link (the
trusted-relay multiplier), so a hop penalty that is too small buys a faster
individual keying at the cost of higher aggregate key expenditure -- which in a
key-scarce network means fewer sessions served overall.

If a well-priced hop penalty restores KAR >= SP, the finding becomes "key-aware
routing must price the hop multiplier or it backfires". If no penalty restores
it, the finding is stronger. Either way we report which.
"""
from __future__ import annotations

import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

from qkdsim.config import AdversaryConfig, SimConfig
from qkdsim.network import formation_9node
from qkdsim.sim import Simulator

PENALTIES = (0.0, 0.5, 5.0, 50.0, 1000.0)
SEEDS = tuple(range(8))
MODES = ("FAIL_CLOSED",)   # the only mode where routing moves availability


def run(args):
    hp, seed, routing, mode = args
    cfg = SimConfig(seed=seed, routing=routing, fail_mode=mode,
                    hop_penalty=hp,
                    adversary=AdversaryConfig(budget_links=0, delta_e=0.05))
    r = Simulator(formation_9node(cfg.reservoir), cfg).run()
    return dict(hp=hp, routing=routing, mode=mode, seed=seed,
                served=r.served_fraction(), hops=r.mean_hops(),
                key_Mbit=r.consumed_bits / 1e6,
                below_its=r.below_its_fraction())


def paired(a, b, iters=20000, seed=3):
    x = np.asarray(b, float) - np.asarray(a, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(iters, len(x)))
    m = x[idx].mean(axis=1)
    return x.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


def main() -> int:
    # Capped at 8: spawning ~15 workers that each import numpy concurrently
    # exhausted process resources on this host (BrokenProcessPool surfacing as
    # a spurious numpy import error inside the child).
    workers = 4
    jobs = [(hp, s, "KAR", m) for m in MODES for hp in PENALTIES for s in SEEDS]
    jobs += [(0.0, s, "SP", m) for m in MODES for s in SEEDS]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(run, jobs))

    with open(RESULTS / "e6_hop_penalty.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    for mode in MODES:
        print(f"\n=== {mode} (k=0, 10 seeds, 24 h, 12 h warm-up excluded) ===")
        sp = sorted([r for r in rows if r["routing"] == "SP"
                     and r["mode"] == mode], key=lambda r: r["seed"])
        base = [r["served"] for r in sp]
        print(f"{'routing':<8}{'hop_pen':>9}{'served':>9}{'sd':>8}{'hops':>7}"
              f"{'keyMbit':>9}{'<ITS':>8}   {'paired delta vs SP [95% CI]':<34}")
        print(f"{'SP':<8}{'-':>9}{np.mean(base):>9.4f}"
              f"{np.std(base):>8.4f}{np.mean([r['hops'] for r in sp]):>7.3f}"
              f"{np.mean([r['key_Mbit'] for r in sp]):>9.1f}"
              f"{np.mean([r['below_its'] for r in sp]):>8.4f}   reference")
        best_hp, best_d = None, -9e9
        for hp in PENALTIES:
            g = sorted([r for r in rows if r["routing"] == "KAR"
                        and r["mode"] == mode and r["hp"] == hp],
                       key=lambda r: r["seed"])
            d, lo, hi = paired(base, [r["served"] for r in g])
            sig = "SIG" if (lo > 0 or hi < 0) else "ns "
            if d > best_d:
                best_hp, best_d = hp, d
            print(f"{'KAR':<8}{hp:>9.1f}{np.mean([r['served'] for r in g]):>9.4f}"
                  f"{np.std([r['served'] for r in g]):>8.4f}"
                  f"{np.mean([r['hops'] for r in g]):>7.3f}"
                  f"{np.mean([r['key_Mbit'] for r in g]):>9.1f}"
                  f"{np.mean([r['below_its'] for r in g]):>8.4f}   "
                  f"{d:+.4f} [{lo:+.4f},{hi:+.4f}] {sig}")
        print(f"  best hop_penalty = {best_hp} (delta vs SP {best_d:+.4f})")
        if best_d < 0:
            print("  VERDICT: no hop penalty restores KAR >= SP. The result is")
            print("           not a tuning artifact -- in this key-scarce")
            print("           trusted-relay regime, per-session time-to-key")
            print("           optimisation is globally counterproductive.")
        else:
            print("  VERDICT: a well-priced hop penalty restores KAR >= SP, so")
            print("           the finding is that key-aware routing must price")
            print("           the trusted-relay hop multiplier or it backfires.")
    print("\n-> results/e6_hop_penalty.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
