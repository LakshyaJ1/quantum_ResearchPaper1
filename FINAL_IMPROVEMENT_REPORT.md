# FINAL IMPROVEMENT REPORT

**Paper:** *Fail-Closed or Fail-Degraded? Quantifying Forced Assurance Loss in Contested Multi-Hop QKD Networks*
**Purpose:** adjudicate six review items. **No paper changes have been made.** Each item was treated as a research question and checked against the artifact, not accepted at face value.
**Two of six are misdiagnosed**, and **one is far more valuable than the feedback realised** — it would find a real error in our model.

---

## 0. Verdict summary

| # | Item | Verdict | Effort | Acceptance gain | Scientific value | Risk |
|---|---|---|---|---|---|---|
| 4 | Validation breadth | **MUST DO** (redirected) | 3–5 h | **High** | **Very high** — finds a real model error | Low (finding is publishable either way) |
| 2 | Handoff / context document | **MUST DO** | 1–2 h | None (not in paper) | High (project continuity) | None |
| 1a | System architecture figure | **MUST DO** | 2–3 h | **High** | Medium | Low |
| 5 | Introduction restructure | **SHOULD DO** (misdiagnosed) | 2–3 h | Medium–high | Low | Low |
| 1b | ML section expansion (~½ page) | **SHOULD DO** | 4–6 h | Low–medium | **High** | **Medium** — venue-fit |
| 1c | Conclusion AI paragraph | **SHOULD DO** | 30 min | Low | Medium | Low |
| 3a | Sensitivity visualisation | **SHOULD DO** | 1–2 h | Medium | Medium | Low |
| 6 | Table III readability | **SHOULD DO** (not as proposed) | 1 h | Low–medium | Low | Low |
| 3b | Distribution / variance plots | **OPTIONAL** | 2 h | Low | Low–medium | Low (costs space) |
| 4x | Cross-validate vs NetSquid / QuISP / SeQUeNCe | **DO NOT ADD** | — | — | — | Impossible; see §4 |
| 4y | QKDNetSim cross-validation before submission | **DO NOT ADD** (future work) | 1–3 days | Low | Medium | High |
| 1x | Reframe as an AI paper / change title | **DO NOT ADD** | — | **Negative** | — | High |

**Total recommended effort: 15–20 h.** Space is available: body is **3 673 words** against an IEEE 6-page budget of ~5 000–5 800, i.e. **~1 300–2 100 words (1–1.7 pages) spare.** Every recommendation below fits without cutting existing content.

---

## 1. Item 4 — Validation breadth. **MUST DO, and it is the most valuable item here**

### The feedback
*"The simulator is validated against only one published SECOQC measurement — that is weak. Better validation could include NetSquid, QuISP, QKDNetSim, multiple published datasets."*

### What I checked
The criticism is **correct and it is the single strongest reject-risk in the paper**. But the proposed remedies split into one that is impossible, one that is impractical, and one that is both cheap and far more valuable than suggested.

**(a) NetSquid / QuISP / SeQUeNCe cross-validation is impossible, not merely hard.** Source-tree inspection (recorded in the Phase-1 dossier §2.6) established that none of the three contains a trusted-relay or key-pool model at all: SeQUeNCe's `sequence/qkd/` is point-to-point BB84 plus Cascade; QuISP has no key pools; NetSquid has neither, and additionally gates both package and documentation behind registration with no OSI licence. **You cannot cross-validate a trusted-relay key-economy simulator against tools that do not model trusted relay or key economies.** This is a factual answer with evidence, not an excuse, and the paper should state it in exactly those terms.

**(b) QKDNetSim cross-validation is the only genuine option and should be future work.** It does have the `QKDBuffer` and `Relay()` machinery. But it requires an ns-3 3.46 source build plus `git apply` patches, its README and project site disagree on the ns-3 version, its repository history was squashed with no tags or releases, and QKDNetSim+ (arXiv:2402.10822) **found that nodes did not adequately process received key material and that the crypto handler malfunctioned — in exactly the layer we would be validating against.** Validating against a tool with known defects in the layer under test is not obviously an improvement. Effort 1–3 days with a real chance of failure. Recommend: state this reasoning explicitly and list it as future work.

