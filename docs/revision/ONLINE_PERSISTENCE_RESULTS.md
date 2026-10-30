# Persistence diagnostic on disjoint confirmation seeds

This is a post-hoc mechanism diagnostic motivated by the completed online-adversary study. It is separate from the preregistered learning experiment and uses new seeds 3100-3105 rather than the exploratory 3000-3005. All three chain depths (2, 4, 6), concurrent budgets (1, 2), 24-hour horizon, 2% spendable initial stock, ISR scale 0.1, n_auth = 7, retained keys, independent environment and fail-degraded operation remain fixed. There are 108 attacked runs and 18 shared no-attack controls.

Saved exploratory feedback logs exactly reconstruct the lower realized online link-hours as paths become temporarily transport-unusable. At budget two, original online exposure falls from 43.89 link-hours at depth two to 38.95 at depth six, while the fixed cut spends 48. The model permits fresh generation on a released target when its own channel is up. These observations identify the exposure confound; the new experiment tests the effect of the persistence intervention instead of treating adaptivity as intrinsically stronger or weaker.

The release variant is the unchanged original route-feedback selector. The persistent variant first takes exactly the same weighted route-coverage choices, then fills unused slots from the previous target set in its prior order. If previous targets are insufficient, the frozen weighted-cut ordering and its canonical tail initialize the remaining slots. Committed-route observations, path weights, tie breaking and 60-second update times are unchanged. Selection and subsequent route feedback can respond endogenously to the changed persistence. This is not a new optimal-attacker claim.

FAL counts G1/G2-entitled requests delivered at G3/G4 over all G1/G2-entitled arrivals, including blocked requests. Excess FAL subtracts the matched no-attack value within each seed. The 95% percentile intervals use 20,000 paired bootstrap resamples, seed 71, over six confirmation seeds. Null and negative differences are retained. These are exploratory simulation-model statements, with no multiplicity-adjusted significance claim.

| Depth | Budget | Persistent minus release FAL [95% CI] | Persistent minus fixed cut FAL [95% CI] |
|---|---:|---|---|
| 2 | 1 | 0.0010 [-0.0013, 0.0027] | 0.0241 [0.0123, 0.0345] |
| 2 | 2 | 0.2066 [0.1837, 0.2291] | 0.0000 [0.0000, 0.0000] |
| 4 | 1 | 0.0061 [0.0013, 0.0098] | 0.0008 [-0.0152, 0.0148] |
| 4 | 2 | 0.3742 [0.3382, 0.4151] | 0.0000 [0.0000, 0.0000] |
| 6 | 1 | 0.0092 [0.0026, 0.0164] | -0.0352 [-0.0486, -0.0223] |
| 6 | 2 | 0.5419 [0.4972, 0.5808] | 0.0000 [0.0000, 0.0000] |

| Depth | Budget | Release excess FAL [95% CI] | Persistent excess FAL [95% CI] | Fixed-cut excess FAL [95% CI] |
|---|---:|---|---|---|
| 2 | 1 | 0.0659 [0.0584, 0.0733] | 0.0669 [0.0601, 0.0730] | 0.0428 [0.0350, 0.0498] |
| 2 | 2 | 0.7226 [0.7024, 0.7444] | 0.9292 [0.9202, 0.9370] | 0.9292 [0.9202, 0.9370] |
| 4 | 1 | 0.0691 [0.0629, 0.0747] | 0.0752 [0.0680, 0.0819] | 0.0743 [0.0618, 0.0873] |
| 4 | 2 | 0.5384 [0.4985, 0.5666] | 0.9126 [0.9009, 0.9248] | 0.9126 [0.9009, 0.9248] |
| 6 | 1 | 0.0684 [0.0634, 0.0728] | 0.0776 [0.0738, 0.0812] | 0.1127 [0.1030, 0.1228] |
| 6 | 2 | 0.3550 [0.3167, 0.3956] | 0.8969 [0.8904, 0.9022] | 0.8969 [0.8904, 0.9022] |

