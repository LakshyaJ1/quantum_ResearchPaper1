r"""Establish why class-aware reservation floors starve the lowest traffic class.

Fail-closed operation with class-aware floors reports zero non-ITS service, which
reads as a clean assurance win. Per-class rates show it is achieved by serving 0.0000 of the LOG
class -- the one class whose authorised floor (G3) is itself below ITS. This asks
whether that is a parameter choice or a property of stacked reservation floors.

Mechanism under test. Floors are ordered so that lower-priority classes must leave
more key behind. A higher-priority class therefore draws the store down to ITS OWN
floor and pins it there. If a lower class's floor lies above that pin level, the
lower class never runs at all -- deterministic starvation rather than
deprioritisation. Measured occupancy on the three demand-saturated free-space links
is ~10.8x m_min under CAF, exactly m_thr, which is ISR's floor; LOG's floor is
20.6x m_min. So the inversion is present at the shipped setting.

If starvation is structural, compressing the stack toward m_min will not restore LOG
service. If it is parametric, it will.

Run: python experiments/diag_caf_starvation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qkdsim.config import AdversaryConfig, ReservoirConfig, SimConfig
from qkdsim.network import formation_9node
from qkdsim.sim import Simulator

SEEDS = range(3)

# (label, basis, fracs) -- basis is the span the fraction multiplies.
SETTINGS = [
    ("shipped: frac x (m_max - m_min)", "max", {1: 0.0, 2: 0.20, 3: 0.40}),
    ("m_thr basis, same fracs",         "thr", {1: 0.0, 2: 0.20, 3: 0.40}),
    ("m_thr basis, compressed 10x",     "thr", {1: 0.0, 2: 0.02, 3: 0.04}),
    ("m_thr basis, compressed 100x",    "thr", {1: 0.0, 2: 0.002, 3: 0.004}),
    ("flat: all classes at m_min",      "thr", {1: 0.0, 2: 0.0, 3: 0.0}),
]


def patched(basis, fracs):
    def _floors(self, priority):
        if not self.cfg.reservation_floors:
            return None
        f = fracs.get(priority, max(fracs.values()))
        if f <= 0.0:
            return None
        out = {}
        for k in self.topo.all_link_keys():
            st = self.topo.stores[k]
            top = st.m_max if basis == "max" else st.m_thr
            out[k] = st.m_min + f * (top - st.m_min)
        return out
    return _floors


def run(basis, fracs):
    orig = Simulator._reservation_floors
    Simulator._reservation_floors = patched(basis, fracs)
    try:
        rows = []
        for sd in SEEDS:
            cfg = SimConfig(seed=sd, routing="KAR", fail_mode="FAIL_CLOSED",
                            reservation_floors=True,
                            adversary=AdversaryConfig(budget_links=0))
            r = Simulator(formation_9node(cfg.reservoir), cfg).run()
            rows.append((r.served_fraction(), r.below_its_fraction(),
                         r.served_fraction("C2"), r.served_fraction("ISR"),
                         r.served_fraction("LOG")))
        return np.mean(rows, axis=0)
    finally:
        Simulator._reservation_floors = orig


def main() -> int:
    rc = ReservoirConfig()
    print(f"m_min={rc.m_min}  m_thr={rc.m_thr} ({rc.m_thr/rc.m_min:.1f}x m_min)"
          f"  m_max={rc.m_max} ({rc.m_max/rc.m_min:.0f}x m_min)")
    print("\nFloor levels implied by each setting, as a multiple of m_min:")
    for label, basis, fr in SETTINGS:
        top = rc.m_max if basis == "max" else rc.m_thr
        lv = {p: (rc.m_min + f * (top - rc.m_min)) / rc.m_min
              for p, f in fr.items()}
        print(f"  {label:<34} ISR {lv[2]:>6.2f}x   LOG {lv[3]:>6.2f}x")

    print(f"\n{'setting':<34}{'avail':>8}{'<ITS':>8}"
          f"{'C2':>8}{'ISR':>8}{'LOG':>8}")
    log_ever = False
    for label, basis, fr in SETTINGS:
        av, bi, c2, isr, log = run(basis, fr)
        if log > 0.01:
            log_ever = True
        print(f"{label:<34}{av:>8.4f}{bi:>8.4f}{c2:>8.4f}{isr:>8.4f}{log:>8.4f}")

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    if log_ever:
        print("PARAMETRIC. Compressing the floor stack restores LOG service, so")
        print("the shipped 0.0000 is a badly scaled constant, not a property of")
        print("reservation floors. Report the corrected setting.")
    else:
        print("STRUCTURAL. LOG stays at 0.0000 under every ordered stack tested.")
        print("A higher-priority class pins the reservoir at its own floor, so any")
        print("strictly lower floor for a lower-priority class starves it on a")
        print("demand-saturated link. Re-tuning cannot fix it; the finding is that")
        print("stacked reservation floors are unimplementable on saturated links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