**(c) "Multiple published datasets" is the right instinct and is nearly free — because we already hold the numbers.** We currently use Tokyo, Cambridge, Hefei, SwissQuantum, SECOQC and Ciena/JPMorgan measurements as **parameter provenance** but reproduce only one as a **validation target**. Three more independent reproductions are available at trivial cost. I tested whether they would pass:

| Check | Measured | Our model | Outcome |
|---|---|---|---|
| **V1 (existing)** SECOQC key-store drain | 3.5 MiB at 8192 bit/s ≈ 1 h | **3584 s** vs reference 3584 s | **passes exactly** |
| **V2 (new)** Cambridge relay overhead | 1000 global keys ← ~180 kbyte QKD key ⇒ **3.69×** for a ~400-bit key | 2.23× at 1 hop, 4.47× at 2 hops | **passes conditionally** — measured value sits between; implies mean relay length ≈1.61 hops, plausible for a 3-node triangle but must be justified |
| **V3 (new)** SECOQC AES-VPN authentication share | 5824 bit/round, 512 bit cipher ⇒ **91.2% authentication** | 750 bit/hop, 494 overhead ⇒ **65.9%** | **FAILS — we under-charge authentication by 5.4×** |
| **V4 (new)** Hefei OTP voice capacity | 11 simultaneous 2.4 kbps OTP pairs on 6–60.5 kbps links | not yet tested | unknown |

### Why this is the highest-value item in the report
**V3 fails, and the failure matters.** Our authentication model charges 494 bits of overhead on a 256-bit block; the one published measurement of a comparable case charges ~5 312. So:

1. **Our small-block key-capacity results are optimistic**, by up to ~5× on the overhead term.
2. **Our E5 headline is itself understated.** We currently report that the literature's bare *D·n* law understates key consumption by 2.93×. Against measurement the true understatement for small blocks is substantially larger. That strengthens the finding rather than weakening it.
3. It converts "validated against one measurement" into "validated against four, with one discrepancy quantified and its direction stated" — which is a **stronger** position than four clean passes, because it demonstrates the validation is capable of failing.

**A validation suite that cannot fail is not a validation suite.** This is the item I would prioritise above all others.

### Plan
1. Add V2, V3, V4 to `experiments/e1_validation.py` as reported checks (not hard gates, since V3 is expected to fail).
2. Investigate V3: determine whether SECOQC's "two portions of 256 bits on both sides" implies 4×256 cipher bits, and whether their per-round overhead includes IPsec framing we do not model. Either reconcile or report the residual honestly.
3. Add a short §IV subsection: *Validation against published measurements*, with a four-row table.
4. State the (a) and (b) findings above in one paragraph, factually and with citations.

**Risk:** low. If V3 cannot be reconciled we report the discrepancy and adjust the E5 claim's direction — which is a finding. **Acceptance gain: high**, because "only one validation" is exactly the objection a systems-lab reviewer raises first.

---

## 2. Item 2 — Handoff / context document. **MUST DO**

Straightforward and necessary: a single markdown file sufficient for another researcher (or a post-compaction session) to resume from scratch — the repositioning history and *why* it happened, every literature decision and its evidence status, all parameter provenance, the eleven findings with the commands that produce them, the four self-corrections and what they teach, the known-open items, and the file map.

Distinct from the existing documents, which are each partial: the dossier is literature-only, the design document is pre-registration, RESULTS is findings-only. Nothing currently records the *decision history* — why the paper was repositioned, why the horizon changed from 4 h to 24 h, why γ has two values.

**Effort 1–2 h · no paper impact · high project value · no risk.** Recommend writing it first, since everything else risks context loss.

---

## 3. Item 1 — AI/ML content. **SHOULD DO, with an important caveat**

### The research question you actually asked
*Is there a genuine AI contribution that emerges from this work without forcing it?*

**Yes — four, and they are already in the data.** None requires new experiments. This is the important finding of this section: you do not need to add AI work, you need to *write up AI work you have already done and currently under-report in six lines.*

