# Fail-Closed or Fail-Degraded? Quantifying Forced Assurance Loss in Contested Multi-Hop QKD Networks

**Target:** IEEE WiCOMM-2026, Track 2 (Quantum Communications; Cyber Security and Cryptography)
**Status:** complete draft. **Every number below is produced by the committed simulator** and cross-referenced to [RESULTS.md](RESULTS.md). Figures are in `figures/` as vector PDF.

> Notes to the author are in `[[double brackets]]` and must be deleted before submission.

---

## Abstract

Standards permit a quantum key distribution network to degrade rather than fail: ITU-T Y.3803 states that when insufficient key is available for one-time-pad key relay, a symmetric cipher such as AES may be used instead, with the substitution recorded in key-manager metadata. Field deployments do exactly this. A parallel line of engineering rejects the practice, treating the same transition as a *downgrade attack* to be prevented by failing closed. The trade-off between these two positions has not been quantified. We quantify it. We model a nine-node tactical trusted-relay formation and a parametric relay chain with per-link key reservoirs, a four-state link model in which an adversary raising the quantum bit error rate past the security-abort threshold drives the secret-key rate to zero rather than merely degrading it, and explicit per-hop relay authentication. We define **forced assurance loss** — the fraction of sessions *entitled* to an information-theoretically delivered key that were served without one — and the **downgrade-forcing cost** *k\**, the adversary budget required to induce it. Suppressing 2 of 9 links collapses fail-closed availability from 0.812 to 0.304 while fail-degraded operation holds availability at 0.973 and instead forces 69.0% of entitled traffic below its authorised grade; at 5 links the same budget buys either total denial or total assurance loss. We further report three negative results that cut against current practice. Once a post-quantum fallback exists, routing policy has *no* effect on availability (paired difference 0.0000, 95% CI [0.0000, 0.0000]), so the service-rejection metric the key-aware-routing literature reports becomes degenerate. Under fail-closed operation, key-aware routing is *significantly worse* than shortest path (−2.7 percentage points) because the trusted-relay hop multiplier converts marginally longer paths into 6.0% higher key expenditure; no hop-penalty setting repairs this. And the downgrade-forcing cost depends overwhelmingly on assumed adversary sophistication: *k\** = *d*+1 for a greedy centrality-guided adversary but a flat 2 at every chain depth *d* for a minimum-cut adversary. Finally, a policy-space audit finds the hand-designed heuristic attains 104.8% of the best learned grade-selection policy and wins on 7 of 7 out-of-distribution conditions. We release the simulator.

**Index Terms** — quantum key distribution, trusted-relay networks, key management, post-quantum cryptography, crypto-agility, graceful degradation, military communications.

---

## I. Introduction

A brigade formation in mountainous terrain is connected to its rear area by a chain of relay sites. Beyond the reach of a single quantum channel, keys are relayed through trusted nodes: node *A* and node *B* share a key, *B* and *C* share another, and an end-to-end key is delivered by hop-by-hop one-time-pad re-encryption with information-theoretically secure authentication [Salvail]. The immediate consequence is that an *n*-hop path consumes key material on every one of its *n* links. With free-space per-hop rates measured in hundreds of bits per second, key becomes a depletable, contested resource.

What happens when it runs out is, remarkably, an open disagreement in the literature rather than an open problem.

**One position: degrade.** ITU-T Y.3803 clause 8.2.3, implementing requirement Req_KM 7 of Y.3801, states that if the necessary number of keys for one-time-pad-encrypted key relay is not available, a backup method using a symmetric cipher such as AES may be used, and requires the key manager to record which method was used in metadata. Deployments follow: a fully managed three-node relayed-QKD network transitions to centrally generated classical quantum-safe keys when quantum keys become unavailable [Makris]. Key-management architectures place the same substitution behind an unchanged key-delivery interface, governed by security policy [James].

**The opposite position: refuse.** A layered QKD-plus-post-quantum design published in 2026 treats precisely this transition as an attack surface: a fail-safe mechanism *prevents downgrade attacks* by interrupting the data tunnel after a defined time, and on repeated failure both components inject random keys rather than falling back [Spooren]. The concern is well founded and older than the mechanism: an adversary unable to steal quantum keys will instead deny service in order to *force* the use of classical cryptography [Schartner].

Both positions are defensible. Neither has been measured against the other. `[[This paragraph is the paper. Do not soften it.]]`

**What is already known, and what we therefore do not claim.** Key-availability-aware routing in trusted-relay QKD networks is an established literature — surveys catalogue 26 strategies, and the field-level headline is that key-aware dynamic routing reduces service rejection by 25–40% relative to static shortest path [Cvitić]. Per-link key reservoirs with low-water marks and multi-class admission control are likewise published [Mehic; Cao]; reserving key on intermediate relay nodes for a guaranteed service class dates to 2011 [Cheng]. Graded key delivery exists: four named security levels selected by a central controller, with a hardened key-derivation function combining a QKD segment and a post-quantum KEM at the middle tier [Sanz]. A quantity closely related to ours — the fraction of traffic benefiting from QKD-supported keys — has been defined for power-system communications [Zhu]. **We reproduce these as baselines and cite them as prior art. Our contribution is not any of them.**

**Contributions.**
1. A **threat-aware degradation model** in which adversarial pressure is expressed in absolute QBER units and a link driven past the security-abort threshold produces *zero* secret key, with classical-channel denial and QBER-invisible detector attacks as separate states (§III-B).
2. **Forced assurance loss** and the **downgrade-forcing cost** *k\**, defined on traffic *entitled* to information-theoretic key rather than on raw grade composition, and the quantification of the fail-closed/fail-degraded exchange rate (§V-A, §V-C).
3. Three **negative results** about key-aware routing under a post-quantum fallback, each with paired confidence intervals under common random numbers (§V-B).
4. A **policy-space audit** whose yield is two methodological findings: training inside the reservoir transient teaches the wrong regime, and a single-class assurance floor is gameable (§V-E).
5. A released simulator validated against a published field measurement.

