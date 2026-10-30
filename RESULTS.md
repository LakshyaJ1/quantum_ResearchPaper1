# RESULTS — Fail-Closed or Fail-Degraded? Forced Security-Grade Loss in Contested Multi-Hop QKD Networks

**Artifact:** `qkdsim/` (simulator) · `experiments/` (E1–E7) · `results/` (CSVs) · `figures/` (PDF+PNG)
**Protocol:** 24 h simulated horizon, **first 12 h discarded as warm-up**, common random numbers across policies, paired bootstrap CIs (20 000 resamples).
**Design frozen before any run:** [PHASE2_DESIGN.md](PHASE2_DESIGN.md). Parameter provenance: [PHASE1_LITERATURE_DOSSIER.md](PHASE1_LITERATURE_DOSSIER.md).

> Every number below was produced by the committed code. Nothing is transcribed from the earlier draft, whose figures were placeholders.

---

## E1 — Validation gate: **43/43 checks pass**

`python experiments/e1_validation.py` → exit 0. The gate blocks all downstream claims.

| Group | Checks |
|---|---|
| Rate model | ρ(e₀)=1 exactly; ρ(e)=0 for e ≥ e_abort; monotone decreasing below abort |
| Threshold physics | f=1.00 zero at **e≈0.110** (Shor–Preskill ~11% ✓); f=1.16 zero at **e≈0.099** (realistic EC *lowers* the cliff); e_abort=0.075 below both |
| Tokyo calibration | γ=3.4 gives **ρ(0.06)=0.098** — inside the measured 8–12% band; γ=1 gives 0.505 |
| Reservoir | starts at m_max; overflow **discards** (never exceeds m_max); cannot draw below m_min; READY/WARNING/CHARGING/EMPTY transitions correct |
| Accounting | AUTH_OFF = bare *D*; AUTH_ON = **750 bit/hop at D=256** (2.93×, vs Cambridge's measured 3.6×); <1% overhead at 1 Mbit blocks |
| Key conservation | Σ session debits == Σ store debits **exactly** (29 638 848.0 vs 29 638 848.0), both fail modes; key_bits == hops × cost_per_hop with 0 mismatches; G4 consumes zero quantum key; no negative reservoir |
| Degenerate | abundant key → 100% served at authorised floor, 0 violations; zero key → FAIL_DEGRADED 100% G4 / FAIL_CLOSED 100% blocked |
| **SECOQC Fig. 22** | 8192 bit/s OTP drains 3.5 MiB of a 5.5 MiB store in **t = 3584 s** vs the published ≈1 hour (reference arithmetic 3584 s) — **exact** |
| Common random numbers | identical arrival stream across policies at equal seed (352 vs 352 sessions); different seed differs |

The threshold check is worth keeping in the paper: **realistic error-correction inefficiency moves the information-theoretic cliff from 11.0% down to 9.9%**, and the deployed engineering abort (7.5%, from Tokyo's LDPC ladder) sits below both.

---

## E3 — Fail-closed vs fail-degraded under adversarial pressure  ⟵ **HEADLINE**

12 seeds · KAR routing · Δe = 0.05 per attacked link (e₀=0.03, so e_abort=0.075 is reached) · betweenness-guided adversary. Figure: `fig1_failmode`, `fig2_grade_composition`.

| mode | k | availability | blocked | G1 | G2 | G3 | G4 | forced below grade |
|---|---|---|---|---|---|---|---|---|
| FAIL_CLOSED | 0 | 0.8124 | 0.1876 | 0.041 | 0.590 | 0.369 | 0.000 | **0.000** |
| FAIL_CLOSED | 1 | 0.8264 | 0.1736 | 0.077 | 0.564 | 0.358 | 0.000 | **0.000** |
| FAIL_CLOSED | 2 | **0.3039** | 0.6961 | 0.166 | 0.508 | 0.326 | 0.000 | **0.000** |
| FAIL_CLOSED | 5 | **0.0000** | 1.0000 | — | — | — | — | — |
| FAIL_DEGRADED | 0 | **0.9733** | 0.0267 | 0.034 | 0.659 | 0.308 | 0.000 | 0.166 |
| FAIL_DEGRADED | 1 | **0.9733** | 0.0267 | 0.065 | 0.607 | 0.299 | 0.029 | 0.157 |
| FAIL_DEGRADED | 2 | **0.9733** | 0.0267 | 0.052 | 0.174 | 0.100 | **0.675** | **0.690** |
| FAIL_DEGRADED | 5 | **0.9733** | 0.0267 | 0.000 | 0.000 | 0.000 | **1.000** | **1.000** |

**The exchange rate, stated exactly.** The same adversary budget buys either denial or downgrade, and the transition is a cliff, not a slope:

- **k = 2** (2 of 9 links): fail-closed availability collapses **0.812 → 0.304**; fail-degraded holds availability at 0.973 and instead pushes **69.0%** of entitled traffic below its authorised grade, with the PQC-only share jumping 0.029 → **0.675**.
- **k = 5**: fail-closed reaches **total denial** (availability 0.000); fail-degraded reaches **total assurance loss** (100% G4, 100% forced below grade) at unchanged availability.
- Fail-closed's forced-degradation column is **identically zero by construction** — it refuses rather than degrades. That is the point of the comparison, not a missing measurement.

Mechanism, verified: the two highest-betweenness links (`BDE1–BDE2`, `REL1–BDE1`) are the only quantum-viable routes into BDE1, so suppressing both severs quantum key to **2 of 3 forward posts** while FWD3 remains reachable via `BASE–REL2–BDE2–FWD3`. Hence the 1/3 availability floor under fail-closed. *Suppressing 2 of 9 links is sufficient.*

---

## E2 — Does the van Duijn null survive? **Yes, and worse than that.**

12 seeds, paired bootstrap on common seeds. Figure: `fig4_policy_pareto`.

### Under FAIL_DEGRADED (k=0)

| policy | availability | blocked | forced | hops | key (Mbit/12 h) |
|---|---|---|---|---|---|
| SP | 0.9733 ± 0.0074 | 0.0267 | — | 3.060 | 436.8 |
| KAR | 0.9733 ± 0.0074 | 0.0267 | — | 3.083 | 463.7 |
| KAR+CAF | 0.9733 ± 0.0074 | 0.0267 | — | 3.107 | 398.7 |

Paired Δ vs SP: availability **+0.0000, CI [+0.0000, +0.0000]** for both — *not significant, and exactly zero*. Key: KAR **+27.0 Mbit [+25.3, +28.9] SIGNIFICANT**; KAR+CAF **−38.1 Mbit [−40.5, −35.7] SIGNIFICANT**.

> **Finding 1.** Once a post-quantum fallback exists, routing policy has **no effect whatsoever on availability** — availability is set by connectivity and the fallback, not by key-awareness. The metric the entire key-aware-routing literature reports (service rejection / blocking) becomes **degenerate**. Routing then differs only in key expenditure and latency.

### Under FAIL_CLOSED (k=0)

| policy | availability | blocked | forced below ITS | hops | key (Mbit/12 h) |
|---|---|---|---|---|---|
| SP | **0.8392** ± 0.0078 | 0.1608 | 0.3569 | 3.062 | 437.8 |
| KAR | **0.8124** ± 0.0081 | 0.1876 | 0.3687 | 3.086 | 464.1 |
| KAR+CAF | **0.5092** ± 0.0080 | 0.4908 | **0.0000** | 3.128 | 399.3 |

Paired Δ vs SP: KAR availability **−0.0268, CI [−0.0293, −0.0243] SIGNIFICANT**; KAR+CAF **−0.3299, CI [−0.3333, −0.3264] SIGNIFICANT**.

> **Finding 2 (counterintuitive, and it survives scrutiny).** Key-aware routing is **significantly *worse*** than shortest path on availability: −2.7 percentage points. Mechanism: KAR selects marginally longer paths (3.086 vs 3.062 hops) and the trusted-relay hop multiplier converts that into **+6.0% key expenditure**, which in a key-scarce network means fewer sessions served. Per-session time-to-key optimisation is **globally counterproductive**. This runs against the field-level headline that key-aware dynamic routing reduces service rejection by 25–40%.

> **Finding 3 (a clean Pareto trade).** Class-aware reservation floors convert availability into assurance: availability **0.839 → 0.509** (−33.0 pp) in exchange for forced-below-ITS **0.357 → 0.0000**. Every session it does serve is served with an information-theoretically delivered key. A designer must choose where on this curve to sit; there is no free improvement.

---

## E6a — Is Finding 2 a tuning artifact? **No.**

The obvious objection is that KAR's hop penalty is mispriced. Swept it (8 seeds, FAIL_CLOSED, k=0):

| routing | hop penalty | availability | hops | key (Mbit) | paired Δ vs SP [95% CI] |
|---|---|---|---|---|---|
| SP | — | 0.8393 ± 0.0058 | 3.064 | 438.6 | reference |
| KAR | 0.0 | 0.8123 | 3.088 | 464.2 | −0.0270 [−0.0298, −0.0239] SIG |
| KAR | 0.5 | 0.8123 | 3.087 | 464.2 | −0.0270 [−0.0298, −0.0239] SIG |
| KAR | 5.0 | 0.8123 | 3.087 | 464.2 | −0.0270 [−0.0298, −0.0239] SIG |
| KAR | 50.0 | 0.8135 | 3.086 | 463.3 | −0.0259 [−0.0288, −0.0227] SIG |
| KAR | 1000.0 | 0.8386 | **3.065** | **440.0** | −0.0007 [−0.0013, −0.0002] SIG |

**No penalty restores KAR ≥ SP.** As the penalty grows, KAR *degenerates into* SP (hops 3.065 ≈ 3.064, key 440.0 ≈ 438.6) — the best it can do is abandon key-awareness entirely. The effect is small in absolute terms (2.7 pp) but statistically unambiguous under common random numbers.

---

## E5 — When does the literature's bare *D·n* key-cost law fail?

Wegman–Carter authentication costs *k* bits per authenticated message and only **logarithmically** in message length, so the answer is a function of relay block size. Figure: `fig5_auth_overhead`.

### (a) Analytic crossover

| D (bit) | cost/hop | factor | regime |
|---|---|---|---|
| 256 | 750 | **2.930×** | dominated by authentication |
| 512 | 1 006 | 1.965× | material |
| 1 024 | 1 518 | 1.482× | material |
| 2 048 | 2 542 | 1.241× | material |
| 8 192 | 8 686 | 1.060× | negligible |
| 144 000 | 144 494 | 1.003× | negligible |
| 1 000 000 | 1 000 494 | 1.000× | negligible |

Both published anchors sit in the top rows: SECOQC measured **~91%** of a 256-bit-rekey AES VPN's key consumption as ITS authentication; Cambridge measured **3.6×** for a ~400-bit relayed global key.

### (b) Operational consequence, by workload

| workload | law | key (Mbit) | availability | forced |
|---|---|---|---|---|
| OTP-dominated | bare *D·n* | 464.3 | 0.9726 | 0.159 |
| OTP-dominated | with auth | 463.8 | 0.9726 | 0.165 |
| small-block | bare *D·n* | **65.4** | 0.9655 | 0.000 |
| small-block | with auth | **191.7** | 0.9655 | 0.000 |

> **Finding 4, bounded honestly.** The bare law understates key consumption by **2.93×** for small-block rekey traffic and by **1.00×** when large OTP sessions dominate. In our formation this does **not** change service outcomes in either regime — so it is a **capacity-planning error, not a service error**. It matters because the modal deployed workload *is* small-block: 256 bit per minute per encryptor (SwissQuantum, IDQ Geneva, ADVA), and 1 key/s per 800 Gbps channel in the Ciena + Toshiba + JPMorgan deployment.

---

## E4 — Downgrade-forcing cost *k\*(φ)* vs relay-chain depth

6 seeds · 624 configurations · parametric chain of depth *d* with one lateral alternate. Metric: **forced** degradation — sessions *entitled* to an ITS-delivered key (authorised floor ≥ G2) that were served below it. Figure: `fig3_forcing_cost`.

| *d* | links | nominal forced | betweenness *k\**(0.25) | betweenness *k\**(0.5) | **min-cut *k\**(0.25)** | **min-cut *k\**(0.5)** |
|---|---|---|---|---|---|---|
| 1 | 1 | 0.000 | 1 | 1 | 1 | 1 |
| 2 | 5 | 0.000 | 3 | 3 | **2** | **2** |
| 3 | 7 | 0.000 | 4 | 4 | **2** | **2** |
| 4 | 9 | 0.000 | 5 | 5 | **2** | **2** |
| 5 | 11 | 0.000 | 6 | 6 | **2** | **2** |
| 6 | 13 | 0.000 | 7 | 7 | **2** | **2** |

> **Finding 5.** The downgrade-forcing cost depends overwhelmingly on **assumed adversary sophistication**, not on the network. A greedy, betweenness-guided adversary needs **k\* = d + 1** links, growing linearly with chain depth. An optimal **min-cut** adversary needs **exactly 2 links at every depth**, because the primary and alternate paths are edge-disjoint. At d = 6 that is 7 links versus 2 — **a 3.5× overstatement of resilience** if only the greedy adversary is reported. Deeper relay chains buy *no* additional protection against a competent adversary.

Two problems were found by interrogating the first pass and **fixed rather than reported**:

1. The greedy adversary wastes budget on the *already-severed* primary path before touching the alternate — hence the spurious d+1 law. Both targeting models are now first-class (`AdversaryConfig.targeting`).
2. The original metric (`below_its`) counted LOG traffic whose authorised floor is *already* G3, crediting the adversary before it acted. The corrected metric shows **nominal forced degradation = 0.000 at every depth**, so every point on the curve is attributable to the attack.

---

## E7 — Policy-space audit (ML): **the heuristic wins, and that is the result**

Direct policy search (cross-entropy method, 12 iterations × 20 candidates) over a **12-cell state→grade lookup table**; every candidate scored by full simulation rollouts, so the sequential key economy is evaluated exactly rather than approximated by an invented opportunity-cost term. Policy space 2.44 × 10⁸. CPU only, 738 s. Figure: `fig6_policy_audit`.

### Full-horizon evaluation (24 h, 8 seeds)

| policy | J | availability | ITS share | floor violations | C2 below ITS | key (Mbit) |
|---|---|---|---|---|---|---|
| heuristic | **1.1287** | 0.8123 | 0.6327 | 0.0000 | 0.0000 | 464.2 |
| searched (shielded) | 1.0774 | 0.9726 | 0.6048 | 0.3952 | 0.0000 | 373.6 |
| searched (unshielded) | 1.3734 | 0.9726 | 1.0000 | 0.1985 | 0.0000 | **42.0** |

### Out-of-distribution stress — heuristic wins **7 / 7**

| condition | heuristic J | searched J | Δ | winner |
|---|---|---|---|---|
| SKR ×0.25 | 1.0932 | 0.9888 | −0.1044 | heuristic |
| SKR ×0.50 | 1.1034 | 1.0198 | −0.0836 | heuristic |
| SKR ×2.00 | 1.2030 | 1.1989 | −0.0041 | heuristic |
| adversary k=2 | 0.6374 | 0.5543 | −0.0831 | heuristic |
| adversary k=4 | 0.6374 | 0.5543 | −0.0831 | heuristic |
| dual outage | 0.9658 | 0.8628 | −0.1029 | heuristic |
| demand ×2 | 1.1040 | 1.0034 | −0.1006 | heuristic |

> **Finding 6 (the pre-committed null — holding at the stated weights, and weight-dependent).** The heuristic attains **104.8%** of the best shielded policy found and wins on **every** out-of-distribution condition at λ = 0.5, *w* = 0.5.
>
> **But the null is not weight-robust, and checking mattered.** The policies do not order componentwise: the searched policy wins **availability 0.9726 vs 0.8123**, paying with 39.5% forced downgrades and 0.6048 vs 0.6327 ITS share. Solving *J*_h > *J*_s gives the heuristic winning **iff λ > 0.370** (at *w* = 0.5; 0.406 at *w* = 0, 0.335 at *w* = 1, 0.264 at *w* = 2).
>
> **Report the indifference point as the result.** λ\* ≈ 0.37 asks the operator a decidable question: *is one forced downgrade of entitled traffic worth more or less than 0.37 of a served session?* Above it, the simple heuristic is correct and no learned policy is needed; below it, the network should run closer to the searched policy and accept the assurance loss. Locating λ\* required the search, because it depends on the achievable trade-off surface — a property of the key economy, not of the objective. This is a better contribution than a beaten baseline.

> **Finding 7 — a methodological warning that generalises beyond this paper.** The searched policy *beat* the heuristic on the 6 h training horizon (J 1.4591 vs 1.2978) and *lost* on the 24 h evaluation horizon (1.0774 vs 1.1287). The reason is diagnostic: the training horizon sat **inside the 12 h drain-from-full transient**, where free-space key is still abundant. **Training a policy on a QKD network simulator inside its reservoir transient teaches the wrong regime.** Anyone applying RL to key-scarce QKD control must verify that training spans steady state.

> **Finding 8 — the ablation exposed a specification gap in our own policy, which is more valuable than a performance number.** The unshielded search scored highest (J 1.3734) by cutting key consumption from 464 to **42 Mbit — an 11× reduction — while keeping 100% of traffic on ITS-delivered key.** It achieved this by serving OTP-entitled ISR traffic at G2 (256 bit) instead of G1 (144 000 bit): still information-theoretically *delivered*, but a violation of ISR's authorised one-time-pad floor. **The shield constrained only command traffic, so it did not prevent this**, and C2-below-ITS is 0.0000 in *both* arms. The ablation therefore does **not** measure "the price of the C2 guarantee" — it demonstrates that an assurance policy specifying a floor for one class only is gameable, and that an objective which prices floor violations below key savings will be gamed. Per-class floors must be specified and priced explicitly.

### The searched policy, effective (post-shield) — auditable by construction

The policy class is a 12-cell table, so no distillation is needed. The shield intervened in **1 of 12** states; the effective policy differs from the heuristic in 8.

| state | heuristic | searched (raw) | searched (effective) | note |
|---|---|---|---|---|
| C2 · starved | G3 | G1 | G1 | differs |
| C2 · warning | G2 | G2 | G2 | |
| C2 · mid | G2 | **G4** | **G1** | **shield clipped** |
| C2 · ample | G2 | G2 | G2 | |
| ISR · starved | G2 | G3 | G3 | differs |
| ISR · warning | G1 | G4 | G4 | differs |
| ISR · mid | G1 | G1 | G1 | |
| ISR · ample | G1 | G1 | G1 | |
| LOG · starved | G4 | G3 | G3 | differs |
| LOG · warning | G3 | G4 | G4 | differs |
| LOG · mid | G3 | G2 | G2 | differs |
| LOG · ample | G3 | G2 | G2 | differs |

Reporting the **raw** table would let a reader conclude that command traffic is served at G4; it never is. The shield projects it to G1 before it reaches the key economy (`results/e7_policy_table_effective.csv`).

---

## Cross-cutting findings worth foregrounding in the paper

1. **The fail-closed / fail-degraded exchange rate is a cliff at k=2 of 9 links**, and both endpoints are total: complete denial or complete assurance loss for the same budget.
2. **A post-quantum fallback makes the routing literature's headline metric degenerate.** Blocking stops responding to routing entirely (paired Δ exactly 0.0000, CI [0, 0]).
3. **Key-aware routing can be actively harmful** in a key-scarce trusted-relay network (−2.7 pp availability, +6.0% key), and **no hop-penalty setting repairs it** — the best it can do is degenerate into shortest path.
4. **Reservation floors trade 33 pp of availability for zero forced ITS loss** — a genuine, quantified Pareto choice.
5. **Reported resilience depends overwhelmingly on assumed adversary sophistication**: k\* = d+1 for a greedy adversary versus a flat 2 for a min-cut adversary. Deeper relay chains buy no protection against a competent attacker.
6. **A formation deploying with topped-up reservoirs runs ~12 h before the free-space key economy binds at all** — the same drain-from-full dynamic SECOQC measured in Fig. 22. Results measured inside that transient are dominated by the initial fill; the original draft's 4 h horizon left the stores at ~59% of capacity.
7. **The learned policy loses to the heuristic 7/7 out of distribution**, and the ML section's real yield is two negative results: training inside the reservoir transient teaches the wrong regime, and a single-class assurance floor is gameable (11× key saving by downgrading OTP-entitled traffic).

## Suggested figure order for a 6-page IEEE submission

| Fig | File | Carries |
|---|---|---|
| 1 | `fig1_failmode` | The headline exchange rate: availability vs assurance loss under swept pressure, both modes |
| 2 | `fig2_grade_composition` | Grade composition of served traffic — the operator-facing indicator standards lack |
| 3 | `fig3_forcing_cost` | Downgrade-forcing cost vs chain depth, greedy vs min-cut adversary |
| 4 | `fig4_policy_pareto` | Availability against key spend: KAR spends more for less |
| 5 | `fig5_auth_overhead` | Where the bare *D·n* law fails (block-size crossover) |
| 6 | `fig6_policy_audit` | Policy-space audit, out-of-distribution |

All figures are vector PDF at IEEE column width, use a CVD-validated 4-hue palette with **mandatory secondary encoding** (distinct linestyle + marker + hatch per series) so identity survives greyscale print, and carry no dual axes.

## Reproduction

```
python experiments/e1_validation.py                       # gate: 43/43, exit 0
python experiments/run_experiments.py --seeds 12 --only e2,e3,e5
python experiments/run_experiments.py --seeds 6  --only e4
python experiments/e6_hop_penalty.py
python experiments/e7_policy_audit.py --iters 12 --pop 20
python experiments/e7_effective_table.py
python experiments/make_figures.py
```

Deterministic given the seeds. Cap worker counts at 8: spawning ~15 concurrent
numpy-importing workers exhausted process resources on this host.

## E6b — Sensitivity, and a bug the sensitivity caught

Running the sensitivities I had *claimed* in the design produced the two most consequential corrections of the whole project.

### The cliff is conditional on the adversary being able to abort a link

At `e_abort = 0.075` with Δe = 0.05 on e₀ = 0.03, the injected QBER (0.08) crosses the abort threshold and the link produces **zero** key — hence the k=2 cliff. At `e_abort = 0.11` the same injection does **not** cross, the link merely degrades, and the headline largely vanishes:

| γ | e_abort | mode | avail k=0 | avail k=2 | forced k=0 | forced k=2 |
|---|---|---|---|---|---|---|
| 1.0 | 0.075 | FAIL_CLOSED | 0.8102 | **0.3020** | 0.0000 | 0.0000 |
| 1.0 | 0.075 | FAIL_DEGRADED | 0.9703 | 0.9703 | 0.0000 | **0.6765** |
| 1.0 | 0.110 | FAIL_CLOSED | 0.8102 | **0.7929** | 0.0000 | 0.0000 |
| 1.0 | 0.110 | FAIL_DEGRADED | 0.9703 | 0.9703 | 0.0000 | **0.0018** |
| 3.4 | 0.075 | FAIL_CLOSED | 0.8102 | **0.3020** | 0.0000 | 0.0000 |
| 3.4 | 0.075 | FAIL_DEGRADED | 0.9703 | 0.9703 | 0.0000 | **0.6765** |
| 3.4 | 0.110 | FAIL_CLOSED | 0.8102 | 0.7668 | 0.0000 | 0.0000 |
| 3.4 | 0.110 | FAIL_DEGRADED | 0.9703 | 0.9703 | 0.0000 | 0.0433 |

> **Finding 9 — the result is insensitive to γ and sharply sensitive to e_abort, and that is the useful part.** γ (the 5× calibration ambiguity that most worried me) changes almost nothing: 0.3020 at both values. The abort threshold changes everything — and the Δe sweep below shows exactly why, with a clean predictive form. Had the sensitivity been asserted rather than run, the paper would have shipped a headline conditional on an unexamined parameter.

### The forcing cost is two-dimensional, with a sharp two-threshold law

Sweeping the per-link injection Δe at both abort thresholds (k = 2, γ = 1.0, 6 seeds):

| e_abort | needs Δe ≥ | Δe=0.03 | 0.04 | **0.05** | 0.06 | **0.08** | 0.10 |
|---|---|---|---|---|---|---|---|
| 0.075 | **0.045** | 0.7982 | 0.7956 | **0.3020** | 0.3020 | 0.3020 | 0.3020 |
| 0.110 | **0.080** | 0.7982 | 0.7956 | 0.7929 | 0.7807 | **0.3020** | 0.3020 |

*(fail-closed availability; fail-degraded forced assurance loss transitions identically, 0.0000 → 0.6765)*

> **Finding 10 — the law.** The cliff lands **exactly at Δe ≥ e_abort − e₀** in both cases, and above it the collapse is *total and identical* (0.3020 / 0.6765) no matter how much further the adversary pushes. So the downgrade-forcing cost has two thresholds, both of which must be met:
>
> **(a) per-link capability** Δe ≥ e_abort − e₀ , and **(b) budget** k ≥ the minimum edge cut.
>
> Below either, essentially nothing happens; above both, the outcome saturates immediately. This is directly actionable for a defender: raising the abort threshold from 0.075 to 0.11 raises the injection an adversary must achieve from 0.045 to 0.080 — a **78% increase in required adversary capability** — obtainable through better reconciliation efficiency rather than more key rate.

### The post-quantum fallback is immune only to *quantum*-channel attacks

Fail-degraded availability is constant at 0.9703 across every budget under QBER injection — not because the fallback is resilient, but because **a link in ABORT still carries a pristine classical channel, and ML-KEM needs only that channel.** Denying the classical channel instead forces OUTAGE and removes the fallback:

| attack (k=2, Δe=0.05) | FAIL_CLOSED avail | FAIL_DEGRADED avail | FD forced loss |
|---|---|---|---|
| QBER injection | 0.3020 | **0.9703** | 0.6765 |
| **classical-channel denial** | 0.2963 | **0.3127** | 0.0000 |

> **Finding 11.** Classical-channel denial collapses fail-degraded availability from 0.9703 to **0.3127**, leaving it just **1.6 points** better than fail-closed. **The entire advantage of degrading gracefully is conditional on the classical channel surviving.** Reporting only QBER injection would materially overstate the fallback's value. Forced loss is 0.0000 under this attack because the severed posts are blocked outright rather than downgraded — there is no channel left on which to downgrade them.
>
> *Reading note: the A3 block in `results/e6b.log` averages its QBER-injection rows over the whole Δe sweep and so understates them; the figures above are taken at Δe = 0.05, matching Table I.*

### The bug that finding caught

The first classical-denial run returned availability **0.0000 for both fail modes**, which is impossible — one forward post remains reachable after two links are cut. Diagnosis: `_tick_outages` skipped recovery for any link whose `outage` flag was set whenever `deny_classical` was enabled, so every *stochastic* outage also became permanent and the network died over a 24 h horizon. Fixed by testing membership of an explicit adversary-held set (`Simulator._adv_links`). Gate re-run: 43/43.

**This is the clearest argument for the validation-first discipline in this project.** The bug produced a plausible number (total denial under a denial attack *sounds* right), sat in a code path no unit test covered, and was caught only because a sensitivity run returned a value that was impossible on inspection.

## E8 — Validation against four published measurements, and what failing two of them taught

Reproducing one measurement is a weak validation claim, and the obvious alternative — cross-validating against another simulator — is unavailable: SeQUeNCe, NetSquid and QuISP contain no trusted-relay or key-pool model, so they cannot check a key-economy simulator. Three further published measurements were already sitting in our own parameter table.

| Check | Measured | Model | Verdict |
|---|---|---|---|
| **V1** SECOQC key-store drain [Peev 2009 Fig. 22] | 3.5 MiB at 8192 bit/s ≈ 1 h | **3584 s** vs reference 3584 s | **PASS, exact** |
| **V2** Cambridge relay overhead [Dynes 2019] | **3.69×** the ~400-bit key | 2.23× | **FAIL, low by 1.65×** |
| **V3** SECOQC AES-VPN auth share [Peev 2009 §5.1.1 fn.27] | **91.2%** (5824 bit/round, 512 cipher) | 65.9% (750 bit/hop) | **FAIL, low by 5.4×** |
| **V4** Hefei OTP voice concurrency [Chen 2021] | 11 simultaneous pairs | 1.2–12.6 predicted range | **PASS, untuned** |

> **Finding 12 — two failures, one cause, and it is our own parameter.** Both disagreements run the same direction. Solving each measurement for the number of authenticated messages per key delivery gives **n_auth ≈ 6.6** for a relay hop (V2) and **≈ 40** for an application-level tunnel (V3), against the **2** we had assumed from the mutual-authentication argument. These are not in conflict — they measure different layers. **Our n_auth = 2 was a lower bound, not a measurement, and the per-hop key cost is correspondingly optimistic.**
>
> This *strengthens* the E5 finding rather than weakening it: calibrated to Cambridge, the understatement in the literature's bare *D·n* law grows from **2.93× to 5.41×** for 256-bit blocks. The error we identified is larger than we originally reported.

### E6c — does the headline survive the recalibration?

Higher `n_auth` means higher per-hop cost means tighter scarcity, so the headline had to be re-checked before it could be reported. Sweeping `n_auth ∈ {2, 7, 20, 40}` (8 seeds):

| n_auth | cost/hop at D=256 | source | FC avail k=0 | FC avail k=2 | FD forced k=2 |
|---|---|---|---|---|---|
| 2 | 750 bit | assumed lower bound | 0.812 | **0.302** | 0.678 |
| **7** | **1385 bit** | **Cambridge, calibrated** | 0.806 | **0.299** | 0.678 |
| 20 | 3036 bit | intermediate | 0.795 | 0.292 | 0.678 |
| 40 | 5576 bit | SECOQC app. tunnel | 0.764 | 0.281 | 0.679 |

> **Finding 13 — the headline is robust to a 7.4× change in per-hop key cost.** Fail-closed availability at k=2 moves only 0.302 → 0.281 across the whole range, and fail-degraded forced loss is flat at 0.678. Aggregate key consumption barely moves either (~215 Mbit throughout), and the reason is instructive: **ISR's 144 kbit one-time-pad sessions dominate the key budget**, so a term of at most a few thousand bits per hop is lost in the noise. The authentication correction therefore matters for **capacity planning in small-block deployments** and not for this paper's headline — the same workload-dependence E5 already reported.

**Why this matters methodologically.** The validation was capable of failing, and did. Four clean passes would have been a weaker result than three passes plus one quantified, direction-known discrepancy, because a suite that cannot fail demonstrates nothing about the model.

## Known limitations to state in the paper

Above-the-physics abstraction (per-link secret-key rates are parameterised inputs, not simulated photonics). Two γ variants reported because the measured degradation (Tokyo, 8–12% at QBER 5–7%) and the asymptotic BB84 expression (≈50% at the same QBER) disagree; the gap is published as a sensitivity rather than resolved. Relay nodes assumed trusted — node compromise appears only as an availability event. Detector blinding extracts key **without raising QBER** and is therefore invisible to any QBER-driven model, including this one; stated explicitly. Single formation plus one parametric chain family. No published FSO hard-outage duration or frequency distribution exists, so those parameters are swept, not asserted. Reservoir capacity likewise has no vendor-published value in ~15 datasheets surveyed.
