# PAPER 2 — DRAFT
## Terrain-Aware Learned Propagation Surrogate with Calibrated Uncertainty for Mountainous Tactical Link Planning

**Target:** IEEE WiCOMM-2026, Track 4 (Communication and Signal Processing — Channel Modelling)
**Status:** complete draft. The pipeline is real and validated; **the terrain source in the current run is synthetic** and must be replaced with real DEM tiles before submission. Every number that changes is tagged `[REPLACE]`.

> **⚠️ BLOCKING PRECONDITION — read before anything else.**
> The results below were produced on **synthetic fractal terrain**, because real elevation tiles could not be downloaded in the environment where the pipeline was built. The physics, features, model, calibration, cross-region protocol and timing are all correct and real. Only the terrain is a stand-in.
> **Therefore, until you re-run on real DEM: do not use the word "Himalayan," any Indian place name, or any claim about a specific sector anywhere in this paper.** Get two DEM tiles from OpenTopography / NASA Earthdata / Copernicus / Bhoonidhi, reproject to UTM, re-run, and replace every `[REPLACE]` number. Instructions are in `FACT_CHECK_AND_48H_PLAN.md` §2. If that cannot be completed cleanly, submit Paper 1 only and take this one to a later venue — it is the higher-ceiling idea and deserves better than a rushed six pages.

> Text in `[[double brackets]]` is an instruction to you, not paper text.

---

## Abstract

Planning tactical radio links in mountainous terrain is dominated by terrain diffraction and trans-horizon propagation, the regime in which fast statistical models are least accurate and physics-based solvers are too slow to evaluate the thousands of candidate site pairs a planner must consider. Learned propagation models have advanced rapidly, but almost entirely for urban, building-dominated scenarios, and they are typically reported as point predictions without an uncertainty statement — which is precisely what a link planner needs. We construct a terrain-conditioned surrogate that predicts excess loss over free space from a terrain profile and link geometry, trained against labels from a multi-mechanism physics model combining ITU-R P.526-style multiple knife-edge diffraction by the Deygout construction with a simplified trans-horizon scatter mechanism and earth-curvature correction. We add conformalised quantile regression so that predictions carry finite-sample prediction intervals, and we evaluate under a **cross-region protocol**: train in one terrain sector, test in a second sector with different spatial statistics. On held-out links in the training sector the surrogate attains 5.86 dB mean absolute error and 7.78 dB RMSE `[REPLACE]`; on the unseen sector, error inflates by 40% to 8.22 dB `[REPLACE]`. Split-conformal calibration raises 90% interval coverage from 81.4% to 91.3% within the training sector but yields only 83.1% on the unseen sector `[REPLACE]`, demonstrating empirically that the exchangeability assumption underlying conformal guarantees is violated by terrain shift. Framed as the planner's actual decision — will this link close within the budget? — the surrogate is 93.3% accurate in-region and 92.2% cross-region, with the operationally critical false-go rate rising from 5.5% to 9.2% `[REPLACE]`. Evaluating a full 160-site candidate matrix (12 720 links) takes 0.068 s against 1.585 s for the physics model, a 23× reduction `[REPLACE]`. We conclude that terrain-region generalisation and calibrated uncertainty, not headline in-domain accuracy, are the properties that determine whether a learned propagation model is usable for link planning.

**Index Terms** — radio propagation, terrain diffraction, path loss prediction, radio maps, surrogate models, uncertainty quantification, conformal prediction, tactical communications.

---

## I. Introduction

A signals officer planning connectivity across a mountain sector must answer a combinatorial question: given a set of candidate relay sites, which pairs will support a link at the required margin? For *N* candidate sites there are *N(N−1)/2* pairs, and every pair must be evaluated across several frequency bands and antenna-height options. Two established tools bracket the problem badly. Statistical path-loss models are fast but insensitive to the specific ridge that blocks the specific path. Physics-based solvers — multiple knife-edge diffraction methods, and at the high-fidelity end three-dimensional ray tracing — capture the terrain but scale poorly with the number of pairs, bands and configurations to be searched.

Learning a surrogate for the physics model is the natural response, and there is now a substantial literature doing so. It is, however, overwhelmingly **urban**: the canonical public benchmark comprises city maps with building footprints, and the most-cited architectures learn from building geometry. Terrain-dominated, long-range, trans-horizon propagation — where the obstruction is a mountain rather than a building, ranges are tens of kilometres, and the governing parameters are diffraction over ridgelines and scatter angle — is comparatively neglected. Two further gaps matter for our use case. First, learned propagation models are usually evaluated in-domain: train and test in the same environment. A planner deploys the model in terrain it has never seen, and nobody reports what that costs. Second, predictions are usually point estimates. A planner cannot act on a point estimate: the operational question is not "what is the path loss" but "am I confident enough that this link closes to commit a relay detachment to that ridge."

