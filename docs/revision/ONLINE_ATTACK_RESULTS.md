# Online route-feedback adversary results

This standalone study compares fixed all-pairs betweenness, a weighted structural cut, and an online route-feedback selector on two-path relay chains of depth 2, 4 and 6. Each primary path has a lateral alternative one hop longer. Concurrent attack budgets are one or two relative-cost units. Six paired seeds are used for every cell. Eighteen shared no-attack runs supply depth/seed-matched controls, giving 126 completed runs.

All runs last 24 hours with no warmup exclusion, initial spendable stock at 2% of the reservoir range, ISR arrival scale 0.1, n_auth = 7, independent environmental generation/transport processes and fail-degraded service. Generator suppression preserves accepted stored keys. These are explicit model assumptions, not measured attack powers or hardware certification.

The online selector updates every 60 seconds. It observes only genuinely committed positive-key relay routes in the preceding window and current classical reachability. Unobserved viable alternatives receive weight 0.01; observed paths receive their count of successful relay events. At each choice it maximizes uncovered route weight per relative edge cost, with canonical undirected-edge lexicographic ties, and removes covered paths before spending the next slot. It releases its previous set when installing the new one. At time zero all viable paths have the same prior weight. It sees neither key contents/inventory levels nor future arrivals or outages. This is a strong modeled controller-observing adversary, not a proof of optimal interdiction.

FAL here counts G1/G2-entitled requests delivered at G3/G4 divided by all G1/G2-entitled arrivals, including blocked requests. The separate all-arrival forced-loss fraction and below-floor fraction are also exported. Excess FAL subtracts the matched no-attack fraction within each seed. All 95% intervals use 20,000 paired seed bootstrap resamples with seed 71 and six independent seed-level units. Negative excess and inconclusive intervals are retained. They quantify simulation-realization uncertainty, not physical-model uncertainty; multiple comparisons are exploratory.

| Depth | Concurrent budget | Static betweenness raw FAL [95% CI] | Weighted cut raw FAL [95% CI] | Online raw FAL [95% CI] |
|---|---:|---|---|---|
| 2 | 1 | 0.0507 [0.0423, 0.0616] | 0.0507 [0.0423, 0.0616] | 0.0581 [0.0498, 0.0673] |
| 2 | 2 | 0.0507 [0.0423, 0.0616] | 0.9303 [0.9191, 0.9416] | 0.7327 [0.7103, 0.7508] |
| 4 | 1 | 0.0864 [0.0794, 0.0950] | 0.0864 [0.0794, 0.0950] | 0.0793 [0.0688, 0.0899] |
| 4 | 2 | 0.0864 [0.0794, 0.0950] | 0.9200 [0.9096, 0.9297] | 0.5282 [0.5099, 0.5468] |
| 6 | 1 | 0.1277 [0.1159, 0.1435] | 0.1277 [0.1159, 0.1435] | 0.0687 [0.0642, 0.0739] |
| 6 | 2 | 0.1277 [0.1159, 0.1435] | 0.9025 [0.8917, 0.9132] | 0.3590 [0.3322, 0.3884] |

| Depth | Concurrent budget | Static excess FAL [95% CI] | Cut excess FAL [95% CI] | Online excess FAL [95% CI] |
|---|---:|---|---|---|
| 2 | 1 | 0.0507 [0.0423, 0.0616] | 0.0507 [0.0423, 0.0616] | 0.0581 [0.0498, 0.0673] |
| 2 | 2 | 0.0507 [0.0423, 0.0616] | 0.9303 [0.9191, 0.9416] | 0.7327 [0.7103, 0.7508] |
| 4 | 1 | 0.0863 [0.0794, 0.0949] | 0.0863 [0.0794, 0.0949] | 0.0792 [0.0687, 0.0899] |
| 4 | 2 | 0.0863 [0.0794, 0.0949] | 0.9200 [0.9096, 0.9297] | 0.5282 [0.5098, 0.5467] |
| 6 | 1 | 0.1277 [0.1159, 0.1435] | 0.1277 [0.1159, 0.1435] | 0.0687 [0.0642, 0.0739] |
| 6 | 2 | 0.1277 [0.1159, 0.1435] | 0.9025 [0.8917, 0.9132] | 0.3590 [0.3322, 0.3884] |