---

## II. Related Work

**TABLE 0 — positioning.** ✓ present · ◐ partial · ✗ absent. *MH* multi-hop trusted relay; *KS* per-link key scarcity modelled; *PC* priority/multi-class traffic; *CT* contested or adversarial conditions; *SW* adversarial pressure **swept**; *FB* fallback to weaker crypto; *FA* **forced-assurance metric** (fraction of *entitled* traffic served below information-theoretic key).

| Work | MH | KS | PC | CT | SW | FB | FA |
|---|---|---|---|---|---|---|---|
| van Duijn *et al.*, ONDM 2024 | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Mehic *et al.*, IEEE/ACM ToN 2020 | ✓ | ✓ | ✓ | ◐ | ✗ | ✗ | ✗ |
| Cheng *et al.*, AIAI 2011 | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Johann *et al.*, JOCN 2024 | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Hao *et al.*, Photonics 2025 (RL) | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Johann *et al.*, Photonics 2026 (GAT-DRL) | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Cao *et al.*, Opt. Express 2017 (KoD) | ✓ | ✓ | ◐ | ✗ | ✗ | ✗ | ✗ |
| Cicconetti *et al.*, SMARTCOMP 2023 | ✓ | ◐ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Tysowski *et al.*, QST 2018 | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |
| Sanz *et al.* (QuLore), 2025 | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ |
| Zhu, arXiv:2510.15248, 2025 | ◐ | ✓ | ✓ | ✗ | ✗ | ✓ | ◐ |
| Spooren *et al.*, QCNC 2026 | ✓ | ✗ | ✗ | ◐ | ✗ | ✗ (fail-closed) | ✗ |
| Makris *et al.*, ECOC 2024 (field) | ✓ | ◐ | ✗ | ◐ | ✗ | ✓ | ✗ |
| Barral *et al.*, 2026 (testbed) | ✓ | ◐ | ✗ | ◐ | ✗ | ✓ | ✗ |
| Li *et al.*, 2025 (jamming RWA) | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Ghorab *et al.*, BDCC 2025 (MTD) | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ |
| Hafeez *et al.*, Sci. Rep. 2026 (UAV FSO) | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |
| **This work** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** |

Two columns matter. **FA is empty in every prior row**: the fraction of *entitled* traffic forced below information-theoretic key is not reported anywhere we could find — Zhu defines the closest antecedent (a QKD-supported traffic fraction) but not against swept pressure and not restricted to entitled traffic. And **no prior row combines FB with SW**: works that model a fallback do not sweep adversarial pressure, and works that sweep pressure do not model a fallback. The fail-closed/fail-degraded comparison requires both.

**Trusted-relay key economy.** The *n*-fold cost of relayed key is standard: an emulated ETSI-014 trusted-relay study states that one-time-pad plus an information-theoretic MAC consumes two link keys per hop per relay message [vanDuijn]; the mechanism is specified in ITU-T Y.3803 clause 8.2.3 and analysed in [Salvail]. We adopt it without claiming it.

**Routing and admission.** Five-way and six-way routing comparisons on meshed trusted-node topologies exist [Johann; vanDuijn], as do secret-key-aware routing with residual-key forecasting [Yang], key-pool-threshold routing [Cao], priority-ranked routing [Chen], reinforcement-learned routing [Hao; Johann2026], and online admission control [Cicconetti]. Critically, [vanDuijn] reports that differences *among* resource-aware strategies are statistically insignificant and recommends the cheapest variant — a null result we set out to test rather than ignore.

**Graded and hybrid key supply.** Concatenation-style hybrids are hardware-demonstrated [Garms] and standard: in the accepted sense, *hybrid* means simultaneous combination via a key combiner such that the result is secure if at least one component is unbroken [IETF-hybrid; NIST-SP800-227]. **A QKD→PQC substitution is therefore not hybrid**, and we call it a labelled grade downgrade throughout. Graded delivery with per-class fallback [Tysowski; Sanz], coexistence of QKD and PQC keys in one store distinguishable by metadata [Doering], and mixed QKD/PQC relay paths in a deployed inter-domain testbed [Barral] all precede us.

**Contested QKD.** Jamming-aware routing with a worst-case attack-radius metric [Li], attacker-pervasiveness sweeps under a moving-target defence [Ghorab], and an attack-parameterised mobile free-space QKD study with a hard QBER < 11% feasibility cut and post-quantum failover [Hafeez] establish that contested QKD networking is an active area — as does NATO research task group IST-218 on multi-domain QKD for military use. **We do not claim this setting is unexamined.**

**The gap we occupy.** Across this corpus, no work reports the fraction of *entitled* traffic forced below information-theoretic key as a function of swept adversarial pressure, and none compares fail-closed against fail-degraded operation on common ground.

---

## III. System Model

### A. Topology and key economy

We model (T1) a nine-node formation — a rear node, two relays, two brigade nodes and three forward posts joined by nine links, one fibre backbone segment and eight free-space hops of three grades — and (T2) a parametric relay chain of depth *d* with one longer lateral alternate, which isolates the interaction between hop count and adversarial pressure.

Each link *e* holds a key reservoir with the four-state semantics of the QKDNetSim key buffer (READY / CHARGING / WARNING / EMPTY keyed on a refill threshold and a minimum), and generated key exceeding capacity is **discarded, not queued**. Capacity, threshold and minimum take the values in that simulator's shipped SECOQC configuration: 52 428 800, 11 324 620 and 1 048 576 bits. The minimum doubles as an **authentication reserve**: SECOQC held a 2 MiB floor purely to guarantee that enough key remained to authenticate future classical-channel communication [Peev]. No vendor publishes a key-storage capacity — across roughly fifteen datasheets it appears only as an unquantified feature — so capacity is swept rather than asserted, and results are reported against the dimensionless ratio of capacity to rate × holding time.

