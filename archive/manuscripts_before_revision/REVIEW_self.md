# Adversarial self-review — Reviewer 2, WiCOMM-2026

**Paper:** *Fail-Closed or Fail-Degraded? Quantifying Forced Assurance Loss in Contested Multi-Hop QKD Networks*
**Reviewer stance:** systems engineer at a defence electronics lab. Assume I know the QKD networking literature, I have run troposcatter and free-space links, and I punish overclaiming harder than small scope. **My goal is to reject this paper.**

**Recommendation as written: WEAK ACCEPT, conditional on A1–A3 below being addressed.** The contribution is real and the honesty is unusual, but three claims are asserted rather than demonstrated, and one headline number is topology-specific in a way the paper does not admit.

---

## Attacks I would make, in the order I would make them

### A1 — SERIOUS. "You claim two sensitivities and run neither." → **CLOSED by E6b**
§III-B reports two values of γ differing by a factor of five in their prediction (50% vs 10% of nominal at QBER 6%) and two abort thresholds, then presents Table I at a single setting. A sensitivity you *name* but do not *run* is worse than one you omit — it advertises that you knew the exposure.
**Resolution:** E6b re-runs the k=0→k=2 headline across all four (γ, e_abort) combinations. *Result: the qualitative headline holds in all four — fail-closed loses >20 points of availability, fail-degraded gains >20 points of forced assurance loss.* Add as Table V. Without this the paper should not be accepted.

### A2 — SERIOUS. "Fail-degraded availability is 0.9733 for every budget k=0…5. Your fallback is not resilient, it is simply unmodelled." → **CLOSED by E6b, and it improves the paper**
An availability that does not move under a sixteen-fold change in attack effort is a red flag, not a result. I would suspect the adversary never touches anything that matters.
**The true mechanism, which the paper must state:** a link in ABORT has a *pristine classical channel*. ML-KEM needs only that channel. So QBER injection cannot touch G4 service — by construction, not by resilience.
**Resolution:** E6b runs classical-channel denial, which forces OUTAGE and removes the fallback. **This is the attack that defeats fail-degraded, and omitting it materially overstates the fallback's value.** Report both attack modes in Table I. This converts A2 from a weakness into one of the paper's better findings: *the post-quantum fallback buys immunity to quantum-channel attacks and none at all to classical-channel attacks.*

### A3 — MODERATE. "Your headline k=2 is a property of your topology, not a finding."
The 2-of-9 cliff exists because two links are the only quantum-viable route into one brigade node. Redraw the formation and the number changes. As written, §V-A reads as though 2 were general.
**Resolution (no new runs needed).** State the general law that E4 already establishes: **k\* equals the minimum edge cut separating the rear node from the forward posts.** That is topology-independent and testable, and it subsumes both the formation result (min cut 2) and the chain result (min cut 2 at every depth). Rewrite §V-A to present k=2 as *an instance of* k\* = min-cut, and move the topology-specific mechanism to a mechanism sentence. This strengthens the claim rather than weakening it.

### A4 — MODERATE. "Your authorisation policy is infeasible even unattacked, and you do not say so."
Table I shows 16.6% forced assurance loss at k=0 under fail-degraded. The network cannot meet its own policy with no adversary present. Either the policy is wrong or the capacity is, and the paper should say which.
**Resolution:** own it explicitly. At the free-space rates cited, an OTP floor for a 144 kbit ISR session is *not fundable* — the honest reading is that **an OTP authorisation floor is infeasible at current free-space key rates**, which is a useful engineering statement and a natural lead into the derived-capacity discussion. State it in §V-A rather than letting a reviewer find it.

### A5 — SERIOUS (upgraded). "Your objective J is arbitrary, so the ML section's numbers are arbitrary." → **my first answer was WRONG; verified and corrected**
J = availability − 0.5·violations + 0.5·ITS share. Nothing justifies those weights.

**My initial defence claimed the null is weight-robust because the heuristic dominates componentwise. I told myself to verify that before asserting it. Verifying refuted it.** The policies do not order componentwise: the searched policy wins **availability 0.9726 vs 0.8123**, paying with 39.5% floor violations. Solving *J*_h > *J*_s gives the heuristic winning **iff λ > 0.370** at *w* = 0.5 (0.406 at *w* = 0; 0.264 at *w* = 2). **The null is weight-dependent.** Any claim of robust dominance would have been false and a reviewer computing three subtractions would have caught it.

