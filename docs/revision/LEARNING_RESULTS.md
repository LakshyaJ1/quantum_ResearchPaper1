# Learning results from the completed registered experiment

This report retains every registered policy, condition and seed, including negative differences and intervals that include zero. The policy tables were selected using validation outcomes and frozen before final-test evaluation. The tables below report treatment-minus-BudgetGreedy differences; positive service/utility differences favor the treatment, while positive loss differences indicate more service below the requested assurance.

The benchmark contains seven fixed test conditions and twelve realization seeds (5000–5011). For the overall comparison, each condition first receives equal weight within a seed; the bootstrap then resamples those twelve seed-level averages. The 84 condition/seed cells are not treated as independent draws. Intervals use 20,000 paired percentile resamples at seed 71. They quantify realization uncertainty for this fixed benchmark, not uncertainty over an unknown population of deployment conditions. Multiple comparisons are exploratory and no multiplicity-adjusted significance claim is made.

Utility is timely-service availability minus 0.75 times the below-floor delivery count divided by all arrivals. Qualified availability counts timely deliveries at the requested floor or above, divided by all arrivals. Floor loss uses all arrivals as its denominator. Forced-payload loss uses the payload bits of all G1/G2-entitled arrivals; it records lower contractual assurance, not demonstrated plaintext disclosure. Conditional metrics retain their explicit denominators in the CSVs. Undefined conditional values remain null in JSON and empty in CSV; no seed or condition is silently dropped.

| Learned training regime | Mean utility difference [95% CI] | Qualified availability difference [95% CI] | Floor-loss difference [95% CI] |
|---|---|---|---|
| short_nominal | -0.0047 [-0.0058, -0.0035] | -0.0008 [-0.0019, +0.0004] | -0.0155 [-0.0159, -0.0152] |
| full_nominal | -0.0036 [-0.0040, -0.0034] | +0.0004 [-0.0000, +0.0006] | -0.0159 [-0.0163, -0.0156] |
| full_robust | +0.0011 [+0.0002, +0.0020] | +0.0010 [+0.0001, +0.0020] | +0.0001 [-0.0001, +0.0003] |

Per-condition utility differences against BudgetGreedy are shown without excluding unfavorable or null outcomes.

| Condition | Short nominal [95% CI] | Full nominal [95% CI] | Full robust [95% CI] |
|---|---|---|---|
| attack2 | -0.0112 [-0.0127, -0.0086] | -0.0096 [-0.0096, -0.0095] | +0.0026 [+0.0001, +0.0064] |
| correlated_weather | -0.0073 [-0.0120, -0.0019] | -0.0012 [-0.0034, +0.0001] | +0.0027 [+0.0003, +0.0058] |
| nominal | -0.0000 [-0.0001, +0.0001] | -0.0000 [-0.0001, +0.0000] | -0.0018 [-0.0019, -0.0017] |
| overload_isr1 | -0.0050 [-0.0052, -0.0048] | -0.0046 [-0.0048, -0.0044] | +0.0004 [+0.0003, +0.0005] |
| rate_half | -0.0007 [-0.0009, -0.0005] | -0.0005 [-0.0007, -0.0003] | +0.0001 [-0.0000, +0.0002] |
| unseen_parallel3_attack3 | -0.0087 [-0.0124, -0.0048] | -0.0096 [-0.0097, -0.0095] | +0.0051 [+0.0013, +0.0089] |
| unseen_ring | +0.0001 [-0.0003, +0.0006] | +0.0002 [+0.0000, +0.0003] | -0.0016 [-0.0019, -0.0013] |

All per-class estimates, all three learned-versus-StrictFloor comparisons, and the StrictFloor-versus-BudgetGreedy comparison are exported alongside the headline tables. StrictFloor and BudgetGreedy use the same model and arrival traces; the learned policies share the fixed runtime exception projection. The independent audit found zero excess over the declared exception cap at every observed arrival prefix in every verified training, validation and test rollout. This is a simulator accounting result under the declared projection, not certification of a cryptographic implementation.

The selected controller is the best observed under the limited CEM search and registered validation rule. The robust-training objective averages three conditions; it does not optimize the worst case. No superiority, weight robustness, global optimality or deployment safety beyond the tested model is inferred from a mean ranking alone.

| Stage | Requested rollouts | Unique completed rollouts | Unique simulated arrival-horizon hours | Sum of recorded unique rollout wall seconds |
|---|---:|---:|---:|---:|
| train | 1440 | 1110 | 19728.0 | 8941.0 |
| validation | 72 | 60 | 1440.0 | 781.1 |
| test | 420 | 420 | 10080.0 | 4618.7 |

Repeated deterministic evaluations are counted in the requested budget but execute once through the verified cache. Simulated hours here count the arrival horizon, excluding the short deadline drain. Summed rollout wall durations overlap under parallel execution and are not elapsed coordinator time. The completed training coordinator invocation took 2498.9 seconds; final-test coordination took 1160.5 seconds.

