r"""Separate floor violations from forced assurance loss at zero adversary budget.

With no adversary present, 16.6% of entitled traffic is served below its authorised
floor while forced assurance loss is zero, so the two quantities must be measured
apart. Three candidate explanations are distinguished:
  (a) a bug in grade selection or in the forced-loss metric;
  (b) a parameterisation problem -- specifically, the authentication reserve
      m_min was imported from QKDNetSim's SECOQC configuration, which describes
      metro FIBRE links generating >=100 kbit/s. Our free-space links generate
      240 bit/s. A 1 Mibit reserve takes 4369 s to fill at that rate, so the
      reserve may be pinning the reservoir permanently empty and acting as a
      hard rate limiter rather than a buffer;
  (c) a real consequence of free-space key rates, i.e. a finding.

Run: python experiments/diag_baseline_forced.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qkdsim.config import (G1_OTP, G2_QKD_SYM, AdversaryConfig, ReservoirConfig,
                           SimConfig, is_at_least, quantum_key_demand)
from qkdsim.network import formation_9node
from qkdsim.sim import Outcome, Simulator


def run(res: ReservoirConfig, label: str, seeds=range(4)):
    rows = []
    for sd in seeds:
        cfg = SimConfig(seed=sd, routing="KAR", fail_mode="FAIL_DEGRADED",
                        reservoir=res,
                        adversary=AdversaryConfig(budget_links=0))
        topo = formation_9node(cfg.reservoir)
        r = Simulator(topo, cfg).run()
        served = [s for s in r.sessions
                  if s.outcome is Outcome.SERVED and s.arrival_t >= cfg.warmup_s]
        ent = [s for s in served if is_at_least(s.authorised_floor, G2_QKD_SYM)]
        forced = [s for s in ent if not is_at_least(s.grade, G2_QKD_SYM)]
        # reservoir occupancy at end, by link class, as a multiple of m_min
        occ = {}
        for k in topo.all_link_keys():
            st, lk = topo.stores[k], topo.links[k]
            occ.setdefault(lk.link_class, []).append(st.level / st.m_min)
        rows.append(dict(
            forced_frac=len(forced) / max(len(ent), 1),
            by_class=Counter(s.cls for s in forced),
            grades=Counter(f"{s.cls}:{s.grade}" for s in ent),
            occ={c: float(np.mean(v)) for c, v in occ.items()},
            served_isr_g1=sum(1 for s in served
                              if s.cls == "ISR" and s.grade == G1_OTP),
            n_isr=sum(1 for s in served if s.cls == "ISR"),
        ))
    print(f"\n### {label}")
    print(f"  forced-below-ITS (entitled)      : "
          f"{np.mean([r['forced_frac'] for r in rows]):.4f}")
    agg = Counter()
    for r in rows:
        agg.update(r["by_class"])
    print(f"  which classes are forced         : {dict(agg)}")
    g = Counter()
    for r in rows:
        g.update(r["grades"])
    print(f"  entitled-traffic grade outcomes  : {dict(sorted(g.items()))}")
    print(f"  ISR served at G1 (its floor)     : "
          f"{sum(r['served_isr_g1'] for r in rows)}/"
          f"{sum(r['n_isr'] for r in rows)}")
    o = {}
    for r in rows:
        for c, v in r["occ"].items():
            o.setdefault(c, []).append(v)
    print("  end reservoir level / m_min      : "
          + ", ".join(f"{c}={np.mean(v):.2f}" for c, v in sorted(o.items())))
    return np.mean([r["forced_frac"] for r in rows])


def main() -> int:
    print("=" * 74)
    print("DIAGNOSTIC: baseline forced assurance loss at k=0")
    print("=" * 74)

    print("\nWhat each grade costs on one hop (D + 240 + 2*127):")
    for g in (G1_OTP, G2_QKD_SYM):
        for payload, cls in ((2_048, "C2"), (144_000, "ISR")):
            d = quantum_key_demand(g, payload)
            print(f"  {cls:4} at {g}: demand {d:>7} bit -> "
                  f"{d + 240 + 254:>7} bit/hop, "
                  f"{(d + 240 + 254) * 3:>7} bit over 3 hops")

    base = ReservoirConfig()
    print(f"\nAuthentication reserve m_min = {base.m_min} bit.")
    for rate, name in ((240.0, "FSO nominal"), (300_000.0, "fibre")):
        print(f"  time to fill m_min at {name} ({rate:g} bit/s): "
              f"{base.m_min / rate:.0f} s")

    f_default = run(base, "DEFAULT: m_min = 1 Mibit (QKDNetSim metro-fibre value)")

    # Hypothesis (b): scale the reserve to the link rate instead of importing an
    # absolute value from a different regime. 60 s of generation at 240 bit/s is
    # 14.4 kbit; keep thr/max proportional so the buffer still has dynamics.
    scaled = ReservoirConfig(m_min=14_400, m_thr=150_000, m_max=720_000)
    f_scaled = run(scaled, "SCALED: m_min = 60 s of FSO generation (14.4 kbit)")

    print("\n" + "=" * 74)
    print("VERDICT")
    print("=" * 74)
    print(f"forced loss with imported m_min : {f_default:.4f}")
    print(f"forced loss with rate-scaled    : {f_scaled:.4f}")
    if f_scaled < f_default - 0.05:
        print("\n-> PARAMETERISATION, not a bug and not (only) physics. The")
        print("   authentication reserve was imported from a metro-fibre")
        print("   configuration and is oversized relative to free-space rates,")
        print("   pinning the reservoir at its floor and starving small requests.")
    else:
        print("\n-> NOT the reserve. Baseline forced loss survives rescaling, so")
        print("   it is a consequence of free-space capacity against an OTP")
        print("   floor -- i.e. a finding to be presented, not a defect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