Threshold assessments identify only the smallest tested concurrent budget in {1, 2} whose mean excess FAL reaches 0.5. A separate column requires the lower confidence limit to reach 0.5. An empty crossing means it was not established on this tested grid. This is not a universal two-link result or a global optimum, and it does not equate the number of distinct links visited during a campaign with concurrent attack capacity.

| Depth | Method | Smallest tested budget with mean excess FAL >= 0.5 | Smallest tested budget with lower CI >= 0.5 |
|---|---|---|---|
| 2 | static_betweenness | not established | not established |
| 2 | weighted_cut | 2 | 2 |
| 2 | online_route_feedback | 2 | 2 |
| 4 | static_betweenness | not established | not established |
| 4 | weighted_cut | 2 | 2 |
| 4 | online_route_feedback | 2 | 2 |
| 6 | static_betweenness | not established | not established |
| 6 | weighted_cut | 2 | 2 |
| 6 | online_route_feedback | not established | not established |

Equal concurrent budget caps are the primary comparison. Actual link-time cost is separately measured as the integral of selected relative edge cost over time; online control may leave slots unused when no viable uncovered route remains. Retarget latency, equipment relocation, sensing, coordination and switching overhead are unmodeled. Distinct links touched is a campaign-footprint count and cannot be interpreted as the same cost as the simultaneous slot budget.

| Depth | Method | Budget | Mean retarget changes | Mean distinct links touched | Mean relative-cost link-hours |
|---|---|---:|---:|---:|---:|
| 2 | static_betweenness | 1 | 0.00 | 1.00 | 24.00 |
| 2 | static_betweenness | 2 | 0.00 | 2.00 | 48.00 |
| 2 | weighted_cut | 1 | 0.00 | 1.00 | 24.00 |
| 2 | weighted_cut | 2 | 0.00 | 2.00 | 48.00 |
| 2 | online_route_feedback | 1 | 677.17 | 2.00 | 23.88 |
| 2 | online_route_feedback | 2 | 175.33 | 2.00 | 43.89 |
| 4 | static_betweenness | 1 | 0.00 | 1.00 | 24.00 |
| 4 | static_betweenness | 2 | 0.00 | 2.00 | 48.00 |
| 4 | weighted_cut | 1 | 0.00 | 1.00 | 24.00 |
| 4 | weighted_cut | 2 | 0.00 | 2.00 | 48.00 |
| 4 | online_route_feedback | 1 | 584.50 | 2.00 | 23.59 |
| 4 | online_route_feedback | 2 | 269.67 | 2.00 | 41.34 |
| 6 | static_betweenness | 1 | 0.00 | 1.00 | 24.00 |
| 6 | static_betweenness | 2 | 0.00 | 2.00 | 48.00 |
| 6 | weighted_cut | 1 | 0.00 | 1.00 | 24.00 |
| 6 | weighted_cut | 2 | 0.00 | 2.00 | 48.00 |
| 6 | online_route_feedback | 1 | 509.67 | 2.00 | 23.20 |
| 6 | online_route_feedback | 2 | 360.00 | 2.00 | 38.95 |

Every changed attack set, every online update and recent route-count input, the route registry, total route observations, arrival digest, fixed-arrival-horizon environment digest, per-class outcomes and key accounting are retained in the per-seed JSON files. All paired methods and controls passed exact arrival/environment digest checks, no run exceeded its concurrent budget, and retained-buffer key accounting passed in every run. The fixed digest interval excludes policy-dependent deadline drain lengths.

Source/runtime fingerprint: `f007330e9cf450df6ce9ea2bd9b0a5bc09992f49f144c015e2908fc8042fb388`. Unique recorded runs: 126. Coordinator elapsed time: 1006.8 seconds. Sum of per-run wall durations: 1003.3 seconds; these overlap if workers run in parallel.

Machine-readable results are in results/revision/online_adversary/: analysis.json, per_seed_per_class.csv, estimates.csv, paired_contrasts.csv, thresholds.csv and runs/*.json. Raw and excess threshold rows for all registered methods are retained without selecting a favorable result.
