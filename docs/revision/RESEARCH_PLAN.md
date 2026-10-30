# Research revision plan

## Objective and delivery constraints

Revise WiCOMM 2026 paper 167 against both official review PDFs using reproducible numerical evidence. Preserve a substantial AI and machine learning contribution without implying learning is useful before testing it. The camera-ready paper must be 4 to 6 pages in IEEE conference format. Deliver matching LaTeX, Word, and PDF manuscripts, a reviewer compliance PDF, reproducible source code and results, and a beginner explanation. IEEE PDF eXpress certification (conference 69954X) is a separate external step; local PDF validation is not certification. The supplied deadline is 30 September 2026. Author names must not change from the initial submission.

## Preservation and evidence policy

The starting tracked code is commit `0d1e2fa`; `archive/code_before_revision_0d1e2fa.zip` preserves it. The starting manuscript and notes are copied to `archive/manuscripts_before_revision`. Historical result files remain in `results/`; new runs go only to `results/revision/`. Existing literature dossiers are search leads, not proof. Cite primary documents actually retrieved or explicitly label an inaccessible source. A simulated rate, assumed workload, policy limit, fitted parameter, arithmetic consistency check, and hardware measurement must remain distinguishable.

## Research design

The original model conflates stopping new key generation with invalidating previously generated keys. Correct the stock-flow distinction first. A finite key reserve may continue to support relay over a working authenticated classical channel after quantum generation stops. This motivates a finite-horizon assurance survival analysis, rather than a claim that a generation cut instantly eliminates all quantum-key service.

Compare fail-closed, unrestricted fallback, fixed interpretable control, and learned control on the same arrival and outage realization. Report timely availability and floor-compliant availability with the same arrival denominator. Report entitled requests blocked, served with their required key assurance, or degraded as an exhaustive decomposition. Report both request-weighted and payload-weighted loss. Payload exposure is not a measured harm or sensitivity scale. Estimate attack-attributable change using paired attack and no-attack runs under the same environment; do not assign every adverse outcome to the adversary.

A policy-learning experiment will use disjoint simulator seeds for training, selection, and final evaluation. Preserve raw per-seed results and all candidate/search metadata. Compare a modest interpretable policy class against the heuristic in the same class. Evaluate nominal training and training across varied environments; separately assess the impact of training before versus after reserve depletion. Any runtime guarantee comes from its explicit deterministic action filter, not the learning procedure. The search optimum is only the best observed candidate within a recorded search budget.

The additional analytical result is a cumulative cut-budget necessary condition derived from conservation of stored and generated key. Validate exact special cases with deterministic workloads and use it as a bound, not as a universal equality for routed stochastic multi-class service. Heterogeneous disruption costs are scenario weights, not measured attack expenditure. Do not present graph-theoretic identities as new discoveries.

## Work packages and ownership

The official-review agent owns `official_review_matrix.md`, source extraction, and `literature_verified.md`. It maps every review comment and question to a concrete revision and verifies reference status. The core-code agent owns corrections in existing `qkdsim` modules and `tests/test_revision_core.py`, including stored-key usability, deadlines, policy-floor enforcement, and measurement-window consistency. The documentation agent owns `RESEARCH_EXPLAINED.md`, a repository coverage map, and `finite_reservoir_theory.md`. The coordinating agent owns new revision experiment modules, statistical analysis, figures, manuscript construction, and final integration.

## Verification sequence

First reproduce the historical validation gate and at least one historical run. Record defects with focused regression tests before changing semantics. Then pass the corrected invariant and deadline tests. Next test the revision scenario generator, policy budget enforcement, attack/no-attack pairing, and analytical special cases before a large run. Benchmark and use at most eight simulation processes total. Freeze experiment settings before final test evaluation and save code hashes, dependency versions, seeds, configuration, timings, and raw metrics. Analyze seed-level paired differences with confidence intervals, including class-specific outcomes and multiple uncertainty sources kept separate.

The main numerical grid covers multiple graph families with terminal cut sizes 1 through 4, free-space and mixed-media settings, conservative authentication count 7 with 2 and 40 sensitivities, sustainable and overloaded OTP-class arrival rates, independent and correlated environmental events, finite disruption durations, adaptive versus static targeting, and separate loss of quantum generation and classical transport. Main results must use a sustainable baseline; overload remains an explicit stress condition. Rates, capacities, horizons, and initial reserve states are swept when they affect the central finding. Analysis must check whether apparent regime transitions are definitions, truncation effects, or empirical consequences.

Finally regenerate every manuscript figure and numerical table from new machine-readable outputs. Rewrite around supported results, with no requirement that a proposed method win. Keep the main paper within six pages by moving experiment detail and full responses to supporting files. Compile LaTeX, render every PDF and Word page, inspect layout, audit all cross-references and citations, and check manuscript/source numerical agreement. Record any author-only or external-service step honestly without calling it completed.

## Current status

Repository and official-review inspection are under way. The historical 43-check gate and a seed-0 headline replay pass, but these checks did not detect the stored-key abort semantics, eight-node description, overlapping learning seeds, mixed accounting windows, or overly broad cut interpretation. The revision must correct those before reusing historical conclusions.
