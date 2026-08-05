"""E6b -- Sensitivity of the headline result to its uncertain parameters.

Four questions, each answered by re-running rather than by argument:

  A1  the degradation exponent gamma is unresolved by a factor of five, so the
      headline is re-run at both the asymptotic and the measured calibration
  A2  the security-abort threshold is an engineering value, so 0.11 is run as well
  A3  fail-degraded availability is invariant under QBER injection; classical-channel
      denial is run to show the attack that does defeat it
  A4  the injection axis, to locate the capability threshold
  A5  the budget axis at each sub-threshold injection, to test whether budget
      substitutes for capability

Usage: python experiments/e6b_sensitivity.py [--from-csv]
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

from qkdsim.config import AdversaryConfig, PhysicsConfig, SimConfig
from qkdsim.network import formation_9node
from qkdsim.sim import Simulator

SEEDS = tuple(range(6))


def run(args):
    gamma, e_abort, deny, k, mode, seed, delta_e = args
    cfg = SimConfig(
        seed=seed, routing="KAR", fail_mode=mode,
        physics=PhysicsConfig(gamma=gamma, e_abort=e_abort),
        adversary=AdversaryConfig(budget_links=k, delta_e=delta_e,
                                  deny_classical=deny),
    )
    r = Simulator(formation_9node(cfg.reservoir), cfg).run()
    return dict(gamma=gamma, e_abort=e_abort, deny_classical=deny, k=k,
                mode=mode, seed=seed, delta_e=delta_e,
                avail=r.served_fraction(), blocked=r.blocked_fraction(),
                forced=r.forced_below_its_fraction(),
                viol=r.floor_violation_fraction(),
                g4=r.grade_composition()["G4"],
                key_Mbit=r.consumed_bits / 1e6)


def mean(rows, key):
    v = [r[key] for r in rows if r[key] == r[key]]
    return float(np.mean(v)) if v else float("nan")


def load_csv():
    """Re-read a completed run to re-derive the tables without resimulating."""
    with open(RES / "e6b_sensitivity.csv", newline="") as fh:
        out = []
        for r in csv.DictReader(fh):
            out.append(dict(
                gamma=float(r["gamma"]), e_abort=float(r["e_abort"]),
                deny_classical=r["deny_classical"].lower() == "true",
                k=int(r["k"]), mode=r["mode"], seed=int(r["seed"]),
                delta_e=float(r["delta_e"]), avail=float(r["avail"]),
                blocked=float(r["blocked"]), forced=float(r["forced"]),
                viol=float(r["viol"]), g4=float(r["g4"]),
                key_Mbit=float(r["key_Mbit"])))
        return out


def main() -> int:
    if "--from-csv" in sys.argv:
        rows = load_csv()
        print(f"re-deriving tables from {len(rows)} stored rows "
              f"(no simulation)\n")
        return report(rows)
    jobs = [(g, ea, dn, k, m, s, 0.05)
            for g in (1.0, 3.4)
            for ea in (0.075, 0.11)
            for dn in (False, True)
            for k in (0, 2)
            for m in ("FAIL_CLOSED", "FAIL_DEGRADED")
            for s in SEEDS]
    # A4: the delta_e axis. The cliff should sit where the injection is large
    # enough to cross the abort threshold, i.e. delta_e >= e_abort - e0.
    jobs += [(1.0, ea, False, 2, m, s, de)
             for ea in (0.075, 0.11)
             for de in (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)
             for m in ("FAIL_CLOSED", "FAIL_DEGRADED")
             for s in SEEDS]
    # A5: budget x capability. A4 varies capability at ONE budget (k=2), which
    # cannot support a claim about substituting budget for capability. This block
    # varies the budget at each SUB-threshold injection, so that "more links do
    # not compensate for weaker injection" is tested rather than asserted.
    # k=2 is already covered by A4; e_abort is fixed at the primary 0.075.
    jobs += [(1.0, 0.075, False, k, m, s, de)
             for de in (0.01, 0.02, 0.03, 0.04)
             for k in (1, 3, 4, 5)
             for m in ("FAIL_CLOSED", "FAIL_DEGRADED")
             for s in SEEDS]
    print(f"running {len(jobs)} configurations ...")
    # Process-pool spawn on this host intermittently dies (BrokenProcessPool).
    # Run in small batches with a fresh pool each, and fall back to serial for
    # any batch that fails, so the experiment completes deterministically.
    rows = []
    BATCH = 24
    for i in range(0, len(jobs), BATCH):
        chunk = jobs[i:i + BATCH]
        try:
            with ProcessPoolExecutor(max_workers=6) as ex:
                rows.extend(list(ex.map(run, chunk)))
        except Exception as exc:
            print(f"  batch {i // BATCH}: pool failed ({type(exc).__name__}), "
                  f"running {len(chunk)} serially")
            rows.extend(run(j) for j in chunk)
        print(f"  {min(i + BATCH, len(jobs))}/{len(jobs)} done", flush=True)
    with open(RES / "e6b_sensitivity.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return report(rows)


def report(rows) -> int:
    # Every selector must pin delta_e: the A4 and A5 blocks add rows at the same
    # (gamma, e_abort, k) with other injections, so omitting it averages
    # sub-threshold and super-threshold results together.
    print("\n=== A1/A2: does the k=0 -> k=2 headline hold across gamma and "
          "e_abort? (QBER injection, delta_e = 0.05) ===")
    print(f"{'gamma':>6}{'e_abort':>9}  {'mode':<15}"
          f"{'avail k=0':>10}{'avail k=2':>10}{'forced k=0':>12}{'forced k=2':>12}")
    verdict_ok = True
    for g in (1.0, 3.4):
        for ea in (0.075, 0.11):
            for m in ("FAIL_CLOSED", "FAIL_DEGRADED"):
                sel = lambda k: [r for r in rows if r["gamma"] == g
                                 and r["e_abort"] == ea and not r["deny_classical"]
                                 and r["k"] == k and r["mode"] == m
                                 and r["delta_e"] == 0.05]
                a0, a2 = mean(sel(0), "avail"), mean(sel(2), "avail")
                f0, f2 = mean(sel(0), "forced"), mean(sel(2), "forced")
                print(f"{g:>6.1f}{ea:>9.3f}  {m:<15}{a0:>10.4f}{a2:>10.4f}"
                      f"{f0:>12.4f}{f2:>12.4f}")
                # A collapse is only expected where delta_e crosses the abort
                # threshold, i.e. 0.05 >= e_abort - e0. At e_abort = 0.11 the
                # injection is sub-threshold and no collapse SHOULD occur.
                if 0.05 >= ea - 0.03:
                    if m == "FAIL_CLOSED" and not (a2 < a0 - 0.2):
                        verdict_ok = False
                    if m == "FAIL_DEGRADED" and not (f2 > f0 + 0.2):
                        verdict_ok = False
    print(f"\n  VERDICT: where the injection crosses the abort threshold, the")
    print(f"  qualitative headline {'HOLDS' if verdict_ok else 'DOES NOT HOLD'}"
          f" at both gamma values.")
    print("  (fail-closed loses >20 pts availability; fail-degraded gains >20 pts")
    print("   forced assurance loss, at k=2 vs k=0.) At e_abort=0.11, delta_e=0.05")
    print("   is sub-threshold, so the absence of a collapse is the capability")
    print("   threshold at work rather than a failure of the headline.")

    print("\n=== A3: classical-channel denial -- the attack that defeats "
          "fail-degraded (delta_e = 0.05) ===")
    print(f"{'attack':<26}{'mode':<16}{'avail':>9}{'blocked':>9}"
          f"{'forced':>9}{'G4 share':>10}")
    for dn, label in ((False, "QBER injection"), (True, "classical denial")):
        for m in ("FAIL_CLOSED", "FAIL_DEGRADED"):
            sel = [r for r in rows if r["deny_classical"] == dn
                   and r["k"] == 2 and r["mode"] == m
                   and r["gamma"] == 1.0 and r["e_abort"] == 0.075
                   and r["delta_e"] == 0.05]
            print(f"{label:<26}{m:<16}{mean(sel,'avail'):>9.4f}"
                  f"{mean(sel,'blocked'):>9.4f}{mean(sel,'forced'):>9.4f}"
                  f"{mean(sel,'g4'):>10.4f}")
    print("\n=== A4: the delta_e axis -- the cliff is at delta_e >= "
          "e_abort - e0 (e0 = 0.03) ===")
    print(f"{'e_abort':>8}{'needs de':>10}{'delta_e':>9}"
          f"{'FC avail':>10}{'FD forced':>11}")
    for ea in (0.075, 0.11):
        need = ea - 0.03
        for de in (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10):
            fc = mean([r for r in rows if r["e_abort"] == ea
                       and r["delta_e"] == de and r["k"] == 2
                       and r["mode"] == "FAIL_CLOSED"
                       and not r["deny_classical"] and r["gamma"] == 1.0],
                      "avail")
            fd = mean([r for r in rows if r["e_abort"] == ea
                       and r["delta_e"] == de and r["k"] == 2
                       and r["mode"] == "FAIL_DEGRADED"
                       and not r["deny_classical"] and r["gamma"] == 1.0],
                      "forced")
            mark = "  <-- crosses abort" if de >= need else ""
            print(f"{ea:>8.3f}{need:>10.3f}{de:>9.2f}{fc:>10.4f}{fd:>11.4f}{mark}")

    print("\n=== A5: does BUDGET substitute for CAPABILITY below threshold? ===")
    print("  e_abort=0.075, so the capability threshold is delta_e = 0.045.")
    print(f"  {'delta_e':>8}" + "".join(f"{'k=' + str(k):>10}" for k in
                                        (1, 2, 3, 4, 5)) + "   FC availability")
    flat = True
    for de in (0.01, 0.02, 0.03, 0.04):
        cells = []
        for k in (1, 2, 3, 4, 5):
            v = mean([r for r in rows if r["gamma"] == 1.0
                      and r["e_abort"] == 0.075 and not r["deny_classical"]
                      and r["k"] == k and r["delta_e"] == de
                      and r["mode"] == "FAIL_CLOSED"], "avail")
            cells.append(v)
        span = max(cells) - min(cells)
        if span > 0.05:
            flat = False
        print(f"  {de:>8.2f}" + "".join(f"{c:>10.4f}" for c in cells)
              + f"   span {span:.4f}")
    print(f"  {'delta_e':>8}" + "".join(f"{'k=' + str(k):>10}" for k in
                                        (1, 2, 3, 4, 5)) + "   FD forced loss")
    for de in (0.01, 0.02, 0.03, 0.04):
        cells = []
        for k in (1, 2, 3, 4, 5):
            v = mean([r for r in rows if r["gamma"] == 1.0
                      and r["e_abort"] == 0.075 and not r["deny_classical"]
                      and r["k"] == k and r["delta_e"] == de
                      and r["mode"] == "FAIL_DEGRADED"], "forced")
            cells.append(v)
        print(f"  {de:>8.2f}" + "".join(f"{c:>10.4f}" for c in cells)
              + f"   max {max(cells):.4f}")
    print(f"\n  VERDICT: budget {'DOES NOT' if flat else 'DOES'} substitute for "
          f"capability below the threshold.")
    print("  (flat = availability spans <0.05 across a 5x range in link budget)")

    qi = mean([r for r in rows if not r["deny_classical"] and r["k"] == 2
               and r["mode"] == "FAIL_DEGRADED" and r["gamma"] == 1.0
               and r["e_abort"] == 0.075 and r["delta_e"] == 0.05], "avail")
    cd = mean([r for r in rows if r["deny_classical"] and r["k"] == 2
               and r["mode"] == "FAIL_DEGRADED" and r["gamma"] == 1.0
               and r["e_abort"] == 0.075 and r["delta_e"] == 0.05], "avail")
    print(f"\n  Fail-degraded availability under QBER injection: {qi:.4f}")
    print(f"  Fail-degraded availability under classical denial:  {cd:.4f}"
          f"   (delta {cd - qi:+.4f})")
    print("  A post-quantum fallback needs the classical channel. Denying that")
    print("  channel removes the fallback, so fail-degraded is NOT immune --")
    print("  it is immune only to attacks on the QUANTUM channel.")
    print("\n-> results/e6b_sensitivity.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
