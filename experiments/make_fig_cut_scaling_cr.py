r"""Figure 2, camera-ready: service at the all-terminal minimum cut is set by
the pre-placed stock behind the cut, and forced assurance loss by the supply
left after one cut link is suppressed.

(a) x = predicted stock-limited fraction k U / (D T); y = observed fail-closed
    availability A (filled, 95% CI) and fail-degraded floor-compliant service Q
    (open, concentric) at attack budget = cut cost. Dashed line is 1:1.
(b) x = residual cut supply (k-1) R / D after the budget-1 attack, which the
    run files show removes exactly one cut link in every graph; y = fail-
    degraded forced assurance loss F (95% CI), log scale.

Nothing plotted is retyped. D (mean floor-grade demand across the cut), U
(usable initial stock per link), T, R and the cut come from qkdsim.config,
revision.scenarios and the Case defaults; A, Q, F and their percentile-
bootstrap intervals come from results/revision/analysis/main_summary.csv
(traffic_class 'all', default Case, main grid), and every mean is re-derived
from the 12 raw run files (seeds 3000-3011) and must agree. Points sharing a
predicted x (the three k = 2 graphs) are dodged horizontally for legibility;
true and plotted x are both written to the provenance file.

Style follows make_fig_architecture_cr.py: one IEEE column, exact size (no
tight bbox), Times, >= 7 pt, Okabe-Ito colours with redundant marker shapes.

Output: figures/camera_ready/fig2_cut_scaling.pdf/.png (300 dpi) and
fig2_cut_scaling.provenance.json.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import csv
import dataclasses
import json
import math
from itertools import combinations
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.font_manager import fontManager
from matplotlib.lines import Line2D
from matplotlib.ticker import (FixedLocator, FuncFormatter, LogLocator,
                               NullFormatter)
from matplotlib.transforms import Bbox

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qkdsim.config import (LINK_CLASSES, TRAFFIC_CLASSES,  # noqa: E402
                           AccountingConfig, PhysicsConfig, ReservoirConfig,
                           quantum_key_demand)
from qkdsim.network import Topology  # noqa: E402
from revision.scenarios import Case, attack_order, build_topology  # noqa: E402

SUMMARY = ROOT / "results" / "revision" / "analysis" / "main_summary.csv"
RUNS = ROOT / "results" / "revision" / "runs"
SEEDS = tuple(range(3000, 3012))          # main grid
OUT = ROOT / "figures" / "camera_ready"
STEM = "fig2_cut_scaling"

W, H = 3.45, 1.75                 # inches; IEEE single column
FS, FS_TITLE = 7.0, 8.0           # points at final size

# Okabe-Ito (colour-blind safe); identity is also carried by marker shape.
BLUE, VERM, GREEN = "#0072B2", "#D55E00", "#009E73"
ORANGE, PURPLE = "#E69F00", "#CC79A7"
INK, INK2 = "#000000", "#444444"

# topology id, label, marker, colour, marker-size factor (diamond reads large)
GRAPHS = (
    ("formation", "formation", "o", BLUE, 1.00),
    ("ring", "ring", "s", VERM, 0.90),
    ("grid", "grid", "^", GREEN, 1.05),
    ("parallel3", "3-path", "D", ORANGE, 0.82),
    ("parallel4", "4-path", "v", PURPLE, 1.05),
)
EXPECTED_K = {"formation": 2, "ring": 2, "grid": 2, "parallel3": 3,
              "parallel4": 4}
EXPECTED_DBAR = 397.218           # bit/s; pins the derivation below
EXPECTED_U = 1_027_604.48         # bits

# horizontal dodge for graphs sharing a predicted x (ring left, grid right)
DODGE_A = {"ring": -0.85, "grid": +0.85}      # percentage points
DODGE_B = {"ring": -0.055, "grid": +0.055}    # supply-ratio units
MS_FILL, MS_OPEN, MS_B = 2.6, 4.6, 3.6

# axes rectangles, inches: (left, bottom, width, height)
AX_BOTTOM, AX_TOP = 0.335, H - 0.36
AX_A = (0.335, AX_BOTTOM, 1.285, AX_TOP - AX_BOTTOM)
AX_B = (2.085, AX_BOTTOM, 1.305, AX_TOP - AX_BOTTOM)
TITLE_B_X = 1.745


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
    "axes.linewidth": 0.6,
    "axes.labelsize": FS,
    "axes.labelpad": 1.5,
    "xtick.labelsize": FS,
    "ytick.labelsize": FS,
})


# --------------------------------------------------------------------------
# model constants, derived from the simulator
# --------------------------------------------------------------------------
CASE0 = Case()


def floor_demand(case: Case):
    """Mean per-hop key debit across one link at each class's authorised
    floor grade: sum over classes of arrival rate x (D + metadata + n_auth
    tags). Every request crosses the cut exactly once (checked below)."""
    acc = AccountingConfig(n_auth=case.n_auth)
    parts = []
    for tc in TRAFFIC_CLASSES:
        rate = tc.arrival_rate * (case.isr_scale if tc.name == "ISR" else 1.0)
        q = acc.cost_per_hop(quantum_key_demand(tc.authorised_floor,
                                                tc.payload_bits))
        parts.append({"class": tc.name, "floor": tc.authorised_floor,
                      "rate_per_s": rate, "debit_bits": q})
    return sum(p["rate_per_s"] * p["debit_bits"] for p in parts), parts


def usable_stock(case: Case):
    """Spendable bits above the authentication reserve at t = 0, per link
    (same arithmetic as revision.scenarios.make_simulator)."""
    res = ReservoirConfig()
    m_min = round(res.m_min * case.reservoir_scale)
    m_max = round(res.m_max * case.reservoir_scale)
    return case.initial_spendable_fraction * (m_max - m_min), m_min


def graph_facts(name: str, case: Case):
    topo = build_topology(name, ReservoirConfig())
    _, costs, cut = attack_order(topo, case.attack_method,
                                 case.fibre_attack_cost)
    cut = [Topology.key(*e) for e in cut]
    k = len(cut)
    assert k == EXPECTED_K[name], (name, cut)
    assert sum(costs[e] for e in cut) == k, name     # free-space cost 1 each
    rates = {LINK_CLASSES[topo.links[e].link_class].rate_bps * case.rate_scale
             for e in cut}
    classes = {topo.links[e].link_class for e in cut}
    assert len(rates) == 1, (name, rates)
    # generation suppression: e0 + delta_e >= e_abort, so the link yields 0
    phys = PhysicsConfig(e_abort=case.e_abort, gamma=case.gamma)
    for e in cut:
        link = topo.links[e]
        link.outage, link.excess_qber = False, case.delta_e
        assert link.qber(phys) >= phys.e_abort
        assert link.current_rate_bps(phys) == 0.0, (name, e)
        link.excess_qber = 0.0
    # every simple rear -> forward path (routing uses simple paths only)
    # crosses the cut exactly once
    rear = next(n for n, r in topo.node_roles.items() if r == "rear")
    fwd = sorted(n for n, r in topo.node_roles.items() if r == "forward")
    cutset, crossings, n_paths = set(cut), set(), 0
    for f in fwd:
        for p in nx.all_simple_paths(topo.graph, rear, f):
            n_paths += 1
            crossings.add(sum(Topology.key(u, v) in cutset
                              for u, v in zip(p, p[1:])))
    assert crossings == {1}, (name, crossings)
    return dict(k=k, cut=sorted(cut), cut_link_class=classes.pop(),
                cut_rate_bps=rates.pop(), nodes=topo.graph.number_of_nodes(),
                links=topo.graph.number_of_edges(), simple_paths=n_paths)


# --------------------------------------------------------------------------
# observed values
# --------------------------------------------------------------------------
def _same(a, b) -> bool:
    try:
        return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12)
    except (TypeError, ValueError):
        return str(a) == str(b)


def summary_rows():
    varying = {"topology", "attack_budget", "fail_mode"}
    fixed = [f.name for f in dataclasses.fields(Case) if f.name not in varying]
    out = {}
    with SUMMARY.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["traffic_class"] != "all":
                continue
            if not all(_same(r[f], getattr(CASE0, f)) for f in fixed):
                continue
            key = (r["topology"], r["fail_mode"], float(r["attack_budget"]))
            assert key not in out, key
            out[key] = r
    return out


def observe(rows, topo, fail_mode, budget, metric, facts, U, m_min):
    """CSV value and interval, re-derived mean from the raw run files."""
    r = rows[(topo, fail_mode, float(budget))]
    cid = r["case_id"]
    assert int(r["n_seeds"]) == len(SEEDS)
    assert int(r[f"{metric}_defined_seeds"]) == len(SEEDS)
    assert float(r["cut_cost"]) == facts["k"]
    assert int(r["node_count"]) == facts["nodes"]
    assert int(r["edge_count"]) == facts["links"]
    want = dataclasses.asdict(dataclasses.replace(
        CASE0, topology=topo, attack_budget=budget, fail_mode=fail_mode))
    vals, attacked = [], set()
    for seed in SEEDS:
        d = json.loads((RUNS / f"{cid}_seed{seed}.json").read_text())
        assert d["case_id"] == cid and d["seed"] == seed
        assert all(_same(d["case"][f], v) for f, v in want.items()), cid
        t = d["topology"]
        assert sorted(Topology.key(*e) for e in t["all_terminal_cut"]) \
            == facts["cut"], cid
        att = tuple(sorted(Topology.key(*e) for e in t["attacked_edges"]))
        assert float(t["spent_attack_budget"]) == float(budget), cid
        attacked.add(att)
        for stored in d["accounting"]["initial_stored_bits"].values():
            assert math.isclose(stored - m_min, U, abs_tol=1e-6), cid
        vals.append(d["summary"]["all"][metric])
    assert len(attacked) == 1, (cid, attacked)
    attacked = [list(e) for e in attacked.pop()]
    raw_mean = sum(vals) / len(vals)
    value = float(r[metric])
    assert math.isclose(raw_mean, value, rel_tol=1e-9, abs_tol=1e-12), \
        (cid, metric, raw_mean, value)
    return dict(case_id=cid, topology=topo, fail_mode=fail_mode,
                attack_budget=budget, metric=metric, value=value,
                ci95_lo=float(r[f"{metric}_lo"]),
                ci95_hi=float(r[f"{metric}_hi"]), raw_seed_mean=raw_mean,
                seeds=[SEEDS[0], SEEDS[-1]], n_seeds=len(SEEDS),
                attacked_edges=attacked)


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------
def inch_axes(fig, rect):
    l, b, w, h = rect
    return fig.add_axes([l / W, b / H, w / W, h / H])


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(which="major", width=0.6, length=2.4, pad=1.6)
    ax.tick_params(which="minor", width=0.4, length=1.4)


def errbar(ax, x, obs, color, scale=100.0):
    y, lo, hi = (obs[k] * scale for k in ("value", "ci95_lo", "ci95_hi"))
    ax.errorbar([x], [y], yerr=[[y - lo], [hi - y]], fmt="none",
                ecolor=color, elinewidth=0.6, capsize=1.3, capthick=0.6,
                zorder=2)


def draw_a(ax, pts):
    lim = 14.0
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ticks = [0, 3, 6, 9, 12]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.plot([0, lim], [0, lim], color=INK2, lw=0.7, ls=(0, (3.0, 2.0)),
            zorder=1)
    ax.text(3.2, 1.55, "1:1", color=INK2, ha="left", va="center_baseline")
    for g, lab, m, col, f in GRAPHS:
        p = pts[g]
        x = p["x_plotted_pct"]
        errbar(ax, x, p["A"], col)
        ax.plot([x], [100 * p["Q"]["value"]], ls="none", marker=m,
                ms=MS_OPEN * f, mfc="white", mec=col, mew=0.7, zorder=3)
        ax.plot([x], [100 * p["A"]["value"]], ls="none", marker=m,
                ms=MS_FILL * f, mfc=col, mec=col, mew=0.0, zorder=4)
    for k, x in sorted({(p["k"], p["x_pred_pct"]) for p in pts.values()}):
        low = min(100 * min(p["A"]["ci95_lo"], p["Q"]["ci95_lo"])
                  for p in pts.values() if p["k"] == k)
        ax.text(x + 0.9, low - 0.8, f"$k{{=}}{k}$", ha="center", va="top")
    handles = [Line2D([], [], ls="none", marker="o", ms=MS_FILL, mfc=INK2,
                      mec=INK2, mew=0),
               Line2D([], [], ls="none", marker="o", ms=MS_OPEN, mfc="white",
                      mec=INK2, mew=0.7)]
    leg = ax.legend(handles, ["fail-closed $A$", "fail-degraded $Q$"],
                    loc="upper left", frameon=False, fontsize=FS,
                    handlelength=0.9, handletextpad=0.35, labelspacing=0.2,
                    borderpad=0.1, borderaxespad=0.15)
    ax.set_xlabel(r"Predicted $kU/(\bar{D}T)$ (%)")
    ax.set_ylabel("Observed (%)")
    return leg


def draw_b(ax, pts):
    ax.set_yscale("log")
    ax.set_xlim(0.3, 2.1)
    ax.set_ylim(0.01, 30)
    ax.xaxis.set_major_locator(FixedLocator([0.5, 1.0, 1.5, 2.0]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}"))
    ax.yaxis.set_major_locator(FixedLocator([0.01, 0.1, 1, 10]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=range(2, 10)))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.axvline(1.0, color=INK2, lw=0.8, ls=(0, (1.0, 1.6)), zorder=1)
    ax.text(1.045, 21.0, "supply = demand", color=INK2, ha="left",
            va="center_baseline")
    for g, lab, m, col, f in GRAPHS:
        p = pts[g]
        x = p["x_plotted_ratio"]
        errbar(ax, x, p["F"], col)
        ax.plot([x], [100 * p["F"]["value"]], ls="none", marker=m,
                ms=MS_B * f, mfc=col, mec=col, mew=0.0, zorder=4)
    # k labels: under the k = 2 group, beside the single-graph points
    for k in sorted({p["k"] for p in pts.values()}):
        grp = [p for p in pts.values() if p["k"] == k]
        x = grp[0]["x_residual_ratio"]
        if len(grp) > 1:
            low = min(100 * p["F"]["ci95_lo"] for p in grp)
            ax.text(x, low / 1.7, f"$k{{=}}{k}$", ha="center", va="top")
        else:
            side = 1 if x < 1.5 else -1
            ax.text(x + side * 0.075, 100 * grp[0]["F"]["value"],
                    f"$k{{=}}{k}$", ha="left" if side > 0 else "right",
                    va="center")
    ax.set_xlabel(r"Residual supply $(k{-}1)\,R/\bar{D}$")
    ax.set_ylabel("Forced loss $F$ (%)")


def check_layout(fig, texts, markers):
    """Fail on text-text overlap, text outside the figure, or in-axes text
    covering a data marker or error bar."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    boxes = [(n, a.get_window_extent(r)) for n, a in texts]
    fb = fig.bbox
    problems = []
    for n, b in boxes:
        if b.x0 < fb.x0 - 0.5 or b.y0 < fb.y0 - 0.5 or \
                b.x1 > fb.x1 + 0.5 or b.y1 > fb.y1 + 0.5:
            problems.append(f"{n} outside figure: "
                            f"{[round(v / fig.dpi, 3) for v in b.extents]} in")
    for (n1, b1), (n2, b2) in combinations(boxes, 2):
        if b1.overlaps(b2):
            problems.append(f"{n1} overlaps {n2}")
    for n, b in boxes:
        for mn, mb in markers:
            if b.overlaps(mb):
                problems.append(f"{n} covers {mn}")
    return problems


