# Exploratory class-importance sensitivity of frozen policies

This is post-hoc reweighting of already-completed outcomes from the same five frozen policies. No controller was retrained, reselected or optimized for these weights. Only the three previously declared vectors (C2, ISR, LOG) = (1,1,1), (5,2,1) and (10,3,1) are evaluated. They are illustrative preferences, not calibrated harm costs.

For each condition and seed, weighted utility is sum_c w_c(S_c - 0.75 D_c) / sum_c w_c N_c, where N_c counts all arrivals of class c, S_c counts timely served arrivals, and D_c counts timely below-floor deliveries. Both numerator and denominator change with the weights. Raw counts and integer quarter-unit numerators/denominators are exported. The seven fixed conditions are averaged equally within each seed, then the twelve seed-level averages are paired with BudgetGreedy. Intervals are 95% percentile intervals from 20,000 bootstrap resamples with seed 71. The 84 condition/seed cells are not treated as independent observations.

Every declared vector and every frozen policy is retained, including null or unfavorable differences. This sensitivity is conditional on the fixed benchmark; it does not establish robustness over unknown deployments or weight-robust optimality. Request-class weighting also does not by itself calibrate the harm of losing entitlement to OTP-protected payload.

| C2 / ISR / LOG weights | Strict floor minus greedy [95% CI] | Short nominal minus greedy [95% CI] | Full nominal minus greedy [95% CI] | Multi-condition minus greedy [95% CI] |
|---|---|---|---|---|
| 1 / 1 / 1 | -0.003607 [-0.003955, -0.003394] | -0.004678 [-0.005774, -0.003459] | -0.003607 [-0.003955, -0.003394] | +0.001066 [+0.000191, +0.002032] |
| 5 / 2 / 1 | -0.001512 [-0.001902, -0.001272] | -0.002307 [-0.003392, -0.001107] | -0.001512 [-0.001902, -0.001272] | +0.001078 [+0.000181, +0.002040] |
| 10 / 3 / 1 | -0.001070 [-0.001473, -0.000820] | -0.001807 [-0.002890, -0.000608] | -0.001070 [-0.001473, -0.000820] | +0.001102 [+0.000199, +0.002065] |

Equal weights reproduce the original aggregate count numerator and denominator exactly for all 420 frozen rows. The largest difference from the previously stored floating-point utility is 1.11e-16, consistent with the different order of floating-point arithmetic. No stored experiment outcome is changed.

Frozen policy manifest hash: `245ecb9ce401bbffb160cee4051e98b2eed915d73b96566b5a601d8e5c83b987`. Completed test-report hash: `5e1250250f86d4aa5b00e02a85b09b9227a286084d2ef5a8277002962bd39457`. The existing analysis gate revalidated policy selection provenance, matched arrival traces, raw counts, exception caps and disjoint train/validation/test seeds before reweighting.

The complete JSON and CSV files retain absolute weighted-utility intervals, all per-condition and fixed-benchmark paired intervals, per-seed averages and all condition/seed weighted numerators and denominators. They are results/revision/learning_analysis/weight_sensitivity.json, weight_sensitivity.csv, weight_sensitivity.per_seed.csv and weight_sensitivity.per_condition.csv. No additional weights are proposed from these outcomes.
