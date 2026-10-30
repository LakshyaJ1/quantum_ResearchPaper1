# Scientific editorial review of paper_revised.tex

Read-only review of the working manuscript, completed main summaries and comparisons, deterministic theory records, model/protocol code, and verified source register. Incomplete held-out learning outcomes were not opened. Remaining-results sections are deliberately pending and are not treated as omissions to be filled with conjecture. The manuscript itself was not edited.

The current scientific framing is substantially improved: key service is distinguished from payload delivery, retained stock is separated from production, G2 does not claim ITS payload encryption, forced loss uses entitled arrivals, the cut budget is necessary rather than achievable, and the learning guarantee belongs to the monitor. All current numerical outcome assertions and table values checked below agree with their cited machine-readable evidence at the displayed precision.

Priority corrections

At line 54, change “zero above it” to “zero at or above it.” The implementation uses QBER greater than or equal to the abort threshold in qkdsim/physics.py:44-45 and 87-102. Add “where H_2 is binary entropy.” Using e for both an edge index and its QBER argument in R_e(e) is avoidable: use x for the scalar QBER in Eq. (2), retaining e as the link index. This does not change the model.

At lines 79-82, define a vertex set W and use delta(W), leaving U_e for usable stock. A precise replacement lead is: “Fix a vertex set W. Let C_W(T) contain floor-compliant requests completed by T whose endpoints lie on opposite sides of delta(W), and let q_s be the minimum per-hop debit among grades meeting request s's floor.” This closes both the undefined cut symbol and the meaning of minimum debit. Gross G_e before overflow and separate usable stock U_e are now correct.

At line 74, make D_ITS explicitly a subset of E intersect S, and change “released tables” to “accompanying tables.” No verified public artifact release address is present. Define the served-entitled denominator of F_given_S as |E intersect S| if that conditional statistic is retained in the paper. “ITS-key-entitled” should consistently mean requests whose floor is G1 or G2, not every request using some quantum bits.

At line 107, specify “independent free-space generation and all-link transport failures.” revision/scenarios.py:175-181 does not apply the stochastic generation-down process to fiber. The common correlated process also affects only free-space generators. At line 48, “A transport-disconnected request cannot be served, even with pre-positioned key material” is more precise than suggesting any single transport failure kills all service despite alternate paths.

At line 32, omit “tabular” before Q-learning. The verified Hao evidence is its publisher-deposited abstract, which supports Q-learning with discretized occupancy but was not accompanied by accessible full algorithm text. The narrower wording loses no useful contrast with this paper's grade action. Other related-work descriptions are consistent with source-register entries L01–L03 and L05–L16, including preprint status and the selected legacy buffer constants. The prior-art credit can be shortened as proposed below without replacing it with an absence claim.

At lines 18 and 109, say policy comparisons are paired “within each condition,” and identify reported percentages as means of seedwise proportions. Same-topology policy/attack pairs share exogenous realizations; changed topologies and changed outage conditions do not represent one identical physical realization. The displayed figures already use means of twelve seed rates, not pooled counts.

At line 100, “best validation-selected restart finalist under this search budget” is more exact than “best found”: validation compares two training-selected finalists, not every candidate encountered. Keep the states, actions, budget, search sizes, horizons and split logic. The current conditional-CI and horizon-causality qualifications at lines 109 and 139 are appropriate. For compact reproducibility, spell out validation as three conditions times four seeds and retain the exact seed lists and full test roster in the artifact.

When the remaining results are inserted, explicitly identify the main case as retained stock and generation suppression for the full arrival horizon; the default selected-link QBER increment is 0.05, taking nominal 0.03 to 0.08. The current low-reserve framing is appropriate. Do not imply the 2% result is a full-reservoir deployment, that seven authentication messages were independently calibrated, or that the method found an optimal finite-horizon attacker.

Quantitative audit

