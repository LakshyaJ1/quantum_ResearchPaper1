"""Read-only audit of the historical simulator; writes only to stdout.

Run against commit 0d1e2fa to reproduce historical diagnostic results after fixes.
"""
from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import networkx as nx
import numpy as np
from qkdsim.config import AdversaryConfig, OutageConfig, SimConfig
from qkdsim.network import chain_topology, formation_9node
from qkdsim.sim import Simulator, Session
from qkdsim.rl import Shield, TablePolicy


def session(cls="C2", floor="G2", deadline=5.0):
    return Session(0, cls, 0.0, 2048, "N0", "N1", floor, deadline, 1)


def main():
    out = {}
    cfg = SimConfig(horizon_s=10, warmup_s=0,
                    outage=OutageConfig(mean_uptime_s=1e12, mean_outage_s=1))
    topo = formation_9node(cfg.reservoir)
    sim = Simulator(topo, cfg)
    out["topology"] = dict(nodes=len(topo.graph), links=len(topo.graph.edges),
        cuts={n: nx.edge_connectivity(topo.graph, "BASE", n)
              for n in ("FWD1", "FWD2", "FWD3")})
    bet = sorted(nx.edge_betweenness_centrality(topo.graph).items(),
                 key=lambda kv: (-kv[1], kv[0]))
    g = topo.graph.copy()
    g.remove_edges_from([e for e, _ in bet[:2]])
    out["topology"]["top2_betweenness"] = [e for e, _ in bet[:2]]
    out["topology"]["reachable_after_top2"] = [n for n in ("FWD1", "FWD2", "FWD3")
                                                        if nx.has_path(g, "BASE", n)]
    tp = chain_topology(1, cfg.reservoir)
    sm = Simulator(tp, cfg)
    tp.link("N0", "N1").excess_qber = 0.05
    initial = tp.store("N0", "N1").available()
    out["buffered_abort"] = dict(available_bits=initial,
        rate=tp.link("N0", "N1").current_rate_bps(cfg.physics),
        serve_g2=sm._try_grade(session(), "G2", 0),
        serve_g4=sm._try_grade(session(), "G4", 0))
    tp = chain_topology(1, cfg.reservoir)
    sm = Simulator(tp, cfg)
    late = session(deadline=1)
    sm.pending = [late]
    sm._tick_serve(2)
    out["expired_session"] = dict(outcome=late.outcome.value, ttk=late.ttk, deadline=late.deadline_s)
    zero = session(deadline=0)
    out["pqc_deadline"] = dict(served=sm._try_grade(zero, "G4", 0), ttk=zero.ttk)
    cfg_closed = SimConfig(horizon_s=10, warmup_s=0, fail_mode="FAIL_CLOSED")
    sm = Simulator(chain_topology(1, cfg_closed.reservoir), cfg_closed,
                   grade_policy=lambda s, sim: "G4")
    downgraded = session()
    sm._serve_or_wait(downgraded, 0)
    out["learned_fail_closed"] = dict(outcome=downgraded.outcome.value,
                                     grade=downgraded.grade,
                                     floor_violation=downgraded.floor_violation)
    out["shield_projection"] = TablePolicy([3] * 12, Shield())(session(), sm)
    out["csv_inventory"] = {}
    for path in sorted((ROOT / "results").glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        cols = list(rows[0]) if rows else []
        out["csv_inventory"][path.name] = dict(rows=len(rows), columns=cols,
            seeds=sorted({int(r["seed"]) for r in rows}) if "seed" in cols else None)
    e2 = list(csv.DictReader((ROOT / "results/e2_policy.csv").open(newline="")))
    closed = lambda policy: sorted([r for r in e2 if r["policy"] == policy and
        r["fail_mode_t"] == "FAIL_CLOSED" and r["k"] == "0"], key=lambda r: int(r["seed"]))
    a, b = closed("SP"), closed("KAR")
    diffs = np.array([float(y["served"]) - float(x["served"]) for x,y in zip(a,b)])
    rng = np.random.default_rng(12345)
    boot = diffs[rng.integers(0,len(diffs),size=(20000,len(diffs)))].mean(axis=1)
    out["paired_KAR_minus_SP"] = dict(delta=float(diffs.mean()),
        ci95=np.quantile(boot,[0.025,0.975]).tolist(), n=len(diffs))
    if "--replay" in sys.argv:
        cfg = SimConfig(seed=0, fail_mode="FAIL_CLOSED")
        rr = Simulator(formation_9node(cfg.reservoir),cfg).run()
        ref = b[0]
        out["replay_seed0"] = dict(served=rr.served_fraction(), saved=float(ref["served"]),
            consumed_Mbit=rr.consumed_bits/1e6, saved_Mbit=float(ref["consumed_Mbit"]))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
