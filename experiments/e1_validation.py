"""E1 -- Validation gate. Nothing downstream is believed until this passes.

"""
from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qkdsim.config import (G1_OTP, G2_QKD_SYM, G4_PQC, AccountingConfig,
                           OutageConfig, PhysicsConfig, ReservoirConfig,
                           SimConfig, quantum_key_demand)
from qkdsim.network import formation_9node
from qkdsim.physics import BufferState, KeyStore, h2, rate_fraction
from qkdsim.sim import Outcome, Simulator

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(ok), detail))


def base_cfg(**kw) -> SimConfig:
    # warmup_s=0: validation reasons over EVERY session, including the
    # drain-from-full transient. Steady-state experiments set it to 12 h.
    d = dict(horizon_s=3600.0, warmup_s=0.0, seed=0,
             outage=OutageConfig(mean_uptime_s=1e12, mean_outage_s=1.0))
    d.update(kw)
    return SimConfig(**d)


# ---------------------------------------------------------------- 4. cliff
def t_cliff() -> None:
    p = PhysicsConfig()
    check("cliff: rho(e0) == 1", abs(rate_fraction(p.e0, p) - 1.0) < 1e-12,
          f"rho({p.e0}) = {rate_fraction(p.e0, p):.6f}")
    check("cliff: rho(e_abort) == 0", rate_fraction(p.e_abort, p) == 0.0,
          f"rho({p.e_abort}) = {rate_fraction(p.e_abort, p)}")
    check("cliff: rho above abort == 0",
          all(rate_fraction(e, p) == 0.0 for e in (0.08, 0.11, 0.2, 0.5)))
    es = [0.03 + 0.001 * i for i in range(int((p.e_abort - 0.03) / 0.001))]
    vals = [rate_fraction(e, p) for e in es]
    check("cliff: monotone decreasing below abort",
          all(vals[i] >= vals[i + 1] - 1e-12 for i in range(len(vals) - 1)))

    # Where the rate expression itself reaches zero, as a function of the
    # error-correction inefficiency f.
    #   f = 1.00 (Shannon limit) -> H2(e) >= 1/2   -> e ~ 0.110, which is the
    #       textbook asymptotic one-way BB84 threshold (Shor-Preskill PRL 85:441;
    #       Rath arXiv:2603.27278 quote ~11%).
    #   f = 1.16 (realistic EC)  -> H2(e) >= 1/2.16 -> e ~ 0.099.
    # Realistic error correction therefore LOWERS the cliff below the textbook
    # 11%, and our engineering e_abort = 0.075 sits below both. This is a
    # feature of the model, not a discrepancy, and belongs in the paper.
    def zero_of(f: float) -> float | None:
        return next((e for e in [0.0005 * i for i in range(1, 600)]
                     if 1.0 - f * h2(e) - h2(e) <= 0.0), None)

    z_shannon = zero_of(1.0)
    z_real = zero_of(p.f_ec)
    check("cliff: f=1.00 zero in [0.105, 0.115] (Shor-Preskill ~11%)",
          z_shannon is not None and 0.105 <= z_shannon <= 0.115,
          f"zero at e={z_shannon}")
    check("cliff: f=1.16 zero in [0.095, 0.105] (realistic EC lowers it)",
          z_real is not None and 0.095 <= z_real <= 0.105,
          f"zero at e={z_real}")
    check("cliff: e_abort sits below both zeros",
          p.e_abort < (z_real or 1.0) < (z_shannon or 1.0),
          f"e_abort={p.e_abort} < {z_real} < {z_shannon}")

    # gamma = 3.4 must reproduce the Tokyo All-Vienna 8-12% datapoint at QBER 6%
    g = replace(p, gamma=3.4)
    v = rate_fraction(0.06, g)
    check("Tokyo calibration: rho(0.06) in [0.08, 0.12] at gamma=3.4",
          0.08 <= v <= 0.12, f"rho(0.06) = {v:.4f}")
    v1 = rate_fraction(0.06, p)
    check("physics variant: rho(0.06) ~ 0.50 at gamma=1",
          0.45 <= v1 <= 0.55, f"rho(0.06) = {v1:.4f}")


