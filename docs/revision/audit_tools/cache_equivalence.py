"""Compare complete corrected rollouts with/without pure rate memoization.

Only patches a function inside this audit process; does not edit simulator code.
"""
from pathlib import Path
import functools
import hashlib
import json
import sys
import time
from dataclasses import asdict

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import qkdsim.physics as physics
from revision.scenarios import Case, make_simulator


def main():
    plain = getattr(physics.rate_fraction, "__wrapped__", physics.rate_fraction)
    cached = functools.lru_cache(maxsize=256)(plain)
    quick = "--quick" in sys.argv
    case = Case(horizon_s=3600 if quick else 86400, outage_model="correlated", mean_uptime_s=900,
                mean_outage_s=240, attack_budget=2, attack_start_s=9000,
                attack_duration_s=20000, e_abort=0.11, gamma=3.4,
                buffer_policy="purge")
    rows = []
    serializations = []
    implementations = [("plain", plain), ("memoized", cached)]
    if quick:
        implementations += [("memoized", cached), ("plain", plain)]
    for name, fn in implementations:
        physics.rate_fraction = fn
        start = time.perf_counter()
        result = make_simulator(case, 4321).run()
        elapsed = time.perf_counter() - start
        serialized = json.dumps(asdict(result), sort_keys=True)
        serializations.append(serialized)
        rows.append({"implementation": name, "wall_s": elapsed,
                     "sessions": len(result.sessions),
                     "result_sha256": hashlib.sha256(serialized.encode()).hexdigest()})
    physics.rate_fraction = plain
    assert all(s == serializations[0] for s in serializations), "Memoization changed a result field"
    print(json.dumps({"case": asdict(case), "complete_result_equal": True,
                      "runs": rows, "cache": cached.cache_info()._asdict()}, indent=2))


if __name__ == "__main__":
    main()