| Manuscript location | Checked claim | Evidence and verdict |
|---|---|---|
| Abstract, lines 115 and 132 | Closed 6.70%, unrestricted fallback 97.53%, fallback qualified 6.61%, offered-entitled loss 90.08% with [89.20,90.97], below-floor payload fraction 92.24%, no-attack closed 97.53% | main_summary.csv and main_numbers.tex agree after rounding. The no-attack and attacked fallback service happen to round to the same 97.53%; their assurance outcomes differ. |
| Line 115 | Qualified-service difference -0.09 percentage points with [-0.11,-0.07] | main_paired_comparisons.csv gives -0.0943630 pp with [-0.1141472,-0.0732426]. Correct. |
| Class table | All nine means and eighteen interval endpoints | class_table.tex matches the three class rows of main_summary.csv under the two-edge cut. Closed Q equals closed A. Correct. |
| Lines 50-65 | QBER 0.03, f=1.16, thresholds 0.075/0.11, gamma 1/3.4; four grade demands; 240-bit metadata and 127-bit tag; n_auth 7/2/40 gives G2 debits 1385/750/5576 | Matches PhysicsConfig, quantum_key_demand and AccountingConfig. These are specified parameters, not physical validation. Only the equality wording at the threshold needs correction. |
| Line 65 | Payloads 2048/144000/320000; deadlines 5/30/120; rates 0.05/0.002/0.03; mean debit 397.218 bit/s versus 480 bit/s; ISR scales 0.03/0.1/1 | Matches the traffic classes and Case construction. Arithmetic is 0.05(1385)+0.002(145129)+0.03(1257)=397.218. The text correctly calls this a nominal capacity check, not stability evidence. |
| Lines 76 and 86 | Importance vectors; 3 times 1900/750 pooled count 7 versus actual 6, residual 400 per source-side branch; 4 times 749/750 pooled count 3 versus actual 0 | Matches revision_analyze.py and completed theory_checks.json. The parallel fixtures have two-hop branches with matching per-edge stocks; add “two-hop” once if space permits. |
| Lines 90-100 | 0.5-second hop penalty; at most four paths/plus two hops; 18 states, five actions, 20% urgency; 0/0.1/0.1 exception budgets; 10 tables times 4 generations times 2 restarts; six rollouts each; 6/24-hour horizons; 12 validation cells; 12 final seeds over 7 conditions | Matches model and registered learning code. These are protocol facts; no held-out performance was inspected. Committed-services accounting and the completed-subset argument are consistent with the sequential implementation. |
| Lines 103-105 | Formation (8,9); ring eight; grid 3 by 3; parallel graphs (8,9)/(10,12); relevant cuts 1 per formation leaf and 2 all-terminal, other terminal cuts 2/2/3/4; rates 200–400/300000 and 240; capacity/threshold/reserve 52428800/11324620/1048576; 50 Mibit; 2% spendable initial stock 1027604.48 bits | Matches graph constructors and config. Buffer parameter provenance is L13, not a hardware capacity claim. Main weighted formation all-terminal cut costs two at fiber weight ten. |
| Lines 107-109 | Relative costs 1 versus 10, sensitivity 1/100; up/down 3600/120 and correlated 900/600; 1-second ticks, 24 hours, main/sensitivity/threshold seed counts 12/8/6, 20000 bootstrap resamples | Matches code and manifests. Main is complete at 360 runs; sensitivity and threshold manifests were incomplete during this review, so their settings are confirmed but outcomes remain pending. Separate fallback comparison has eight seeds. |
| Bibliography | Standards, DOI/preprint status, legacy commit 394bfed in 2024 | Matches the verified source register. The paper does not reproduce the old unverified physical-validation claims. Preserve the explicit response explaining why historical checks were reclassified. |

The main abstract's 360 simulations include no-attack, one-link and full-cut cells: they are 30 configurations times twelve seeds, not 360 full-cut runs. Current phrasing is acceptable, but “A 360-run, five-topology grid includes 24-hour generation cuts...” is unambiguous. No current numerical mismatch requires rerunning the completed main experiments.

Word-reduction package

The following nine complete paragraph replacements save 311 whitespace-delimited source words against the reviewed version. A typesetting word counter may differ because of TeX commands and hyphenation. They preserve the substantive AI/ML protocol at lines 90–100 and retain specific assumptions where needed. Apply by matching paragraph content if ongoing edits have moved line numbers. The scientific correction suggestions above add only a small amount of text, leaving the net reduction within the requested 250–400 words.

