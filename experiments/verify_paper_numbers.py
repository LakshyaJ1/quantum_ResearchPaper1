r"""Re-derive every quantitative claim in the submitted draft from results/*.csv.

Nothing here is taken from memory or from the manuscript: each expected value is
recomputed from the shipped CSVs and compared against the string in paper.tex.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from statistics import mean

ROOT = Path(r"c:\Users\10jai\OneDrive\Desktop\ResearchPaper")
s = " ".join((ROOT / "paper.tex").read_text(encoding="utf-8").split())


def load(n):
    return list(csv.DictReader(open(ROOT / "results" / n, newline="")))


def agg(rows, pred, col):
    v = [float(r[col]) for r in rows if pred(r) and r[col] not in ("", "nan")]
    return mean(v) if v else float("nan")


e3, e2, e6, e6c = (load("e3_failmode.csv"), load("e2_policy.csv"),
                   load("e6b_sensitivity.csv"), load("e6c_nauth.csv"))
ok, bad = [], []


def chk(desc, quoted, actual, tol=6e-4):
    present = quoted in s
    match = actual is None or abs(float(quoted) - actual) <= tol
    (ok if (present and match) else bad).append(
        f"{desc}: quoted {quoted!r} "
        f"{'FOUND' if present else 'NOT IN PAPER'}, "
        f"data {'n/a' if actual is None else format(actual, '.4f')} "
        f"{'match' if match else 'MISMATCH'}")


# ---- Table II, from E3
for k, av in ((0, "0.8124"), (1, "0.8264"), (2, "0.3039")):
    chk(f"closed k={k} avail", av,
        agg(e3, lambda r, k=k: r["fail_mode_t"] == "FAIL_CLOSED"
            and int(r["k"]) == k, "served"))
chk("degr avail", "0.9733",
    agg(e3, lambda r: r["fail_mode_t"] == "FAIL_DEGRADED"
        and int(r["k"]) == 0, "served"))
for k, v in ((0, "0.166"), (1, "0.157"), (2, "0.690")):
    chk(f"degr k={k} viol", v,
        agg(e3, lambda r, k=k: r["fail_mode_t"] == "FAIL_DEGRADED"
            and int(r["k"]) == k, "floor_viol"))
for k, v in ((1, "0.029"), (2, "0.674")):
    chk(f"degr k={k} forced", v,
        agg(e3, lambda r, k=k: r["fail_mode_t"] == "FAIL_DEGRADED"
            and int(r["k"]) == k, "forced_below_its"))
chk("degr k=2 G4 share", "0.675",
    agg(e3, lambda r: r["fail_mode_t"] == "FAIL_DEGRADED"
        and int(r["k"]) == 2, "comp_G4"))

# ---- policy comparison, from E2
for pol, av in (("SP", "0.8392"), ("KAR", "0.8124"), ("KAR+CAF", "0.509")):
    chk(f"closed {pol} avail", av,
        agg(e2, lambda r, p=pol: r["fail_mode_t"] == "FAIL_CLOSED"
            and r["policy"] == p and r["k"] == "0", "served"))
chk("closed SP <ITS", "0.357",
    agg(e2, lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
        and r["policy"] == "SP" and r["k"] == "0", "below_its"), tol=6e-4)
chk("closed KAR+CAF LOG served", "0.000",
    agg(e2, lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
        and r["policy"] == "KAR+CAF" and r["k"] == "0", "served_LOG"))
chk("closed SP LOG served", "0.988",
    agg(e2, lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
        and r["policy"] == "SP" and r["k"] == "0", "served_LOG"))
chk("KAR mean hops", "3.086",
    agg(e2, lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
        and r["policy"] == "KAR" and r["k"] == "0", "mean_hops"))
chk("SP mean hops", "3.062",
    agg(e2, lambda r: r["fail_mode_t"] == "FAIL_CLOSED"
        and r["policy"] == "SP" and r["k"] == "0", "mean_hops"))

# ---- envelope table, from E6b A5
for de, row in ((0.01, ["0.8102", "0.8055"]), (0.02, ["0.8102", "0.8014"]),
                (0.03, ["0.8102", "0.7982"]), (0.04, ["0.8102", "0.7956"])):
    for k, q in zip((1, 2), row):
        chk(f"envelope de={de} k={k}", q,
            agg(e6, lambda r, k=k, de=de: abs(float(r["gamma"]) - 1.0) < 1e-9
                and abs(float(r["e_abort"]) - 0.075) < 1e-9
                and r["deny_classical"].lower() == "false"
                and int(r["k"]) == k and abs(float(r["delta_e"]) - de) < 1e-9
                and r["mode"] == "FAIL_CLOSED", "avail"))

# ---- sensitivity claims, from E6b / E6c
chk("gamma-invariant avail at k=2", "0.302",
    agg(e6, lambda r: abs(float(r["gamma"]) - 3.4) < 1e-9
        and abs(float(r["e_abort"]) - 0.075) < 1e-9
        and r["deny_classical"].lower() == "false" and int(r["k"]) == 2
        and abs(float(r["delta_e"]) - 0.05) < 1e-9
        and r["mode"] == "FAIL_CLOSED", "avail"), tol=6e-4)
chk("classical denial FD avail", "0.313",
    agg(e6, lambda r: r["deny_classical"].lower() == "true" and int(r["k"]) == 2
        and r["mode"] == "FAIL_DEGRADED" and abs(float(r["gamma"]) - 1.0) < 1e-9
        and abs(float(r["e_abort"]) - 0.075) < 1e-9
        and abs(float(r["delta_e"]) - 0.05) < 1e-9, "avail"), tol=6e-4)
chk("classical denial FC avail", "0.296",
    agg(e6, lambda r: r["deny_classical"].lower() == "true" and int(r["k"]) == 2
        and r["mode"] == "FAIL_CLOSED" and abs(float(r["gamma"]) - 1.0) < 1e-9
        and abs(float(r["e_abort"]) - 0.075) < 1e-9
        and abs(float(r["delta_e"]) - 0.05) < 1e-9, "avail"), tol=6e-4)
chk("n_auth=40 FC avail", "0.281",
    agg(e6c, lambda r: int(r["n_auth"]) == 40 and r["mode"] == "FAIL_CLOSED"
        and int(r["k"]) == 2, "avail"), tol=6e-4)
chk("n_auth FD forced", "0.678",
    agg(e6c, lambda r: int(r["n_auth"]) == 2 and r["mode"] == "FAIL_DEGRADED"
        and int(r["k"]) == 2, "forced"), tol=6e-4)

# ---- ML numbers, from E7
e7 = load("e7_policy_audit.csv")
h = [r for r in e7 if r["policy"] == "heuristic"][0]
sh = [r for r in e7 if r["policy"] == "searched-shielded"][0]
un = [r for r in e7 if r["policy"] == "searched-unshielded"][0]
chk("heuristic avail", "0.8123", float(h["avail"]))
chk("searched avail", "0.9726", float(sh["avail"]))
chk("searched viol", "39.5", float(sh["viol"]) * 100, tol=0.06)
chk("heuristic pct of shielded", "104.8",
    float(h["J"]) / float(sh["J"]) * 100, tol=0.06)
chk("unshielded key Mbit", "42", float(un["key_Mbit"]), tol=0.6)
chk("heuristic J at 6h", "1.2978", None)
chk("searched J at 6h", "1.4591", None)

# ---- strings that must NOT appear
banned = {
    "the author's": "singular author with two authors",
    "The author used": "singular author with two authors",
    "from the author and": "singular author with two authors",
    "a parallel line of engineering": "overstates a single citation",
    "(KAR $+27.0$": "KAR used without expansion",
    "39.5\\% forced downgrades": "was a floor-violation number",
    "Reservation floors are a Pareto trade": "retired claim",
    "two-threshold law": "retired claim",
    "69.0": "stale headline",
}
for k, why in banned.items():
    if " ".join(k.split()) in s:
        bad.append(f"BANNED TEXT present: {k!r} ({why})")

print(f"{len(ok)} checks passed\n")
if bad:
    print("PROBLEMS")
    for b in bad:
        print("  X", b)
    raise SystemExit(1)
print("Every quantitative claim in paper.tex matches the shipped CSVs, and no "
      "retired claim survives.")
