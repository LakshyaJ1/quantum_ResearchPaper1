# PROJECT HANDOFF — complete context for resuming this work

**Read this first if you are picking the project up cold, or resuming after context compaction.** It records not just *what* exists but *why every decision was made*, which the other documents do not. Where a decision was later reversed, the reversal and its cause are recorded — those reversals are the most useful part of this file.

**Paper:** *Fail-Closed or Fail-Degraded? Quantifying Forced Assurance Loss in Contested Multi-Hop QKD Networks*
**Venue:** IEEE WiCOMM-2026, DEAL (DRDO), Dehradun · Track 2 (Quantum Communications; Cyber Security & Cryptography)
**Author context:** AI/ML engineer background, limited prior wireless/QKD domain knowledge. This matters: the project deliberately routes domain risk into citable prior art rather than hand-rolled physics.

---

## 1. What this paper is, in one paragraph

Standards permit a QKD network to fall back to weaker key supply when quantum key runs out (ITU-T Y.3803 cl. 8.2.3 allows AES in place of one-time-pad relay). A parallel line of security engineering refuses, treating that transition as a *downgrade attack* and failing closed instead. Both positions are published; neither has ever been measured against the other. This paper measures the trade-off in a contested multi-hop trusted-relay network, defines the metric that makes it measurable (**forced assurance loss** — the fraction of traffic *entitled* to information-theoretic key that was served without it), and reports the adversary budget required to induce it (**downgrade-forcing cost**).

---

## 2. Decision history — the part no other document records

### 2.1 The paper was repositioned once, substantially

The original concept (in `PAPER1_QKD_PQC_tactical.md`, a placeholder draft with invented numbers) claimed five contributions: a key-economy model with the hop multiplier, a shortest-path-vs-key-aware routing comparison, class-aware admission with reservation floors, a three-grade security model, and a fraction-of-traffic-per-grade metric.

**All five were already published.** A five-agent adversarial prior-art sweep (~250 tool calls) established:

| Original claim | Killed by |
|---|---|
| Key-economy model, hop multiplier | van Duijn ONDM 2024 states it verbatim ("two link keys per hop") |
| SP vs key-aware routing | van Duijn 2024; Johann JOCN 2024 (five algorithms); Hao 2025; Yang 2018 |
| Class-aware admission + reservation floors | Mehic IEEE/ACM ToN 2020 (`M_min` floor + 3 DSCP classes); Cheng/Sun/Ji **2011** |
| Three named security grades incl. hybrid tier | Sanz *et al.* 2025 (QuLore) — L1–L4, KDF-combined middle tier, same ETSI+FIPS anchoring |
| Starvation → labelled downgrade | Schartner & Rass **2010**; Makris ECOC 2024 (field); **ITU-T Y.3803 Req_KM 7 standardises it** |
| Fraction served per grade | Zhu arXiv:2510.15248 (`ρ_k,t`, fallback occupancy, SLA framing) |
| "Tactical/contested is unstudied" | **False** — NATO RTG IST-218, MuQuaNet, EDF-QSTN call, Hafeez *Sci. Rep.* 2026 |

**The repositioning:** move from "we propose X" to "standards and security engineering disagree about X; we measure the disagreement." Routing was demoted to a cited, reproduced baseline. The user approved this explicitly.

**Later refinement (important).** Retrieving Tysowski *et al.* 2018 in full showed it states **both branches of the fork under policy control**: *"When the quantum key pool is exhausted, it falls back to key derivation if allowed by the policy, or blocks the host."* So even the *framing* of the choice is 2018 prior art. What survives is the **measurement** — that paper is a design specification with no simulation or experiment (full-text grep: `simulat` = 0, `measured` = 0). The introduction now credits Tysowski explicitly and narrows the claim to measurement. **Do not re-inflate this claim.**

### 2.2 Why the horizon changed from 4 h to 24 h