**A1 — Specification gaming in a safety-constrained control task.** The unshielded search cut key consumption 11× (464→42 Mbit) while keeping 100% of traffic on ITS-*delivered* key, by serving one-time-pad-entitled traffic at G2. It satisfied the letter of the objective while violating its intent, and the shield failed to prevent it because it constrained only one traffic class. This is a discovered — not constructed — specification-gaming instance in a security-critical domain, and the lesson (*per-class floors must be specified and priced, not just the top class*) is transferable.

**A2 — Non-stationarity from resource depletion, and training-window design.** The searched policy beat the heuristic at a 6 h training horizon and lost at 24 h, because the 6 h window sat inside the 12 h reservoir drain-from-full transient where key is still abundant. Generalisable claim: **in environments with a depletable resource, the training horizon must span the depletion timescale or the agent learns a regime the deployed system leaves.** This is a measured instance of a real RL environment-design failure, and it is a *specific, checkable critique of the QKD-RL literature* — none of the learned-routing papers (Johann 2026, Hao 2025, Xie 2025, Seok 2025) reports its training horizon relative to reservoir dynamics.

**A3 — Interpretability by construction versus post-hoc distillation.** We searched a 12-cell tabular policy rather than training a network and distilling it (VIPER-style). Consequence: no distillation step, no fidelity loss to report, auditable by inspection. And there is a genuine interpretability trap worth reporting: the *raw* table assigns G4 to command traffic in one state, while the *effective* (post-shield) policy assigns G1 — a reader of the raw policy would wrongly conclude the safety guarantee was violated. Reporting effective rather than raw policies is a small, transferable methodological point.

**A4 — Policy search as preference elicitation rather than optimisation.** λ\* ≈ 0.37 locates the operator's indifference point: *is one forced downgrade worth more or less than 0.37 of a served session?* Using search to find where a decision flips — rather than to beat a baseline — directly answers "why bother with learning if the heuristic wins", and λ\* is only obtainable by search because it depends on the achievable trade-off surface, a property of the key economy rather than of the objective.

### Is half a page available? **Yes.**
Body is 3 673 words against ~5 000–5 800. Half a page in IEEE two-column is ~450–500 words. Affordable with room left for the architecture figure and a sensitivity figure.

### The caveat you should weigh — and it is a real tension
This is a defence **communications** venue reviewed by systems engineers. Your own venue study warns (§0.3, finding 1) that a paper reading as machine learning gets triaged as off-topic, and that the same work framed around the communications problem gets read. So:

- **Expand §V-F from ~0.6 to ~1.1 pages. Do not touch the title, and do not add ML to the abstract's opening.** The ML must remain the last results subsection, framed as *why learning did not help here and what that teaches*, not as a contribution competing with the systems results.
- **There is a genuine conflict between what is best for this paper and what is best for your portfolio.** A half-page of well-argued negative-result AI content is the most this venue will reward. The full AI contribution — A1–A4 developed properly, benchmarked honestly against Johann 2026, with a larger search budget — is a *second paper* at an ML-literate venue, which the Phase-1 dossier already recommended. That paper would represent your AI background far better than anything this one can carry. **I recommend doing both, in that order, and not overloading this one.**

### Sub-item 1a — system architecture figure. **MUST DO, independent of the AI question**
The paper currently has **no architecture or topology figure at all.** That is a straightforward defect: your venue study lists a legible architecture diagram as an acceptance factor, the IEEE skeleton specifies one for the System Model section, and a reader cannot presently see the nine-node formation, the grade lattice, or where the control policy sits relative to the key economy. One figure serves the systems reading *and* the AI reading (it shows the policy's action space and the shield's position in the loop). **Effort 2–3 h · high acceptance gain · low risk.**

### Sub-item 1c — conclusion paragraph. **SHOULD DO**
One paragraph stating that interpretable heuristics outperformed learned policies under distribution shift, with the mechanism (transient training) and the transferable lesson. **30 minutes**, and it is the sentence an AI-aware reader will remember.