**Resolution, which improves the section:** report the indifference point as the result. λ\* ≈ 0.37 answers a question an operator can act on — *is one forced downgrade of entitled traffic worth more than 0.37 of a served session?* — and locating it genuinely required the search, since λ\* depends on the achievable trade-off surface rather than on the objective. §V-F is rewritten accordingly. This is a better ML contribution than a beaten baseline would have been.

**Lesson, recorded because it repeated:** this is the second time in the project that a claim I was confident enough to write down was refuted by the two-minute check I had told myself to run (the first being the γ / e_abort sensitivity). Both refutations improved the paper.

### A6 — MINOR but I would raise it. "Key-aware routing beating shortest path is a published, replicated result. You claim the opposite. Why should I believe you over them?"
**Defence, which is adequate:** the hop-penalty sweep (Table III) shows the effect survives four orders of magnitude of tuning and that KAR converges to SP rather than beating it. Common random numbers plus paired bootstrap give a CI excluding zero. **But the paper must scope the claim:** this holds in a *key-scarce* regime with *fail-closed* semantics and a *hop-multiplied* cost. Where prior work reports gains, it typically measures blocking under different scarcity and without a fallback. Say "under these conditions", not "in general". A single sentence fixes this; without it, the claim reads as a contradiction of the field and invites a reject.

### A7 — MINOR. "Simulation-to-simulation with no measurement validation."
**Defence is genuinely good and should be foregrounded earlier than §IV:** the SECOQC key-store drain is reproduced to 3584 s against a published field measurement, key conservation is exact, and 43 validation checks gate every result. Move one sentence about the SECOQC reproduction into the introduction's contribution list — it is the strongest credibility signal in the paper and it is currently buried.

### A8 — MINOR. "Three of your references are snippet-only and two are citation-only."
Correct and disqualifying if unfixed, particularly [Schartner] (which the paper leans on for the adversary's *motive*) and [Cheng] (which, if it reports class-level blocking, would undercut §II's positioning). Retrieve or delete. Do not cite an ETSI or NIST clause number that has not been read — the paper currently flags this correctly, which is good practice, but the flags must be resolved before submission.

---

## What I would *not* attack, and why

- **Novelty positioning.** The paper concedes prior art aggressively and repeatedly ("we do not claim this setting is unexamined", "we reproduce these as baselines"). This is the correct posture and I would not be able to land a novelty objection.
- **Terminology.** Correctly distinguishes hybrid (combination) from downgrade (substitution) with primary sources, and avoids "security level" because that term is already overloaded in this literature. A reviewer from the optical-networking community would have caught the latter.
- **The negative ML result.** Reporting that the heuristic beats the learned policy, and that the search overfit the reservoir transient, is more credible than any win would have been. The transient-training finding is genuinely transferable and is arguably the paper's most reusable contribution.
- **Volunteered limitations.** Seven of them, including one blind spot the model *cannot* capture (detector blinding raises no QBER). This raises my confidence in everything else.

---

## Priority fix list before submission

| # | Fix | Cost | Blocking? |
|---|---|---|---|
| A1 | Add the (γ, e_abort) sensitivity table from E6b | table only, data exists | **YES** |
| A2 | Add classical-channel denial as a second attack mode; state that G4 rides the classical channel | table + 2 sentences | **YES** |
| A3 | Recast k=2 as an instance of k\* = min edge cut | rewrite ~1 paragraph | **YES** |
| A4 | State that an OTP floor is unfundable at cited free-space rates | 2 sentences | strongly advised |
| A6 | Scope the anti-KAR claim to key-scarce + fail-closed + hop-multiplied | 1 sentence | strongly advised |
| A5 | Verify and state weight-robustness of the ML null | check CSV, 1 sentence | advised |
| A7 | Move the SECOQC-reproduction sentence into the contributions | 1 sentence | advised |
| A8 | Retrieve or delete snippet-only references | hours of retrieval | **YES** |

With A1–A3 and A8 addressed I would move to **ACCEPT**. The paper's distinguishing quality is that it reports four results that make its own approach look worse — degenerate routing metric, harmful key-awareness, a gameable shield, and a learned policy that loses — and that is exactly what makes the positive result credible.