The original draft used 4 h. Measured: with reservoirs initialised full (as QKDNetSim's shipped SECOQC script does), free-space stores take **~12 h** to fall from capacity to the authentication reserve. At 4 h they are still at **59%** of capacity, so a 4 h run measures the initial fill rather than the key economy. First-half/second-half metrics agree only from ~12 h onward. Hence 24 h horizon, first 12 h discarded as warm-up.

**The transient is reported as a finding, not silently discarded:** a formation deploying with topped-up reservoirs runs for hours before the key economy binds at all — the same drain-from-full dynamic SECOQC measured.

### 2.3 Why the link model has four states, not two

The original two-state Gilbert–Elliott model gave a degraded link 5% of nominal rate. That is indefensible under attack: Alléaume *et al.* state that a DoS adversary acts on the quantum channel *specifically to raise noise above the security threshold*, and that any perturbation strong enough to do so disrupts key generation entirely. An adversary modelled as producing 5% throughput is an adversary who failed. Replaced with NOMINAL / DEGRADED / ABORT (rate = 0) / OUTAGE.

### 2.4 Why γ has two values and why that turned out not to matter

The degradation exponent γ is calibrated two ways that disagree five-fold at QBER 6%: the asymptotic BB84 rate expression gives ~50% of nominal (γ=1), while the only *measured* degraded-link datapoint — Tokyo's deliberately misaligned entanglement link at QBER 5–7% delivering 0.25 kbps against 2–3 kbps nominal — gives 8–12% (γ=3.4). Both are reported.

**Running the sensitivity showed γ barely matters** (fail-closed availability at k=2 is 0.3020 at *both* values) while `e_abort` decides everything. That produced the two-threshold law (§4, Finding 10). **This is the single best example in the project of why an asserted sensitivity must actually be run.**

### 2.5 Why a purpose-built simulator

Source-tree inspection: SeQUeNCe's `sequence/qkd/` is point-to-point BB84 + Cascade with no trusted relay and no key pools; QuISP has no key pools and inherits OMNeT++'s non-commercial licence; NetSquid has neither and gates package *and* docs behind registration with no OSI licence (an artifact-availability problem for a paper). QKDNetSim is the only on-target tool — and we adopt its `QKDBuffer` semantics verbatim for citability — but its routing is self-described as "an early version of routing table", its controller implements exactly one policy, and **admission control does not exist**, which is precisely what this study compares. QKDNetSim+ (arXiv:2402.10822) additionally found that nodes did not adequately process received key material and the crypto handler malfunctioned, *in the layer we would be validating against*.

---

### 2.6 Why `n_auth` is swept rather than fixed (added after the improvement round)

We originally fixed the number of authenticated messages per key delivery at 2, reasoning that mutual authentication consumes two one-time keys per round. Validating against two published measurements (E8) showed this is a **lower bound, not a measurement**: Cambridge's measured relay overhead implies ≈7 and SECOQC's application-level tunnel implies ≈40. The headline was then re-checked across `n_auth ∈ {2,7,20,40}` (E6c) and survives — it moves fail-closed availability at k=2 only from 0.302 to 0.281, because one-time-pad ISR traffic dominates the key budget and swamps the authentication term. **Do not re-fix `n_auth` at 2.**

### 2.7 Why there are two paper files

`paper.tex` is the 6-page submission variant. `paper_extended.tex` is the same results with fuller related work, setup and limitations (~7.5 pp), and is the base for a journal version. The page limit in the CFP was never verified (flagged as an open question in `Report.md` §1.4), so both exist rather than guessing. Neither has been compiled — there is no LaTeX on the authoring machine; `experiments/check_tex.py` does structural validation only, and float packing decides the final half page, so the first Overleaf build is where the page count is actually settled.

## 3. The four self-corrections — read these before trusting anything

Four times a claim written down with confidence was refuted by a check that had been deferred. Every refutation improved the paper. This is the project's methodological signature and it should be preserved.

**(1) The γ / e_abort sensitivity.** Claimed in the design, never run. Running it showed the headline is conditional on the adversary crossing the abort threshold, producing the two-threshold law — a sharper result than the original claim.

**(2) A bug caught by an impossible number.** The first classical-denial run returned availability **0.0000 for both fail modes**, which cannot happen while one forward post remains reachable. Cause: `_tick_outages` keyed outage recovery off the `outage` flag rather than adversary-set membership, so every *stochastic* outage also became permanent and the network died over a 24 h horizon. Fixed via an explicit `Simulator._adv_links` set. **The bug produced a plausible number** (total denial under a denial attack sounds right) in a path no unit test covered.

**(3) The ML null was claimed weight-robust; it isn't.** The self-review asserted the heuristic dominates componentwise and flagged "verify before asserting". Verifying refuted it: the searched policy wins **availability 0.9726 vs 0.8123**, paying with 39.5% floor violations. The null holds only for λ > 0.370. The correction produced a better result — an operator indifference point rather than a beaten baseline.

**(4) The novelty framing itself.** See §2.1 — Tysowski 2018 states both branches of the fork.

---

## 4. The eleven findings

Full tables in `RESULTS.md`. Compressed:

1. **The exchange rate is a cliff.** Suppressing links equal to the minimum edge cut (2 of 9) collapses fail-closed availability 0.812 → 0.304, or holds fail-degraded at 0.973 while forcing 69.0% of entitled traffic below its authorised grade. At 5 links: total denial, or total assurance loss, for the same budget.
2. **k\* = minimum edge cut.** The general law; 2 is the instance.
3. **The service metric goes degenerate under a fallback.** Paired availability difference between all three routing policies is **0.0000, CI [0.0000, 0.0000]** — zero width. The metric the key-aware-routing literature reports stops responding.
4. **Key-aware routing is significantly *worse*** under fail-closed (−2.7 pp, CI [−0.0293, −0.0243]) because +6.0% key on marginally longer paths starves later sessions.
5. **Not a tuning artifact.** No hop-penalty setting restores KAR ≥ SP; at penalty 10³ KAR *degenerates into* SP (3.065 vs 3.064 hops).
6. **Reservation floors are a Pareto trade:** availability 0.839 → 0.509 for forced loss 0.357 → 0.0000.
7. **Authentication accounting is workload-dependent:** 2.93× understatement for 256-bit blocks, 1.00× for OTP-dominated. A *capacity-planning* error, not a service error. (⚠ but see §6 — this understates the true discrepancy against measurement.)
8. **Adversary sophistication dominates:** k\* = d+1 greedy vs a flat 2 for min-cut. At d=6, a 3.5× overstatement of resilience.
9. **γ insensitive, e_abort decisive.**
10. **Two-threshold law:** the cliff lands *exactly* at Δe ≥ e_abort − e₀, and saturates immediately above. Both thresholds necessary: per-link capability **and** budget ≥ min-cut. Raising e_abort 0.075 → 0.11 raises required adversary capability **78%** — obtainable from better reconciliation, not more key rate.
11. **The fallback needs the classical channel.** Fail-degraded availability 0.970 → **0.313** under classical-channel denial, only 1.6 points above fail-closed. The entire advantage of degrading gracefully is conditional on the classical channel surviving.

**Plus the ML results:** heuristic attains 104.8% of the best searched policy and wins **7/7** out-of-distribution; λ\* ≈ 0.37 indifference point; training inside the reservoir transient teaches the wrong regime; a single-class assurance floor is gameable (11× key saving by downgrading OTP-entitled traffic).

---

## 5. Parameter provenance — every number traceable

Full chain in `PHASE1_LITERATURE_DOSSIER.md` §2.2, §2.7, §2.8. Load-bearing values:

| Parameter | Value | Source | Status |
|---|---|---|---|
| Nominal QBER e₀ | 0.03 | Tokyo measured 2.7–3.8% | verified |
| e_abort | 0.075 | Tokyo's deployed LDPC ladder has rungs only <3.5/5.5/7.5%, none above | verified |
| ITS zero | 11.0% at f=1.0; **9.9% at f=1.16** | Shor–Preskill; realistic EC *lowers* the cliff | verified |
| Reservoir min/thr/max | 1 048 576 / 11 324 620 / 52 428 800 bit | QKDNetSim shipped SECOQC script (`secoqc_p2p_qkd_system.cc`) | verified from source |
| Authentication reserve rationale | 2 MiB floor "to ensure enough key remains to authenticate future communication" | SECOQC (Peev 2009) — a **non-QoS** floor rationale | verified |
| Relay tag | 127 bit | Walenta arXiv:1309.2583 | verified |
| Metadata | 240 bit (30 B) | Y.3803 Note 2, "a few 10s of bytes" | verified |
| ISR demand | 144 000 bit = **2.4 kbps** × 60 s | Chen 2021 npj QI 7:134 — *"the speed of real-time voice telephone was 2.4 kbps"* | **verified at source in body text** |
| LOG demand | 320 000 bit | same paper — *"the speed of file transmission was 320 kbps"* | **verified at source** |
| C2 demand | 256 bit/rekey | modal industry unit (SwissQuantum, IDQ Geneva, ADVA) | verified |
| Fibre rate | 300 kb/s @ 10 dB | Toshiba LD/MU datasheet | verified |
| FSO rate | ~240 bit/s | DRDO–IIT Delhi, >1 km entanglement, QBER <7% | **secondary source — retrieve PIB PRID 2136702** |
| 64 kbit reservoir (original draft) | **DELETED** | ~3 orders of magnitude below every published value | — |

**Never assert:** any vendor key-storage capacity (absent from ~15 datasheets surveyed — a clean, citable gap), any free-space hard-outage duration or frequency distribution (none published), or any ETSI clause not personally read.

---

## 6. Open items and known problems

### Blocking for submission
1. **Cheng/Sun/Ji 2011** (IET AIAI, pp. 220–224) — citation only, no preprint. If it reports class-level blocking with per-class floors, the related-work positioning needs softening. `paper.tex:527`.
2. **James *et al.* ARES 2023** — abstract verified, ACM full text 403s. `paper.tex:529`.
3. **ETSI GS QKD 014 / 020 clauses** — etsi.org 403s every automated fetch. The "grade as a delivered per-request attribute" gap claim rests on the *absence* of a provenance field. **Do not assert it without reading the clauses.**
4. Author, affiliation, repository URL, first Overleaf build.

### Known model limitation, quantified
**Our authentication model under-charges by ~5.4× for 256-bit blocks against the one published measurement.** SECOQC measured 5824 bit/round with 512 bit cipher key (91.2% authentication); our model gives 750 bit/hop with 494 overhead (65.9%). Consequence: **small-block key-capacity results are optimistic.** This is being addressed as validation check V3 — see the improvement report §1.

### Deliberately out of scope
Terrain-correlated correlated outage on free-space chains (deferred to the journal version); node compromise as a confidentiality event; detector blinding (raises no QBER, so invisible to this model *by construction* — stated as a limitation); measurement validation against real hardware.

---

## 7. Code architecture

```
qkdsim/
  config.py    parameters, each with a provenance comment; grade lattice;
               AdversaryConfig(budget_links, delta_e, targeting, deny_classical)
  physics.py   h2(), rate_fraction() [the four-state rate model], Link, KeyStore
               (QKDNetSim QKDBuffer semantics: 4 states, overflow DISCARDS)
  network.py   Topology (+ path caching), formation_9node, chain_topology,
               select_path_sp / select_path_kar
  sim.py       Simulator: tick loop, adversary targeting (betweenness | mincut),
               grade selection, fail modes, Results with all metrics
  rl.py        state encoding, Shield, TablePolicy, heuristic_table, objective
experiments/
  e1_validation.py      43-check gate -- MUST pass before any result is believed
  run_experiments.py    E2 policy, E3 fail-mode, E4 forcing cost, E5 auth
  e6_hop_penalty.py     is "KAR is worse" a tuning artifact? (no)
  e6b_sensitivity.py    gamma / e_abort / delta_e / classical denial
  e7_policy_audit.py    CEM policy search, shield ablation, OOD grid
  e7_effective_table.py raw -> post-shield policy projection
  make_figures.py       6 vector figures, CVD-validated palette
  check_tex.py          LaTeX structural validation (no local LaTeX available)
  verify_hefei.py       verify the load-bearing 2.4 kbps traffic parameter
```

### Invariants the code enforces (do not break these)
- `D` charged on **every** hop, never once end-to-end; **one debit per link per relay**, not per endpoint.
- Reservoir never negative, never above `m_max`; overflow **discarded** and accounted.
- G4 (PQC-only) consumes **zero** quantum key and routes over links in ABORT — a link in ABORT still has a working classical channel. *This is why the fallback buys availability, and why classical denial defeats it.*
- Common random numbers: identical arrival stream and channel realisation per seed across policies. Without this, paired comparisons are invalid.
- Paired bootstrap over common seeds, 20 000 resamples.

### Environment gotchas
- **Cap worker processes at 8.** ~15 concurrent numpy-importing workers exhausted process resources, surfacing as a spurious numpy import error inside children. `e6b_sensitivity.py` has a batched pool + serial fallback.
- **No local LaTeX.** Use `check_tex.py`, compile on Overleaf.
- **Bash heredocs collapse backslash escapes** — writing Python that emits LaTeX or `\n` via `python - <<EOF` corrupts it. Use the Write tool for scripts.
- Multiprocessing cannot spawn from `python -` stdin on Windows; worker functions must live in a real file.
- Disk was 100% full at one point; `pip` fails silently-ish. Check `df -h /` if installs misbehave.

---

## 8. Reproduction

```
python experiments/e1_validation.py                       # gate: 43/43, exit 0
python experiments/run_experiments.py --seeds 12 --only e2,e3,e5
python experiments/run_experiments.py --seeds 6  --only e4
python experiments/e6_hop_penalty.py
python experiments/e6b_sensitivity.py
python experiments/e7_policy_audit.py --iters 12 --pop 20
python experiments/e7_effective_table.py
python experiments/make_figures.py
python experiments/check_tex.py
```

Deterministic given seeds. Full set ≈30 min on 8 cores, no GPU.

---

## 9. Document map

| File | Role |
|---|---|
| **PROJECT_HANDOFF.md** | this file — context, decisions, gotchas |
| `paper.tex` | IEEEtran submission source (validated, not yet compiled) |
| `PAPER_DRAFT_v2.md` | long-form draft, fuller prose than the .tex |
| `RESULTS.md` | all findings with tables and provenance |
| `PHASE1_LITERATURE_DOSSIER.md` | prior art, parameter provenance, **23 domain errors to avoid** |
| `PHASE2_DESIGN.md` | frozen pre-registration (blank result tables) |
| `REVIEW_self.md` | adversarial self-review + priority fixes |
| `FINAL_IMPROVEMENT_REPORT.md` | the approved change plan currently being executed |
| `Report.md` | original 30-idea venue study (why this topic, who reviews it) |
| `PAPER1_*.md`, `PAPER2_*.md` | **superseded placeholder drafts — numbers in these are invented, do not cite** |

---

## 10. If you are resuming mid-execution

The approved change plan is `FINAL_IMPROVEMENT_REPORT.md` §8. Order: handoff document (this file) → validation V2/V3/V4 → architecture figure → introduction restructure → sensitivity figure → ML section rewrite + conclusion paragraph → Table III → re-check → optional distribution plot.

**The one item not to skip under time pressure is the validation suite (item 4).** It is the only change that alters what the paper knows, and V3 is expected to fail in a way that must be reported.

**Writing standard for the paper:** academic prose in a consistent human voice — varied sentence length, concrete rather than abstract claims, active voice, no formulaic connectives or hedge-stacking. State findings plainly, including the ones that make the approach look worse; that honesty is the paper's distinguishing quality and it also reads as authored rather than generated. Note that IEEE requires disclosure of AI assistance in the acknowledgements.
