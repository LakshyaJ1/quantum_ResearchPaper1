"""E7 -- Policy-space audit of the control heuristics.

Claim (narrow, falsifiable):
    Within model M, the hand-designed heuristic attains X% of the best policy
    discoverable in M under a hard constraint on command traffic.

This is a statement about our design's HEADROOM, not about the world. Evaluation
is deliberately out-of-distribution rather than nominal: if the heuristic
degrades more gracefully than the searched policy, we publish that -- it is a
stronger and more credible result than any win.

Run: python experiments/e7_policy_audit.py [--iters N] [--pop N]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

from qkdsim.config import AdversaryConfig, OutageConfig, ReservoirConfig, SimConfig
from qkdsim.network import formation_9node
from qkdsim.rl import (ACTION_NAMES, DEFER, N_STATES, Shield, TablePolicy,
                       heuristic_table, objective, score_components,
                       state_label)
from qkdsim.sim import Simulator

N_ACTIONS = len(ACTION_NAMES)


# --------------------------------------------------------------------------
def _eval(args) -> Dict[str, float]:
    """Score one policy table. Top-level for multiprocessing."""
    table, seed, shield_on, cond, horizon, warmup = args
    cfg = SimConfig(
        horizon_s=horizon, warmup_s=warmup, seed=seed, routing="KAR",
        fail_mode="FAIL_DEGRADED",
        reservoir=ReservoirConfig(),
        adversary=AdversaryConfig(budget_links=cond.get("k", 0),
                                  delta_e=cond.get("delta_e", 0.05)),
        outage=OutageConfig(mean_uptime_s=cond.get("uptime", 3600.0),
                            mean_outage_s=cond.get("outage", 120.0)),
    )
    topo = formation_9node(cfg.reservoir)
    scale = cond.get("rate_scale", 1.0)
    if scale != 1.0:
        for k in topo.all_link_keys():
            topo.links[k].nominal_rate_bps *= scale
    traffic = None
    if cond.get("demand_scale", 1.0) != 1.0:
        from qkdsim.config import TRAFFIC_CLASSES
        from dataclasses import replace as _rep
        ds = cond["demand_scale"]
        traffic = tuple(_rep(t, arrival_rate=t.arrival_rate * ds)
                        for t in TRAFFIC_CLASSES)
    pol = (TablePolicy(table, Shield(enabled=shield_on))
           if table is not None else None)
    sim = (Simulator(topo, cfg, grade_policy=pol) if traffic is None
           else Simulator(topo, cfg, traffic=traffic, grade_policy=pol))
    r = sim.run()
    out = score_components(r)
    out["seed"] = seed
    return out


def score(table, seeds: Sequence[int], shield_on: bool, cond: Dict,
          ex, horizon: float, warmup: float) -> Tuple[float, Dict[str, float]]:
    jobs = [(table, s, shield_on, cond, horizon, warmup) for s in seeds]
    rows = list(ex.map(_eval, jobs))
    keys = [k for k in rows[0] if k != "seed"]
    mean = {k: float(np.mean([r[k] for r in rows])) for k in keys}
    return mean["J"], mean


# --------------------------------------------------------------------------
def cem_search(ex, iters: int, pop: int, elite_frac: float,
               seeds: Sequence[int], horizon: float, warmup: float,
               shield_on: bool, rng: np.random.Generator
               ) -> Tuple[Tuple[int, ...], float, List[Dict]]:
    """Cross-entropy method over a categorical policy table.

    Every candidate is scored by FULL simulation rollouts, so the sequential key
    economy (serving now depletes key later) is evaluated exactly rather than
    approximated by an invented opportunity-cost term.
    """
    probs = np.full((N_STATES, N_ACTIONS), 1.0 / N_ACTIONS)
    n_elite = max(2, int(pop * elite_frac))
    best_tab, best_j = None, -1e18
    history: List[Dict] = []
    for it in range(iters):
        cands = []
        for _ in range(pop):
            tab = tuple(int(rng.choice(N_ACTIONS, p=probs[s]))
                        for s in range(N_STATES))
            cands.append(tab)
        js = []
        for tab in cands:
            j, _ = score(tab, seeds, shield_on, {}, ex, horizon, warmup)
            js.append(j)
        order = np.argsort(js)[::-1]
        elites = [cands[i] for i in order[:n_elite]]
        if js[order[0]] > best_j:
            best_j, best_tab = js[order[0]], cands[order[0]]
        counts = np.full((N_STATES, N_ACTIONS), 1.0)  # Laplace smoothing
        for tab in elites:
            for s, a in enumerate(tab):
                counts[s, a] += 1.0
        probs = counts / counts.sum(axis=1, keepdims=True)
        history.append({"iter": it, "best_J": float(js[order[0]]),
                        "mean_J": float(np.mean(js)),
                        "running_best_J": float(best_j)})
        print(f"    iter {it:>2}  best={js[order[0]]:.4f}  "
              f"mean={np.mean(js):.4f}  running_best={best_j:.4f}")
    return best_tab, best_j, history


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=12)
    ap.add_argument("--pop", type=int, default=20)
    ap.add_argument("--train-seeds", type=int, default=2)
    ap.add_argument("--eval-seeds", type=int, default=8)
    ap.add_argument("--workers", type=int, default=0)
    a = ap.parse_args()
    import os
    workers = a.workers or min(8, max(1, (os.cpu_count() or 2) - 1))

    TRAIN_H, TRAIN_W = 21_600.0, 10_800.0    # 6 h / 3 h for search speed
    EVAL_H, EVAL_W = 86_400.0, 43_200.0      # full 24 h / 12 h for reporting
    train_seeds = list(range(a.train_seeds))
    eval_seeds = list(range(a.eval_seeds))
    rng = np.random.default_rng(7)

    print("=" * 78)
    print("E7  POLICY-SPACE AUDIT")
    print(f"states={N_STATES} actions={N_ACTIONS} "
          f"policy space={N_ACTIONS**N_STATES:.3g}")
    print(f"CEM: iters={a.iters} pop={a.pop} train_seeds={len(train_seeds)} "
          f"workers={workers}")
    print("=" * 78)
    t0 = time.time()

    with ProcessPoolExecutor(max_workers=workers) as ex:
        heur = heuristic_table()
        print("\n[1] Heuristic baseline (same policy class, apples-to-apples)")
        j_h_tr, _ = score(heur, train_seeds, True, {}, ex, TRAIN_H, TRAIN_W)
        print(f"    train-horizon J = {j_h_tr:.4f}")

        print("\n[2] CEM search, SHIELDED (C2 never below G2)")
        best, j_best_tr, hist = cem_search(
            ex, a.iters, a.pop, 0.25, train_seeds, TRAIN_H, TRAIN_W, True, rng)

        print("\n[3] CEM search, UNSHIELDED (ablation: price of the C2 guarantee)")
        best_u, j_best_u_tr, hist_u = cem_search(
            ex, a.iters, a.pop, 0.25, train_seeds, TRAIN_H, TRAIN_W, False,
            np.random.default_rng(8))

        # ---- full-horizon evaluation, nominal ---------------------------
        print("\n[4] Full-horizon evaluation (24 h, 12 h warm-up excluded)")
        rows = []
        for name, tab, sh in (("heuristic", heur, True),
                              ("searched-shielded", best, True),
                              ("searched-unshielded", best_u, False)):
            j, comp = score(tab, eval_seeds, sh, {}, ex, EVAL_H, EVAL_W)
            comp["policy"] = name
            comp["condition"] = "nominal"
            rows.append(comp)
        print(f"    {'policy':<21}{'J':>8}{'avail':>8}{'ITS%':>8}"
              f"{'viol':>8}{'C2<ITS':>9}{'key Mbit':>10}")
        for r in rows:
            print(f"    {r['policy']:<21}{r['J']:>8.4f}{r['avail']:>8.4f}"
                  f"{r['its_share']:>8.4f}{r['viol']:>8.4f}"
                  f"{r['c2_below_its']:>9.4f}{r['key_Mbit']:>10.1f}")

        jh = next(r["J"] for r in rows if r["policy"] == "heuristic")
        jb = next(r["J"] for r in rows if r["policy"] == "searched-shielded")
        ju = next(r["J"] for r in rows if r["policy"] == "searched-unshielded")
        print(f"\n    HEADROOM: heuristic attains {100.0 * jh / jb:.1f}% of the "
              f"best shielded policy found (J {jh:.4f} vs {jb:.4f}).")
        print(f"    PRICE OF THE C2 GUARANTEE: unshielded J {ju:.4f} vs "
              f"shielded {jb:.4f}  (delta {ju - jb:+.4f})")
        c2u = next(r["c2_below_its"] for r in rows
                   if r["policy"] == "searched-unshielded")
        print(f"    Unshielded C2 traffic below ITS: {c2u:.4f} "
              f"(shield holds this at 0 by construction)")

        # ---- OOD grid ----------------------------------------------------
        print("\n[5] Out-of-distribution stress (trained nominal, tested shifted)")
        conds = {
            "SKR x0.25": {"rate_scale": 0.25},
            "SKR x0.50": {"rate_scale": 0.50},
            "SKR x2.00": {"rate_scale": 2.00},
            "adversary k=2": {"k": 2},
            "adversary k=4": {"k": 4},
            "dual outage": {"uptime": 900.0, "outage": 240.0},
            "demand x2": {"demand_scale": 2.0},
        }
        print(f"    {'condition':<16}{'heur J':>9}{'srch J':>9}{'delta':>9}"
              f"{'heur ITS%':>11}{'srch ITS%':>11}{'winner':>9}")
        ood = []
        for cname, cond in conds.items():
            jh_c, ch = score(heur, eval_seeds, True, cond, ex, EVAL_H, EVAL_W)
            jb_c, cb = score(best, eval_seeds, True, cond, ex, EVAL_H, EVAL_W)
            win = "searched" if jb_c > jh_c else "heuristic"
            print(f"    {cname:<16}{jh_c:>9.4f}{jb_c:>9.4f}{jb_c - jh_c:>+9.4f}"
                  f"{ch['its_share']:>11.4f}{cb['its_share']:>11.4f}{win:>9}")
            ch.update({"policy": "heuristic", "condition": cname})
            cb.update({"policy": "searched-shielded", "condition": cname})
            ood += [ch, cb]
        rows += ood

        # ---- artifacts ---------------------------------------------------
        with open(RESULTS / "e7_policy_audit.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("    -> results/e7_policy_audit.csv")

        print("\n[6] THE SEARCHED POLICY, in full. This is the auditable artifact:")
        print("    (the policy class is a 12-cell lookup table, so it is")
        print("     interpretable by construction -- no distillation needed)")
        print(f"\n    {'state':<28}{'heuristic':>12}{'searched':>12}")
        tbl = []
        for i in range(N_STATES):
            h_a, b_a = ACTION_NAMES[heur[i]], ACTION_NAMES[best[i]]
            flag = "" if h_a == b_a else "   <-- differs"
            print(f"    {state_label(i):<28}{h_a:>12}{b_a:>12}{flag}")
            tbl.append({"state": state_label(i), "heuristic": h_a,
                        "searched": b_a, "differs": h_a != b_a})
        with open(RESULTS / "e7_policy_table.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["state", "heuristic",
                                               "searched", "differs"])
            w.writeheader()
            w.writerows(tbl)
        (RESULTS / "e7_history.json").write_text(json.dumps(
            {"shielded": hist, "unshielded": hist_u}, indent=2))
        print("    -> results/e7_policy_table.csv, results/e7_history.json")

    print(f"\ntotal wall time: {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