Replace the paragraph at line 25 (43 source words saved):

```tex
QKD key-supply interruptions can be handled by waiting, blocking or computational fallback. ITU-T Y.3803 permits policy-controlled symmetric relay substitution and records the method~\cite{itu}; Tysowski \emph{et al.} describe fallback and blocking~\cite{tysowski}, and Spooren \emph{et al.} implement layered failure timers~\cite{spooren}. We examine how these choices interact with usable stored key.
```

Replace the paragraph at line 27 (42 source words saved):

```tex
A relay formation may mix command-key requests, an expensive one-time-pad class and logistics traffic. We distinguish successful key service from satisfaction of its assurance requirement, and loss of replenishment from loss of accepted stored key.
```

Replace the paragraph at line 29 (55 source words saved):

```tex
We evaluate finite reserves, interruption duration, relative link-suppression budgets and learned grade allocation under class-specific exception permissions. Timely and floor-compliant service share an arrival denominator; ITS-key entitlement, payload and class-importance metrics expose different losses. A cumulative cut-budget inequality and exact fixtures delimit feasible service. The learning study compares a compact controller with a greedy policy under the same monitor.
```

Replace the paragraph at line 34 (47 source words saved):

```tex
Opportunistic QKD studies single-link reservoirs and correlated depletion/recovery~\cite{opportunistic}; QuIKS combines end-to-end buffering, reactive control and device traces~\cite{quiks}; Zhu studies finite buffers, fallback fractions and class-sensitive output~\cite{zhu}. Building on these, we jointly evaluate targeted generation interruptions, relative link costs, paired excess entitlement loss and learned class-exception allocation.
```

Replace the paragraph at line 36 (20 source words saved):

```tex
Established runtime filtering~\cite{shield} motivates our deterministic prefix-count exception monitor, whose contract is specified below.
```

Replace the paragraph at line 46 (28 source words saved):

```tex
Stored keys are retained while synchronized, unexpired and uncompromised. The purge alternative discards spendable stock when generation fails but preserves the protected reserve. These alternatives reflect the generation/storage distinction~\cite{itu} and implementation-dependent shutdown or synchronization policies~\cite{tysowski}.
```

Replace the paragraph at line 57 (25 source words saved):

```tex
The policy order is G1, G2, G3, G4. G1 requires payload-length OTP key; G2 a 256-bit QKD-delivered symmetric key; G3 128 QKD bits as a hybrid ingredient; and G4 no quantum key. G2 classifies information-theoretic key delivery with computational payload encryption. The ordering specifies contracts, not universal cryptographic strength or hybrid-combiner security.
```

Replace the paragraph at line 111 (15 source words saved):

```tex
Verification checks conservation, reserve and deadline invariants, exact resource fixtures, matched exogenous traces and prefix budgets. Published accounting and capacity comparisons provide provenance and consistency checks; this study includes no independent network or cryptographic validation.
```

Replace the paragraph at line 137 (36 source words saved):

```tex
The simulator assumes trusted relays, synchronized valid stores, instant state information and atomic debits. It does not model payload transmission, cipher/KEM execution or relay compromise. Finite candidate routes, fixed class payloads and illustrative supply/outage processes limit external validity. Payload and priority weights measure contractual exposure, not realized harm.
```

Keep the unique qualifications near their mechanism: valid retained stock, contractual grade order, illustrative n_auth, unmatched arrival/completion horizons, marginal intervals conditional on the selected table, and the horizon intervention's changed exposure/state coverage. Those are interpretive requirements. Repeated statements that this is not new theory, not hardware validation, not universal strength ordering, or not an exhaustive literature review can be consolidated instead of repeated after each contribution.

For the remaining approximately 600 words, prioritize concrete sensitivity outcomes, the limited online-attack result, and held-out learned-versus-greedy differences with intervals. Reuse the definitions already given; do not spend that space re-explaining A, Q, F or the prefix monitor. A paired null or negative learning result remains substantive evidence. This review establishes consistency of the current text, not final scientific acceptance, page compliance after additions, or external certification.

