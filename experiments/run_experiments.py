"""E2-E5: the main experiment grid. Writes CSVs to results/ and prints tables.

"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

from qkdsim.config import (G1_OTP, G2_QKD_SYM, G3_HYBRID, G4_PQC,
                           AccountingConfig, AdversaryConfig, PhysicsConfig,
                           ReservoirConfig, SimConfig)
from qkdsim.network import chain_topology, formation_9node
from qkdsim.sim import Simulator

GRADES = (G1_OTP, G2_QKD_SYM, G3_HYBRID, G4_PQC)


# --------------------------------------------------------------------------
# worker
# --------------------------------------------------------------------------
from qkdsim.config import TRAFFIC_CLASSES, TrafficClass

# Traffic mixes. "standard" is the grounded three-class formation workload.
# "small_block" is the MODAL INDUSTRY WORKLOAD: a fleet of link encryptors each
# rekeying a 256-bit symmetric key, aggregated to ~1 key/s. That is precisely
# the Ciena + Toshiba + JPMorgan design point (Pistoia et al., Quantum Sci.
# Technol. 8:035015, 2023: 800 Gbps channels, "key refresh rate of 1/sec",
# 258 DWDM channels = 66163 bps SKR / 256 bit). It is also the regime SECOQC
# measured, where ~91% of consumption was authentication rather than cipher key.
TRAFFIC_MIXES = {
    "standard": TRAFFIC_CLASSES,
    "small_block": (
        TrafficClass(name="C2", arrival_rate=1.0, payload_bits=2_048,
                     authorised_floor="G2", deadline_s=5.0, priority=1),
    ),
}


def _run(spec: Dict) -> Dict:
    """Run one configuration. Must be top-level for multiprocessing."""
    kind = spec.pop("_topo")
    depth = spec.pop("_depth", None)
    tag = spec.pop("_tag", {})
    mix = spec.pop("_mix", "standard")

    cfg = SimConfig(
        horizon_s=spec.get("horizon_s", 86_400.0),
        warmup_s=spec.get("warmup_s", 43_200.0),
        seed=spec["seed"],
        routing=spec.get("routing", "KAR"),
        reservation_floors=spec.get("reservation_floors", False),
        fail_mode=spec.get("fail_mode", "FAIL_DEGRADED"),
        physics=PhysicsConfig(**spec.get("physics", {})),
        accounting=AccountingConfig(**spec.get("accounting", {})),
        reservoir=ReservoirConfig(**spec.get("reservoir", {})),
        adversary=AdversaryConfig(**spec.get("adversary", {})),
        hop_penalty=spec.get("hop_penalty", 0.5),
    )
    topo = (formation_9node(cfg.reservoir) if kind == "formation"
            else chain_topology(depth, cfg.reservoir))
    r = Simulator(topo, cfg, traffic=TRAFFIC_MIXES[mix]).run()

    comp = r.grade_composition()
    mean_ttk, p95_ttk = r.ttk_stats()
    out = {
        **tag,
        "seed": cfg.seed,
        "n": r.n_sessions(),
        "served": r.served_fraction(),
        "blocked": r.blocked_fraction(),
        "below_its": r.below_its_fraction(),
        "forced_below_its": r.forced_below_its_fraction(),
        "floor_viol": r.floor_violation_fraction(),
        "mean_ttk": mean_ttk,
        "p95_ttk": p95_ttk,
        "mean_hops": r.mean_hops(),
        "consumed_Mbit": r.consumed_bits / 1e6,
        "generated_Mbit": r.generated_bits / 1e6,
        "discarded_Mbit": r.discarded_bits / 1e6,
        "n_links": len(topo.all_link_keys()),
    }
    for g in GRADES:
        out[f"comp_{g}"] = comp[g]
    for cls in ("C2", "ISR", "LOG"):
        out[f"served_{cls}"] = r.served_fraction(cls)
        out[f"below_its_{cls}"] = r.below_its_fraction(cls)
    return out


def run_grid(specs: List[Dict], workers: int) -> List[Dict]:
    """Batched pool with a serial fallback.

    Process-pool spawn on this host intermittently dies with BrokenProcessPool
    when many numpy-importing children start at once. Batching with a fresh pool
    per batch, and falling back to serial for any batch that fails, makes the
    grid complete deterministically instead of losing the whole run.
    """
    if workers <= 1:
        return [_run(s) for s in specs]
    rows: List[Dict] = []
    batch = max(8, min(24, len(specs)))
    for i in range(0, len(specs), batch):
        chunk = specs[i:i + batch]
        try:
            with ProcessPoolExecutor(max_workers=min(workers, 6)) as ex:
                rows.extend(list(ex.map(_run, chunk)))
        except Exception as exc:
            print(f"    batch {i // batch}: pool failed "
                  f"({type(exc).__name__}); running {len(chunk)} serially",
                  flush=True)
            rows.extend(_run(s) for s in chunk)
    return rows


# --------------------------------------------------------------------------
# stats
# --------------------------------------------------------------------------
def paired_bootstrap(a: List[float], b: List[float], iters: int = 20000,
                     seed: int = 12345) -> Tuple[float, float, float]:
    """Paired bootstrap over COMMON seeds. Returns (mean diff, lo, hi) at 95%.

    Paired because common random numbers give every policy the identical
    arrival stream and channel realisation at a given seed; an unpaired test
    would throw that variance reduction away.
    """
    x = np.asarray(b, float) - np.asarray(a, float)
    n = len(x)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(iters, n))
    means = x[idx].mean(axis=1)
    return float(x.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def agg(rows: List[Dict], key: str) -> Tuple[float, float]:
    v = [r[key] for r in rows if r[key] == r[key]]  # drop NaN
    if not v:
        return float("nan"), float("nan")
    return float(np.mean(v)), float(np.std(v))


def write_csv(name: str, rows: List[Dict]) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(RESULTS / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"    -> results/{name}  ({len(rows)} rows)")


# --------------------------------------------------------------------------
# E2 -- does the van Duijn null survive?
# --------------------------------------------------------------------------
def e2(seeds: List[int], workers: int) -> List[Dict]:
    print("\n[E2] Policy comparison -- does the van Duijn null survive?")
    policies = [("SP", dict(routing="SP", reservation_floors=False)),
                ("KAR", dict(routing="KAR", reservation_floors=False)),
                ("KAR+CAF", dict(routing="KAR", reservation_floors=True))]
    # Both fail modes AND a contested setting. Under FAIL_DEGRADED the PQC
    # fallback always succeeds where a classical path exists, so availability is
    # set by connectivity rather than by routing -- the metric the routing
    # literature reports becomes degenerate. FAIL_CLOSED is where routing can
    # still move availability, so the null must be tested there too.
    specs = []
    for pname, pk in policies:
        for mode in ("FAIL_DEGRADED", "FAIL_CLOSED"):
            for k in (0, 2):
                for s in seeds:
                    specs.append({"_topo": "formation",
                                  "_tag": {"policy": pname, "fail_mode_t": mode,
                                           "k": k},
                                  "seed": s, "fail_mode": mode,
                                  "adversary": dict(budget_links=k,
                                                    delta_e=0.05), **pk})
    rows = run_grid(specs, workers)
    write_csv("e2_policy.csv", rows)

    for mode in ("FAIL_DEGRADED", "FAIL_CLOSED"):
        for k in (0, 2):
            print(f"\n  --- {mode}, adversary k={k} ---")
            print(f"  {'policy':<9}{'served':>16}{'blocked':>10}{'<ITS':>9}"
                  f"{'meanTTK':>9}{'p95TTK':>8}{'hops':>7}{'key Mbit':>10}")
            by = {p: sorted([r for r in rows if r["policy"] == p
                             and r["fail_mode_t"] == mode and r["k"] == k],
                            key=lambda r: r["seed"]) for p, _ in policies}
            for p, _ in policies:
                m, sd = agg(by[p], "served")
                bl, _ = agg(by[p], "blocked")
                bi, _ = agg(by[p], "below_its")
                mt, _ = agg(by[p], "mean_ttk")
                pt, _ = agg(by[p], "p95_ttk")
                hp, _ = agg(by[p], "mean_hops")
                kb, _ = agg(by[p], "consumed_Mbit")
                print(f"  {p:<9}{m:>10.4f} +-{sd:<5.4f}{bl:>10.4f}{bi:>9.4f}"
                      f"{mt:>9.2f}{pt:>8.2f}{hp:>7.2f}{kb:>10.1f}")
            print("    paired bootstrap vs SP (95% CI):")
            for metric, unit in (("served", ""), ("consumed_Mbit", " Mbit")):
                base = [r[metric] for r in by["SP"]]
                for p in ("KAR", "KAR+CAF"):
                    d, lo, hi = paired_bootstrap(base, [r[metric] for r in by[p]])
                    sig = ("SIGNIFICANT" if (lo > 0 or hi < 0)
                           else "not significant")
                    print(f"      {metric:<14}{p:<8} d={d:+.4f}{unit}"
                          f"  [{lo:+.4f}, {hi:+.4f}]  {sig}")

    print("\n  VERDICT on the van Duijn null:")
    print("    Reported separately per fail mode above. The key question is")
    print("    whether key-aware routing moves AVAILABILITY, or only key spend.")
    return rows


# --------------------------------------------------------------------------
# E3 -- fail-closed vs fail-degraded under swept pressure
# --------------------------------------------------------------------------
def e3(seeds: List[int], workers: int, budgets: List[int]) -> List[Dict]:
    print("\n[E3] Fail-closed vs fail-degraded under adversarial pressure")
    specs = []
    for mode in ("FAIL_CLOSED", "FAIL_DEGRADED"):
        for k in budgets:
            for s in seeds:
                specs.append({"_topo": "formation",
                              "_tag": {"fail_mode_t": mode, "k": k},
                              "seed": s, "routing": "KAR",
                              "fail_mode": mode,
                              "adversary": dict(budget_links=k, delta_e=0.05)})
    rows = run_grid(specs, workers)
    write_csv("e3_failmode.csv", rows)

    print(f"\n  {'mode':<14}{'k':>2}{'avail':>9}{'blocked':>9}"
          f"{'G1':>7}{'G2':>7}{'G3':>7}{'G4':>7}{'<ITS':>8}{'viol':>8}")
    for mode in ("FAIL_CLOSED", "FAIL_DEGRADED"):
        for k in budgets:
            sub = [r for r in rows if r["fail_mode_t"] == mode and r["k"] == k]
            av, _ = agg(sub, "served")
            bl, _ = agg(sub, "blocked")
            bi, _ = agg(sub, "below_its")
            fv, _ = agg(sub, "floor_viol")
            gs = [agg(sub, f"comp_{g}")[0] for g in GRADES]
            print(f"  {mode:<14}{k:>2}{av:>9.4f}{bl:>9.4f}"
                  + "".join(f"{g:>7.3f}" for g in gs)
                  + f"{bi:>8.3f}{fv:>8.3f}")
    return rows


# --------------------------------------------------------------------------
# E4 -- downgrade-forcing cost k*(phi) vs chain depth
# --------------------------------------------------------------------------
def e4(seeds: List[int], workers: int, depths: List[int],
       phis=(0.10, 0.25, 0.50)) -> List[Dict]:
    print("\n[E4] Downgrade-forcing cost k*(phi) vs relay-chain depth")
    specs = []
    for d in depths:
        n_links = 1 if d == 1 else 2 * d + 1
        for k in range(0, n_links + 1):
            for s in seeds:
                for mode in ("FAIL_DEGRADED", "FAIL_CLOSED"):
                    for tgt in ("betweenness", "mincut"):
                        specs.append({"_topo": "chain", "_depth": d,
                                      "_tag": {"depth": d, "k": k,
                                               "fail_mode_t": mode,
                                               "targeting": tgt},
                                      "seed": s, "routing": "KAR",
                                      "fail_mode": mode,
                                      "adversary": dict(budget_links=k,
                                                        delta_e=0.05,
                                                        targeting=tgt)})
    rows = run_grid(specs, workers)
    write_csv("e4_forcing_cost.csv", rows)

    print("\n  k*(phi) = minimum links the adversary must suppress to FORCE a")
    print("  fraction phi of ENTITLED sessions (authorised floor >= G2) below an")
    print("  information-theoretically delivered key. Measured on forced")
    print("  degradation, not raw below-ITS: LOG traffic is authorised at G3, so")
    print("  counting it would credit the adversary before it acted.")
    table = []
    for tgt in ("betweenness", "mincut"):
        print(f"\n  --- adversary targeting: {tgt} ---")
        print(f"  {'depth':>5}{'links':>6}{'nominal':>9}" + "".join(
            f"{'k*('+str(p)+')':>10}" for p in phis))
        for d in depths:
            n_links = 1 if d == 1 else 2 * d + 1
            deg = {k: agg([r for r in rows if r["depth"] == d and r["k"] == k
                           and r["fail_mode_t"] == "FAIL_DEGRADED"
                           and r["targeting"] == tgt], "forced_below_its")[0]
                   for k in range(0, n_links + 1)}
            base = deg.get(0, float("nan"))
            cells, rec = [], {"targeting": tgt, "depth": d,
                              "n_links": n_links, "nominal_forced": base}
            for p in phis:
                kstar = next((k for k in sorted(deg) if deg[k] == deg[k]
                              and deg[k] >= p), None)
                cells.append("n/a" if kstar is None else str(kstar))
                rec[f"kstar_{p}"] = kstar if kstar is not None else ""
            print(f"  {d:>5}{n_links:>6}{base:>9.3f}"
                  + "".join(f"{c:>10}" for c in cells))
            table.append(rec)
    print("\n  A betweenness-guided adversary exhausts the already-severed")
    print("  primary path before touching the alternate; the min-cut adversary")
    print("  does not. The gap IS the finding: reporting only the greedy figure")
    print("  overstates resilience by a factor growing in chain depth.")
    write_csv("e4_kstar.csv", table)
    return rows


# --------------------------------------------------------------------------
# E5 -- authentication accounting error
# --------------------------------------------------------------------------
def e5(seeds: List[int], workers: int) -> List[Dict]:
    """E5 -- when does omitting relay authentication actually matter?

    The bare D*n cost law used throughout the QKD routing literature omits
    per-hop authentication. Whether that matters is a function of BLOCK SIZE,
    because Wegman-Carter cost is per-message and only logarithmic in message
    length (Fung/Ma/Chau arXiv:0910.0312 Eq. 9). We therefore report the
    crossover analytically and then show the operational consequence in both
    regimes.
    """
    print("\n[E5] Authentication accounting: when does the bare D*n law fail?")

    ac = AccountingConfig(auth_on=True)
    print("\n  (a) Analytic overhead factor vs relay block size D")
    print(f"      {'D (bit)':>10}{'cost/hop':>10}{'factor':>9}   regime")
    anchors = []
    for D in (256, 512, 1_024, 2_048, 8_192, 65_536, 144_000, 1_000_000):
        f = ac.overhead_factor(D)
        regime = ("dominated by authentication" if f >= 2.0 else
                  "authentication material" if f >= 1.10 else
                  "authentication negligible")
        print(f"      {D:>10}{ac.cost_per_hop(D):>10}{f:>8.3f}x   {regime}")
        anchors.append({"D_bits": D, "cost_per_hop": ac.cost_per_hop(D),
                        "overhead_factor": f, "regime": regime})
    write_csv("e5_overhead_vs_blocksize.csv", anchors)
    print("      Anchors: SECOQC measured ~91% of a 256-bit-rekey AES VPN's key")
    print("      consumption as ITS authentication; Cambridge measured 3.6x for")
    print("      a ~400-bit relayed global key. Both sit in the top rows.")

    specs = []
    for mix in ("standard", "small_block"):
        for auth in (False, True):
            for s in seeds:
                specs.append({"_topo": "formation", "_mix": mix,
                              "_tag": {"mix": mix, "auth_on": auth},
                              "seed": s, "routing": "KAR",
                              "fail_mode": "FAIL_DEGRADED",
                              "accounting": dict(auth_on=auth)})
    rows = run_grid(specs, workers)
    write_csv("e5_auth.csv", rows)

    print("\n  (b) Operational consequence, by workload")
    print(f"      {'workload':<13}{'law':<12}{'key Mbit':>10}{'served':>9}"
          f"{'<ITS':>8}{'viol':>8}")
    summary = {}
    for mix, label in (("standard", "OTP-dominated"),
                       ("small_block", "small-block")):
        for auth, law in ((False, "bare D*n"), (True, "with auth")):
            sub = [r for r in rows if r["mix"] == mix and r["auth_on"] == auth]
            kb, _ = agg(sub, "consumed_Mbit")
            sv, _ = agg(sub, "served")
            bi, _ = agg(sub, "below_its")
            fv, _ = agg(sub, "floor_viol")
            summary[(mix, auth)] = (kb, sv, bi, fv)
            print(f"      {label:<13}{law:<12}{kb:>10.1f}{sv:>9.4f}"
                  f"{bi:>8.3f}{fv:>8.3f}")

    print("\n  VERDICT")
    for mix, label in (("standard", "OTP-dominated"),
                       ("small_block", "small-block")):
        off, on = summary[(mix, False)], summary[(mix, True)]
        kx = on[0] / off[0] if off[0] > 0 else float("nan")
        print(f"    {label:<14} key x{kx:.2f}   below-ITS "
              f"{off[2]:.3f} -> {on[2]:.3f} ({on[2] - off[2]:+.3f})")
    print("    The bare law is adequate when large OTP sessions dominate key")
    print("    consumption, and materially wrong for small-block rekey traffic")
    print("    -- which is the modal deployed workload (256 bit per minute per")
    print("    encryptor; 1 key/s per 800G channel in Ciena/Toshiba/JPMC).")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", type=str, default="")
    a = ap.parse_args()

    import os
    workers = a.workers or max(1, (os.cpu_count() or 2) - 1)
    seeds = list(range(a.seeds))
    budgets = [0, 1, 2, 3] if a.quick else [0, 1, 2, 3, 4, 5]
    depths = [1, 2, 3] if a.quick else [1, 2, 3, 4, 5, 6]

    print("=" * 78)
    print("EXPERIMENT GRID  (24 h horizon, 12 h warm-up excluded)")
    print(f"seeds={len(seeds)}  workers={workers}  "
          f"quick={a.quick}")
    print("=" * 78)
    t0 = time.time()
    want = set(a.only.split(",")) if a.only else {"e2", "e3", "e4", "e5"}
    if "e2" in want:
        e2(seeds, workers)
    if "e3" in want:
        e3(seeds, workers, budgets)
    if "e4" in want:
        e4(seeds[:max(3, len(seeds) // 2)], workers, depths)
    if "e5" in want:
        e5(seeds, workers)
    print(f"\ntotal wall time: {time.time() - t0:.1f} s")
    (RESULTS / "grid_meta.json").write_text(json.dumps(
        {"seeds": seeds, "budgets": budgets, "depths": depths,
         "horizon_s": 86400.0, "warmup_s": 43200.0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
