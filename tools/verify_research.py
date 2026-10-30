"""Run the research validation gate without pytest's unsafe host-version probe.

The tests themselves are unchanged: unittest classes and parameterized test
functions are adapted into one unittest suite, with no skipped function tests.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import inspect
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def suite_for(path):
    namespace=runpy.run_path(str(path),run_name=f'_gate_{path.stem}')
    suite=unittest.TestSuite()
    for obj in namespace.values():
        if inspect.isclass(obj) and issubclass(obj,unittest.TestCase) and obj is not unittest.TestCase:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
    generated=type(f'{path.stem}_functions',(unittest.TestCase,),{})
    for name,fn in namespace.items():
        if not name.startswith('test_') or not inspect.isfunction(fn):
            continue
        marks=[mark for mark in getattr(fn,'pytestmark',[]) if mark.name=='parametrize']
        if len(marks)>1:
            raise RuntimeError(f'Explicit adapter required for multiple parametrizations: {path}/{name}')
        if marks:
            names=marks[0].args[0]
            names=[n.strip() for n in names.split(',')] if isinstance(names,str) else list(names)
            values=marks[0].args[1]
        else:
            names=[]
            values=[()]
            if inspect.signature(fn).parameters:
                raise RuntimeError(f'Unprovided fixture arguments: {path}/{name}')
        for i,value in enumerate(values):
            args=value if isinstance(value,tuple) else (value,)
            kwargs=dict(zip(names,args)) if marks else {}
            if marks and len(kwargs)!=len(names):
                raise RuntimeError(f'Parametrization arity mismatch: {path}/{name}')
            def run(self,function=fn,arguments=kwargs):
                function(**arguments)
            setattr(generated,f'{name}_{i:02}',run)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(generated))
    return suite


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--test',help='Run one test-file stem only')
    args=parser.parse_args()
    suites=[]
    counts={}
    for path in sorted((ROOT/'tests').glob('test_*.py')):
        if args.test and path.stem!=args.test:
            continue
        suite=suite_for(path)
        counts[path.name]=suite.countTestCases()
        if counts[path.name]==0:
            raise RuntimeError(f'Test module contains no collected checks: {path}')
        suites.append(suite)
    if not suites:
        raise ValueError('No test modules selected')
    if args.list:
        print(json.dumps({'collected':counts,'total':sum(counts.values())},indent=2))
        return 0
    started=time.perf_counter()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(suites))
    historical=None
    if not args.test:
        run=subprocess.run([sys.executable,'-X','utf8','-u',str(ROOT/'experiments/e1_validation.py')],
                           cwd=ROOT,text=True,capture_output=True,encoding='utf-8',timeout=120)
        historical={'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
        print(run.stdout)
        if run.stderr:
            print(run.stderr,file=sys.stderr)
    report={'timestamp_utc':datetime.now(timezone.utc).isoformat(),
            'python':sys.version,'os_name':os.name,
            'windows_version':list(sys.getwindowsversion()) if os.name=='nt' else None,
            'test_modules':counts,'regression_tests_run':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),
            'skipped':len(result.skipped),'legacy_validation':historical,
            'wall_s':time.perf_counter()-started,
            'passed':result.wasSuccessful() and not result.skipped
                     and (historical is None or historical['returncode']==0)}
    destination=ROOT/'results/revision/verification'
    destination.mkdir(exist_ok=True)
    filename='research_gate.json' if not args.test else f'{args.test}_gate.json'
    (destination/filename).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['regression_tests_run','failures','errors','skipped','passed']},indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
