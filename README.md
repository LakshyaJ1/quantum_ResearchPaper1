# Forced Assurance Loss in Contested Multi-Hop QKD Networks

Simulator, experiments and results for the paper *Fail-Closed or Fail-Degraded? A
Simulation Study of Forced Assurance Loss in Contested Multi-Hop QKD Networks*.

The study asks what a trusted-relay QKD network should do when secret key runs short:
refuse service, or keep the circuit up on a computationally secure key. It measures
what each choice costs and what an adversary must spend to force it.

## Layout

```
qkdsim/          discrete-event simulator
  config.py        all parameters, each with its provenance
  physics.py       key-rate model, four link states, reservoir semantics
  network.py       topologies and path selection
  sim.py           session arrival, admission, grade assignment, accounting
  rl.py            grade-assignment policy search and safety shield
experiments/     experiment scripts, one per reported result
results/         generated CSVs backing every table and figure
figures/         generated figures
```

## Reproducing the paper

```bash
python experiments/e1_validation.py            # 43-check gate; must pass first
python experiments/run_experiments.py         # main grid (E2-E5)
python experiments/e6b_sensitivity.py         # sensitivity and operating envelope
python experiments/e6c_nauth.py               # authentication-cost robustness
python experiments/e7_policy_audit.py         # policy-space audit
python experiments/e8_published_validation.py # checks against published measurements
python experiments/make_figures.py            # figures from the CSVs
```

Runs are deterministic: seeds are fixed and common random numbers are used across
policies, so a re-run reproduces the reported values exactly. The full set takes about
30 minutes on eight CPU cores. No GPU and no proprietary dependencies.

`experiments/verify_paper_numbers.py` re-derives every quantitative claim in the
manuscript from `results/` and fails if any has drifted.

## Requirements

Python 3.10+, `numpy`, `pandas`, `matplotlib`. No network access is needed at run
time.

## Notes on the model

Key is a depletable per-link resource: an *n*-hop relayed path consumes it on every
link, and per-hop cost includes relay metadata and information-theoretic
authentication, not just the delivered key. Sessions are served at one of four
assurance grades, from one-time pad down to post-quantum only, and each traffic class
carries an authorised floor. When the key economy cannot meet a floor the controller
either blocks (fail-closed) or serves below it and records the violation
(fail-degraded).

Two metrics are reported and are not interchangeable. *Floor violation* counts served
sessions below the grade their class authorises, which may still be delivered by QKD.
*Forced assurance loss* counts sessions entitled to an information-theoretically
secure key that are served without one.

Every parameter in `config.py` carries a source. Values that could not be grounded in
the literature are swept rather than asserted; the authentication message count is the
one such term and is reported at the optimistic end of its calibrated range.

## Limitations

Per-link key rates are parameterised inputs, not simulated photonics. The two
degradation calibrations disagree by a factor of five and both are reported. Relay
nodes are assumed trusted, with compromise modelled only as an availability event.
Detector blinding raises no QBER and is therefore invisible to this model by
construction. The headline result rests on one nine-node formation, with a chain
family used for the depth study.

## Citation

Please cite the paper. ITU-T and ETSI specifications referenced by the model are not
redistributed here.