**Assurance grades.** Sessions are served at one of four grades, cost-decreasing, mapping onto Y.3803's OTP→AES fallback and onto the four levels of [Sanz]:

| Grade | Quantum key demand | Payload security |
|---|---|---|
| G1 one-time pad | **= payload bits** | information-theoretic |
| G2 QKD-keyed symmetric | 256 bit | computational payload, ITS-delivered key |
| G3 hybrid QKD ⊕ ML-KEM-768 | 128 bit + KEM | ≥ strongest component |
| G4 ML-KEM-768 only | 0 bit | computational |

G1's demand follows Shannon: perfect secrecy requires key at least equal to message entropy [Shannon, §10]. We charge one key bit per payload bit, which is the worst case and exact for incompressible payloads. G3 uses an approved domain-separated combiner, not a bare XOR [NIST-SP800-227].

Each traffic class carries an **authorised floor** — the lowest grade policy permits. When the key economy cannot meet it, the controller either blocks the session (**FAIL_CLOSED**) or serves it below the floor and records an auditable **floor violation** (**FAIL_DEGRADED**).

### B. Link model and adversary

A two-state model that gives a degraded link a fixed fraction of nominal rate is not defensible under attack: a denial-of-service adversary acts on the quantum channel specifically to raise noise above the security threshold, and any perturbation strong enough to do so disrupts key generation entirely [Alléaume]. We therefore use four states:

| State | Rate | Trigger |
|---|---|---|
| NOMINAL | *R*₀ | *e* = *e*₀ |
| DEGRADED | *R*₀·ρ(*e*) | *e*₀ < *e* < *e*_abort |
| ABORT | **0** | *e* ≥ *e*_abort |
| OUTAGE | **0** | cut, LOS loss, **or classical-channel denial** |

with ρ(*e*) = [max(0, 1 − *f*H₂(*e*) − H₂(*e*)) / (1 − *f*H₂(*e*₀) − H₂(*e*₀))]^γ, error-correction inefficiency *f* = 1.16, and *e*₀ = 0.03 (Tokyo QKD Network measured 2.7–3.8% [Sasaki]). We report γ = 1 (asymptotic BB84 form, following the structure of [Ma]) and γ = 3.4, calibrated to the only measured degraded-link datapoint we could find: a deliberately misaligned entanglement link at QBER 5–7% delivered 0.25 kbps against 2–3 kbps nominal, i.e. 8–12% of nominal [Sasaki]. The two give 50% and 10% at QBER 6% respectively; **we publish the disagreement as a sensitivity rather than resolve it.**

*e*_abort = 0.075 is an engineering value: the deployed key-distillation engine in [Sasaki] provides LDPC coding rates only for QBER below 3.5%, 5.5% and 7.5%, with no rung above. We report 0.11 as a sensitivity. Note that realistic error correction *lowers* the information-theoretic zero from 11.0% (Shannon limit, matching Shor–Preskill) to 9.9% at *f* = 1.16; the engineering abort sits below both.

**Two failure modes bypass QBER entirely** and are modelled as separate states, which we state as a strength rather than hide. Denial of the classical post-processing channel leaves the quantum channel pristine while stopping key production [Mehic]. Detector blinding extracts the full key *without raising QBER* [Lydersen] and is therefore invisible to any QBER-driven model, including ours.

**Adversary.** The adversary cannot break QKD, so it attacks availability in order to force a downgrade — the incentive identified in [Schartner]. It selects *k* links and injects excess QBER Δ*e* = 0.05 on each; with *e*₀ = 0.03, Δ*e* = 0.045 suffices to reach abort. Expressing pressure in absolute QBER units makes it physically checkable, deliberately replacing a dimensionless multiplier. We report **two targeting models**: greedy by edge betweenness, and **minimum edge cut** — the honest worst case.

### C. Key accounting

Per-hop cost is *D* + *M*_meta + *n*_auth·*t*, with metadata 240 bit (Y.3803 relays a *key file*; metadata is "typically a few tens of bytes" and is normally OTP-encrypted too), tag *t* = 127 bit [Walenta], and *n*_auth = 2 for mutual authentication [DeLazzari]. Wegman–Carter cost is per message and only *logarithmic* in message length [Fung]. At *D* = 256 this is 750 bit/hop, a factor 2.93; Cambridge measured 3.6× for a ~400-bit relayed global key [Dynes]. Setting the authentication terms to zero reproduces the bare *D·n* law used throughout the routing literature, which we treat as an ablation rather than a footnote — SECOQC measured that **~91%** of a live AES-VPN's key consumption was authentication rather than cipher key [Peev].

### D. Traffic

Demands are taken from measured deployments, not constructed. C2 command traffic: 2048 bit payload, floor G2, 5 s deadline, λ = 0.05 s⁻¹ — 256 bit per minute per encryptor is the modal deployed consumption unit [Stucki; IDQ]. ISR: 144 000 bit, floor **G1**, 30 s, λ = 0.02 s⁻¹ — a 60 s session of the 2.4 kbps real one-time-pad voice run for 31 months on a 46-node metropolitan QKD network [Chen2021]. LOG: 320 000 bit, floor G3, 120 s, λ = 0.03 s⁻¹ — the same network's measured 320 kbps one-time-pad file transfer.

---

## IV. Experimental Setup

Discrete-event simulation at 1 s resolution, **24 h horizon with the first 12 h discarded**. The warm-up is necessary and is itself a finding: with reservoirs initialised full, free-space stores take ~12 h to fall from capacity to the authentication reserve, and first-half/second-half metrics agree only from that point. A 4 h run leaves them at 59% of capacity and therefore measures the initial fill, not the key economy.

Policies use **common random numbers** — identical arrival streams and channel realisations at a given seed — so comparisons are paired; without this a 3-point service difference is partly noise. Confidence intervals are paired bootstraps over common seeds, 20 000 resamples. 12 seeds for the main comparisons, 6 for the depth sweep, 8 for the audit.

