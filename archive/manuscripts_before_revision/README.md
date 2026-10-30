# Forced assurance loss in contested multi-hop QKD networks

Code and results for our WiCOMM-2026 paper, *Fail-Closed or Fail-Degraded? A
Simulation Study of Forced Assurance Loss in Contested Multi-Hop QKD Networks*.

The question is what a trusted-relay QKD network should do once it can no longer
supply enough key: refuse service, or keep the circuit up on a computationally secure
key instead. We built a discrete-event simulator to measure what each choice costs and
what an adversary has to spend to force it.

## Running it

Python 3.10+, with `numpy`, `pandas` and `matplotlib`. Nothing else, and no network
access at run time.

Run the validation gate first — if it fails, don't trust anything downstream:

```bash
python experiments/e1_validation.py
```

Then the experiments, in any order:

```bash
python experiments/run_experiments.py         # main grid, E2-E5
python experiments/e6b_sensitivity.py         # gamma, abort threshold, operating envelope
python experiments/e6c_nauth.py               # authentication cost
python experiments/e7_policy_audit.py         # policy search
python experiments/e8_published_validation.py # checks against published measurements
python experiments/make_figures.py            # figures, from the CSVs in results/
```

The whole set takes about half an hour on eight cores. Seeds are fixed and policies
share common random numbers, so re-running gives the same numbers we report — worth
checking, since that is the point of releasing this.

`e6b_sensitivity.py --from-csv` re-derives its tables from the stored CSV without
re-simulating, which saves a lot of time if you only want to inspect the output.

## Layout

```
qkdsim/config.py     every parameter, with the paper or spec it came from
qkdsim/physics.py    key-rate model, four link states, reservoir semantics
qkdsim/network.py    topologies and path selection
qkdsim/sim.py        arrivals, admission, grade assignment, key accounting
qkdsim/rl.py         grade-assignment policy search and the safety shield
experiments/         one script per reported result, plus two diagnostics
results/             the CSVs behind every table and figure
figures/             generated figures, PDF and PNG
```

## Reading the results

Two columns in the CSVs are easy to confuse, and they are not interchangeable:

- `floor_viol` — sessions served below the grade their traffic class authorises. These
  may still have been delivered by QKD.
- `forced_below_its` — sessions *entitled* to an information-theoretically secure key
  that were served without one.

The second is the metric the paper is about. At zero adversary budget the first is
non-zero and the second is zero, which is the distinction `diag_baseline_forced.py`
exists to demonstrate.

`config.py` carries the provenance for every number. Where we could not ground a value
in the literature we sweep it rather than assert it; the count of authenticated
messages per key delivery is the one such term, and we report at the optimistic end of
its calibrated range and sweep the rest.

ITU-T and ETSI documents referenced by the model are not redistributed here.
