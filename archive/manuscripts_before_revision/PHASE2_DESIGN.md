# PHASE 2 — Frozen System Design & Experiment Protocol

**Paper:** *Fail-Closed or Fail-Degraded? Quantifying Forced Security-Grade Loss in Contested Multi-Hop QKD Networks*
**Scope:** reduced systems scope + ML policy-space audit. Terrain-correlated outage model deferred to the journal version.
**Status:** FROZEN before implementation. Result tables below are deliberately blank — they are filled only after the runs, to prevent unconscious cherry-picking (Report.md §VII.4).

Every parameter traces to [PHASE1_LITERATURE_DOSSIER.md](PHASE1_LITERATURE_DOSSIER.md). Nothing is invented.

---

## 1. Research question

Standards permit degradation: **ITU-T Y.3803 cl. 8.2.3 / Req_KM 7** — "If the necessary number of keys for OTP-encrypted key relay is not available, a backup method with symmetric key cipher such as AES can be used," with the method recorded in KMA metadata. Field deployments do it (Makris ECOC 2024; Y.3803-consistent AES-256 fallback).

Security engineering rejects it: **Spooren et al., IEEE QCNC 2026** — "a fail-safe mechanism prevents **downgrade attacks**, where the data tunnel is interrupted after a defined time." Fail-closed by design.

**Nobody has quantified the exchange rate between these two positions.** We do, and we add the adversary's side of it:

> **Q1.** Under adversarial pressure, what does fail-degraded operation buy in availability, and what does it cost in delivered security grade?
> **Q2.** How cheaply can an adversary *force* a target fraction of traffic below information-theoretically-delivered key? (**downgrade-forcing cost**)
> **Q3.** Does the key-aware-routing null result of van Duijn et al. (ONDM 2024) survive under contested conditions and a grade-aware objective?
> **Q4.** How much do the literature's bare `D·n` key-cost models understate consumption by omitting relay authentication?

---

## 2. Grade lattice

Cost-decreasing, maps onto Y.3803's OTP→AES fallback and onto QuLore's L1–L4. **Never called "hybrid" except for G3**, which genuinely combines (draft-ietf-tls-hybrid-design §1.2; NIST SP 800-227 §4.6).

| Grade | Name | Quantum key demand per session | Security of payload | Anchor |
|---|---|---|---|---|
| **G1** | OTP / ITS | **= payload bits** | information-theoretic | Shannon 1949 §10, `R_M L_M ≤ R_K L_K` (p. 682) |
| **G2** | QKD-keyed symmetric | **256 bit** per rekey | computational payload, **ITS-delivered key** | Y.3803 Req_KM 7; all field deployments |
| **G3** | Hybrid QKD ⊕ ML-KEM | **128 bit** + ML-KEM-768 | computational, ≥ strongest component | QuLore L3; NIST SP 800-227 §4.6 combiner |
| **G4** | ML-KEM only | **0 bit** | computational only | QuLore L4; FIPS 203 |

ML-KEM-768 wire cost (G3, G4): encapsulation key 1184 B + ciphertext 1088 B = **2272 B**, shared secret 32 B; setup latency parameter `pqc_setup_s`.
**Terminology:** the delivered attribute is the **assurance grade**, never "security level" (that means key *length* in DDKA-QKDN and key-*update period* in the RWTA literature).

