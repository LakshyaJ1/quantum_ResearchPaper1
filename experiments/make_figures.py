"""Publication figures. Vector PDF + PNG, IEEE two-column, greyscale-legible.

DESIGN CONTRACT (from the dataviz method):
  * Categorical hues assigned in FIXED order, never cycled. Palette validated:
    node scripts/validate_palette.js "#2a78d6,#eb6834,#1baf7a,#eda100" --mode light
    -> all checks PASS (worst adjacent CVD dE 9.1 protan, normal-vision 22.9).
    One contrast WARN (aqua/yellow below 3:1 on the surface) which obligates
    visible labels -- satisfied by the always-present legend and direct labels.
  * SECONDARY ENCODING IS MANDATORY, not decorative: every series carries a
    distinct linestyle AND marker, so identity survives greyscale print and
    colour-vision deficiency. Colour alone never distinguishes a series.
  * Never a dual y-axis. Two measures of different scale -> two panels.
  * Recessive grid and axes; text in ink tokens, never in the series colour.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RES = ROOT / "results"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True)

# validated categorical palette, fixed order
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d8d7d2"
# secondary encoding, index-matched to C
LS = ["-", "--", "-.", ":"]
MK = ["o", "s", "^", "D"]

COL_W, COL_H = 3.45, 2.35          # single IEEE column
WIDE_W, WIDE_H = 7.10, 2.55        # full two-column width

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5,
    "legend.fontsize": 7, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.edgecolor": INK2, "axes.linewidth": 0.6,
    "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.grid": True, "axes.grid.axis": "y",
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "figure.dpi": 200,
    "lines.linewidth": 1.5, "lines.markersize": 4.0,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{name}.{ext}")
    plt.close(fig)
    print(f"  -> figures/{name}.pdf/.png")


def have(name: str) -> bool:
    ok = (RES / name).exists()
    if not ok:
        print(f"  [skip] results/{name} not found")
    return ok


# ---------------------------------------------------------------- fig 1
def fig_failmode() -> None:
    """THE headline: the same attack budget buys either denial or downgrade."""
    if not have("e3_failmode.csv"):
        return
    d = pd.read_csv(RES / "e3_failmode.csv")
    g = d.groupby(["fail_mode_t", "k"]).agg(
        avail=("served", "mean"), avail_sd=("served", "std"),
        forced=("forced_below_its", "mean"),
        forced_sd=("forced_below_its", "std"),
        viol=("floor_viol", "mean"),
        below=("below_its", "mean")).reset_index()

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(WIDE_W, WIDE_H))
    for i, mode in enumerate(["FAIL_CLOSED", "FAIL_DEGRADED"]):
        s = g[g.fail_mode_t == mode].sort_values("k")
        lbl = "fail-closed" if mode == "FAIL_CLOSED" else "fail-degraded"
        a1.errorbar(s.k, s.avail, yerr=s.avail_sd, color=C[i], ls=LS[i],
                    marker=MK[i], capsize=2, label=lbl)
        a2.errorbar(s.k, s.forced, yerr=s.forced_sd, color=C[i], ls=LS[i],
                    marker=MK[i], capsize=2, label=lbl)
    a1.set_xlabel("adversary budget $k$ (links suppressed)")
    a1.set_ylabel("session availability")
    a1.set_title("(a) availability", loc="left", color=INK)
    a1.set_ylim(-0.03, 1.05)
    a2.set_xlabel("adversary budget $k$ (links suppressed)")
    a2.set_ylabel("forced assurance loss (entitled traffic)")
    a2.set_title("(b) forced assurance loss", loc="left", color=INK)
    a2.set_ylim(-0.03, 1.05)
    # Both curves start at zero and that is the point: with no adversary every
    # entitled session gets an ITS-delivered key, so there is no baseline to
    # subtract. Fail-closed stays at zero because it refuses rather than
    # degrades, so it cannot lose assurance by construction.
    a2.annotate("zero at $k=0$: no baseline loss\nfail-closed refuses instead",
                (1.5, 0.02), fontsize=6.5, color=INK2, va="bottom")
    a1.legend(loc="lower left")
    a2.legend(loc="upper left")
    save(fig, "fig1_failmode")


# ---------------------------------------------------------------- fig 2
def fig_composition() -> None:
    """Grade composition of SERVED traffic -- the operator-facing indicator that
    current QKD resilience standards have no vocabulary for."""
    if not have("e3_failmode.csv"):
        return
    d = pd.read_csv(RES / "e3_failmode.csv")
    d = d[d.fail_mode_t == "FAIL_DEGRADED"]
    g = d.groupby("k")[["comp_G1", "comp_G2", "comp_G3", "comp_G4"]].mean()
    g = g.dropna()
    fig, ax = plt.subplots(figsize=(COL_W, COL_H))
    names = ["G1 OTP (ITS)", "G2 QKD-keyed", "G3 hybrid", "G4 PQC only"]
    bottom = np.zeros(len(g))
    hatch = ["", "///", "...", "xxx"]   # greyscale/forced-colors fallback
    for i, (col, nm) in enumerate(zip(g.columns, names)):
        ax.bar(g.index, g[col], bottom=bottom, color=C[i], width=0.72,
               label=nm, edgecolor="white", linewidth=0.7, hatch=hatch[i])
        bottom += g[col].values
    ax.set_xlabel("adversary budget $k$")
    ax.set_ylabel("share of served sessions")
    ax.set_ylim(0, 1.0)
    ax.set_axisbelow(True)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    save(fig, "fig2_grade_composition")


# ---------------------------------------------------------------- fig 3
def fig_forcing_cost() -> None:
    """Downgrade-forcing cost vs chain depth, for both adversary models. The gap
    between them is the finding: a greedy adversary looks far more expensive
    than an optimal one, so quoting only the greedy figure overstates
    resilience."""
    if not have("e4_kstar.csv"):
        return
    k = pd.read_csv(RES / "e4_kstar.csv")
    col = next((c for c in k.columns if c.startswith("kstar_0.5")), None)
    if col is None or "targeting" not in k.columns:
        print("  [skip] fig3 needs the two-adversary E4 rerun")
        return
    fig, ax = plt.subplots(figsize=(COL_W, COL_H))
    for i, tgt in enumerate(["betweenness", "mincut"]):
        s = k[k.targeting == tgt].sort_values("depth")
        y = pd.to_numeric(s[col], errors="coerce")
        ax.plot(s.depth, y, color=C[i], ls=LS[i], marker=MK[i],
                label=f"{tgt} adversary")
    ax.set_xlabel("relay-chain depth $d$ (hops)")
    ax.set_ylabel(r"$k^*(\phi{=}0.5)$  links to suppress")
    ax.legend(loc="upper left")
    save(fig, "fig3_forcing_cost")


# ---------------------------------------------------------------- fig 4
def fig_policy() -> None:
    """Availability against key expenditure. Key-aware routing spends MORE key
    for LESS availability -- the hop multiplier converts longer paths directly
    into key, so per-session time-to-key optimisation is globally
    counterproductive here."""
    if not have("e2_policy.csv"):
        return
    d = pd.read_csv(RES / "e2_policy.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(WIDE_W, WIDE_H))
    for ax, mode, ttl in ((a1, "FAIL_CLOSED", "(a) fail-closed"),
                          (a2, "FAIL_DEGRADED", "(b) fail-degraded")):
        s = d[(d.fail_mode_t == mode) & (d.k == 0)]
        for i, p in enumerate(["SP", "KAR", "KAR+CAF"]):
            g = s[s.policy == p]
            ax.errorbar(g.consumed_Mbit.mean(), g.served.mean(),
                        yerr=g.served.std(), xerr=g.consumed_Mbit.std(),
                        color=C[i], marker=MK[i], ms=6, capsize=2, label=p,
                        ls="none")
            ax.annotate(p, (g.consumed_Mbit.mean(), g.served.mean()),
                        textcoords="offset points", xytext=(6, 4),
                        fontsize=7, color=INK2)
        ax.set_xlabel("key consumed (Mbit / 12 h)")
        ax.set_title(ttl, loc="left", color=INK)
    a1.set_ylabel("session availability")
    a1.legend(loc="lower left")
    save(fig, "fig4_policy_pareto")


# ---------------------------------------------------------------- fig 5
def fig_auth() -> None:
    """Relay authentication overhead vs block size. Wegman-Carter cost is per
    message and only logarithmic in message length, so the literature's bare
    D*n law is adequate for large OTP blocks and wrong by ~3x for the modal
    256-bit rekey."""
    if not have("e5_overhead_vs_blocksize.csv"):
        return
    d = pd.read_csv(RES / "e5_overhead_vs_blocksize.csv")
    fig, ax = plt.subplots(figsize=(COL_W, COL_H))
    ax.semilogx(d.D_bits, d.overhead_factor, color=C[0], ls=LS[0],
                marker=MK[0], label="cost / naive $D$")
    ax.axhline(1.0, color=INK2, lw=0.7, ls=(0, (2, 2)))
    ax.annotate("bare $D{\\cdot}n$ law", (d.D_bits.iloc[-1], 1.0),
                textcoords="offset points", xytext=(-52, 5), fontsize=6.5,
                color=INK2)
    for x, lab in ((256, "256 b rekey\n(modal)"), (144_000, "OTP voice\nsession")):
        if (d.D_bits == x).any():
            y = float(d.loc[d.D_bits == x, "overhead_factor"].iloc[0])
            ax.annotate(lab, (x, y), textcoords="offset points",
                        xytext=(7, -2), fontsize=6.5, color=INK2)
    ax.set_xlabel("relay block size $D$ (bit)")
    ax.set_ylabel("key cost per hop / $D$")
    ax.set_ylim(0.9, 3.2)
    ax.legend(loc="upper right")
    save(fig, "fig5_auth_overhead")


# ---------------------------------------------------------------- fig 6
def fig_audit() -> None:
    """Policy-space audit, evaluated out-of-distribution rather than nominally."""
    if not have("e7_policy_audit.csv"):
        return
    d = pd.read_csv(RES / "e7_policy_audit.csv")
    keep = ["heuristic", "searched-shielded"]
    d = d[d.policy.isin(keep)]
    conds = list(dict.fromkeys(d.condition))
    x = np.arange(len(conds))
    w = 0.36
    fig, ax = plt.subplots(figsize=(WIDE_W, WIDE_H))
    for i, p in enumerate(keep):
        s = d[d.policy == p].set_index("condition").reindex(conds)
        ax.bar(x + (i - 0.5) * w, s["J"], width=w * 0.92, color=C[i],
               label=p, edgecolor="white", linewidth=0.6,
               hatch=["", "///"][i])
    ax.set_xticks(x)
    ax.set_xticklabels(conds, rotation=28, ha="right", fontsize=6.8)
    ax.set_ylabel("objective $J$")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", ncol=2)
    save(fig, "fig6_policy_audit")


# ---------------------------------------------------------------- fig 7
def fig_two_threshold() -> None:
    """The two-threshold law, which currently exists only as a table.

    Each curve should fall at its OWN predicted threshold, delta_e = e_abort - e0.
    Drawing the predicted thresholds as reference lines turns the claim into
    something the reader verifies by eye rather than takes on trust -- the curve
    and the line coincide, or the claim is wrong.

    Small multiples rather than a heatmap: two series over one axis stays legible
    in greyscale with linestyle+marker encoding, whereas a colour-mapped surface
    does not survive print without a second channel.
    """
    if not have("e6b_sensitivity.csv"):
        return
    d = pd.read_csv(RES / "e6b_sensitivity.csv")
    d = d[(~d.deny_classical) & (d.gamma == 1.0) & (d.k == 2)]
    if d.empty:
        print("  [skip] fig7 needs the delta_e sweep")
        return
    E0 = 0.03
    # Each panel reports ONE fail mode. Averaging across modes silently mixes
    # fail-closed availability (~0.80) with fail-degraded (~0.97) and produces a
    # plausible but wrong curve -- the shape survives, the values do not.
    fc = d[d["mode"] == "FAIL_CLOSED"]
    fd = d[d["mode"] == "FAIL_DEGRADED"]

    # Single-column variant for the 6-page submission: fail-closed availability
    # only. Both modes turn at the same threshold, so one panel carries the law
    # and the other is a sentence of prose.
    figc, axc = plt.subplots(figsize=(COL_W, COL_H))
    for i, ea in enumerate(sorted(d.e_abort.unique())):
        sa = (fc[fc.e_abort == ea].groupby("delta_e")["avail"].mean()
              .reset_index().sort_values("delta_e"))
        axc.plot(sa.delta_e, sa["avail"], color=C[i], ls=LS[i], marker=MK[i],
                 label=rf"$e_{{\rm abort}}={ea:g}$")
        axc.axvline(ea - E0, color=C[i], lw=0.8, ls=(0, (1, 2)), alpha=0.9)
        axc.annotate(rf"$\Delta e={ea - E0:.3f}$", (ea - E0, 0.05),
                     textcoords="offset points", xytext=(3, 0), rotation=90,
                     fontsize=6, color=C[i], va="bottom")
    axc.set_xlabel(r"per-link QBER injection $\Delta e$")
    axc.set_ylabel("availability (fail-closed)")
    axc.set_ylim(-0.03, 1.02)
    axc.legend(loc="lower left")
    save(figc, "fig7c_two_threshold_col")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(WIDE_W, WIDE_H))
    for i, ea in enumerate(sorted(d.e_abort.unique())):
        sa = (fc[fc.e_abort == ea].groupby("delta_e")["avail"].mean()
              .reset_index().sort_values("delta_e"))
        sf = (fd[fd.e_abort == ea].groupby("delta_e")["forced"].mean()
              .reset_index().sort_values("delta_e"))
        lbl = rf"$e_{{\rm abort}}={ea:g}$"
        a1.plot(sa.delta_e, sa["avail"], color=C[i], ls=LS[i], marker=MK[i],
                label=lbl)
        a2.plot(sf.delta_e, sf["forced"], color=C[i], ls=LS[i], marker=MK[i],
                label=lbl)
        thr = ea - E0
        for ax in (a1, a2):
            ax.axvline(thr, color=C[i], lw=0.8, ls=(0, (1, 2)), alpha=0.9)
        a1.annotate(rf"$\Delta e = {thr:.3f}$", (thr, 0.06),
                    textcoords="offset points", xytext=(3, 0), rotation=90,
                    fontsize=6, color=C[i], va="bottom")
    a1.set_xlabel(r"per-link QBER injection $\Delta e$")
    a1.set_ylabel("session availability (fail-closed)")
    a1.set_title("(a) fail-closed availability", loc="left", color=INK)
    a1.set_ylim(-0.03, 1.02)
    a2.set_xlabel(r"per-link QBER injection $\Delta e$")
    a2.set_ylabel("forced below authorised grade")
    a2.set_title("(b) fail-degraded assurance loss", loc="left", color=INK)
    a2.set_ylim(-0.03, 1.02)
    a1.legend(loc="lower left")
    a2.legend(loc="upper left")
    a2.annotate("dotted lines: predicted\nthreshold "
                r"$\Delta e = e_{\rm abort}-e_0$",
                (0.055, 0.44), fontsize=6, color=INK2)
    save(fig, "fig7_two_threshold")


# ---------------------------------------------------------------- fig 8
def fig_nauth() -> None:
    """Robustness of the headline to the authentication recalibration.

    E8 showed our n_auth = 2 is a lower bound; Cambridge's measured relay
    overhead implies ~7 and SECOQC's application tunnel ~40. Raising it tightens
    scarcity, so the headline has to be re-checked -- this figure is that check.
    """
    if not have("e6c_nauth.csv"):
        return
    d = pd.read_csv(RES / "e6c_nauth.csv")
    fc = (d[(d["mode"] == "FAIL_CLOSED")].groupby(["n_auth", "k"])["avail"]
          .mean().unstack())
    fd = (d[(d["mode"] == "FAIL_DEGRADED")].groupby(["n_auth", "k"])["forced"]
          .mean().unstack())
    x = np.arange(len(fc.index))
    w = 0.36
    fig, ax = plt.subplots(figsize=(COL_W, COL_H))
    ax.bar(x - w / 2, fc[0], width=w * 0.92, color=C[0], label="avail., $k=0$",
           edgecolor="white", linewidth=0.6)
    ax.bar(x + w / 2, fc[2], width=w * 0.92, color=C[1], label="avail., $k=2$",
           edgecolor="white", linewidth=0.6, hatch="///")
    ax.plot(x, fd[2], color=INK, ls=LS[2], marker=MK[2], ms=4.5,
            label="forced loss, $k=2$")
    ax.set_xticks(x)
    ax.set_xticklabels([str(int(n)) for n in fc.index])
    ax.set_xlabel(r"authenticated messages per key delivery $n_{\rm auth}$")
    ax.set_ylabel("fraction")
    ax.set_ylim(0, 1.02)
    ax.set_axisbelow(True)
    ax.legend(loc="center right", fontsize=6.2)
    save(fig, "fig8_nauth_robustness")


def main() -> int:
    print("building figures ...")
    fig_failmode()
    fig_composition()
    fig_forcing_cost()
    fig_policy()
    fig_auth()
    fig_audit()
    fig_two_threshold()
    fig_nauth()
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
