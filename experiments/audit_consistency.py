r"""Final consistency audit before submission.

Checks the eight properties the brief requires, plus the specific defects this
revision was meant to remove.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from statistics import mean

ROOT = Path(r"c:\Users\10jai\OneDrive\Desktop\ResearchPaper")
s = (ROOT / "paper.tex").read_text(encoding="utf-8")
s_flat = " ".join(s.split())
body = s.split(r"\begin{thebibliography}", 1)[0]
fail: list[str] = []
warn: list[str] = []

# ---- 1. obsolete statements from earlier drafts -------------------------
banned = {
    "two-threshold law": "reframed contribution must not reappear",
    "the general law, not the instance": "k* claim was demoted",
    "actionable in an unexpected direction": "overreaching phrase",
    "single disagreement": "validation count was one-fails",
    "69.0": "stale headline (now 67.4)",
    "69\\%": "stale headline (now 67.4)",
    "Neither position has been measured": "unbounded absence claim",
    "[[": "placeholder",
    "%%": "internal provenance note",
    "stops responding to the thing it measures": "overreaching phrase",
    "Key-aware routing is worse": "unscoped claim",
    "infeasible even unattacked": "premise was wrong",
    "39.5\\% forced downgrades": "was a floor-violation number",
    "Reservation floors are a Pareto trade": "CAF was not a trade",
    "even at maximum link budget": "budget was not swept",
    "a parallel line of security engineering": "one citation only",
}
for k, why in banned.items():
    if " ".join(k.split()) in s_flat:
        fail.append(f"obsolete text present: {k!r}  ({why})")

# ---- 2. numbers must match the current CSVs ----------------------------
def col(name, pred, key):
    rows = list(csv.DictReader(open(ROOT / "results" / name, newline="")))
    v = [float(r[key]) for r in rows if pred(r) and r[key] not in ("", "nan")]
    return mean(v) if v else float("nan")


e3 = "e3_failmode.csv"
checks = [
    ("0.8124", col(e3, lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
                   and r["k"] == "0", "served")),
    ("0.3039", col(e3, lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
                   and r["k"] == "2", "served")),
    ("0.9733", col(e3, lambda r: r["fail_mode_t"] == "FAIL_DEGRADED"
                   and r["k"] == "0", "served")),
    ("0.674",  col(e3, lambda r: r["fail_mode_t"] == "FAIL_DEGRADED"
                   and r["k"] == "2", "forced_below_its")),
    ("0.166",  col(e3, lambda r: r["fail_mode_t"] == "FAIL_DEGRADED"
                   and r["k"] == "0", "floor_viol")),
]
for quoted, actual in checks:
    if abs(float(quoted) - actual) > 5e-4:
        fail.append(f"quoted {quoted} but data gives {actual:.4f}")
    if quoted not in s:
        warn.append(f"value {quoted} verified in data but not found in paper")

e2 = "e2_policy.csv"
for quoted, pred, key in [
    ("0.8392", lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
     and r["policy"] == "SP" and r["k"] == "0", "served"),
    ("0.5092", lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
     and r["policy"] == "KAR+CAF" and r["k"] == "0", "served"),
    ("0.3569", lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
     and r["policy"] == "SP" and r["k"] == "0", "below_its"),
    ("0.3077", lambda r: r["fail_mode_t"] == "FAIL_DEGRADED"
     and r["policy"] == "SP" and r["k"] == "0", "below_its"),
]:
    a = col(e2, pred, key)
    if abs(float(quoted) - a) > 5e-4:
        fail.append(f"Table III quotes {quoted}, data gives {a:.4f} ({key})")

# 67.4% must appear and 0.674 must be the tabulated value
if "67.4" not in s:
    fail.append("headline 67.4% missing")

# ---- 2b. E6b A5: non-substitutability must be in the data ---------------
e6 = list(csv.DictReader(open(ROOT / "results" / "e6b_sensitivity.csv",
                              newline="")))


def a5(k, de, mode, col):
    v = [float(r[col]) for r in e6
         if abs(float(r["gamma"]) - 1.0) < 1e-9
         and abs(float(r["e_abort"]) - 0.075) < 1e-9
         and r["deny_classical"].lower() == "false"
         and int(r["k"]) == k and abs(float(r["delta_e"]) - de) < 1e-9
         and r["mode"] == mode]
    return mean(v) if v else float("nan")


spans = []
for de in (0.01, 0.02, 0.03, 0.04):
    cells = [a5(k, de, "FAIL_CLOSED", "avail") for k in (1, 2, 3, 4, 5)]
    if any(c != c for c in cells):
        fail.append(f"E6b A5 grid incomplete at delta_e={de}")
        continue
    spans.append(max(cells) - min(cells))
    worst = max(a5(k, de, "FAIL_DEGRADED", "forced") for k in (1, 2, 3, 4, 5))
    if worst > 0.001:
        fail.append(f"A5: forced loss {worst:.4f} at delta_e={de}, "
                    f"paper claims <0.0002")
if spans and max(spans) > 0.015 + 5e-4:
    fail.append(f"A5: availability span {max(spans):.4f} exceeds the 0.015 quoted")
if "at most 0.015" not in s_flat:
    fail.append("MISSING: sec V-D must quote the measured A5 span")

# ---- 2c. Table III LOG column must match E2 -----------------------------
e2r = list(csv.DictReader(open(ROOT / "results" / "e2_policy.csv", newline="")))
for pol, quoted in (("SP", 0.9881), ("KAR", 0.9881), ("KAR+CAF", 0.0000)):
    v = mean(float(r["served_LOG"]) for r in e2r
             if r["fail_mode_t"] == "FAIL_CLOSED" and r["policy"] == pol
             and r["k"] == "0")
    if abs(v - quoted) > 5e-4:
        fail.append(f"Table III LOG for closed {pol}: quoted {quoted}, "
                    f"data {v:.4f}")

# ---- 3. every figure referenced, every table discussed -----------------
for env, kind in (("figure", "fig"), ("table", "tab")):
    for m in re.finditer(r"\\label\{(" + kind + r":[^}]*)\}", body):
        lab = m.group(1)
        if len(re.findall(r"\\ref\{" + re.escape(lab) + r"\}", body)) == 0:
            fail.append(f"{kind} label never referenced: {lab}")

figs = re.findall(r"includegraphics\[[^\]]*\]\{([^}]*)\}", s)
for f in figs:
    if not (ROOT / "figures" / f).exists():
        fail.append(f"missing figure file: {f}")

# ---- 4. citations ------------------------------------------------------
cited = set()
for m in re.finditer(r"\\cite\{([^}]*)\}", s):
    cited |= {k.strip() for k in m.group(1).split(",")}
items = set(re.findall(r"\\bibitem\{([^}]*)\}", s))
if cited - items:
    fail.append(f"cited without bibitem: {sorted(cited - items)}")
if items - cited:
    fail.append(f"bibitem never cited: {sorted(items - cited)}")

# ---- 5. required new content present -----------------------------------
required = {
    "A Simulation Study": "title discloses simulation",
    "IEEEauthorblockN": "author block filled",
    "the authors'": "author count consistent in back matter",
    "Lakshya Jain": "author 1 present",
    "Siddhi Arora": "author 2 present",
    "Divya Mishra": "author 3 present",
    "reproducing two and failing two": "abstract and intro disclose both failures",
    "Acknowledgements": "AI disclosure section",
    "large language model": "AI disclosure text",
    "do not substitute": "capability/budget non-substitutability",
    "an observation, not a": "k* demoted",
    "which adversary a study reports": "greedy-vs-mincut promoted",
    "no baseline artefact to subtract": "zero-baseline stated",
    "internal consistency rather than": "V1 relabelled",
    "order of magnitude": "V4 relabelled",
    "did not reimplement a published key-aware": "KAR claim rescoped",
    "cut-limited": "n_auth question answered",
    "studies are included if they": "Table I selection rule",
    "more consequential target": "novelty framing",
    "not locate a published buffer capacity": "absence claim softened",
    "No study measures either position": "abstract absence softened",
    "39.5\\% floor violations": "V-E metric conflation fixed",
    "best \\emph{shielded} searched": "V-E comparator named correctly",
    "One row is non-monotone": "k=1 mechanism explained",
    "inadvertent admission control": "k=1 mechanism explained",
    "admission decision, not a graded control": "CAF reframed",
    "no useful\nintermediate": "CAF non-tunability stated",
    "Scarcity here is per link": "aggregate-utilisation disclosure",
    "1.8\\% of aggregate capacity": "utilisation number stated",
    "optimistic end": "n_auth calibration stated",
    "one design stating that position": "single-citation framing softened",
}
for k, why in required.items():
    if " ".join(k.split()) not in s_flat:
        fail.append(f"MISSING required revision: {why} ({k!r})")

# ---- 6. internal contradictions ----------------------------------------
n_fail_words = len(re.findall(r"failing two|V2 and V3 both fail",
                              s))
if n_fail_words < 2:
    warn.append("validation-failure count stated fewer than twice")
if re.search(r"one of which it fails", s):
    fail.append("introduction still says one failure")

print("=" * 70)
print("FINAL CONSISTENCY AUDIT")
print("=" * 70)
print(f"figures: {len(figs)} referenced, all present")
print(f"citations: {len(cited)} cited, {len(items)} bibitems, exact match")
print(f"validation-failure count stated consistently: "
      f"{'yes' if not re.search('one of which it fails', s) else 'NO'}")
print()
if warn:
    print("WARNINGS")
    for w in warn:
        print("  ~", w)
    print()
if fail:
    print("FAILURES")
    for f_ in fail:
        print("  X", f_)
    raise SystemExit(1)
print("All audit checks pass.")