### Plan for item 1
1. Architecture figure: block diagram — key economy (reservoirs, per-hop accounting) → control plane (routing, admission, grade selection, shield) → assurance grades → metrics, with the adversary's two attack surfaces (quantum channel, classical channel) marked. Single column.
2. Rewrite §V-F to ~1.1 pages, organised as: *why learning was considered* (the literature is saturated with learned routing, so we asked a different question) → *why the heuristic won* (λ\* boundary, componentwise non-dominance) → *why the shift occurred* (A2, transient) → *why interpretability was chosen* (A3) → *what gaming revealed* (A1) → *why this is an AI result*.
3. Conclusion paragraph.
4. **Do not** change title, abstract emphasis, or the contribution ordering.

---

## 4. Item 5 — Introduction. **SHOULD DO, but the feedback is misdiagnosed**

### The feedback
*"60–70% of the introduction is actually Related Work."*

### What I measured
Introduction is `paper.tex:69–121`, 53 lines, 5 paragraphs:

| Para | Lines | % | Content | Belongs in Intro? |
|---|---|---|---|---|
| 1 | 5 | 9% | QKD trusted relay, hop multiplier, scarcity | **Yes** — background |
| 2 | 12 | 23% | The standards-vs-security disagreement | **Yes** — this *is* the problem statement, delivered through literature |
| 3 | 10 | 19% | Tysowski credit | **No** — related work (but the closing gap sentence stays) |
| 4 | 8 | 15% | "What we do not claim" | **No** — pure related work, 6 citations, duplicates §II |
| 5 | 13 | 25% | Contributions | **Yes** |

**Literature-only content is 34%, not 60–70%.** The figure rises to ~57% only if paragraph 2 is counted as related work, which would be wrong — the disagreement *is* the research problem, and stating it requires citing the two positions.

**However, there is a real and arguably worse defect the feedback missed: there is no problem statement in operational terms, and no "why this matters".** The introduction goes physics → literature disagreement → contributions. It never says why a tactical operator should care, and it contains no operational scenario. Your own venue study is explicit that the operational scene belongs in the first two sentences for this reviewer pool. So the fix is not merely "move related work out" — it is "add the missing motivation, and move the duplicated literature out to make room".

### Plan
- Add 3–4 sentences of operational framing at the very top (relay chain in mountainous terrain, command/imagery/logistics traffic, what an outage versus a silent downgrade means to a commander).
- **Delete paragraph 4 entirely** — it duplicates §II and Table I already carries the positioning.
- Compress paragraph 3 from 10 lines to ~4, keeping the Tysowski quotation (it is load-bearing for the novelty claim) and moving the rest to §II.
- Add an explicit one-sentence gap statement and an explicit "why it matters" sentence before the contributions.

**Net: roughly space-neutral.** Effort 2–3 h · medium–high acceptance gain (first-page impressions decide triage) · low scientific value · low risk.

---

## 5. Item 6 — Table III readability. **SHOULD DO, but not as proposed**

### The feedback
*"Table III is dense. Splitting into Availability and Routing Cost would improve readability."*

### What I checked
Table III (`tab:policy`) is 6 columns × 6 rows: Mode, Policy, Availability, Forced, Hops, Key. Six columns is not objectively dense — Table I carries eight. **The real readability problems are different:**

1. **The fail-degraded rows show `---` in the Forced column**, which reads as missing data. It is not: those rows are the degenerate case where all three policies coincide.
2. **The paper's actual result for this table — the paired differences and their confidence intervals — is in the prose, not the table.** A reader cannot see from the table that KAR's −2.7 points is significant while the fail-degraded differences are exactly zero. That is the substantive readability defect.

**Splitting into two tables would make this worse**, not better: it costs two captions in a tight page budget and it breaks the paired within-mode comparison, which is the whole point of using common random numbers.

### Plan
Keep one table. Add a **paired Δ vs SP [95% CI]** column. Replace `---` with an explicit `0.000` plus a footnote that all policies coincide under fail-degraded operation. Consider moving Hops to a footnote if width becomes a problem.

**Effort 1 h · low–medium acceptance gain · low risk.** This improves rigour as well as readability, which the proposed split would not.

---

## 6. Item 3 — More visualisation. **SPLIT VERDICT**