Freeze timestamp: 2026-09-26T00:39:57.132467+00:00. Test start: 2026-09-26T00:39:57.272338+00:00. Test completion: 2026-09-26T00:59:17.693419+00:00. The logged order was checked, and training, validation and test seed sets are disjoint.

Freeze SHA-256: `245ecb9ce401bbffb160cee4051e98b2eed915d73b96566b5a601d8e5c83b987`. Test report SHA-256: `5e1250250f86d4aa5b00e02a85b09b9227a286084d2ef5a8277002962bd39457`. Every referenced rollout record and its duplicated report fields passed integrity and count checks.

The full selected tables follow. Actions are raw table proposals executed through the common budget projection; an action label alone does not imply that an exception was allowed.

| Regime | State | Action |
|---|---|---|
| short_nominal | C2 / affordable / not_urgent | G4 |
| short_nominal | C2 / affordable / urgent | floor |
| short_nominal | C2 / refill_within_deadline / not_urgent | affordable_fallback |
| short_nominal | C2 / refill_within_deadline / urgent | affordable_fallback |
| short_nominal | C2 / unfundable_now / not_urgent | affordable_fallback |
| short_nominal | C2 / unfundable_now / urgent | affordable_fallback |
| short_nominal | ISR / affordable / not_urgent | floor |
| short_nominal | ISR / affordable / urgent | defer |
| short_nominal | ISR / refill_within_deadline / not_urgent | floor |
| short_nominal | ISR / refill_within_deadline / urgent | floor |
| short_nominal | ISR / unfundable_now / not_urgent | floor |
| short_nominal | ISR / unfundable_now / urgent | floor |
| short_nominal | LOG / affordable / not_urgent | G2 |
| short_nominal | LOG / affordable / urgent | G2 |
| short_nominal | LOG / refill_within_deadline / not_urgent | affordable_fallback |
| short_nominal | LOG / refill_within_deadline / urgent | defer |
| short_nominal | LOG / unfundable_now / not_urgent | floor |
| short_nominal | LOG / unfundable_now / urgent | G2 |
| full_nominal | C2 / affordable / not_urgent | floor |
| full_nominal | C2 / affordable / urgent | floor |
| full_nominal | C2 / refill_within_deadline / not_urgent | floor |
| full_nominal | C2 / refill_within_deadline / urgent | floor |
| full_nominal | C2 / unfundable_now / not_urgent | floor |
| full_nominal | C2 / unfundable_now / urgent | floor |
| full_nominal | ISR / affordable / not_urgent | floor |
| full_nominal | ISR / affordable / urgent | floor |
| full_nominal | ISR / refill_within_deadline / not_urgent | floor |
| full_nominal | ISR / refill_within_deadline / urgent | floor |
| full_nominal | ISR / unfundable_now / not_urgent | floor |
| full_nominal | ISR / unfundable_now / urgent | floor |
| full_nominal | LOG / affordable / not_urgent | floor |
| full_nominal | LOG / affordable / urgent | floor |
| full_nominal | LOG / refill_within_deadline / not_urgent | floor |
| full_nominal | LOG / refill_within_deadline / urgent | floor |
| full_nominal | LOG / unfundable_now / not_urgent | floor |
| full_nominal | LOG / unfundable_now / urgent | floor |
| full_robust | C2 / affordable / not_urgent | G2 |
| full_robust | C2 / affordable / urgent | G2 |
| full_robust | C2 / refill_within_deadline / not_urgent | affordable_fallback |
| full_robust | C2 / refill_within_deadline / urgent | defer |
| full_robust | C2 / unfundable_now / not_urgent | affordable_fallback |
| full_robust | C2 / unfundable_now / urgent | G2 |
| full_robust | ISR / affordable / not_urgent | defer |
| full_robust | ISR / affordable / urgent | G2 |
| full_robust | ISR / refill_within_deadline / not_urgent | G2 |
| full_robust | ISR / refill_within_deadline / urgent | G4 |
| full_robust | ISR / unfundable_now / not_urgent | G4 |
| full_robust | ISR / unfundable_now / urgent | affordable_fallback |
| full_robust | LOG / affordable / not_urgent | floor |
| full_robust | LOG / affordable / urgent | floor |
| full_robust | LOG / refill_within_deadline / not_urgent | floor |
| full_robust | LOG / refill_within_deadline / urgent | floor |
| full_robust | LOG / unfundable_now / not_urgent | floor |
| full_robust | LOG / unfundable_now / urgent | G4 |

Machine-readable outputs are in results/revision/learning_analysis/: analysis.json, per_seed.csv, per_class.csv, fixed_benchmark_per_seed.csv, estimates.csv, paired_differences.csv and selected_policy_tables.csv. analysis.json includes denominator definitions, search/validation integrity audits and actual compute accounting. All estimates and intervals remain available even when the headline table is inconclusive.