| Depth | Variant | Budget | Realized relative-cost link-hours [95% CI] | Distinct links [95% CI] |
|---|---|---:|---|---|
| 2 | release_on_unusable | 1 | 23.8722 [23.7833, 23.9333] | 2.0000 [2.0000, 2.0000] |
| 2 | release_on_unusable | 2 | 43.9778 [43.6194, 44.3389] | 2.0000 [2.0000, 2.0000] |
| 2 | persistent_slots | 1 | 24.0000 [24.0000, 24.0000] | 2.0000 [2.0000, 2.0000] |
| 2 | persistent_slots | 2 | 48.0000 [48.0000, 48.0000] | 2.0000 [2.0000, 2.0000] |
| 2 | weighted_cut | 1 | 24.0000 [24.0000, 24.0000] | 1.0000 [1.0000, 1.0000] |
| 2 | weighted_cut | 2 | 48.0000 [48.0000, 48.0000] | 2.0000 [2.0000, 2.0000] |
| 4 | release_on_unusable | 1 | 23.5472 [23.4722, 23.6139] | 2.0000 [2.0000, 2.0000] |
| 4 | release_on_unusable | 2 | 41.7056 [41.1333, 42.2389] | 2.0000 [2.0000, 2.0000] |
| 4 | persistent_slots | 1 | 24.0000 [24.0000, 24.0000] | 2.0000 [2.0000, 2.0000] |
| 4 | persistent_slots | 2 | 48.0000 [48.0000, 48.0000] | 2.0000 [2.0000, 2.0000] |
| 4 | weighted_cut | 1 | 24.0000 [24.0000, 24.0000] | 1.0000 [1.0000, 1.0000] |
| 4 | weighted_cut | 2 | 48.0000 [48.0000, 48.0000] | 2.0000 [2.0000, 2.0000] |
| 6 | release_on_unusable | 1 | 23.1417 [22.9917, 23.2917] | 2.0000 [2.0000, 2.0000] |
| 6 | release_on_unusable | 2 | 38.9528 [38.4944, 39.4667] | 2.0000 [2.0000, 2.0000] |
| 6 | persistent_slots | 1 | 24.0000 [24.0000, 24.0000] | 2.0000 [2.0000, 2.0000] |
| 6 | persistent_slots | 2 | 48.0000 [48.0000, 48.0000] | 2.0000 [2.0000, 2.0000] |
| 6 | weighted_cut | 1 | 24.0000 [24.0000, 24.0000] | 1.0000 [1.0000, 1.0000] |
| 6 | weighted_cut | 2 | 48.0000 [48.0000, 48.0000] | 2.0000 [2.0000, 2.0000] |

The comparison changes realized persistence/exposure through an unused-slot rule. Retargeting overhead, mobility, coordination and sensing cost remain unmodeled. Distinct-link campaign footprint is not the same quantity as simultaneous budget. Full exposure can differ from the strong route-feedback policy that releases targets during transport interruptions; the results must not be paraphrased as a universal ranking of adaptive and fixed attackers.

All methods and controls matched exact arrival and fixed-arrival-horizon environmental digests. Concurrent caps, full-exposure retention for the persistent variant and key conservation were checked for every run. Protected previous source, manifest and analysis hashes remained unchanged. Raw baseline/FAL/excess values, per-class counts, cost integrals, retention decisions and changed target sets are preserved.

Confirmation source/runtime hash: `90baaec0d031b0efd250e1210b32f358c135445166ed9416312fee440b05c1ed`. Completed runs: 126. Coordinator wall time: 275.2s. Sum of recorded per-run wall durations: 811.8s, overlapping when workers run concurrently.

Outputs: results/revision/online_persistence/analysis.json, per_seed_per_class.csv, estimates.csv, paired_contrasts.csv and runs/*.json. The manifest includes the original exposure-log audit and the post-hoc protocol. No further empirical study is implied by these results.
