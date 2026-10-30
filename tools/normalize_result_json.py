"""Represent undefined suite metrics as RFC-compatible JSON null.

This is a documented serialization step after simulation. It does not alter any
finite numeric value, source/configuration identifier, counter or random seed.
Only the suite's Python-compatible NaN/Infinity tokens are normalized; signed
learning/fallback/online records already use strict JSON and are not touched.
"""
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def clean(value):
    if isinstance(value,dict):
        return {key:clean(item) for key,item in value.items()}
    if isinstance(value,list):
        return [clean(item) for item in value]
    if isinstance(value,float) and not math.isfinite(value):
        return None
    return value


def reject_constant(value):
    raise ValueError(f'Non-standard JSON numeric token: {value}')


def main():
    records=[]
    total=0
    for path in sorted((ROOT/'results/revision/runs').glob('*.json')):
        before=path.read_bytes()
        parsed=json.loads(before)
        normalized=clean(parsed)
        try:
            json.loads(before,parse_constant=reject_constant)
            total+=1
            continue
        except ValueError:
            pass
        after=json.dumps(normalized,indent=2,allow_nan=False).encode('utf-8')
        reread=json.loads(after,parse_constant=reject_constant)
        if reread!=normalized:
            raise AssertionError(f'Normalization changed semantic values: {path}')
        temp=path.with_suffix('.normalizing')
        temp.write_bytes(after)
        temp.replace(path)
        records.append({'path':path.relative_to(ROOT).as_posix(),
                        'before_sha256':hashlib.sha256(before).hexdigest(),
                        'after_sha256':hashlib.sha256(after).hexdigest()})
        total+=1
    output=ROOT/'results/revision/verification/json_serialization.json'
    output.parent.mkdir(exist_ok=True)
    if records or not output.exists():
        report={'timestamp_utc':datetime.now(timezone.utc).isoformat(),
                'records_checked':total,'records_normalized':len(records),
                'change':'Only nonfinite undefined values replaced with null',
                'finite_values_and_identifiers_preserved':True,
                'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'files':records}
        output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print(f'{total} suite records are strict JSON; {len(records)} normalized in this invocation')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