**Contributions.**
1. A terrain-conditioned surrogate for **excess loss over free space** (residual learning), with features expressed in Fresnel radii so that they are frequency-aware and scale-free (§III-C).
2. A **cross-region evaluation protocol** for learned terrain propagation, and the measurement of the resulting generalisation gap (§V-A).
3. **Calibrated uncertainty** via conformalised quantile regression, with the finding that conformal coverage guarantees degrade measurably under terrain shift — an empirical demonstration of exchangeability violation in a propagation setting (§V-B).
4. A **decision-level evaluation** in terms of link feasibility, including the false-go rate, which is the error type that costs a planner most (§V-C).
5. A measured planning-scale speed-up, and an explicit account of what the surrogate does *not* replace (§VI).

---

## II. Related Work

`[[Convert to a comparison table in the final version.]]`

**Physics-based terrain propagation.** Diffraction over irregular terrain is treated by the ITU-R P.526 recommendation, with multiple-obstacle paths handled by constructions such as Deygout's; trans-horizon propagation is addressed by the P.617 troposcatter method, and P.452/P.1812 combine mechanisms for interference and point-to-area prediction. These models are the reference against which any surrogate should be measured, and they are what we use for labels.

**Learned radio maps and path-loss prediction.** RadioUNet established convolutional path-loss map estimation; the RadioMapSeer benchmark and the ICASSP path-loss radio-map prediction challenges (outdoor 2023, indoor 2025) consolidated the field. Deep spectrum cartography addresses the complementary inverse problem of reconstructing maps from sparse measurements. Recent work is candid that ray-tracing-supervised models are simulation-to-simulation surrogates rather than measurement-validated predictors — a framing we adopt explicitly. Differentiable ray tracers now make high-fidelity, geometry-aware label generation practical, including calibration of environment parameters against measurements.

**Uncertainty quantification.** Conformalised quantile regression provides finite-sample, distribution-free prediction intervals under exchangeability. To our knowledge it has not been applied to terrain propagation surrogates, and the interaction between its exchangeability requirement and geographic domain shift has not been examined in this setting — which is one of our findings.

`[[Table columns: {Work | Environment | Label source | Uncertainty? | Cross-domain test? | Decision-level metric?} — your row should be the only one with the last three ticked.]]`

---

## III. Method

### A. Terrain and link sampling

Terrain is a gridded digital elevation model at `[REPLACE: 90 m — state your DEM resolution]` sample spacing. `[REPLACE: describe the two real sectors — location, extent, elevation range, and why their spatial statistics differ. This paragraph is where the paper earns its "terrain-aware" claim, so write it carefully.]`

*Current placeholder text (delete after DEM swap):* two synthetic fractional-Brownian terrains generated by spectral synthesis with different Hurst exponents (0.78 and 0.62), elevation bands (1600–4400 m and 2500–5600 m) and relief (2800 m and 3100 m), so that the second sector constitutes a genuine distribution shift of comparable difficulty rather than an easier problem.

Links are sampled by drawing a transmitter location, an azimuth and a range in 3–45 km, with transmitter height above ground drawn from {3, 6, 10, 15, 25} m and receiver height from {1.8, 3, 6, 10} m, at carrier frequencies {60, 150, 400 MHz, 1.35, 4.4 GHz} spanning generic VHF/UHF/SHF tactical allocations. Terrain profiles are extracted by bilinear interpolation at 256 points along the great-circle path.

### B. Physics labels

For each link we compute the excess loss over free space by combining two mechanisms.

*Diffraction.* Terrain heights are corrected for earth curvature using an effective-earth-radius factor *k* = 4/3, giving *z<sub>eff</sub>*(*d*) = *z*(*d*) + *d*(*D*−*d*)/(2*kR<sub>e</sub>*). For each intermediate point the Fresnel–Kirchhoff parameter is

  ν = *h* · √( (2/λ)·(*d₁*+*d₂*)/(*d₁d₂*) )

