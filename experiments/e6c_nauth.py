r"""E6c -- Does the headline survive the authentication recalibration?

E8 showed our n_auth = 2 is a lower bound, not a measurement: Cambridge's
measured relay overhead implies n_auth ~ 7, and SECOQC's application-level
tunnel implies ~40. Raising n_auth raises the per-hop key cost, which tightens
scarcity -- so the fail-closed / fail-degraded headline must be re-checked at
the calibrated value before it can be reported.

If the headline reverses at n_auth = 7, the paper's central claim is an artefact
of an optimistic accounting assumption and must be rewritten. If it survives,
the recalibration strengthens the paper: the result holds under a harsher and
better-grounded key economy.
"""
from __future__ import annotations

import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RES = ROOT / "results"
RES.mkdir(exist_ok=True)

from qkdsim.config import AccountingConfig, AdversaryConfig, SimConfig
from qkdsim.network import formation_9node
from qkdsim.sim import Simulator

N_AUTH = (2, 7, 20, 40)
SEEDS = tuple(range(8))


def run(args):
    n_auth, k, mode, seed = args
    cfg = SimConfig(
        seed=seed, routing="KAR", fail_mode=mode,
        accounting=AccountingConfig(n_auth=n_auth),
        adversary=AdversaryConfig(budget_links=k, delta_e=0.05),
    )
    r = Simulator(formation_9node(cfg.reservoir), cfg).run()
    return dict(n_auth=n_auth, k=k, mode=mode, seed=seed,
                avail=r.served_fraction(), blocked=r.blocked_fraction(),
                forced=r.forced_below_its_fraction(),
                viol=r.floor_violation_fraction(),
                g1=r.grade_composition()["G1"],
                g4=r.grade_composition()["G4"],
                key_Mbit=r.consumed_bits / 1e6)


def mean(rows, key):
    v = [r[key] for r in rows if r[key] == r[key]]
    return float(np.mean(v)) if v else float("nan")


def main() -> int:
    jobs = [(n, k, m, s) for n in N_AUTH for k in (0, 2)
            for m in ("FAIL_CLOSED", "FAIL_DEGRADED") for s in SEEDS]
    print(f"running {len(jobs)} configurations ...")
    rows = []
    BATCH = 24
    for i in range(0, len(jobs), BATCH):
        chunk = jobs[i:i + BATCH]
        try:
            with ProcessPoolExecutor(max_workers=6) as ex:
                rows.extend(list(ex.map(run, chunk)))
        except Exception as exc:
            print(f"  pool failed ({type(exc).__name__}); serial fallback")
            rows.extend(run(j) for j in chunk)
        print(f"  {min(i + BATCH, len(jobs))}/{len(jobs)}", flush=True)

    with open(RES / "e6c_nauth.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    ac = {n: AccountingConfig(n_auth=n) for n in N_AUTH}
    print("\n=== Does the headline survive authentication recalibration? ===")
    print(f"{'n_auth':>7}{'cost/hop':>10}{'source':<26}"
          f"{'FC k=0':>8}{'FC k=2':>8}{'FD k=0':>8}{'FD k=2':>8}{'key Mb':>9}")
    src = {2: "assumed lower bound", 7: "Cambridge (calibrated)",
           20: "intermediate", 40: "SECOQC application tunnel"}
    ok = True
    for n in N_AUTH:
        sel = lambda k, m: [r for r in rows if r["n_auth"] == n
                            and r["k"] == k and r["mode"] == m]
        fc0 = mean(sel(0, "FAIL_CLOSED"), "avail")
        fc2 = mean(sel(2, "FAIL_CLOSED"), "avail")
        fd0 = mean(sel(0, "FAIL_DEGRADED"), "forced")
        fd2 = mean(sel(2, "FAIL_DEGRADED"), "forced")
        kb = mean(sel(2, "FAIL_DEGRADED"), "key_Mbit")
        print(f"{n:>7}{ac[n].cost_per_hop(256):>10}{src[n]:<26}"
              f"{fc0:>8.3f}{fc2:>8.3f}{fd0:>8.3f}{fd2:>8.3f}{kb:>9.1f}")
        # headline = fail-closed loses >0.2 availability AND fail-degraded
        # gains >0.2 forced loss, going from k=0 to k=2
        if not (fc2 < fc0 - 0.20 and fd2 > fd0 + 0.20):
            ok = False
    print(f"\n  VERDICT: the headline {'SURVIVES' if ok else 'DOES NOT SURVIVE'}"
          f" at every n_auth tested.")
    if ok:
        print("  The fail-closed/fail-degraded exchange rate is therefore not an")
        print("  artefact of the optimistic n_auth = 2 assumption. Reporting the")
        print("  calibrated value (7) makes the key economy harsher and the")
        print("  result holds, which strengthens rather than weakens the claim.")
    print("\n-> results/e6c_nauth.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