**Simulator choice.** We wrote a purpose-built simulator and validated it against published measurement. Source-tree inspection confirms SeQUeNCe, NetSquid and QuISP contain no trusted-relay or key-pool code; NetSquid additionally gates package and documentation behind registration without an OSI licence, an artifact-availability problem. QKDNetSim is the only on-target tool and we adopt its buffer semantics verbatim for citability, but its routing is self-described as an early version, its controller implements one policy, and **admission control does not exist** — precisely the two things this study compares.

**Validation gate (43/43 checks, all must pass before any result is reported).** Exact key conservation across all sessions and stores; reservoir bounds and state transitions; the rate cliff and both threshold variants; degenerate cases in both fail modes; and a reproduction of the SECOQC rerouting experiment, in which an 8192 bit/s one-time-pad application drained 3.5 MiB of a 5.5 MiB key store in approximately one hour [Peev]: our simulator gives **3584 s** against the reference arithmetic of 3584 s.

---

## V. Results

### A. The fail-closed / fail-degraded exchange rate (Fig. 1, Fig. 2)

**TABLE I — availability and forced assurance loss versus adversary budget** (12 seeds, KAR routing, betweenness targeting)

| mode | *k* | availability | blocked | G1 | G2 | G3 | G4 | forced below grade |
|---|---|---|---|---|---|---|---|---|
| FAIL_CLOSED | 0 | 0.8124 | 0.1876 | 0.041 | 0.590 | 0.369 | 0.000 | **0.000** |
| FAIL_CLOSED | 1 | 0.8264 | 0.1736 | 0.077 | 0.564 | 0.358 | 0.000 | **0.000** |
| FAIL_CLOSED | 2 | **0.3039** | 0.6961 | 0.166 | 0.508 | 0.326 | 0.000 | **0.000** |
| FAIL_CLOSED | 5 | **0.0000** | 1.0000 | — | — | — | — | — |
| FAIL_DEGRADED | 0 | 0.9733 | 0.0267 | 0.034 | 0.659 | 0.308 | 0.000 | 0.166 |
| FAIL_DEGRADED | 1 | 0.9733 | 0.0267 | 0.065 | 0.607 | 0.299 | 0.029 | 0.157 |
| FAIL_DEGRADED | 2 | 0.9733 | 0.0267 | 0.052 | 0.174 | 0.100 | **0.675** | **0.690** |
| FAIL_DEGRADED | 5 | 0.9733 | 0.0267 | 0.000 | 0.000 | 0.000 | **1.000** | **1.000** |

The transition is a **cliff, not a slope**. Suppressing 2 of 9 links collapses fail-closed availability from 0.812 to 0.304, while fail-degraded operation holds availability unchanged at 0.973 and converts the same pressure into 69.0% forced assurance loss, with post-quantum-only service jumping from 2.9% to 67.5%. At *k* = 5 both endpoints are total: complete denial, or complete assurance loss at undiminished availability.

**The general law, not the instance.** The value 2 is not a property of our formation but of its cut structure: **k\* equals the minimum edge cut separating the rear node from the forward posts.** In this formation two links are the only quantum-viable route into one brigade node, so the cut is 2 and availability floors at one third (the remaining post stays reachable). §V-C confirms the same law on a parametric chain, where the cut is 2 at *every* depth. Read k = 2 as an instance; the design quantity is the cut.

**Two caveats that the experiment forced on us, both of which sharpen the result.** First, the cliff requires the adversary to actually *abort* a link: the forcing cost is two-dimensional in (*k*, Δ*e*), with the cliff at **Δ*e* ≥ e_abort − e₀** (§V-F). Second, fail-degraded availability is constant across *k* not because the fallback is resilient but because **a link in ABORT still carries a pristine classical channel, and ML-KEM needs only that channel**. Denying the classical channel instead removes the fallback entirely (§V-F). We report both attack modes; reporting only QBER injection would materially overstate the fallback's value.

Fail-closed's forced-loss column is identically zero *by construction*: it refuses rather than degrades. That is the comparison, not a missing measurement.

**The authorisation policy is infeasible even unattacked, and we say so.** At *k* = 0 fail-degraded operation already shows 16.6% forced assurance loss: at the free-space key rates cited in §III-D, a one-time-pad floor for a 144 kbit ISR session is **not fundable**. That is the honest reading, and it is the natural entry to a capacity requirement — either the rate must rise or the floor must be relaxed to periodic symmetric rekeying.

> **Design implication.** Availability and assurance are not independent objectives that a controller can jointly maximise; under pressure they are a conserved pair, and the choice of fail mode chooses which one the adversary gets to take.

### B. Three negative results for key-aware routing (Fig. 4)

**TABLE II — policy comparison, paired bootstrap over common seeds**

*Under FAIL_DEGRADED (k = 0):*

| policy | availability | hops | key (Mbit/12 h) | Δ availability vs SP [95% CI] |
|---|---|---|---|---|
| SP | 0.9733 ± 0.0074 | 3.060 | 436.8 | reference |
| KAR | 0.9733 ± 0.0074 | 3.083 | 463.7 | **+0.0000 [+0.0000, +0.0000]** |
| KAR+CAF | 0.9733 ± 0.0074 | 3.107 | 398.7 | **+0.0000 [+0.0000, +0.0000]** |

*Under FAIL_CLOSED (k = 0):*

| policy | availability | forced below ITS | hops | key (Mbit) | Δ availability vs SP [95% CI] |
|---|---|---|---|---|---|
| SP | **0.8392** ± 0.0078 | 0.3569 | 3.062 | 437.8 | reference |
| KAR | **0.8124** ± 0.0081 | 0.3687 | 3.086 | 464.1 | **−0.0268 [−0.0293, −0.0243]** |
| KAR+CAF | **0.5092** ± 0.0080 | **0.0000** | 3.128 | 399.3 | **−0.3299 [−0.3333, −0.3264]** |