with *h* the height of the terrain above the transmitter–receiver line. Single-edge loss follows the ITU-R P.526 approximation *J*(ν) = 6.9 + 20 log₁₀( √((ν−0.1)²+1) + ν − 0.1 ) dB for ν > −0.78, and 0 otherwise. Multiple obstacles are combined by the Deygout construction: the principal edge is the point of maximum ν, and the two sub-paths either side contribute recursively to depth one.

*Trans-horizon scatter.* We compute the angular distance between the two radio horizons, θ = θ<sub>t</sub> + θ<sub>r</sub> + *D*/(*kR<sub>e</sub>*), and evaluate a simplified scatter excess loss that retains the dominant dependence on scatter angle and frequency.

*Combination.* The two mechanisms are combined by power sum, so that the stronger path dominates: *L<sub>ex</sub>* = −10 log₁₀(10<sup>−L<sub>diff</sub>/10</sup> + 10<sup>−L<sub>ts</sub>/10</sup>). Total loss is *L* = FSPL + *L<sub>atm</sub>* + *L<sub>ex</sub>*.

**Stated simplifications.** Deygout without the Causebrook correction; recursion depth one; no sub-path attenuation term; a simplified rather than full P.617 troposcatter formulation; a coarse gaseous/vegetation allowance; no clutter database; no time-variability or fading statistics. These are approximations of a reference model, not of reality, and they define the target the surrogate is trained to reproduce. `[[Reviewers will respect this paragraph. Do not soften it.]]`

### C. Surrogate model

The surrogate predicts *L<sub>ex</sub>* — the excess over free space — rather than total loss, since FSPL is known analytically; this is residual learning and it removes the trivial distance dependence from the learning problem.

Features (60 in total): 48 samples of terrain clearance relative to the line of sight, **normalised by the first Fresnel-zone radius at each point**, which makes the representation frequency-aware and scale-free; plus range, log frequency, both antenna heights, maximum clearance in metres and in Fresnel radii, obstructed fraction of the path, terrain standard deviation, relief, both endpoint elevations, and the standard deviation of the terrain gradient.

The predictor is a histogram gradient-boosted regression ensemble: one squared-error model for the conditional median and two quantile models at the 5th and 95th percentiles. `[[If you have time and a GPU, a 1-D CNN over the raw 256-point profile is the natural upgrade and would likely reduce error; report it as future work if you don't.]]`

### D. Calibrated intervals

Raw quantile regression is not guaranteed to attain nominal coverage. We therefore apply split-conformal calibration (conformalised quantile regression) on a held-out calibration set: with *E<sub>i</sub>* = max( *q̂*<sub>0.05</sub>(*x<sub>i</sub>*) − *y<sub>i</sub>*, *y<sub>i</sub>* − *q̂*<sub>0.95</sub>(*x<sub>i</sub>*) ), we take *Q* as the ⌈(*n*+1)(1−α)⌉-th smallest value of *E* and widen the interval symmetrically by *Q*. This yields marginal coverage of at least 1−α provided calibration and test data are exchangeable — an assumption we then deliberately break.

### E. Evaluation protocol

Region A supplies 7000 training links, 1000 calibration links and 1000 held-out test links; Region B supplies 2000 test links never seen in any form. We report mean absolute error, RMSE, bias, 90% interval coverage and width, and a decision-level metric: treating a fixed total-loss budget as the feasibility threshold, we report classification accuracy together with the **false-go rate** (fraction of links the planner is told will close that will not) and the false-no-go rate. An ablation removes the terrain profile features, leaving only geometry and summary statistics — the information a statistical model would have.

---

## IV. Results

**TABLE I — Surrogate accuracy, calibration and decision quality** `[REPLACE ALL VALUES after the DEM swap]`

| Split | *n* | MAE (dB) | RMSE (dB) | Bias (dB) | 90% PI coverage | PI width (dB) | Feasibility acc. | False-go rate |
|---|---|---|---|---|---|---|---|---|
| In-region (A), raw quantiles | 1000 | 5.86 | 7.78 | +0.06 | 0.814 | 22.1 | 0.933 | 0.055 |
| In-region (A), conformal | 1000 | 5.86 | 7.78 | +0.06 | **0.913** | 26.1 | 0.933 | 0.055 |
| **Cross-region (B), conformal** | 2000 | **8.22** | 10.59 | −1.61 | **0.831** | 31.9 | 0.922 | 0.092 |
| In-region, geometry only | 1000 | 6.79 | 9.06 | +0.04 | 0.902 | 28.8 | 0.924 | 0.060 |
| Cross-region, geometry only | 2000 | 9.21 | 11.87 | −0.14 | 0.856 | 34.4 | 0.903 | 0.094 |