# ------------------------------------------------- 2. reservoir bounds
def t_reservoir() -> None:
    rc = ReservoirConfig()
    ks = KeyStore(rc)
    check("reservoir: starts at m_max", ks.level == rc.m_max)
    d = ks.accumulate(1e9)
    check("reservoir: overflow discards, never exceeds m_max",
          ks.level == rc.m_max and d == 1e9, f"discarded {d:.0f}")
    check("reservoir: cannot draw below m_min (auth reserve)",
          not ks.take(rc.m_max - rc.m_min + 1))
    check("reservoir: can draw exactly to m_min",
          ks.take(rc.m_max - rc.m_min) and abs(ks.level - rc.m_min) < 1e-6)
    check("reservoir: EMPTY at m_min", ks.state() is BufferState.EMPTY,
          ks.state().value)
    ks2 = KeyStore(rc)
    check("reservoir: READY when >= m_thr", ks2.state() is BufferState.READY)
    # Drop clearly BELOW the threshold. Taking exactly (m_max - m_thr) lands on
    # m_thr, which is still READY; and landing only one bit below would be
    # pushed back over the threshold by the small accumulate() used to test the
    # rising branch. Leave enough headroom for both branches.
    ks2.take(rc.m_max - rc.m_thr + 10_000)
    check("reservoir: level is below m_thr",
          ks2.level < rc.m_thr, f"level={ks2.level:.0f} thr={rc.m_thr}")
    ks2.accumulate(0.0)
    check("reservoir: below thr and not rising -> WARNING",
          ks2.state() is BufferState.WARNING, ks2.state().value)
    ks2.accumulate(1000.0)
    check("reservoir: still below thr after small top-up",
          ks2.level < rc.m_thr, f"level={ks2.level:.0f}")
    check("reservoir: below thr and rising -> CHARGING",
          ks2.state() is BufferState.CHARGING, ks2.state().value)


# --------------------------------------------------- 1. key conservation
def t_conservation() -> None:
    for mode in ("FAIL_DEGRADED", "FAIL_CLOSED"):
        cfg = base_cfg(fail_mode=mode)
        topo = formation_9node(cfg.reservoir)
        r = Simulator(topo, cfg).run()
        by_session = sum(s.key_bits for s in r.sessions
                         if s.outcome is Outcome.SERVED)
        by_store = sum(topo.stores[k].consumed_bits
                       for k in topo.all_link_keys())
        check(f"conservation [{mode}]: sum(session debits) == sum(store debits)",
              abs(by_session - by_store) < 1e-6,
              f"{by_session:.1f} vs {by_store:.1f}")

        # per-hop law: key_bits must equal hops * cost_per_hop(demand)
        bad = []
        for s in r.sessions:
            if s.outcome is not Outcome.SERVED or s.grade == G4_PQC:
                continue
            want = s.hops * cfg.accounting.cost_per_hop(
                quantum_key_demand(s.grade, s.payload_bits))
            if abs(s.key_bits - want) > 1e-6:
                bad.append((s.sid, s.key_bits, want))
        check(f"conservation [{mode}]: key_bits == hops * cost_per_hop",
              not bad, f"{len(bad)} mismatches")
        check(f"conservation [{mode}]: G4 consumes zero quantum key",
              all(s.key_bits == 0.0 for s in r.sessions
                  if s.grade == G4_PQC))
        check(f"conservation [{mode}]: no negative reservoir",
              all(topo.stores[k].level >= 0.0 for k in topo.all_link_keys()))


# ---------------------------------------------------- 3. degenerate cases
def t_degenerate() -> None:
    # (a) abundant key -> everything served at its authorised floor, no violations
    cfg = base_cfg(fail_mode="FAIL_DEGRADED")
    topo = formation_9node(cfg.reservoir)
    for k in topo.all_link_keys():
        topo.links[k].nominal_rate_bps = 1e9
    r = Simulator(topo, cfg).run()
    check("degenerate: abundant key -> 100% served",
          r.served_fraction() == 1.0, f"{r.served_fraction():.4f}")
    check("degenerate: abundant key -> zero floor violations",
          r.floor_violation_fraction() == 0.0,
          f"{r.floor_violation_fraction():.4f}")
    comp = r.grade_composition("ISR")
    check("degenerate: abundant key -> ISR served at G1 (its floor)",
          comp[G1_OTP] == 1.0, f"G1 share {comp[G1_OTP]:.4f}")

    # (b) zero key: FAIL_DEGRADED serves everything at G4; FAIL_CLOSED blocks all
    res0 = ReservoirConfig(m_initial_frac=0.0)
    for mode, expect in (("FAIL_DEGRADED", "served"), ("FAIL_CLOSED", "blocked")):
        c = base_cfg(fail_mode=mode, reservoir=res0)
        tp = formation_9node(c.reservoir)
        for k in tp.all_link_keys():
            tp.links[k].nominal_rate_bps = 0.0
        rr = Simulator(tp, c).run()
        if expect == "served":
            check("degenerate: zero key + FAIL_DEGRADED -> all served at G4",
                  rr.served_fraction() == 1.0
                  and rr.grade_composition()[G4_PQC] == 1.0,
                  f"served {rr.served_fraction():.3f}, "
                  f"G4 {rr.grade_composition()[G4_PQC]:.3f}")
            check("degenerate: zero key -> all served are floor violations",
                  rr.floor_violation_fraction() == 1.0,
                  f"{rr.floor_violation_fraction():.3f}")
        else:
            check("degenerate: zero key + FAIL_CLOSED -> all blocked",
                  rr.blocked_fraction() == 1.0,
                  f"blocked {rr.blocked_fraction():.3f}")