**Result 1 — the service metric becomes degenerate.** Once a post-quantum fallback exists, routing policy has *exactly no* effect on availability: the paired difference is 0.0000 with a confidence interval of zero width, because the fallback succeeds wherever a classical path exists. Availability is then a property of connectivity, not of key-awareness. **The metric the key-aware-routing literature reports stops responding to the thing it is measuring.** Routing still matters for key expenditure (KAR +27.0 Mbit [+25.3, +28.9]; reservation floors −38.1 Mbit [−40.5, −35.7], both significant) and for latency.

**Result 2 — key-aware routing is worse, not better.** Under fail-closed operation KAR loses 2.7 percentage points of availability to plain shortest path, significantly. The mechanism is the hop multiplier: KAR selects marginally longer paths (3.086 vs 3.062 hops) and every extra hop consumes key on an *additional* link, raising expenditure 6.0% and starving later sessions. **Per-session time-to-key optimisation is globally counterproductive in a key-scarce trusted-relay network.**

We scope this deliberately. It holds **under these three conditions jointly**: key scarcity binding at steady state, fail-closed semantics, and a hop-multiplied cost with per-hop authentication charged. Where prior work reports 25–40% service-rejection improvements [Cvitić], it generally measures blocking under different scarcity and without a fallback in the model. We claim a regime, not a refutation.

We tested the obvious objection — a mispriced hop penalty — by sweeping it over four orders of magnitude (Table III). **No setting restores KAR ≥ SP.** As the penalty grows, KAR converges to shortest-path behaviour (hops 3.065 vs 3.064, key 440.0 vs 438.6 Mbit); the best it can do is abandon key-awareness. The effect is small in absolute terms but statistically unambiguous under common random numbers.

**TABLE III — hop-penalty sensitivity (FAIL_CLOSED, k = 0, 8 seeds)**

| routing | hop penalty | availability | hops | key (Mbit) | Δ vs SP [95% CI] |
|---|---|---|---|---|---|
| SP | — | 0.8393 | 3.064 | 438.6 | reference |
| KAR | 0.0 | 0.8123 | 3.088 | 464.2 | −0.0270 [−0.0298, −0.0239] |
| KAR | 5.0 | 0.8123 | 3.087 | 464.2 | −0.0270 [−0.0298, −0.0239] |
| KAR | 50.0 | 0.8135 | 3.086 | 463.3 | −0.0259 [−0.0288, −0.0227] |
| KAR | 1000.0 | 0.8386 | 3.065 | 440.0 | −0.0007 [−0.0013, −0.0002] |

**Result 3 — reservation floors are a genuine Pareto trade, not an improvement.** Class-aware floors convert availability into assurance: 0.839 → 0.509 (−33.0 points) in exchange for forced-below-ITS 0.357 → **0.0000**. Every session served is served with an information-theoretically delivered key. A designer must choose a point on this curve; there is no free lunch.

### C. Downgrade-forcing cost versus chain depth (Fig. 3)

**TABLE IV — *k\**(φ): links the adversary must suppress to force a fraction φ of *entitled* sessions below information-theoretic key** (6 seeds; nominal forced loss is 0.000 at every depth, so every point is attributable to the attack)

| *d* | links | betweenness *k\**(0.25) | betweenness *k\**(0.5) | **min-cut *k\**(0.25)** | **min-cut *k\**(0.5)** |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 5 | 3 | 3 | **2** | **2** |
| 3 | 7 | 4 | 4 | **2** | **2** |
| 4 | 9 | 5 | 5 | **2** | **2** |
| 5 | 11 | 6 | 6 | **2** | **2** |
| 6 | 13 | 7 | 7 | **2** | **2** |

A greedy centrality-guided adversary requires *k\** = *d* + 1, growing linearly with depth, because it exhausts the *already-severed* primary path before touching the alternate. A minimum-cut adversary requires **exactly two links at every depth**, since the primary and alternate paths are edge-disjoint. At *d* = 6 that is a **3.5× overstatement of resilience** if only the greedy adversary is reported.

> **Design implication.** Adding relay depth buys no protection against a competent adversary. Resilience must be reported against the adversary's *cut structure*, not against a plausible-looking heuristic attack.

### D. When the bare *D·n* key-cost law fails (Fig. 5)

Authentication cost is per message and logarithmic in message length, so the answer is a function of block size: the overhead factor is 2.93× at *D* = 256 bit, 1.24× at 2048, and 1.003× at 144 000. Both published anchors sit in the small-block regime — 91% authentication share for a 256-bit rekey [Peev], 3.6× for a ~400-bit relayed key [Dynes].

Operationally, the bare law understates key consumption by **2.93×** for small-block rekey traffic and **1.00×** when large one-time-pad sessions dominate. In our formation this changes no service outcome in either regime, so it is a **capacity-planning error rather than a service error**. It matters because the modal deployed workload *is* small-block: 256 bit per minute per encryptor, and one key per second per 800 Gbps channel in a deployed layer-1 encryption trial [Pistoia].

### E. Sensitivity, and the two-threshold law (Table V)

Running the sensitivities §III-B names produced the paper's sharpest result.

**γ barely matters; the abort threshold decides everything.** Across all four (γ, *e*_abort) combinations the fail-closed availability at *k* = 2 is 0.3020 for *e*_abort = 0.075 at **both** γ values, and 0.79 / 0.77 for *e*_abort = 0.11. The five-fold calibration ambiguity in the degradation exponent changes almost nothing; the abort threshold changes the result completely.

**TABLE V — fail-closed availability at *k* = 2 versus per-link injection Δ*e*** (γ = 1.0, 6 seeds; e₀ = 0.03)

| *e*_abort | requires Δ*e* ≥ | 0.03 | 0.04 | **0.05** | 0.06 | **0.08** | 0.10 |
|---|---|---|---|---|---|---|---|
| 0.075 | **0.045** | 0.798 | 0.796 | **0.302** | 0.302 | 0.302 | 0.302 |
| 0.110 | **0.080** | 0.798 | 0.796 | 0.793 | 0.781 | **0.302** | 0.302 |

