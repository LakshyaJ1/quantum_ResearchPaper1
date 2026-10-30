"""Small staged one-worker ProcessPool diagnostic, no production artifact writes."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import faulthandler
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
faulthandler.enable()


def worker(kind):
    print(json.dumps({"worker_started":kind, "pid":os.getpid()}), flush=True)
    if kind == "stdlib":
        result = sum(range(1000))
    elif kind == "numpy":
        import numpy as np
        result = float(np.random.default_rng(5).normal(size=10000).mean())
    elif kind == "simulation":
        from revision.scenarios import Case, make_simulator
        result = make_simulator(Case(horizon_s=60), 21).run().served_fraction()
    else:
        from experiments import revision_suite as suite
        from revision.scenarios import Case
        suite.OUT = ROOT / "docs/revision/audit_tools/pool_probe_outputs"
        (suite.OUT / "runs").mkdir(parents=True, exist_ok=True)
        case = Case(horizon_s=86400 if kind == "runner_full" else 60)
        record = {"case_id":suite.case_key(case), "tags":["audit_only"],"case":case.to_dict()}
        print(json.dumps({"runner_imported":True,"case_id":record["case_id"]}),flush=True)
        result = suite.run_job((record,21,suite.fingerprint()))
    return {"kind":kind, "pid":os.getpid(), "result":result}


def main():
    print(json.dumps({"parent_started":True,"pid":os.getpid(),"executable":sys.executable}),flush=True)
    if "--eager-import" in sys.argv:
        from experiments import revision_suite
        print(json.dumps({"eager_runner_imported":True}),flush=True)
    kinds = ("runner_full",) if "--runner-full" in sys.argv else ("stdlib","numpy","simulation")
    for kind in kinds:
        print(json.dumps({"stage":kind,"starting_pool":True}),flush=True)
        start=time.perf_counter()
        with ProcessPoolExecutor(max_workers=1) as pool:
            result = pool.submit(worker,kind).result(timeout=45)
        print(json.dumps({"stage":kind,"completed":result,"elapsed_s":time.perf_counter()-start}),flush=True)


if __name__ == "__main__":
    main()
