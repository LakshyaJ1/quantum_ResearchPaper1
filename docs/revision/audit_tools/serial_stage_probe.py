"""Run an unchanged runner job with stage logging and optional pythonw logs."""
from pathlib import Path
import atexit
import faulthandler
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
if "--file-log" in sys.argv:
    log = (ROOT/"docs/revision/audit_tools/serial_stage_probe.log").open("w",encoding="utf-8",buffering=1)
    sys.stdout = sys.stderr = log
faulthandler.enable()
print("bootstrap",os.getpid(),sys.executable,flush=True)
atexit.register(lambda: print("atexit",flush=True))
from experiments import revision_suite as suite
from qkdsim.sim import Simulator
print("imports completed",flush=True)

if "--diagnostic-dir" in sys.argv:
    suite.OUT = ROOT/"docs/revision/audit_tools/serial_probe_outputs"
    (suite.OUT/"runs").mkdir(parents=True,exist_ok=True)

original = Simulator.run
def traced_run(self):
    print("simulation enter",flush=True)
    result = original(self)
    print("simulation complete",len(result.sessions),flush=True)
    return result
Simulator.run = traced_run
orig_summarize = suite.summarize
counter = 0
def traced_summarize(*args,**kwargs):
    global counter
    counter += 1
    print("summarize enter",counter,flush=True)
    r=orig_summarize(*args,**kwargs)
    print("summarize exit",counter,flush=True)
    return r
suite.summarize=traced_summarize

if __name__=="__main__":
    case=suite.cases_for("main")[0]
    print("case",case,flush=True)
    seed=3006
    print("run_job enter",seed,flush=True)
    print("run_job exit",suite.run_job((case,seed,suite.fingerprint())),flush=True)
