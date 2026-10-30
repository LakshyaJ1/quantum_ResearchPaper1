"""Check that paired fail-mode comparisons used the same static attack sets."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def audit(phase):
    manifest=json.loads((ROOT/f'results/revision/manifest_{phase}.json').read_text())
    groups=defaultdict(set)
    pairs=defaultdict(dict)
    for case in manifest['cases']:
        for seed in manifest['seed_ids']:
            path=ROOT/'results/revision/runs'/f"{case['case_id']}_seed{seed}.json"
            record=json.loads(path.read_text())
            config=record['case']
            edges=tuple(sorted(tuple(edge) for edge in record['topology']['attacked_edges']))
            group=tuple(config[k] for k in ('topology','attack_method','fibre_attack_cost','attack_budget'))
            groups[group].add(edges)
            paired_config=tuple(sorted((k,v) for k,v in config.items() if k!='fail_mode'))
            pairs[(paired_config,seed)][config['fail_mode']]=edges
    mismatches=sum(len(set(pair.values()))!=1 for pair in pairs.values())
    missing=sum(set(pair)!= {'FAIL_CLOSED','FAIL_DEGRADED'} for pair in pairs.values())
    report={'phase':phase,'mode_pairs_checked':len(pairs),
            'target_mismatches':mismatches,'missing_mode_pairs':missing,
            'attack_set_variants':[{'configuration':key,'variants':len(value)} for key,value in groups.items()],
            'passed':mismatches==0 and missing==0}
    destination=ROOT/'results/revision/verification'
    destination.mkdir(exist_ok=True)
    (destination/f'{phase}_attack_pairing.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not report['passed']:
        raise AssertionError(report)
    print(json.dumps(report,indent=2))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',default='main')
    audit(parser.parse_args().phase)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