The cliff lands **exactly at Δ*e* ≥ *e*_abort − e₀**, and above it the outcome saturates immediately and identically. Hence:

> **The downgrade-forcing cost has two thresholds, both necessary: a per-link capability Δ*e* ≥ *e*_abort − e₀, and a budget *k* ≥ the minimum edge cut.** Below either, essentially nothing happens. Above both, the collapse is total regardless of margin.

This is directly actionable, and it points at reconciliation rather than key rate: raising the abort threshold from 0.075 to 0.11 raises the injection an adversary must achieve by **78%**, without any improvement in secret-key rate.

**The fallback needs the classical channel.** Fail-degraded availability is invariant under QBER injection because a link in ABORT still carries a pristine classical channel and ML-KEM needs only that. Under **classical-channel denial** the picture inverts: availability falls from 0.970 to **0.313**, only 1.6 points above fail-closed's 0.296, and forced loss is zero because severed posts are blocked outright rather than downgraded — there is no channel left on which to downgrade them.

> **The entire advantage of degrading gracefully is conditional on the classical channel surviving.** A defender who hardens the quantum channel and leaves the classical channel exposed has bought nothing.

### F. Policy-space audit (Fig. 6)

Learned *routing* for key-scarce QKD networks is saturated [Hao; Johann2026; Xie; Sharma; Seok; Zuo] and learned admission control is saturated in classical networking, so we do not claim a better router. We instead ask a bounded question about our own design: **within this model, how much headroom does the hand-designed heuristic leave?** We search a 12-cell state→grade lookup table (policy space 2.4 × 10⁸) by cross-entropy method, scoring every candidate by full simulation rollouts so the sequential key economy is evaluated exactly rather than approximated. A deterministic shield forbids command traffic below G2; we concede up front that the guarantee comes from the shield, which is verifiable by inspection, and that search only operates inside it. The policy class is auditable by construction, so no policy distillation is required.

**The heuristic wins at the stated weights — and the *boundary* is the real output.** At full horizon it attains **104.8%** of the best searched shielded policy (*J* 1.1287 vs 1.0774) and wins **7 of 7** out-of-distribution conditions, with margins from 0.004 to 0.104. We report this null because we pre-committed to reporting it.

But it would be dishonest to call the null weight-robust, and checking showed it is not. The two policies do **not** order componentwise:

| component | heuristic | searched | better |
|---|---|---|---|
| availability | 0.8123 | **0.9726** | searched |
| floor violations | **0.0000** | 0.3952 | heuristic |
| ITS share | **0.6327** | 0.6048 | heuristic |

The searched policy genuinely buys 16 points of availability, and pays for it with 39.5% forced downgrades. With *J* = availability − λ·violations + *w*·ITS, the heuristic wins **iff λ > 0.37** (at *w* = 0.5; 0.41 at *w* = 0, 0.26 at *w* = 2).

> **This turns an arbitrary weighting into a decision an operator can actually take.** The question is not "which policy is better" but **"is one forced downgrade of entitled traffic worth more or less than 0.37 of a served session?"** If more, the simple heuristic is correct and no learned policy is needed. If less, the network should be run closer to the searched policy and accept the assurance loss. **The learned policy's contribution is to locate that indifference point**, not to beat a baseline — and locating it required the search, because λ\* depends on the achievable trade-off surface, which is a property of the key economy rather than of the objective.

Two findings are more useful than the score.

**Training inside the reservoir transient teaches the wrong regime.** The searched policy *beat* the heuristic on the 6 h training horizon (*J* 1.4591 vs 1.2978) and *lost* at 24 h. The training window sat inside the 12 h drain-from-full transient, where free-space key is still abundant, so the policy optimised a regime the network leaves. Any application of learning to key-scarce QKD control must verify that training spans steady state — a hazard that follows directly from §IV and, we suspect, is easy to miss.

**A single-class assurance floor is gameable.** The unshielded ablation scored highest by cutting key consumption from 464 to **42 Mbit — an 11× reduction — while keeping 100% of traffic on information-theoretically delivered key.** It did so by serving one-time-pad-entitled ISR traffic at G2: still ITS-*delivered*, but a violation of that class's authorised OTP floor. Because the shield constrained only command traffic, it did not prevent this, and command-below-ITS is 0.0000 in both arms. The ablation therefore does **not** measure the price of the command guarantee; it demonstrates that an assurance policy specifying a floor for one class is gameable, and that an objective pricing floor violations below key savings *will* be gamed. **Per-class floors must be specified and priced explicitly** — a specification requirement neither position in §I currently states.

---

## VI. Discussion and Limitations

**What we have shown.** When key runs out, the choice between refusing and degrading is a choice about which resource the adversary is permitted to take, and the exchange rate is steep: two of nine links convert a 0.97-availability network into either a 0.30-availability one or one where 69% of entitled traffic has lost information-theoretic protection. A post-quantum fallback makes the routing literature's headline metric stop responding; key-aware routing can actively harm availability; and reported resilience is dominated by assumed adversary sophistication.

**Limitations, stated plainly.**
1. **Above-the-physics abstraction.** Per-link secret-key rates are parameterised inputs, not simulated photonics. Finite-key effects, reconciliation and privacy amplification are absorbed into a rate. §III-B exists so a reader can locate their own system.
2. **An unresolved calibration gap.** The measured degraded-link datapoint (8–12% of nominal at QBER 5–7%) and the asymptotic rate expression (≈50% at the same QBER) disagree by a factor of five. We report both and resolve neither.
3. **Trust model.** Relay nodes are assumed trusted; node compromise appears only as an availability event, not a confidentiality breach.
4. **A blind spot we can name but not model.** Detector blinding extracts key without raising QBER [Lydersen] and is therefore invisible to this model by construction.
5. **One formation and one chain family**, one traffic profile, one label for "entitled". Generalisation is untested.
6. **Unmeasured parameters are swept, not assumed.** No published free-space hard-outage duration or frequency distribution exists, and no vendor publishes a key-storage capacity.
7. **Search budget.** The policy audit used a modest cross-entropy budget with two training seeds; the null is supported by 8 evaluation seeds and 7/7 out-of-distribution wins, but a larger search could narrow the gap.

