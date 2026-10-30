r"""Figure 1, camera-ready: the formation with its minimum cut, and the three
failure surfaces drawn as separate rows.

Reviewer comment addressed: "Fig. 1(b) is overloaded. Separate the two attack
surfaces." Panel (b) is no longer a control-loop flowchart. It is a three-row
schematic, one row per surface, read left to right as surface -> what stops ->
what still works (System Model: the surfaces are modelled separately).

Panel (a) is built from the simulator, not retyped: links from
qkdsim.network.formation_8node, rates from qkdsim.config.LINK_CLASSES, and the
highlighted cut from revision.scenarios.attack_order(method='weighted_cut')
with the Case default fibre attack cost. The historical figure
(make_fig_architecture.py, left untouched) marked REL1-BDE1 and BDE1-BDE2,
which is not the minimum rear-to-posts cut; the assertion below pins the
correct one so a topology change cannot silently redraw a stale figure.

Notation and spelling follow the camera-ready paper (QBER e, e_0, e_abort,
Delta e; "fibre", "modelled", "pre-placed"). One IEEE column wide, exact size (no
tight bbox), Times, >= 7 pt body text, Okabe-Ito colours with redundant
line-style and marker encoding so the figure survives greyscale printing.

Output: figures/camera_ready/fig1_architecture.pdf and .png (300 dpi).
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import dataclasses
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qkdsim.config import LINK_CLASSES, ReservoirConfig  # noqa: E402
from qkdsim.network import formation_8node  # noqa: E402
from revision.scenarios import Case, attack_order  # noqa: E402

OUT = ROOT / "figures" / "camera_ready"
STEM = "fig1_architecture"

W, H = 3.45, 2.22                 # inches; IEEE single column
FS, FS_TITLE = 7.0, 8.0           # points at final size

# Okabe-Ito (colour-blind safe); identity is also carried by line style.
BLUE, VERM, GREEN = "#0072B2", "#D55E00", "#009E73"
INK, INK2, RULE = "#000000", "#444444", "#b3b3b3"
FILL = {"rear": "#d5e5f3", "relay": "#ffffff", "brigade": "#ffffff",
        "forward": "#e9e9e9"}
SURFACE_FILL = "#fbe8dc"

EXPECTED_CUT = {("BDE1", "REL1"), ("BDE2", "REL2")}


def serif_font() -> str:
    have = {f.name for f in fontManager.ttflist}
    for name in ("Times New Roman", "STIXGeneral", "DejaVu Serif"):
        if name in have:
            return name
    return "serif"


mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": [serif_font(), "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": FS,
    "text.color": INK,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 300,
    "lines.solid_capstyle": "butt",
    "lines.dash_capstyle": "butt",
})


# --------------------------------------------------------------------------
# ground truth from the simulator
# --------------------------------------------------------------------------
def formation_facts():
    topo = formation_8node(ReservoirConfig())
    edges = {}
    for key, link in topo.links.items():
        rate = LINK_CLASSES[link.link_class].rate_bps
        assert rate == link.nominal_rate_bps, key
        edges[tuple(sorted(key))] = (link.link_class, rate)
    fibre_cost = next(f.default for f in dataclasses.fields(Case)
                      if f.name == "fibre_attack_cost")
    _, costs, cut = attack_order(topo, "weighted_cut", fibre_cost)
    cut = {tuple(sorted(k)) for k in cut}
    cost = sum(costs[k] for k in costs if tuple(sorted(k)) in cut)
    assert len(edges) == 9 and len(topo.node_roles) == 8
    assert cut == EXPECTED_CUT, f"minimum cut changed: {sorted(cut)}"
    assert cost == 2.0, cost
    return topo.node_roles, edges, cut, cost


def rate_label(bps: float) -> str:
    return f"{bps / 1000:g} kb/s" if bps >= 1000 else f"{bps:g} b/s"


# --------------------------------------------------------------------------
# panel (a): formation
# --------------------------------------------------------------------------
YT, YM, YB = 1.885, 1.595, 1.305   # top / middle / bottom node rows
POS = {
    "BASE": (0.235, YM),
    "REL1": (1.045, YT), "REL2": (1.045, YB),
    "BDE1": (2.085, YT), "BDE2": (2.085, YB),
    "FWD1": (3.195, YT), "FWD2": (3.195, YM), "FWD3": (3.195, YB),
}
NODE_W, NODE_H = 0.40, 0.155

# label anchor relative to the edge midpoint: (dx, dy, ha, va), inches
LABEL_AT = {
    ("BASE", "REL1"): (-0.030, 0.045, "right", "bottom"),
    ("BASE", "REL2"): (-0.030, -0.045, "right", "top"),
    ("REL1", "REL2"): (0.035, 0.0, "left", "center"),
    ("BDE1", "REL1"): (0.0, 0.058, "center", "bottom"),
    ("BDE2", "REL2"): (0.0, -0.058, "center", "top"),
    ("BDE1", "BDE2"): (-0.035, 0.0, "right", "center"),
    ("BDE1", "FWD1"): (0.0, 0.030, "center", "bottom"),
    ("BDE1", "FWD2"): (0.040, -0.105, "center", "top"),
    ("BDE2", "FWD3"): (0.0, -0.030, "center", "top"),
}


def edge_style(cls: str, cut: bool):
    if cut:
        return dict(color=VERM, lw=2.1, ls=(0, (2.4, 1.2)))
    if cls == "FIBRE":
        return dict(color=BLUE, lw=2.3, ls="-")
    return dict(color=INK2, lw=0.95, ls=(0, (4.0, 2.2)))


def draw_formation(ax, roles, edges, cut, cost):
    ax.text(0.02, H - 0.015, "(a) Formation and its two-edge cut",
            fontsize=FS_TITLE, ha="left", va="top")

    for (u, v), (cls, rate) in edges.items():
        (x1, y1), (x2, y2) = POS[u], POS[v]
        is_cut = (u, v) in cut
        ax.plot([x1, x2], [y1, y2], zorder=1, **edge_style(cls, is_cut))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if is_cut:
            ax.plot([mx], [my], marker="o", ms=7.2, mfc="white", mec="white",
                    zorder=3)
            ax.plot([mx], [my], marker="x", ms=5.6, mew=1.7, color=VERM,
                    zorder=4)
        dx, dy, ha, va = LABEL_AT[(u, v)]
        ax.text(mx + dx, my + dy, rate_label(rate), fontsize=FS, color=INK,
                ha=ha, va=va, zorder=5)

    for name, (x, y) in POS.items():
        ax.add_patch(FancyBboxPatch(
            (x - NODE_W / 2, y - NODE_H / 2), NODE_W, NODE_H,
            boxstyle="round,pad=0,rounding_size=0.035",
            fc=FILL[roles[name]], ec=INK2, lw=0.7, zorder=6))
        ax.text(x, y, name, fontsize=FS, ha="center", va="center_baseline",
                zorder=7)

    handles = [
        Line2D([], [], **edge_style("FIBRE", False)),
        Line2D([], [], **edge_style("FSO", False)),
        (Line2D([], [], **edge_style("FSO", True)),       # overlaid, as drawn
         Line2D([], [], ls="none", marker="o", ms=7.2, mfc="white",
                mec="white"),
         Line2D([], [], ls="none", marker="x", ms=5.6, mew=1.7, color=VERM)),
    ]
    labels = ["fibre", "free-space",
              f"minimum cut (cost {cost:g})"]
    ax.legend(handles, labels, loc="center", ncol=3, frameon=False,
              bbox_to_anchor=(W / 2, 1.025), bbox_transform=ax.transData,
              fontsize=FS, handlelength=2.6, handletextpad=0.5,
              columnspacing=1.5, borderpad=0.0, borderaxespad=0.0)


# --------------------------------------------------------------------------
# panel (b): failure surfaces
# --------------------------------------------------------------------------
ROWS = [
    dict(surface=("Quantum channel",
                  r"QBER $e_0{+}\Delta e \geq e_{\mathrm{abort}}$"),
         stops=("Fresh key generation", "ABORT"), tag=True,
         works=("Stored key above reserve;", "classical relay and fallback")),
    dict(surface=("Classical transport", "denial"),
         stops=("Relay and fallback", "OUTAGE"), tag=True,
         works=("Stored key retained", "for later use")),
    dict(surface=("Online key-", "establishment denial"),
         stops=("KEM fallback setup", "(G3/G4)"), tag=False,
         works=("QKD-keyed G1/G2;", "pre-placed symmetric keys")),
]
GRADES = "Grades:  G1 OTP > G2 QKD-keyed > G3 hybrid > G4 PQC-only"

B_TITLE = 0.955
Y_HEAD = 0.785
ROW_Y = (0.612, 0.367, 0.122)
ROW_H = 0.212
X_BOX0, X_BOX1 = 0.03, 1.035
X_STOP, X_WORK = 1.195, 2.225
LINE_DY = 0.047                 # half the gap between the two text lines


def cross_icon(ax, x, y, s=0.030):
    ax.plot([x - s, x + s], [y - s, y + s], color=VERM, lw=1.3,
            solid_capstyle="round")
    ax.plot([x - s, x + s], [y + s, y - s], color=VERM, lw=1.3,
            solid_capstyle="round")


def check_icon(ax, x, y, s=0.030):
    ax.plot([x - s, x - 0.25 * s, x + 1.05 * s],
            [y + 0.05 * s, y - 0.85 * s, y + 1.0 * s], color=GREEN, lw=1.3,
            solid_capstyle="round", solid_joinstyle="round")


def two_lines(ax, x, y, lines, ha="left", styles=({}, {})):
    for text, dy, st in zip(lines, (LINE_DY, -LINE_DY), styles):
        ax.text(x, y + dy, text, fontsize=FS, ha=ha, va="center_baseline",
                **st)


def draw_surfaces(ax):
    ax.text(0.02, B_TITLE, "(b) Three failure surfaces, modelled separately",
            fontsize=FS_TITLE, ha="left", va="top")

    head = dict(fontsize=FS, va="center_baseline", fontstyle="italic",
                color=INK2)
    ax.text((X_BOX0 + X_BOX1) / 2, Y_HEAD, "Failure surface", ha="center",
            **head)
    cross_icon(ax, X_STOP + 0.028, Y_HEAD + 0.022)
    ax.text(X_STOP + 0.085, Y_HEAD, "Stops", ha="left", **head)
    check_icon(ax, X_WORK + 0.028, Y_HEAD + 0.022)
    ax.text(X_WORK + 0.085, Y_HEAD, "Still works", ha="left", **head)

    for row, y in zip(ROWS, ROW_Y):
        ax.add_patch(FancyBboxPatch(
            (X_BOX0, y - ROW_H / 2), X_BOX1 - X_BOX0, ROW_H,
            boxstyle="round,pad=0,rounding_size=0.04",
            fc=SURFACE_FILL, ec=VERM, lw=0.8, zorder=2))
        two_lines(ax, (X_BOX0 + X_BOX1) / 2, y, row["surface"], ha="center")
        ax.add_patch(FancyArrowPatch(
            (X_BOX1 + 0.02, y), (X_STOP - 0.035, y), arrowstyle="-|>",
            mutation_scale=7, color=INK2, lw=0.8, shrinkA=0, shrinkB=0))
        tag = dict(color=VERM, fontweight="bold") if row["tag"] else {}
        two_lines(ax, X_STOP, y, row["stops"], styles=({}, tag))
        two_lines(ax, X_WORK, y, row["works"])

    # hairlines separate the text columns without boxing every cell
    top, bot = ROW_Y[0] + ROW_H / 2, ROW_Y[-1] - ROW_H / 2
    ax.plot([X_WORK - 0.06] * 2, [bot, top], color=RULE, lw=0.5)
    for ya, yb in zip(ROW_Y, ROW_Y[1:]):
        ym = (ya + yb) / 2
        ax.plot([X_BOX1 + 0.02, W - 0.02], [ym, ym], color=RULE, lw=0.5)

    # The grade order is defined in the text; the panel stays uncluttered.


def main() -> int:
    roles, edges, cut, cost = formation_facts()
    print("minimum rear-to-posts cut:", sorted(cut), "cost", cost)

    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    draw_formation(ax, roles, edges, cut, cost)
    draw_surfaces(ax)

    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{STEM}.{ext}")
    plt.close(fig)
    print(f"-> {OUT.relative_to(ROOT)}/{STEM}.pdf/.png  ({W} x {H} in)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