Label statistics: Region A mean excess loss 52.8 dB (95th percentile 102.8 dB, 96% of links obstructed); Region B mean 66.4 dB (95th percentile 115.1 dB, 99% obstructed) — the unseen sector is the *harder* of the two, so the reported generalisation gap is not an artefact of an easier test set. `[REPLACE]`

**TABLE II — Planning-scale workload** `[REPLACE]`

| Workload | Physics model | Surrogate | Speed-up |
|---|---|---|---|
| 160 candidate sites → 12 720 links | 1.585 s | 0.068 s | 23× |

### A. Terrain features help, and the cross-region gap is real

Including the terrain profile reduces in-region MAE from 6.79 dB to 5.86 dB (−14%) and cross-region MAE from 9.21 dB to 8.22 dB (−11%) `[REPLACE]`. The gain is consistent but moderate: a substantial fraction of the predictable variance is already carried by geometry and coarse terrain statistics. We report this plainly rather than overselling the profile encoder. `[[Reviewers trust authors who publish the modest version of their own result.]]`

The cross-region gap is the headline finding: **error inflates by 40% on an unseen terrain sector**, and the bias flips from +0.06 dB to −1.61 dB, i.e. the surrogate systematically *under-predicts* loss in the new sector — the dangerous direction, because under-predicted loss means over-predicted link viability. This is visible in the prediction–label scatter (Fig. 2) and in the error CDF (Fig. 3).

### B. Conformal calibration works in-region and degrades under shift

Raw quantile intervals attain only 81.4% coverage against a 90% nominal target. Split-conformal widening (+2.02 dB) restores 91.3% in-region — as the theory promises. On the unseen sector the same intervals cover 83.1% `[REPLACE]`: a 7.9-point shortfall that quantifies the violation of exchangeability caused by moving to different terrain. The intervals remain informative and remain wider where the model is less certain (Fig. 4), but they are no longer guaranteed. **The practical implication for a planner is that a model calibrated in one sector must be re-calibrated with a modest number of links from the new sector before its confidence statements can be trusted** — and calibration, unlike training, needs only hundreds of samples, which makes this a tractable operational procedure rather than a blocking limitation.

### C. Decision-level performance is better than the dB error suggests

Framed as the planner's binary question, the surrogate agrees with the physics model on 93.3% of links in-region and 92.2% cross-region. The false-go rate — links predicted to close that do not — rises from 5.5% to 9.2% `[REPLACE]`. This asymmetry matters: a false no-go wastes a candidate site, while a false go can commit a detachment to a ridge that will not communicate. Because the surrogate is systematically optimistic on unseen terrain (§IV-A), we recommend it be used with the **lower** conformal bound rather than the median when the decision is committal, which trades candidate-site recall for protection against false go.

---

## V. Discussion and Limitations

**What this is for.** The surrogate is a *screening* tool. It reduces the candidate set that a full physics or ray-tracing evaluation must consider by roughly an order of magnitude in compute, and it makes interactive replanning feasible. It does not replace the reference model for a final decision, and we do not claim it does.

**Limitations, stated plainly.**
1. `[REPLACE — THE MOST IMPORTANT ONE]` **Terrain source.** Results in this draft were generated on synthetic fractal terrain, so they validate the pipeline rather than any specific sector. `[[After the DEM swap this becomes: results are from two real DEM sectors, but only two, so cross-region conclusions are based on a single shift pair.]]`
2. **Simulation-to-simulation.** Labels come from a simplified multi-mechanism physics model, not from drive tests or field measurements. The surrogate is measured against that model, so its errors compound with the model's own error relative to reality. Measurement validation is the necessary next step and we do not pre-empt its outcome.
3. **Physics simplifications** as enumerated in §III-B, including Deygout without the Causebrook correction and a simplified troposcatter term.
4. **Modest speed-up as measured.** The 23× figure is relative to *our* reference implementation, which is itself fast. The surrogate's advantage grows with the fidelity of the reference solver — for a 3-D ray-traced reference the ratio would be far larger — but we have not measured that and therefore do not claim it.
5. **No time variability.** Only median-condition propagation is modelled; percentage-of-time statistics, fading and weather are absent.
6. **Two sectors only**, one shift pair, one label model.