### 3a — Sensitivity visualisation. **SHOULD DO**
The two-threshold law (Δ*e* ≥ *e*_abort − e₀ **and** *k* ≥ min-cut) is the paper's sharpest and most quotable result and it currently exists **only as a table**. A 2-D visualisation — availability or forced loss over the (Δ*e*, *k*) plane, with the two thresholds drawn as lines — would make a predictive law immediately legible and is the figure most likely to be remembered.

Caution from the visualisation method already applied to the existing figures: a heatmap needs a **sequential single-hue ramp**, not a rainbow, and must stay legible in greyscale. A small-multiples panel (one line plot per *e*_abort) is the safer choice for print and I would default to that unless the heatmap validates cleanly.

**Effort 1–2 h · medium acceptance gain · medium scientific value · low risk.** Data already exists in `results/e6b_sensitivity.csv`.

### 3b — Distribution and variance plots. **OPTIONAL**
Variance is already reported: every table carries SD over 12 seeds, and every headline claim carries a paired bootstrap CI. A distribution plot would add rigour at the margin but would mostly re-present information already present numerically. In a 6-page budget it competes directly with the architecture figure and the sensitivity figure, both of which carry more.

**If space remains after everything else**, the highest-value option is a **time-to-key CDF by traffic class** — it would show the C2/ISR/LOG asymmetry that currently appears only as two summary statistics. Effort 2 h · low acceptance gain · low–medium value · low risk (costs space).

---

## 7. Explicit DO NOT ADD list

| Proposal | Why not |
|---|---|
| Cross-validate against **NetSquid, QuISP, SeQUeNCe** | **Impossible.** Verified by source inspection: none models trusted relay or key pools. Cannot cross-validate a key-economy simulator against tools with no key economy. State this as a fact with evidence. |
| **QKDNetSim** cross-validation before submission | 1–3 days, brittle toolchain (ns-3 source build + patches, version disagreement in its own docs), and QKDNetSim+ documented defects in *exactly* the layer under test. Future work with the reasoning stated. |
| Reframe as an **AI paper**, change the title, or lead the abstract with ML | **Negative acceptance impact** at this venue by your own study's finding. The AI content belongs as the final results subsection plus a conclusion paragraph. |
| Split Table III as proposed | Breaks the paired comparison and costs space; the actual defect is the missing Δ/CI column. |
| New ML experiments (bigger search, DQN, GNN) | Not needed for this paper — A1–A4 already exist in the data. Belongs to the follow-up ML-venue paper. |

---

## 8. Recommended execution order

1. **Item 2** — handoff document (1–2 h). First, so nothing is lost to context compaction.
2. **Item 4** — validation suite V2/V3/V4 + investigate the V3 discrepancy (3–5 h). Highest value; may change an E5 claim, so it must precede final writing.
3. **Item 1a** — architecture figure (2–3 h).
4. **Item 5** — introduction restructure (2–3 h).
5. **Item 3a** — sensitivity figure (1–2 h).
6. **Item 1b + 1c** — ML section rewrite and conclusion paragraph (5–7 h).
7. **Item 6** — Table III (1 h).
8. Re-run `check_tex.py`, confirm page count on first Overleaf build, then re-run the adversarial review pass.
9. **Item 3b** — only if space remains.

**Total 15–20 h.** Item 4 is the one I would not skip under any time pressure; item 3b is the one to drop first.

---

## 9. Honest assessment of what this changes

**Acceptance probability.** The paper is currently a weak-accept in my own adversarial reading, with "validated against a single measurement" and a literature-heavy first page as the two most likely reject grounds. Items 4, 1a and 5 address exactly those. I would expect a solid accept afterwards, contingent on the two remaining paywalled references.

**Scientific quality.** Item 4 is the only one that changes what the paper *knows* — it will likely show our authentication model is optimistic by ~5× on small blocks, which sharpens an existing finding and strengthens the honesty of the validation story. Everything else improves communication rather than content.

**Your AI representation.** The four AI findings are real and worth writing up properly, and half a page is affordable. But be clear-eyed: half a page in a defence communications paper will not represent an AI background well. The follow-up paper — negative results on learned control for key-scarce QKD networks, with the transient-training critique aimed at the existing QKD-RL literature — is the vehicle that would, and it is a genuinely publishable paper on the strength of A1 and A2 alone.