**Future work.** Hardware-in-the-loop coupling through the ETSI key-delivery interfaces; a grade attribute carried on the delivered key so a consumer can enforce policy on it; terrain-correlated, spatially-correlated outage on free-space relay chains, which every model we found treats as independent; and a formal per-class downgrade-authorisation language with commander-visible reporting.

---

## VII. Conclusion

Standards permit a QKD network to fall back to weaker key supply; a parallel line of engineering forbids it as a downgrade attack. We measured the trade-off. In a nine-node contested formation, suppressing two of nine links either collapses availability from 0.812 to 0.304 or holds it at 0.973 while forcing 69.0% of entitled traffic below information-theoretic protection; five links buy total denial or total assurance loss for the same effort. Along the way we found that a post-quantum fallback makes the key-aware-routing literature's service metric degenerate, that key-aware routing costs 2.7 points of availability and cannot be tuned out of it, and that a minimum-cut adversary needs two links at any relay depth where a centrality-guided one appears to need *d*+1. We argue that the security-grade composition of *served* traffic belongs in QKD resilience reporting alongside key-supply continuity, and that a per-class downgrade authorisation policy — with floors specified and priced — belongs in the architecture rather than being retrofitted.

---

## Figures

| File | Caption |
|---|---|
| `fig1_failmode` | Fig. 1. Availability (a) and forced assurance loss (b) versus adversary budget, for fail-closed and fail-degraded operation. Error bars: SD over 12 seeds. Fail-closed cannot lose assurance by construction. |
| `fig2_grade_composition` | Fig. 2. Assurance-grade composition of *served* traffic under fail-degraded operation as adversarial pressure increases. |
| `fig3_forcing_cost` | Fig. 3. Downgrade-forcing cost *k\**(φ=0.5) versus relay-chain depth, for a greedy centrality-guided and an optimal minimum-cut adversary. |
| `fig4_policy_pareto` | Fig. 4. Availability against key expenditure by control policy, under (a) fail-closed and (b) fail-degraded operation. |
| `fig5_auth_overhead` | Fig. 5. Per-hop key cost relative to the bare *D·n* law as a function of relay block size. |
| `fig6_policy_audit` | Fig. 6. Policy-space audit: heuristic versus best searched policy, nominal and out-of-distribution. |

---

## References — **VERIFY BEFORE SUBMISSION**

`[[Verification status is from PHASE1_LITERATURE_DOSSIER.md. Items marked (V) were read in full; (P) partially; (S) snippet only -- retrieve or delete. Aim for 20-25; add 3-5 Indian-context citations.]]`