**Future work.** Real measurement validation; a 1-D or 2-D convolutional profile encoder; extension to 3-D low-altitude airspace for UAV relay placement; multi-fidelity training that mixes cheap ITU-R labels with a small number of ray-traced or measured labels; and integration into an interactive relay-placement optimiser where the uncertainty bound, not the point prediction, drives site selection.

---

## VI. Conclusion

For learned propagation models to be usable in tactical link planning, the properties that matter are not in-domain accuracy but **generalisation to unseen terrain** and **trustworthy uncertainty**. On our physics-labelled terrain data, a gradient-boosted surrogate over Fresnel-normalised clearance profiles achieved 5.86 dB MAE in the sector it was trained on and 8.22 dB on an unseen sector — a 40% inflation, in the optimistic direction — while conformal prediction intervals fell from 91.3% to 83.1% coverage under the same shift `[REPLACE]`. Framed as the planner's feasibility decision, accuracy held above 92% but the false-go rate nearly doubled. Screening a 160-site candidate matrix cost 0.068 s against 1.585 s for the physics model. We therefore argue that cross-region validation and calibrated, re-calibratable uncertainty should be standard reporting practice for learned propagation models intended for operational planning, and we note that re-calibration on a few hundred local links is a realistic field procedure.

---

## Figures (in `out_idea3/`)

| File | Caption to use |
|---|---|
| `fig1_terrain.png` | Fig. 1. The two terrain sectors: training sector (left) and unseen evaluation sector (right). `[REPLACE with real DEM and state locations/extent]` |
| `fig2_pred_vs_true.png` | Fig. 2. Surrogate prediction against physics label, in-region (left) and cross-region (right). Dashed line: ideal. |
| `fig3_error_cdf.png` | Fig. 3. Absolute error distribution in-region and cross-region. |
| `fig4_uncertainty.png` | Fig. 4. Conformal 90% prediction intervals on the unseen sector, links sorted by true loss. |

`[[Add a fifth figure if you have space: error broken down by frequency band and by range. It is cheap to produce from the saved CSVs and it answers the first question a propagation reviewer will ask.]]`

---

## References — **VERIFY EVERY ONE BEFORE SUBMITTING**

1. ITU-R Recommendation P.526, *Propagation by diffraction*.
2. J. Deygout, "Multiple knife-edge diffraction of microwaves," *IEEE Trans. Antennas Propag.*, 1966.
3. ITU-R Recommendation P.617, *Propagation prediction techniques and data required for the design of trans-horizon radio-relay systems*.
4. ITU-R Recommendation P.452, *Prediction procedure for the evaluation of interference between stations on the surface of the Earth*. `[[and/or P.1812 for point-to-area]]`
5. R. Levie, Ç. Yapar, G. Kutyniok, G. Caire, "RadioUNet: Fast radio map estimation with convolutional neural networks," *IEEE Trans. Wireless Commun.*, vol. 20, no. 6, pp. 4001–4015, 2021.
6. Ç. Yapar *et al.*, "Overview of the First Pathloss Radio Map Prediction Challenge," ICASSP 2023. `[[verify]]`
7. S. Bakirtzis *et al.*, "The First Indoor Pathloss Radio Map Prediction Challenge," ICASSP 2025. `[[verify]]`
8. Shrestha *et al.*, "Deep spectrum cartography: Completing radio map tensors using learned neural models," *IEEE Trans. Signal Process.*, vol. 70, pp. 1170–1184, 2022. `[[verify author list]]`
9. J. Hoydis *et al.*, "Sionna RT: Differentiable ray tracing for radio propagation modeling," 2023.
10. Y. Romano, E. Patterson, E. Candès, "Conformalized quantile regression," *NeurIPS*, 2019.
11. `[[Your DEM source citation — SRTM/Copernicus/Bhoonidhi, cited properly with version and access date.]]`
12. `[[A recent (2025–2026) learned-radio-map paper that explicitly frames itself as simulation-to-simulation — strengthens your framing.]]`
13–22. `[[Add: a terrain-diffraction validation study; a troposcatter link-design reference; one or two Indian propagation-measurement papers (mountain or rural); a gradient-boosting reference; a domain-shift/domain-generalisation reference; a link-planning/relay-placement optimisation paper.]]`

---

## Reproducibility statement

The label generator, feature extractor, model, conformal calibration and all evaluation scripts are available at `[[your GitHub URL]]`. `[REPLACE: state DEM tiles, their source, resolution, CRS and access date; the number of links per sector; and the random seeds.]` Training took 3.0 s on a single CPU core; the full pipeline including label generation runs in under one minute.
