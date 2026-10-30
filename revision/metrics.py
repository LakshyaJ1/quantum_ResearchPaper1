"""Common-denominator outcomes and seed-level uncertainty for the revision."""
from __future__ import annotations

import math
import numpy as np

from qkdsim.config import G2_QKD_SYM, is_at_least
from qkdsim.sim import Outcome, Results


def ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else float('nan')


def summarize(results: Results, cls=None, start=None, end=None):
    xs = [s for s in results.sessions
          if (cls is None or s.cls == cls)
          and s.arrival_t >= (results.warmup_s if start is None else start)
          and (end is None or s.arrival_t < end)]
    served = [s for s in xs if s.outcome == Outcome.SERVED
              and s.served_t <= s.arrival_t + s.deadline_s + 1e-9]
    qualified = [s for s in served if is_at_least(s.grade, s.authorised_floor)]
    degraded = [s for s in served if not is_at_least(s.grade, s.authorised_floor)]
    entitled = [s for s in xs if is_at_least(s.authorised_floor, G2_QKD_SYM)]
    entitled_served = [s for s in served if is_at_least(s.authorised_floor, G2_QKD_SYM)]
    forced = [s for s in entitled_served if not is_at_least(s.grade, G2_QKD_SYM)]
    n, ne = len(xs), len(entitled)
    exposure = sum(s.payload_bits for s in xs)
    entitled_exposure = sum(s.payload_bits for s in entitled)
    availability, qualified_availability = ratio(len(served), n), ratio(len(qualified), n)
    degraded_fraction = ratio(len(degraded), n)
    out = dict(
        n_arrivals=n, n_served=len(served), n_qualified=len(qualified),
        n_degraded=len(degraded), n_blocked=n-len(served),
        n_entitled=ne, n_forced=len(forced),
        availability=availability, qualified_availability=qualified_availability,
        degraded_arrival_fraction=degraded_fraction,
        blocked_arrival_fraction=ratio(n-len(served), n),
        forced_entitled_fraction=ratio(len(forced), ne),
        entitled_blocked_fraction=ratio(ne-len(entitled_served), ne),
        entitled_its_fraction=ratio(len(entitled_served)-len(forced), ne),
        conditional_forced_fraction=ratio(len(forced), len(entitled_served)),
        degraded_payload_fraction=ratio(sum(s.payload_bits for s in degraded), exposure),
        forced_payload_fraction=ratio(sum(s.payload_bits for s in forced), entitled_exposure),
        qualified_payload_fraction=ratio(sum(s.payload_bits for s in qualified), exposure),
        key_Mbit=sum(s.key_bits for s in served)/1e6,
        mean_hops=float(np.mean([s.hops for s in served])) if served else float('nan'),
        latency_p95=float(np.percentile([s.served_t-s.arrival_t for s in served],95)) if served else float('nan'),
        first_degraded_s=min((s.served_t for s in degraded), default=float('nan')),
        first_forced_s=min((s.served_t for s in forced), default=float('nan')),
        utility=availability-0.75*degraded_fraction,
    )
    return out


def paired_interval(treatment, control, confidence=.95, resamples=20000, seed=71):
    a, b = np.asarray(treatment, float), np.asarray(control, float)
    if a.shape != b.shape or a.ndim != 1 or len(a) < 2:
        raise ValueError('Need at least two matched independent seed-level pairs')
    if not np.all(np.isfinite(a-b)):
        raise ValueError('Nonfinite metric: report undefined denominators explicitly')
    delta = a-b
    boot = delta[np.random.default_rng(seed).integers(len(delta), size=(resamples,len(delta)))].mean(axis=1)
    alpha = (1-confidence)/2
    lo, hi = np.quantile(boot, [alpha,1-alpha])
    return float(delta.mean()), float(lo), float(hi)


def mean_interval(values, confidence=.95, resamples=20000, seed=71):
    a = np.asarray(values,float)
    return paired_interval(a, np.zeros_like(a), confidence, resamples, seed)