def marker_boxes(ax, pts, panel, fig):
    """Boxes around markers, error bars and the reference line."""
    px = fig.dpi / 72.0
    if panel == "a":
        ref = [(0.25 * i, 0.25 * i) for i in range(57)]           # 1:1
    else:
        ref = [(1.0, 0.01 * 10 ** (0.05 * i)) for i in range(70)]  # x = 1
    out = [(f"{panel}:reference", Bbox([[x - px, y - px], [x + px, y + px]]))
           for x, y in ax.transData.transform(ref)]
    for g, _, _, _, f in GRAPHS:
        p = pts[g]
        if panel == "a":
            x, obs, ms = p["x_plotted_pct"], [p["A"], p["Q"]], MS_OPEN * f
        else:
            x, obs, ms = p["x_plotted_ratio"], [p["F"]], MS_B * f
        for o in obs:
            lo, hi = 100 * o["ci95_lo"], 100 * o["ci95_hi"]
            (x0, y0), (x1, y1) = ax.transData.transform([(x, lo), (x, hi)])
            h = max(ms, 2.6) * px / 2
            out.append((f"{panel}:{g}:{o['metric']}",
                        Bbox([[x0 - h, y0 - h], [x1 + h, y1 + h]])))
    return out


def main() -> int:
    case = CASE0
    dbar, parts = floor_demand(case)
    U, m_min = usable_stock(case)
    T = float(case.horizon_s)
    assert math.isclose(dbar, EXPECTED_DBAR, abs_tol=1e-9), dbar
    assert math.isclose(U, EXPECTED_U, abs_tol=1e-6), U
    rows = summary_rows()
    assert len(rows) == 30, len(rows)

    pts, cut_rates = {}, set()
    for g, lab, *_ in GRAPHS:
        facts = graph_facts(g, case)
        k, R = facts["k"], facts["cut_rate_bps"]
        cut_rates.add(R)
        obs = dict(
            A=observe(rows, g, "FAIL_CLOSED", float(k), "availability",
                      facts, U, m_min),
            Q=observe(rows, g, "FAIL_DEGRADED", float(k),
                      "qualified_availability", facts, U, m_min),
            F=observe(rows, g, "FAIL_DEGRADED", 1.0,
                      "forced_entitled_fraction", facts, U, m_min),
        )
        assert sorted(tuple(e) for e in obs["A"]["attacked_edges"]) \
            == facts["cut"]
        assert sorted(tuple(e) for e in obs["Q"]["attacked_edges"]) \
            == facts["cut"]
        one = [tuple(e) for e in obs["F"]["attacked_edges"]]
        assert len(one) == 1 and one[0] in facts["cut"], (g, one)
        x_pred = k * U / (dbar * T)
        x_res = (k - 1) * R / dbar          # budget 1 removes one cut link
        pts[g] = dict(
            label=lab, **facts, **obs,
            x_pred=x_pred, x_pred_pct=100 * x_pred,
            x_plotted_pct=100 * x_pred + DODGE_A.get(g, 0.0),
            x_residual_ratio=x_res,
            x_plotted_ratio=x_res + DODGE_B.get(g, 0.0))
    assert cut_rates == {240.0}, cut_rates

    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = inch_axes(fig, AX_A), inch_axes(fig, AX_B)
    style(ax_a)
    style(ax_b)
    leg_a = draw_a(ax_a, pts)
    draw_b(ax_b, pts)

    t_a = fig.text(0.02 / W, 1 - 0.012 / H,
                   "(a) Stock-limited service at the cut",
                   fontsize=FS_TITLE, ha="left", va="top")
    t_b = fig.text(TITLE_B_X / W, 1 - 0.012 / H,
                   "(b) One cut link suppressed",
                   fontsize=FS_TITLE, ha="left", va="top")
    handles = [Line2D([], [], ls="none", marker=m, ms=MS_B * f, mfc=c, mec=c,
                      mew=0) for _, _, m, c, f in GRAPHS]
    leg = fig.legend(handles, [lab for _, lab, *_ in GRAPHS], loc="center",
                     ncol=len(GRAPHS), frameon=False, fontsize=FS,
                     bbox_to_anchor=(0.5, 1 - 0.228 / H), handlelength=0.8,
                     handletextpad=0.3, columnspacing=1.1, borderpad=0.0,
                     borderaxespad=0.0)

    texts = [("title a", t_a), ("title b", t_b), ("graph legend", leg),
             ("legend a", leg_a)]
    for name, ax in (("a", ax_a), ("b", ax_b)):
        texts += [(f"{name} xlabel", ax.xaxis.label),
                  (f"{name} ylabel", ax.yaxis.label)]
        texts += [(f"{name} xtick {t.get_text()}", t)
                  for t in ax.get_xticklabels() if t.get_text()]
        texts += [(f"{name} ytick {t.get_text()}", t)
                  for t in ax.get_yticklabels() if t.get_text()]
        texts += [(f"{name} note {t.get_text()}", t) for t in ax.texts]
    fig.canvas.draw()
    markers = marker_boxes(ax_a, pts, "a", fig) + \
        marker_boxes(ax_b, pts, "b", fig)
    problems = check_layout(fig, texts, markers)
    for p in problems:
        print("LAYOUT:", p)
    assert not problems, "layout check failed"

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{STEM}.pdf", metadata={"CreationDate": None})
    fig.savefig(OUT / f"{STEM}.png")
    plt.close(fig)

    prov = {
        "figure": f"figures/camera_ready/{STEM}.pdf/.png",
        "script": "experiments/make_fig_cut_scaling_cr.py",
        "size_in": [W, H],
        "sources": {"summary": "results/revision/analysis/main_summary.csv "
                               "(traffic_class 'all', default Case)",
                    "runs": "results/revision/runs/<case_id>_seed<seed>.json"
                            " summary.all.<metric>",
                    "seeds": list(SEEDS),
                    "interval": "95% marginal percentile bootstrap over "
                                "seeds, as stored in main_summary.csv"},
        "constants": {"D_bar_bps": dbar, "demand_terms": parts,
                      "U_bits": U, "auth_reserve_bits": m_min, "T_s": T,
                      "R_cut_bps": cut_rates.pop(),
                      "attack": {"surface": case.attack_surface,
                                 "duration_s": case.attack_duration_s,
                                 "qber": PhysicsConfig().e0 + case.delta_e,
                                 "e_abort": case.e_abort}},
        "dodge": {"panel_a_pct_points": DODGE_A,
                  "panel_b_ratio_units": DODGE_B},
        "points": {},
    }
    keep = ("case_id", "fail_mode", "attack_budget", "metric", "value",
            "ci95_lo", "ci95_hi", "raw_seed_mean")
    for g, p in pts.items():
        prov["points"][g] = {
            "label": p["label"], "k": p["k"], "nodes": p["nodes"],
            "links": p["links"], "cut": [list(e) for e in p["cut"]],
            "attacked_edges_budget1": p["F"]["attacked_edges"],
            "panel_a": {"x_pred": p["x_pred"],
                        "x_plotted_pct": p["x_plotted_pct"],
                        "A": {k: p["A"][k] for k in keep},
                        "Q": {k: p["Q"][k] for k in keep}},
            "panel_b": {"x_residual_ratio": p["x_residual_ratio"],
                        "x_plotted_ratio": p["x_plotted_ratio"],
                        "F": {k: p["F"][k] for k in keep}},
        }
    (OUT / f"{STEM}.provenance.json").write_text(
        json.dumps(prov, indent=1) + "\n")

    print(f"D_bar = {dbar:.3f} bit/s, U = {U:.2f} bits, T = {T:g} s")
    for g, p in pts.items():
        a, q, fl = p["A"], p["Q"], p["F"]
        print(f"{p['label']:9s} k={p['k']} cut={p['cut']} "
              f"budget1={p['F']['attacked_edges']}")
        print(f"   (a) x={100 * p['x_pred']:.2f}%  "
              f"A={100 * a['value']:.3f} [{100 * a['ci95_lo']:.3f}, "
              f"{100 * a['ci95_hi']:.3f}]  "
              f"Q={100 * q['value']:.3f} [{100 * q['ci95_lo']:.3f}, "
              f"{100 * q['ci95_hi']:.3f}]")
        print(f"   (b) x={p['x_residual_ratio']:.3f}  "
              f"F={100 * fl['value']:.3f} [{100 * fl['ci95_lo']:.3f}, "
              f"{100 * fl['ci95_hi']:.3f}]%")
    print(f"-> {OUT.relative_to(ROOT)}/{STEM}.pdf/.png/.provenance.json "
          f"({W} x {H} in)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