# ------------------------------------- 5. SECOQC Fig. 22 drain reproduction
def t_secoqc_fig22() -> None:
    """Peev et al., New J. Phys. 11:075001 (2009), Fig. 22.

    An application consuming ~1 KiB/s = 8192 bit/s by one-time pad drained
    3.5 MiB of a 5.5 MiB key store in approximately one hour, after which the
    network rerouted. Reference arithmetic: 3.5 MiB / 1024 B/s = 3584 s.
    """
    consume_bps = 8192.0
    start_bits = 5.5 * 1024 * 1024 * 8
    drain_bits = 3.5 * 1024 * 1024 * 8
    rc = ReservoirConfig(m_min=0, m_thr=int(start_bits * 0.5),
                         m_max=int(start_bits), m_initial_frac=1.0)
    ks = KeyStore(rc)
    t = 0.0
    while ks.consumed_bits < drain_bits and t < 20000.0:
        ks.take(consume_bps * 1.0)
        t += 1.0
    check("SECOQC Fig.22: 3.5 MiB drained at 8192 bit/s in ~3584 s",
          abs(t - 3584.0) <= 2.0, f"t = {t:.0f} s (reference 3584 s)")

    # and the OTP demand law that produces that drain rate
    check("SECOQC: OTP key demand == payload bits (Shannon)",
          quantum_key_demand(G1_OTP, 144_000) == 144_000)
    check("SECOQC: G2 demand is one 256-bit key",
          quantum_key_demand(G2_QKD_SYM, 144_000) == 256)


# -------------------------------------------- 6. common random numbers
def t_crn() -> None:
    a = base_cfg(fail_mode="FAIL_DEGRADED", routing="SP")
    b = base_cfg(fail_mode="FAIL_CLOSED", routing="KAR")
    ra = Simulator(formation_9node(a.reservoir), a).run()
    rb = Simulator(formation_9node(b.reservoir), b).run()
    sa = [(s.sid, s.cls, s.arrival_t, s.src, s.dst) for s in
          sorted(ra.sessions, key=lambda s: s.sid)]
    sb = [(s.sid, s.cls, s.arrival_t, s.src, s.dst) for s in
          sorted(rb.sessions, key=lambda s: s.sid)]
    check("CRN: identical arrival stream across policies at equal seed",
          sa == sb, f"{len(sa)} vs {len(sb)} sessions")
    c = base_cfg(seed=1)
    rc_ = Simulator(formation_9node(c.reservoir), c).run()
    sc = [(s.sid, s.cls, s.arrival_t) for s in
          sorted(rc_.sessions, key=lambda s: s.sid)]
    check("CRN: different seed gives a different stream",
          [(x[0], x[1], x[2]) for x in sa] != sc)


# ------------------------------------------- 4b. authentication accounting
def t_accounting() -> None:
    on = AccountingConfig(auth_on=True)
    off = AccountingConfig(auth_on=False)
    check("accounting: AUTH_OFF reproduces the bare D law",
          off.cost_per_hop(256) == 256)
    check("accounting: AUTH_ON at D=256 is 750 bit/hop",
          on.cost_per_hop(256) == 750, str(on.cost_per_hop(256)))
    f = on.overhead_factor(256)
    check("accounting: overhead factor at D=256 in [2.9, 3.6] "
          "(Cambridge measured 3.6x)", 2.9 <= f <= 3.6, f"{f:.3f}x")
    fbig = on.overhead_factor(1_000_000)
    check("accounting: overhead negligible at 1 Mbit blocks (<1%)",
          fbig < 1.01, f"{fbig:.5f}x")
    check("accounting: zero demand costs zero", on.cost_per_hop(0) == 0)


def main() -> int:
    t_cliff()
    t_reservoir()
    t_accounting()
    t_conservation()
    t_degenerate()
    t_secoqc_fig22()
    t_crn()

    width = max(len(n) for n, _, _ in CHECKS) + 2
    print("\n" + "=" * (width + 30))
    print("E1 VALIDATION GATE".center(width + 30))
    print("=" * (width + 30))
    failed = 0
    for name, ok, detail in CHECKS:
        tag = " PASS " if ok else " FAIL "
        print(f"[{tag}] {name:<{width}} {detail}")
        failed += (not ok)
    print("-" * (width + 30))
    print(f"{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    if failed:
        print(f"\n{failed} FAILURE(S) -- downstream results are NOT valid.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