1. **[Salvail]** L. Salvail *et al.*, "Security of trusted repeater quantum key distribution networks," *J. Computer Security*, vol. 19, pp. 61–106, 2011. arXiv:0904.4072. **(V)**
2. **[Peev]** M. Peev *et al.*, "The SECOQC quantum key distribution network in Vienna," *New J. Phys.*, vol. 11, 075001, 2009. **(V)**
3. **[Sasaki]** M. Sasaki *et al.*, "Field test of quantum key distribution in the Tokyo QKD Network," *Opt. Express*, vol. 19, no. 11, pp. 10387–10409, 2011. **(V)**
4. **[Ma]** X. Ma, B. Qi, Y. Zhao, H.-K. Lo, "Practical decoy state for quantum key distribution," *Phys. Rev. A*, vol. 72, 012326, 2005. **(V)**
5. **[Alléaume]** R. Alléaume *et al.*, "Using quantum key distribution for cryptographic purposes: a survey," *Theor. Comput. Sci.*, vol. 560, pp. 62–81, 2014. **(V)**
6. **[Shannon]** C. E. Shannon, "Communication theory of secrecy systems," *Bell Syst. Tech. J.*, vol. 28, no. 4, pp. 656–715, 1949, §10. **(V)**
7. **[Mehic]** M. Mehic *et al.*, "A novel approach to quality of service provisioning in trusted relay quantum key distribution networks," *IEEE/ACM Trans. Netw.*, vol. 28, 2020. `[[volume/issue disputed between sources -- resolve]]` **(V)**
8. **[vanDuijn]** T. van Duijn *et al.*, "Routing strategies for quantum key distribution networks based on trusted relay nodes," *ONDM 2024*. **(V)**
9. **[Cvitić]** I. Cvitić, D. Peraković, A. N. Pinto, "Overview of routing approaches in quantum key distribution networks," arXiv:2511.15465, 2025. **(V)** `[[arXiv-only, not peer reviewed; re-verify its numbers at source]]`
10. **[Spooren]** P. Spooren, A. Neuhold, S. Ramacher, T. Hühn, "PQC-enhanced QKD networks: a layered approach," *IEEE QCNC 2026*. arXiv:2604.05599. **(V)**
11. **[Sanz]** A. Sanz *et al.*, "Extending quantum-safe communications to real-world networks: an adaptive security framework," arXiv:2511.22416, 2025. **(V)**
12. **[Zhu]** Z. Zhu, "Techno-economic feasibility analysis of quantum key distribution for power-system communications," arXiv:2510.15248, 2025. **(V)**
13. **[Schartner]** P. Schartner, S. Rass, "Quantum key distribution and denial-of-service: using strengthened classical cryptography as a fallback option," IEEE, 2010. **(S)** `[[retrieve]]`
14. **[Makris]** A. Makris *et al.*, "Field demonstration of a fully managed, L1 encrypted 3-node network with hybrid relayed-QKD," *ECOC 2024*. arXiv:2403.08526. **(V)**
15. **[Dynes]** J. F. Dynes *et al.*, "Cambridge quantum network," *npj Quantum Inf.*, vol. 5, 101, 2019. **(V)**
16. **[Walenta]** N. Walenta *et al.*, "A fast and versatile QKD system with hardware key distillation and wavelength multiplexing," arXiv:1309.2583. **(V)**
17. **[Fung]** C.-H. F. Fung, X. Ma, H. F. Chau, "Practical issues in quantum-key-distribution postprocessing," arXiv:0910.0312. **(V)**
18. **[Chen2021]** Y.-A. Chen *et al.*, 46-node metropolitan QKD network with one-time-pad voice and file services. `[[Hefei QMAN paper -- confirm exact citation]]` **(P)**
19. **[Pistoia]** M. Pistoia *et al.*, "Paving the way towards 800 Gbps quantum-secured optical channel deployment in mission-critical environments," *Quantum Sci. Technol.*, vol. 8, 035015, 2023. **(V)**
20. **[Stucki]** D. Stucki *et al.*, "Long-term performance of the SwissQuantum quantum key distribution network in a field environment," *New J. Phys.*, vol. 13, 123001, 2011. **(V)**
21. **[Lydersen]** L. Lydersen *et al.*, "Hacking commercial quantum cryptography systems by tailored bright illumination," *Nature Photon.*, vol. 4, 2010. **(S)** `[[retrieve]]`
22. **[Li]** M. Li *et al.*, "Routing and wavelength assignment with minimal attack radius for QKD networks," arXiv:2508.10613, 2025. **(P)**
23. **[Hafeez]** M. Hafeez *et al.*, "Quantum-secured routing in drone communication for 6G-enabled smart mobility," *Sci. Rep.*, 2026. **(V)**
24. **[Ghorab]** A. Ghorab, M. Azab *et al.*, "A QKD routing scheme for a zero-trust QKD network system: a moving target defense approach," *Big Data Cogn. Comput.*, vol. 9, no. 4, 76, 2025. **(V)**
25. **[Johann2026]** T. Johann, Kühl, S. Pachnicke, "Adaptive routing for meshed QKD networks of flexible size using deep reinforcement learning," *Photonics*, vol. 13, no. 2, 198, 2026. **(P)**
26. **[Hao]** Y. Hao, Y. Xie, W. Gao, J. Tang, "Q-learning for resource-aware and adaptive routing in trusted-relay QKD network," *Photonics*, vol. 12, no. 10, 969, 2025. **(P)**
27. **[Cheng]** X. Cheng, Y. Sun, Y. Ji, "A QoS-supported scheme for quantum key distribution," *AIAI 2011*, IET, pp. 220–224. **(citation only — retrieve; if it reports class-level blocking, soften §II)**
28. **[Tysowski]** P. K. Tysowski, X. Ling, N. Lütkenhaus, M. Mosca, "The engineering of a scalable multi-site communications system utilizing QKD," *Quantum Sci. Technol.*, vol. 3, no. 2, 024001, 2018. **(citation only — retrieve)**
29. **[IETF-hybrid]** IETF TLS WG, *draft-ietf-tls-hybrid-design*, §1.2. **(V)**
30. **[NIST-SP800-227]** NIST SP 800-227, *Recommendations for Key-Encapsulation Mechanisms*, §4.6. **(secondary source only — read the primary before citing a clause)**
31. ITU-T Recommendation Y.3803, *Quantum key distribution networks — Key management*, 12/2020, cl. 8.2.3, 8.2.5. **(V)**
32. ETSI GS QKD 014 V1.1.1, *Protocol and data format of REST-based key delivery API*. **(V)** `[[352-bit key_size is an EXAMPLE value, not a default -- do not misstate]]`
33. ETSI GS QKD 015 V2.1.1 (SDN control), GS QKD 020 V1.1.1 (interoperable KMS API). **(V for 015/020 machine-readable models)**
34. **[Others]** [Cao] Y. Cao *et al.*, *Opt. Express* 25:26453, 2017; [Yang] C. Yang *et al.*, *China Commun.* 15(2), 2018; [Chen] L. Chen *et al.*, *Entropy* 24(11):1519, 2022; [Cicconetti] C. Cicconetti *et al.*, *IEEE SMARTCOMP 2023*; [Johann] T. Johann *et al.*, *JOCN* 16(3):382, 2024; [Garms] L. Garms *et al.*, *Adv. Quantum Technol.* 7(4):2300304, 2024; [Barral] D. Barral *et al.*, arXiv:2604.20376; [Doering] R. Doering, M. Geitz, R.-P. Braun, ICCNT 2022; [James] P. James *et al.*, *ARES 2023*; [DeLazzari] arXiv:2603.25496; [Xie] Y. Xie *et al.*, *Opt. Express*, 2025; [Sharma] Sharma *et al.*, *IET Quantum Commun.* 4(3), 2023; [Seok] Seok *et al.*, *JNSM* 33:30, 2025; [Zuo] Zuo *et al.*, *ACP 2020*; [IDQ] ID Quantique Geneva canton elections use case.

---

## Reproducibility statement

The simulator, all configurations, the validation gate and the scripts generating every figure and table are available at `[[GitHub URL]]`. Results use 24 h simulated horizons with the first 12 h discarded as warm-up, common random numbers across policies, and paired bootstrap confidence intervals (20 000 resamples): 12 seeds for Tables I–II, 8 for Table III, 6 for Table IV. The complete experiment set runs in approximately 30 minutes on 8 CPU cores; no GPU is used. The validation gate (43 checks) must pass before any result is reported and includes a reproduction of the SECOQC key-store drain measurement to within 1 second. ITU-T and ETSI digital products are not redistributed; a download script is provided. ML-KEM-768 artefact sizes are the FIPS 203 values (encapsulation key 1184 B, ciphertext 1088 B, shared secret 32 B).
