"""Post-process the E7 policy table into the EFFECTIVE (post-shield) policy.

`e7_policy_table.csv` records the raw searched table. The shield projects any
action it forbids onto the strongest permitted grade before it ever reaches the
key economy, so the raw table is NOT what runs. Printing the raw table would let
a reader conclude that command traffic is served below G2, which never happens.

This script writes the effective policy alongside the raw one and flags exactly
where the shield intervened.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RES = ROOT / "results"

from qkdsim.config import G2_QKD_SYM, grade_rank, is_at_least
from qkdsim.rl import ACTION_NAMES, ACTIONS, DEFER

SRC = RES / "e7_policy_table.csv"
if not SRC.exists():
    raise SystemExit("run experiments/e7_policy_audit.py first")


def project(state: str, action: str) -> tuple[str, bool]:
    """Apply the shield exactly as qkdsim.rl.TablePolicy does."""
    is_c2 = state.strip().startswith("C2")
    if not is_c2 or action == "DEFER":
        return action, False
    if is_at_least(action, G2_QKD_SYM):
        return action, False
    # forbidden -> strongest permitted grade
    permitted = [g for g in ACTIONS if is_at_least(g, G2_QKD_SYM)]
    return min(permitted, key=grade_rank), True


rows = list(csv.DictReader(open(SRC, newline="")))
out = []
print(f"{'state':<28}{'heuristic':>10}{'searched(raw)':>15}"
      f"{'searched(effective)':>21}   note")
for r in rows:
    eff, clipped = project(r["state"], r["searched"])
    note = "SHIELD CLIPPED" if clipped else ("differs" if eff != r["heuristic"]
                                            else "")
    print(f"{r['state']:<28}{r['heuristic']:>10}{r['searched']:>15}"
          f"{eff:>21}   {note}")
    out.append({**r, "searched_effective": eff, "shield_clipped": clipped,
                "differs_effective": eff != r["heuristic"]})

with open(RES / "e7_policy_table_effective.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

n_clip = sum(r["shield_clipped"] for r in out)
n_diff = sum(r["differs_effective"] for r in out)
print(f"\nshield intervened in {n_clip}/{len(out)} states; effective policy "
      f"differs from the heuristic in {n_diff}/{len(out)} states.")
print("-> results/e7_policy_table_effective.csv")