**Per-flow authorisation floor.** Each traffic class carries an `authorised_floor` — the lowest grade policy permits. The controller serves at the best grade the key economy affords. If that is below the floor:
- **FAIL_CLOSED** → block the session (Spooren's position).
- **FAIL_DEGRADED** → serve anyway, record a **floor violation** as a first-class, operator-visible event (Y.3803's position, made auditable).

This authorisation model is specified by neither position today and is contribution 3.

---

## 3. Link model — four states

Per dossier §2.1. Two states (`NOMINAL`/`5% bad`) is indefensible: an adversary raising QBER pushes past the security threshold and the rate goes to **zero** (Alléaume et al., quant-ph/0701168).

| State | Rate | Trigger |
|---|---|---|
| NOMINAL | `R₀` | `e = e₀` |
| DEGRADED | `R₀ · ρ(e)` | `e₀ < e < e_abort` |
| ABORT | **0** | `e ≥ e_abort` (security abort; buffer drains) |
| OUTAGE | **0** | hard: LOS loss, fibre cut, **classical-channel denial** |

`ρ(e) = [ max(0, 1 − f·H₂(e) − H₂(e)) / (1 − f·H₂(e₀) − H₂(e₀)) ]^γ`, `H₂` binary entropy, `f = 1.16` (EC inefficiency).

- **`γ = 1`** — asymptotic BB84 physics (Ma et al., *PRA* 72:012326, Eq. 1 form). Yields `ρ(0.06) ≈ 0.50`, cliff at `e ≈ 0.107` ✓ consistent with the ~11% asymptotic threshold.
- **`γ = 3.4`** — calibrated to the only measured degraded-link datapoint: Tokyo All-Vienna BBM92 at QBER 5–7% delivered 0.25 kbps against 2–3 kbps nominal ⇒ **8–12% of nominal**. `0.50^3.4 ≈ 0.10` ✓.
- **Both are reported.** The gap between them (50% vs 10% at QBER 6%) is a real, honest uncertainty — finite-key effects and system specifics — and it becomes a sensitivity row, not a hidden assumption.

`e_abort = 0.075` default (Tokyo's deployed NEC LDPC ladder has rungs only at <3.5/5.5/7.5% — **no rung above 7.5%**); `0.11` as sensitivity (Rath arXiv:2603.27278; Shor–Preskill).

**Two states bypass QBER entirely — modelled separately, and stated as a strength:** classical post-processing channel denial (Mehic: blocking routing or post-processing packets "would disable the link") and detector blinding (Lydersen, *Nat. Photonics* 4, 2010 — full key extracted **without raising QBER**, so QBER-driven models are blind to it by construction).

---

## 4. Key accounting — with authentication

`cost_per_hop(D) = D + M_meta + n_auth · tag_bits`; total over an `h`-hop path = `h · cost_per_hop(D)`.

| Term | Default | Provenance |
|---|---|---|
| `M_meta` | **240 bit** (30 B) | Y.3803 Note 2: relay is in units of a *key file*, metadata "typically a few 10s of bytes", normally OTP-encrypted too |
| `tag_bits` | **127 bit** | Walenta arXiv:1309.2583 (127-bit tag per 2²⁰ bits, ε_AUT ≈ 10⁻³³); `ε_au = n·2^(−k+1)` from Fung/Ma/Chau Eq. 9 |
| `n_auth` | **2** | mutual authentication consumes two independent one-time keys per round (De Lazzari arXiv:2603.25496) |

⇒ at `D = 256`: **750 bit/hop = 2.93× the naive `D`.** Cambridge measured **3.6×** (1440 bit of link key per ~400-bit relayed global key). Same order — we report both and cite Cambridge as the empirical check.

**`AUTH_OFF` ablation** (`cost = D`) is a headline experiment, not a footnote: SECOQC measured **~91% of a live AES-VPN's key consumption was ITS authentication, not cipher key** (728 B per 20 s round; only 2×256 bit are cipher key). Q4 quantifies the resulting error in the literature's standard model.

**Invariants asserted in code** (dossier §2.5): `D` charged on every hop, never once; one debit per link per relay (not per endpoint); source spends no quantum key to *create* the key (local RNG permitted, Y.3803); relay failing at hop `k` has already spent hops `1…k−1`; no route may pass a key back to the calling KMS (ETSI 020 `invalid_routing`).

---

## 5. Key reservoir

QKDNetSim `QKDBuffer` semantics, adopted verbatim for citability. **Units: bits.**

| Field | Default | Provenance |
|---|---|---|
| `M_min` | **1 048 576** | QKDNetSim shipped `secoqc_p2p_qkd_system.cc` |
| `M_thr` | **11 324 620** | same |
| `M_max` | **52 428 800** (50 Mibit) | same |

States: `READY` (`M_cur ≥ M_thr`) · `CHARGING` (below thr, above min, rising) · `WARNING` (below thr, above min, otherwise) · `EMPTY` (`M_cur ≤ M_min`). **Overflow discards generated key** (`AddNewContent` hard-rejects) — not queued.

`M_min` doubles as the **authentication reserve**: SECOQC held a 2 MiB floor "to ensure that … enough key remains in the store to authenticate the future communication on the classical channel." This is a published, non-QoS floor rationale — no reviewer can call it arbitrary, and it is a *different* argument from Mehic's per-class QoS floor.

Swept over **1 Mbit – 1 Gbit** (QKDNetSim's own code-default range), reported against the dimensionless **`C / (R·T)`** so conclusions are scale-free. The 64 kbit of the original draft is ~3 orders of magnitude below every published value and is dropped.

---

## 6. Traffic

All demands grounded — the original 32 kbit "OTP-grade imagery" was incoherent (4 kB is not an imagery product) and is replaced by measured anchors.

| Class | λ (s⁻¹) | Payload | `authorised_floor` | Deadline | Prio | Anchor |
|---|---|---|---|---|---|---|
| **C2** command | 0.05 | 2 048 bit | **G2** | 5 s | 1 | 256-bit AES rekey ≈ modal industry unit (SwissQuantum/IDQ/ADVA: 256 bit per 60 s) |
| **ISR** OTP voice/imagery | 0.02 | **144 000 bit** | **G1** | 30 s | 2 | Hefei 46-node QMAN: real OTP voice at **2.4 kbps**, 60 s session |
| **LOG** bulk | 0.03 | 320 000 bit | **G3** | 120 s | 3 | Hefei: OTP file transfer at **320 kbps** |

Quantum-key demand is then grade-dependent per §2 — ISR at G1 needs 144 kbit **× hops × 2.93** and is the genuine scarcity driver; C2 at G2 needs 256 bit × hops × 2.93 and is cheap. That asymmetry is the paper's economic story and it is now measured rather than asserted.

Arrivals Poisson (the literature's convention — Cvitić survey; flagged as convention, not measurement, and swept for burstiness in the OOD grid).

**Link rates:** fibre backbone **300 kb/s @ 10 dB** (Toshiba LD/MU datasheet); FSO hops **240 bit/s** (DRDO–IIT Delhi, >1 km entanglement, QBER <7% — *retrieve PIB PRID 2136702 before citing*); multi-hop national end-to-end sanity check **9.75–20.85 kbps** (CN-QCN measured).

---

## 7. Topologies

- **T1 — 9-node formation** (BASE, REL1, REL2, BDE1, BDE2, FWD1–3): main policy comparison. One fibre backbone segment, eight FSO hops of three grades. Concrete and illustrable.
- **T2 — parametric chain**, depth `h ∈ {1…6}`, with one lateral alternate path: the depth axis for Q2. Isolates the interaction between hop multiplier and adversarial pressure.

---

## 8. Adversary model — and the downgrade-forcing cost metric

The adversary cannot break QKD, so it attacks **availability to force a grade downgrade** — the incentive Schartner & Rass identified in 2010 and nobody has since measured.

**Action:** select `k` links (budget) and inject excess QBER `Δe` on each; optionally deny the classical channel instead.
**Interpretability:** `Δe` is in absolute QBER units, so "pressure" is physically meaningful and directly answers *"what does ×16 mean?"* — the unanswerable question in the original draft. `e₀ = 0.03` nominal; `Δe = 0.045` reaches `e_abort`.

> **Downgrade-forcing cost `k*(φ)`** = the minimum number of links an adversary must suppress to push a fraction `φ` of *served* sessions below G2 (below ITS-delivered key).

Reported as `k*(φ)` curves against chain depth `h` and against controller mode. Legible to a systems reviewer, and it is an attack-economics quantity, not a service metric — which is why it does not collide with Li et al.'s `maxNAR` (worst-case affected requests) or with the joint-routing paper's attack-success-probability.

**Differentiation to state explicitly in related work:** Li et al. place a single worst-case attack (no intensity sweep); Ghorab et al. sweep attacker pervasiveness on multipath (not grade-aware); the joint routing/relay-key-allocation paper measures compromise probability vs *trusted-node count* and reports diminishing returns — adjacent to our depth axis, so cite and separate.

---

## 9. Control policies

| Policy | Routing | Admission | Mode |
|---|---|---|---|
| `SP` | min hop | none | — |
| `KAR` | min bottleneck expected time-to-key + hop penalty | none | — |
| `KAR+CAF` | KAR | per-class reservation floors above `M_min` | — |
| × | | | `FAIL_CLOSED` / `FAIL_DEGRADED` |

`SP` and `KAR` are **reproduced baselines, cited not claimed** (van Duijn 2024; Johann JOCN 2024; Hao 2025; Yang 2018). Reservation floors are **cited to Mehic ToN 2020 `M_min` and Cheng/Sun/Ji 2011 QKRA**, not claimed as novel.
**Mandatory:** the ML section must beat **KAR**, not `SP`. Beating unweighted shortest path in 2026 is a strawman and will be named one.

---

## 10. Validation gate — runs before any result is believed

1. **Key conservation:** `Σ debits == Σ (h · cost_per_hop(D))` over all served sessions, exactly.
2. **Reservoir bounds:** never `< 0`, never `> M_max`; overflow accounted as discarded.
3. **Degenerate cases:** `R → ∞` ⇒ 100% served at G1; `R = 0` ⇒ 100% G4 under FAIL_DEGRADED, 100% blocked under FAIL_CLOSED.
4. **Cliff:** `ρ(e) = 0` for all `e ≥ e_abort`; `ρ(e₀) = 1`.
5. **⭐ SECOQC Figure 22 reproduction:** an 8192 bit/s OTP application drains **3.5 MiB of a 5.5 MiB keystore in ≈1 hour**, then reroutes. Target: our simulator reproduces the ≈3584 s drain time within a stated tolerance. *This is the answer to "why trust your simulator."*
6. **Common random numbers:** identical arrival streams and channel realisations across policies within each seed, then **paired** bootstrap CIs. Without CRN a 3–4 point service delta is partly noise.
7. **Cross-check:** reproduce QKDNetSim's 6-node SECOQC configuration once and report agreement.

---

## 11. Experiment protocol — tables frozen blank

**E1 — Validation.** All of §10. *(pass/fail table)*

**E2 — Does the van Duijn null survive? (Q3)**

| Policy | Served | Blocked | Mean TTK | p95 TTK | Key consumed | Paired Δ vs SP [95% CI] |
|---|---|---|---|---|---|---|
| SP | | | | | | — |
| KAR | | | | | | |
| KAR+CAF | | | | | | |

**E3 — Fail-closed vs fail-degraded (Q1)**

| Mode | Δe | Availability | G1 % | G2 % | G3 % | G4 % | Floor violations | Blocked |
|---|---|---|---|---|---|---|---|---|
| FAIL_CLOSED | 0 … 0.06 | | | | | | | |
| FAIL_DEGRADED | 0 … 0.06 | | | | | | | |

**E4 — Downgrade-forcing cost (Q2)**

| `h` | `k*(φ=0.1)` | `k*(0.25)` | `k*(0.5)` | FAIL_CLOSED equivalent (blocked fraction) |
|---|---|---|---|---|
| 1 … 6 | | | | |

**E5 — Authentication accounting error (Q4)**

| Model | Key consumed | Sessions served | Overstatement factor |
|---|---|---|---|
| `AUTH_OFF` (literature `D·n`) | | | — |
| `AUTH_ON` (ours) | | | |

**E6 — Sensitivity.** `γ ∈ {1, 3.4}` · `e_abort ∈ {0.075, 0.11}` · `C` over 1 Mbit–1 Gbit reported vs `C/(R·T)` · FSO rate ×{0.25, 0.5, 1, 2, 4}.

---

## 12. ML section — policy-space audit (IN SCOPE)

Framing: **learned policy as heuristic *auditor*, not replacement.** Learned routing is saturated (Johann *Photonics* 2026 GAT-DRL; Hao 2025; Xie 2025; Sharma 2023; Seok 2025; Zuo 2020) and learned admission is saturated in classical networking. What is open: **learned assurance-grade selection driven by ITS-key-reservoir exhaustion, per traffic class, under a hard shield.** Closest prior art is Premakumari et al. (*Sensors* 25:2056, 2025) — action = encryption level, but driven by a threat classifier, with no QKD, no relay, no classes.

**Claim, narrow and falsifiable:**
> Within model M, the hand-designed heuristics attain X% of the best policy discoverable in M under a hard constraint on command traffic; where the learned policy exceeds them, we extract the responsible rule.

- **Action:** joint `(next_hop, admit ∈ {accept, defer, reject}, grade ∈ {G1…G4})`. **The grade action is the whole point** — drop it and this collapses into saturated option (a).
- **Shield (hard, not a reward penalty):** deterministic action mask — C2 never below its authorised floor; no action may drive a reservoir below the reserve guaranteeing C2 continuity for horizon `H`. **Concede up front that the guarantee comes from the shield, verifiable by inspection; learning only searches inside it.**
- **Learner:** tabular Q-learning / 2-layer DQN over aggressively discretised state (node, destination, reservoir occupancy in 4–5 buckets, class, current grade). **CPU only.**
- **Distillation:** VIPER/DAGGER → CART depth ≤ 4, **tree printed in the paper**. Report fidelity and retained performance. The auditable rule set is the artifact a DRDO reviewer values.
- **Evaluation is OOD, not nominal:** SKR ×{0.25, 0.5, 1, 2}; shifted demand mix and burstiness; single and dual link failure; one compromised node. **If the heuristic degrades more gracefully than the learned policy, we publish that** — a stronger, more credible result than any win.
- **Mandatory ablation:** shielded vs unshielded learner ⇒ **the price of the C2 guarantee**, a systems number only the ML apparatus produces.

**Circularity, addressed not dodged:** change the quantifier (a claim about our design's headroom *within M*, same epistemic status as every other simulation result here); make the model's fragility the experiment (the OOD grid measures how much of the result is the simulator); use the accepted **digital-twin** framing (arXiv:2310.09299; IEEE 10711852); anchor every parameter to a standard or measurement; **never claim deployment readiness**. Cite **ITU-T Y.Sup70** (ML in QKDN) to legitimise ML to a standards reviewer — while noting it means "we apply ML to QKDN control" is not itself the contribution.

**Hard gate retained:** if E1–E5 are not complete with ≥1 week to spare for the journal version, the ML section ships as a follow-up paper rather than being thinned here.

---

## 13. Architecture

```
qkdsim/
  config.py       parameters, each with a provenance comment
  entropy.py      H2, rho(e), grade key demand
  links.py        4-state link, QBER dynamics, adversary injection
  keystore.py     QKDBuffer: Mmin/Mthr/Mmax, 4 states, overflow discard
  accounting.py   per-hop cost, invariant assertions
  routing.py      SP, KAR, candidate path enumeration
  control.py      admission, reservation floors, grade selection, fail modes
  sim.py          discrete-event loop, CRN seeding
  metrics.py      service, grade composition, k*(phi), paired bootstrap
  rl/             env, shield, tabular Q, VIPER distillation
experiments/      e1_validation … e6_sensitivity, run_all
tests/            conservation, bounds, degenerate, cliff, secoqc_fig22
```

Reproducibility: fixed seeds, versions pinned, every figure regenerable by one script, config dumped as JSON alongside each result set.
