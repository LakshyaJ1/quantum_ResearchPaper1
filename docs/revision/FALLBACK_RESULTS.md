# Fallback results: key establishment and data transport

All 48 scheduled runs completed: six conditions over seeds 3000 through 3007. Every compared condition has identical arrival and exogenous environment digests for each matched seed. Duplicate/missing records, mixed source hashes, scenario mismatches, or incompatible service/assurance counts cause the analysis to fail rather than produce this report.

The scenario is the eight-node formation, 24 simulated hours, 2% initially spendable stock, retained-key policy, ISR arrival scale 0.1, authentication count 7, independent environmental interruptions, and a weighted all-terminal cut of relative cost two. Generation suppression and transport denial use the same selected cut. The global online key-establishment service flag is an additional controlled dimension; no physical attack cost is assigned to making that service unavailable.

Service here means timely key-supply or modeled session-admission service. No payload cipher, bandwidth/serialization, packet delivery, or application throughput is simulated. Payload-weighted loss is an associated-payload exposure proxy, not observed transmitted or compromised data. The 0.35-second online setup time is an assumption, not a KEM benchmark.

Reported values are means of eight seed-level fractions, with marginal 95% percentile bootstrap intervals in brackets (20,000 resamples, bootstrap seed 71). They are not simultaneous intervals and do not include model uncertainty. Percentages describe the stated denominator; comparison differences are percentage points.

## Joint delivery and assurance outcomes

| Condition | Timely key service % | Authorized key service % | Below-floor service / arrivals % | Below-ITS service / entitled arrivals % | Entitled arrivals blocked % |
|---|---|---|---|---|---|
| Generation cut; online KEM; control up | 97.527 [97.332, 97.705] | 6.874 [6.166, 7.473] | 90.653 [90.151, 91.178] | 89.850 [89.231, 90.507] | 3.296 [3.038, 3.584] |
| Generation cut; online KEM; control down | 5.035 [4.468, 5.598] | 4.971 [4.422, 5.514] | 0.064 [0.032, 0.097] | 0.000 [0.000, 0.000] | 92.046 [91.171, 92.919] |
| Generation cut; pre-positioned key; control up | 97.545 [97.350, 97.724] | 6.874 [6.166, 7.473] | 90.670 [90.166, 91.197] | 89.872 [89.255, 90.528] | 3.274 [3.011, 3.562] |
| Generation cut; pre-positioned key; control down | 97.545 [97.350, 97.724] | 6.874 [6.166, 7.473] | 90.670 [90.166, 91.197] | 89.872 [89.255, 90.528] | 3.274 [3.011, 3.562] |
| Transport cut; online KEM | 0.064 [0.042, 0.085] | 0.064 [0.042, 0.085] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 99.986 [99.966, 100.000] |
| Transport cut; pre-positioned key | 0.064 [0.042, 0.085] | 0.064 [0.042, 0.085] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 99.986 [99.966, 100.000] |

Authorized service, below-floor service, and blocking partition all arrivals. ITS-key service, below-ITS service, and entitled blocking partition all G1/G2-entitled arrivals. These are separate decompositions: G2 can violate an ISR G1 floor while still meeting the ITS-key classification. A smaller below-ITS fraction after blocking more requests is not an assurance improvement for the denied population.

## Paired contrasts

| Treatment minus control | Timely-service difference, pp | Authorized-service difference, pp | Below-ITS difference on entitled arrivals, pp | Entitled-blocking difference, pp |
|---|---|---|---|---|
| Generation cut; online KEM; control down minus Generation cut; online KEM; control up | -92.492 [-93.050, -91.897] | -1.903 [-2.622, -1.153] | -89.850 [-90.507, -89.231] | 88.750 [87.927, 89.530] |
| Generation cut; pre-positioned key; control down minus Generation cut; pre-positioned key; control up | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| Generation cut; pre-positioned key; control down minus Generation cut; online KEM; control down | 92.510 [91.907, 93.075] | 1.903 [1.153, 2.622] | 89.872 [89.255, 90.528] | -88.773 [-89.558, -87.939] |
| Generation cut; pre-positioned key; control up minus Generation cut; online KEM; control up | 0.018 [0.009, 0.025] | 0.000 [0.000, 0.000] | 0.022 [0.011, 0.034] | -0.022 [-0.034, -0.011] |
| Transport cut; pre-positioned key minus Transport cut; online KEM | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| Transport cut; online KEM minus Generation cut; online KEM; control up | -97.463 [-97.624, -97.284] | -6.811 [-7.393, -6.116] | -89.850 [-90.507, -89.231] | 96.690 [96.409, 96.941] |
| Transport cut; pre-positioned key minus Generation cut; pre-positioned key; control up | -97.481 [-97.643, -97.302] | -6.811 [-7.393, -6.116] | -89.872 [-90.528, -89.255] | 96.712 [96.431, 96.967] |

With generation suppressed and the online key-establishment service unavailable, timely service is 5.035 [4.468, 5.598]%. Ideal pre-positioned shared keys yield 97.545 [97.350, 97.724]%, a paired increase of 92.510 [91.907, 93.075] percentage points. Authorized service changes by 1.903 [1.153, 2.622] percentage points. The recovered delivery must therefore be read together with its reported below-floor and below-ITS composition; it is not restored QKD-grade service.

Under transport denial, online KEM and pre-positioned fallback provide 0.064 [0.042, 0.085]% and 0.064 [0.042, 0.085]% timely service respectively. The full cut removes every data path during the attack. The attack ends at the arrival horizon, after which the simulator lets the last arrivals reach their deadlines. Any residual service in this transport-cut cohort is therefore post-release service, not delivery through an unavailable path. This reporting convention must not be mistaken for a permanent transport-cut experiment.

Changing the key-establishment flag has no operational effect on the ideal pre-positioned mode by construction. Its exact paired equality checks that separation; it is not physical evidence that a deployed pre-positioned-key system is unaffected by all control failures.

## Limits and artifacts

Pre-positioned symmetric fallback assumes sufficient, valid, unexpired already-shared key material and zero online setup. Finite stock, expiry, refresh, key-distribution authentication, and KEM computation are not modeled. G3/G4 are assurance-policy labels in this simulation; no KEM or cryptographic combiner is executed. The result separates availability dependencies and does not establish a cryptographic security guarantee.

The complete [summary](../../results/revision/fallback/analysis/summary.csv), [paired comparisons](../../results/revision/fallback/analysis/paired_comparisons.csv), [verification record](../../results/revision/fallback/analysis/verification.json), and [raw per-seed files](../../results/revision/fallback/runs/) retain per-class and payload-weighted metrics in addition to the aggregate values above. An undefined metric is left undefined; it is never replaced with zero or summarized after silently dropping seeds.

Reproduce the analysis without rerunning simulations:

```powershell
python -X faulthandler -u -c "from experiments.analyze_revision_fallback import main; raise SystemExit(main())"
```

The analysis uses [revision/metrics.py](../../revision/metrics.py) and the separate [analysis script](../../experiments/analyze_revision_fallback.py). Its input guards and hand-derived paired-difference checks are in [tests/test_fallback_analysis.py](../../tests/test_fallback_analysis.py).
