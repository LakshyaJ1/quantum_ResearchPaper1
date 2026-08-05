r"""Figure 1 -- system architecture. Two panels, full text width.

(a) the nine-node formation, with link classes and the minimum edge cut marked.
    Marking the cut is the point: it shows at a glance WHY suppressing two links
    severs quantum key to two of three forward posts, which is the paper's
    headline number.

(b) the control loop, showing where each decision sits relative to the key
    economy and where the adversary's two attack surfaces enter. This panel does
    double duty: a systems reader sees the control plane, and a reader coming
    from machine learning sees the policy's action space and the shield's
    position in the loop.

Conventions match make_figures.py: validated 4-hue categorical palette,
secondary encoding by linestyle so identity survives greyscale, recessive text
in ink tokens. No \textsf or \succ -- matplotlib's mathtext does not implement
them and they render literally.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True)

C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2 = "#0b0b0b", "#52514e"

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 7.5, "text.color": INK,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "figure.dpi": 200,
})

POS = {
    "BASE": (0.00, 1.05), "REL1": (1.00, 1.70), "REL2": (1.00, 0.40),
    "BDE1": (2.05, 1.70), "BDE2": (2.05, 0.40),
    "FWD1": (3.10, 2.20), "FWD2": (3.10, 1.35), "FWD3": (3.10, 0.15),
}
EDGES = [
    ("BASE", "REL1", "FIBRE", "300 kb/s"),
    ("BASE", "REL2", "FSO_NOM", "240 b/s"),
    ("REL1", "REL2", "FSO_LAT", "200 b/s"),
    ("REL1", "BDE1", "FSO_NOM", "240 b/s"),
    ("REL2", "BDE2", "FSO_NOM", "240 b/s"),
    ("BDE1", "BDE2", "FSO_LAT", "200 b/s"),
    ("BDE1", "FWD1", "FSO_SHORT", "400 b/s"),
    ("BDE1", "FWD2", "FSO_NOM", "240 b/s"),
    ("BDE2", "FWD3", "FSO_SHORT", "400 b/s"),
]
STYLE = {"FIBRE": ("-", 2.0, C[0]), "FSO_NOM": ("--", 1.3, INK2),
         "FSO_SHORT": ("-.", 1.3, INK2), "FSO_LAT": (":", 1.3, INK2)}
CUT = {("BDE1", "BDE2"), ("REL1", "BDE1")}


def panel_topology(ax):
    for u, v, cls, rate in EDGES:
        (x1, y1), (x2, y2) = POS[u], POS[v]
        ls, lw, col = STYLE[cls]
        cut = (u, v) in CUT or (v, u) in CUT
        ax.plot([x1, x2], [y1, y2], ls=ls, lw=2.6 if cut else lw,
                color=C[1] if cut else col, zorder=1, solid_capstyle="round")
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if cut:
            ax.plot([mx], [my], marker="x", ms=7, mew=2.0, color=C[1], zorder=3)
        ax.text(mx, my + 0.10, rate, fontsize=5.8, color=INK2,
                ha="center", va="bottom", zorder=4)

    for n, (x, y) in POS.items():
        role = ("rear" if n == "BASE" else "fwd" if n.startswith("FWD")
                else "relay")
        fc = {"rear": "#dce8f8", "relay": "#ffffff", "fwd": "#f2f1ee"}[role]
        ax.add_patch(FancyBboxPatch((x - 0.26, y - 0.115), 0.52, 0.23,
                                    boxstyle="round,pad=0.015,rounding_size=0.05",
                                    fc=fc, ec=INK2, lw=0.8, zorder=2))
        ax.text(x, y, n, ha="center", va="center", fontsize=6.6, zorder=3)

    ax.plot([], [], color=C[0], lw=2.0, label="fibre backbone")
    ax.plot([], [], color=INK2, ls="--", lw=1.3, label="free-space optical")
    ax.plot([], [], color=C[1], lw=2.6, marker="x", ms=6,
            label=r"minimum edge cut ($k^*\!=\!2$)")
    ax.legend(loc="lower left", fontsize=5.9, frameon=False,
              handlelength=2.4, borderpad=0.1, labelspacing=0.28)
    ax.set_xlim(-0.48, 3.64); ax.set_ylim(-0.30, 2.60)
    ax.axis("off")
    ax.set_title("(a) formation, and the cut that severs it", loc="left",
                 fontsize=8, color=INK)


def box(ax, x, y, w, h, text, fc="#ffffff", ec=INK2, fs=6.3, lw=0.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.012,rounding_size=0.04",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, zorder=3, linespacing=1.4)


def arrow(ax, p, q, color=INK2, lw=1.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8,
                                 color=color, lw=lw, linestyle=ls,
                                 shrinkA=1, shrinkB=1, zorder=4))


def panel_control(ax):
    # top row: the control chain. Text kept short so nothing overruns a box.
    box(ax, 0.94, 1.56, 1.14, 0.54,
        "key economy\nper-link reservoirs\n"
        r"cost/hop $D{+}M_{\rm meta}{+}n_{\rm auth}t$",
        fc="#dce8f8", fs=5.1)
    box(ax, 2.20, 1.56, 0.78, 0.54, "controller\nroute, admit,\nselect grade",
        fs=6.0)
    box(ax, 3.08, 1.56, 0.70, 0.54, "shield\nC2 never\nbelow G2",
        fc="#f2f1ee", fs=6.0)
    # middle: what gets delivered
    box(ax, 1.06, 0.90, 2.72, 0.40,
        "assurance grade delivered\n"
        "G1 OTP  >  G2 QKD-keyed  >  G3 hybrid  >  G4 PQC", fs=5.5)
    # bottom: what we report
    box(ax, 1.06, 0.24, 2.72, 0.38,
        "reported:  availability  |  forced assurance loss  |  grade mix",
        fc="#eef3ea", fs=5.9)
    # left: the adversary, narrowed to clear the boxes to its right
    box(ax, 0.02, 0.88, 0.66, 0.46,
        "adversary\nbudget $k$\ninjection $\\Delta e$", fc="#fbe6dc", ec=C[1],
        fs=5.9)

    arrow(ax, (2.08, 1.83), (2.20, 1.83))
    arrow(ax, (2.98, 1.83), (3.08, 1.83))
    arrow(ax, (3.43, 1.56), (3.43, 1.30))
    arrow(ax, (2.42, 0.90), (2.42, 0.62))
    # consumption feeds back into the reservoirs
    arrow(ax, (1.34, 1.30), (1.34, 1.56), ls=(0, (3, 2)), lw=0.9)
    ax.text(1.40, 1.43, "key consumed", fontsize=5.4, color=INK2, va="center")

    # the two attack surfaces, each label anchored to its own arrow
    arrow(ax, (0.56, 1.34), (0.92, 1.58), color=C[1], lw=1.3)
    ax.text(0.28, 1.64, "quantum channel\n" r"$\Delta e \Rightarrow$ ABORT",
            fontsize=5.4, color=C[1], ha="center", va="bottom")
    arrow(ax, (0.68, 0.99), (1.04, 1.06), color=C[1], lw=1.3)
    ax.text(0.35, 0.84, "classical channel\n" r"denial $\Rightarrow$ OUTAGE",
            fontsize=5.4, color=C[1], ha="center", va="top")

    ax.set_xlim(-0.04, 3.84); ax.set_ylim(0.10, 2.24)
    ax.axis("off")
    ax.set_title("(b) control loop and the two attack surfaces", loc="left",
                 fontsize=8, color=INK)


def main() -> int:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.10, 2.68))
    panel_topology(a1)
    panel_control(a2)
    fig.subplots_adjust(wspace=0.05)
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"fig0_architecture.{ext}")
    plt.close(fig)
    print("-> figures/fig0_architecture.pdf/.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
