"""Render existing sensitivity evidence into the six-page manuscript tables.

This does not run, change, or select new simulations. Matched load differences
are independently recomputed from the frozen per-seed analysis before export.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.revision_manuscript_data import scenario_row, select_one
from revision.metrics import paired_interval
from revision.scenarios import Case

DATA = ROOT / "results/revision/analysis"
OUT = ROOT / "results/revision/manuscript"


def stacked(mean, low, high):
    return r"\shortstack{" + f"{100*mean:.2f}" + r"\\" + f"({100*low:.2f}, {100*high:.2f})" + "}"


def rendered_evidence():
    raw = pd.read_csv(DATA / "sensitivity_canonical_raw_metrics.csv", float_precision="round_trip")
    pairs = pd.read_csv(DATA / "sensitivity_paired_comparisons.csv", float_precision="round_trip")
    ledger = {"basis": "Existing frozen eight-seed sensitivity cohort; no new runs.",
              "inputs": {}, "load": [], "attack_cost": []}
    for name in ("sensitivity_summary.csv", "sensitivity_canonical_raw_metrics.csv",
                 "sensitivity_paired_comparisons.csv"):
        ledger["inputs"][name] = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
    load_lines = [r"\begin{tabular}{@{}lccc@{}}", r"\toprule",
                  r"ISR factor & Closed $A$ & Fallback $Q$ & $\Delta A$ (pp)\\", r"\midrule"]
    for factor in (0.03, 0.1, 1.0):
        case = Case(attack_budget=2, isr_scale=factor)
        closed = scenario_row("sensitivity", replace(case, fail_mode="FAIL_CLOSED"))
        fallback = scenario_row("sensitivity", case)
        a = raw[(raw.case_id == fallback.case_id) & (raw.traffic_class == "all")].sort_values("seed")
        b = raw[(raw.case_id == closed.case_id) & (raw.traffic_class == "all")].sort_values("seed")
        if len(a) != 8 or len(b) != 8 or a.seed.nunique() != 8 or b.seed.nunique() != 8:
            raise ValueError("Load comparison requires exactly eight unique seeds per mode")
        if a.seed.tolist() != b.seed.tolist() or a.arrival_sha256.tolist() != b.arrival_sha256.tolist():
            raise ValueError("Load modes must have identical paired arrival cohorts")
        mean, low, high = paired_interval(a.availability.to_numpy(), b.availability.to_numpy())
        registered = select_one(pairs, **asdict(case),
                                comparison="degraded_minus_closed", metric="availability",
                                traffic_class="all")
        if not np.allclose((mean, low, high), registered[["difference", "lo", "hi"]].to_numpy(float),
                           rtol=0, atol=1e-12):
            raise ValueError("Recomputed paired interval differs from frozen analysis")
        load_lines.append(f"{factor:g} & {100*closed.availability:.2f} & "
                          f"{100*fallback.qualified_availability:.2f} & "
                          + stacked(mean, low, high) + r"\\[3pt]")
        ledger["load"].append({"isr_factor": factor, "control_case_id": closed.case_id,
                               "treatment_case_id": fallback.case_id,
                               "seeds": [int(s) for s in a.seed],
                               "closed_availability": float(closed.availability),
                               "fallback_availability": float(fallback.availability),
                               "fallback_qualified": float(fallback.qualified_availability),
                               "paired_availability_difference": [mean, low, high]})
    load_lines += [r"\bottomrule", r"\end{tabular}"]

    cost_lines = [r"\begin{tabular}{@{}lccc@{}}", r"\toprule",
                  r"Fiber cost & Static & Residual & Cut\\", r"\midrule"]
    for cost in (1.0, 10.0, 100.0):
        cells = []
        for method in ("static_betweenness", "adaptive_betweenness", "weighted_cut"):
            row = scenario_row("sensitivity", Case(attack_budget=2, fibre_attack_cost=cost,
                                                   attack_method=method))
            seeds = raw[(raw.case_id == row.case_id) & (raw.traffic_class == "all")].seed
            if len(seeds) != 8 or seeds.nunique() != 8:
                raise ValueError("Attack-cost cell requires exactly eight unique seeds")
            values = [float(row[k]) for k in ("forced_entitled_fraction",
                                              "forced_entitled_fraction_lo",
                                              "forced_entitled_fraction_hi")]
            cells.append(stacked(*values))
            ledger["attack_cost"].append({"fibre_relative_cost": cost, "method": method,
                                          "case_id": row.case_id,
                                          "forced_entitled_fraction": values})
        cost_lines.append(f"{cost:g} & " + " & ".join(cells) + r"\\[3pt]")
    cost_lines += [r"\bottomrule", r"\end{tabular}"]
    return {"load_table.tex": "\n".join(load_lines) + "\n",
            "cost_table.tex": "\n".join(cost_lines) + "\n",
            "refinement_claim_ledger.json": json.dumps(ledger, indent=2, allow_nan=False) + "\n"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = rendered_evidence()
    for name, text in expected.items():
        path = OUT / name
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                raise ValueError(f"Missing or stale manuscript evidence: {path}")
        else:
            path.write_text(text, encoding="utf-8")
    print("Verified existing sensitivity evidence and " +
          ("checked" if args.check else "exported") + " two manuscript tables.")


if __name__ == "__main__":
    main()
