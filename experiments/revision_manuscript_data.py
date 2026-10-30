"""Export manuscript numbers and tables with an explicit evidence ledger."""
import json
import math
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
import pandas as pd
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from revision.scenarios import Case
from revision.metrics import paired_interval
DATA=ROOT/'results/revision/analysis'
OUT=ROOT/'results/revision/manuscript'


def _json_ready(value):
    """Represent undefined nonfinite measurements as JSON null, preserving numbers."""
    if isinstance(value,float) and not math.isfinite(value):
        return None
    if isinstance(value,dict):
        return {key:_json_ready(item) for key,item in value.items()}
    if isinstance(value,(list,tuple)):
        return [_json_ready(item) for item in value]
    return value


def _ledger_json(value):
    return json.dumps(_json_ready(value),indent=2,allow_nan=False)


@lru_cache(maxsize=4)
def summary_frame(phase):
    verification=json.loads((DATA/f'{phase}_verification.json').read_text())
    if not verification.get('canonical_runs'):
        raise ValueError('Canonical analysis must finish before manuscript extraction')
    return pd.read_csv(DATA/f'{phase}_summary.csv',float_precision='round_trip')


def scenario_row(phase,case,cls='all'):
    frame=summary_frame(phase)
    selected=frame[frame.traffic_class==cls]
    for key,value in asdict(case).items():
        selected=selected[selected[key]==value]
    if len(selected)!=1:
        raise ValueError(f'Expected one canonical scenario, found{len(selected)}: {case}')
    return selected.iloc[0]


def select_one(frame,**criteria):
    for key,value in criteria.items():
        frame=frame[frame[key]==value]
    if len(frame)!=1:
        raise ValueError(f'Nonunique evidence selection: {criteria}')
    return frame.iloc[0]


def export_remaining_results():
    specifications=[]
    def add(name,row,key,scale=100,digits=2):
        specifications.append((name,row,key,scale,digits))
    def interval(stem,row,metric):
        for suffix,key in [('',metric),('Lo',metric+'_lo'),('Hi',metric+'_hi')]:
            add(stem+suffix,row,key)
    for name,fill in [('Low',.02),('Mid',.1),('Full',1.)]:
        row=scenario_row('sensitivity',Case(attack_budget=2,initial_spendable_fraction=fill,fail_mode='FAIL_CLOSED'))
        interval('Stock'+name+'Closed',row,'availability')
    for name,duration in [('Hour',3600),('Six',21600),('Day',86400)]:
        row=scenario_row('sensitivity',Case(attack_budget=2,attack_duration_s=duration))
        interval('Duration'+name+'Forced',row,'forced_entitled_fraction')
    low=scenario_row('sensitivity',Case(attack_budget=2,n_auth=2,fail_mode='FAIL_CLOSED'))
    high=scenario_row('sensitivity',Case(attack_budget=2,n_auth=40,fail_mode='FAIL_CLOSED'))
    add('AuthLowClosed',low,'availability')
    add('AuthHighClosed',high,'availability')
    raw=pd.read_csv(DATA/'sensitivity_canonical_raw_metrics.csv',float_precision='round_trip')
    a=raw[(raw.case_id==low.case_id)&(raw.traffic_class=='all')].sort_values('seed')
    b=raw[(raw.case_id==high.case_id)&(raw.traffic_class=='all')].sort_values('seed')
    if a.seed.tolist()!=b.seed.tolist() or a.arrival_sha256.tolist()!=b.arrival_sha256.tolist():
        raise ValueError('Authentication contrast is not paired')
    mean,lo,hi=paired_interval(a.availability,b.availability)
    auth=pd.Series({'mean':mean,'lo':lo,'hi':hi,'control_case_id':high.case_id,
                    'treatment_case_id':low.case_id,'n_seeds':len(a)})
    for suffix,key in [('', 'mean'),('Lo','lo'),('Hi','hi')]:
        add('AuthClosedLoss'+suffix,auth,key)
    corr=Case(attack_budget=0,outage_model='correlated',mean_uptime_s=900,mean_outage_s=600)
    interval('CorrelatedBaseForced',scenario_row('sensitivity',corr),'forced_entitled_fraction')
    pairs=pd.read_csv(DATA/'sensitivity_paired_comparisons.csv',float_precision='round_trip')
    criteria=asdict(Case(attack_budget=2,outage_model='correlated',mean_uptime_s=900,mean_outage_s=600))
    criteria.update(comparison='attack_minus_no_attack',metric='forced_entitled_fraction',traffic_class='all')
    excess=select_one(pairs,**criteria)
    for suffix,key in [('', 'difference'),('Lo','lo'),('Hi','hi')]:
        add('CorrelatedExcess'+suffix,excess,key)
    gamma=scenario_row('threshold',Case(topology='parallel3',attack_budget=3,delta_e=.04,gamma=3.4,outage_model='none'))
    interval('ShapeForced',gamma,'forced_entitled_fraction')
    for name,topology,budget in [('Three','parallel3',3),('Four','parallel4',4)]:
        row=scenario_row('threshold',Case(topology=topology,attack_budget=budget,delta_e=.045,outage_model='none'))
        interval('Cut'+name+'Forced',row,'forced_entitled_fraction')
    persistence=pd.read_csv(ROOT/'results/revision/online_persistence/paired_contrasts.csv',float_precision='round_trip')
    for name,treatment,control in [
        ('OnlineRelease','release_on_unusable','no_attack'),
        ('OnlinePersistent','persistent_slots','no_attack'),
        ('OnlinePersistenceGain','persistent_slots','release_on_unusable')]:
        row=select_one(persistence,depth=6,budget=2,treatment=treatment,control=control,
                       **{'class':'all','metric':'forced_entitled_fraction'})
        for suffix,key in [('', 'mean'),('Lo','ci_low'),('Hi','ci_high')]:
            add(name+suffix,row,key)
    fallback=pd.read_csv(ROOT/'results/revision/fallback/analysis/summary.csv',float_precision='round_trip')
    for name,condition,digits in [
        ('FallbackOnline','generation_online_kem_control_down',2),
        ('FallbackPreplaced','generation_preplaced_symmetric_control_down',2),
        ('FallbackTransport','transport_online_kem_control_up',3)]:
        row=select_one(fallback,name=condition,traffic_class='all',metric='availability')
        for suffix,key in [('', 'mean'),('Lo','lo'),('Hi','hi')]:
            add(name+suffix,row,key,digits=digits)
    differences=pd.read_csv(ROOT/'results/revision/fallback/analysis/paired_comparisons.csv',float_precision='round_trip')
    for name,metric in [('FallbackServiceGain','availability'),('FallbackQualifiedGain','qualified_availability')]:
        row=select_one(differences,comparison='preplaced_minus_online_control_down',traffic_class='all',metric=metric)
        for suffix,key in [('', 'difference'),('Lo','lo'),('Hi','hi')]:
            add(name+suffix,row,key)
    macros=[]
    ledger={}
    for name,row,key,scale,digits in specifications:
        value=float(row[key])*scale
        rendered=f'{value:.{digits}f}'
        macros.append(f'\\newcommand{{\\{name}}}{{{rendered}}}')
        ledger[name]={'source_row':row.to_dict(),'field':key,'scale':scale,'display_value':rendered}
    (OUT/'remaining_numbers.tex').write_text('\n'.join(macros)+'\n',encoding='utf-8')
    (OUT/'remaining_claim_ledger.json').write_text(_ledger_json(ledger),encoding='utf-8')


def main():
    frame=pd.read_csv(DATA/'main_summary.csv')
    paired=pd.read_csv(DATA/'main_paired_comparisons.csv')
    def row(mode,cls='all',budget=2):
        rows=frame[(frame.topology=='formation')&(frame.fail_mode==mode)
                   &(frame.traffic_class==cls)&(frame.attack_budget==budget)]
        if len(rows)!=1:
            raise ValueError('Manuscript selection is not unique')
        return rows.iloc[0]
    closed,degraded=row('FAIL_CLOSED'),row('FAIL_DEGRADED')
    fields={
        'MainClosed':(closed,'availability'),
        'MainDegraded':(degraded,'availability'),
        'MainQualified':(degraded,'qualified_availability'),
        'MainForced':(degraded,'forced_entitled_fraction'),
        'MainForcedLo':(degraded,'forced_entitled_fraction_lo'),
        'MainForcedHi':(degraded,'forced_entitled_fraction_hi'),
        'MainPayloadLoss':(degraded,'degraded_payload_fraction'),
        'MainNoAttack':(row('FAIL_CLOSED',budget=0),'availability'),
    }
    values={name:100*float(r[field]) for name,(r,field) in fields.items()}
    evidence={name:{'case_id':r.case_id,'traffic_class':r.traffic_class,'metric':field,
                    'raw_value':float(r[field]),'display_value':f'{values[name]:.2f}'}
              for name,(r,field) in fields.items()}
    diff=paired[(paired.topology=='formation')&(paired.attack_budget==2)
                &(paired.traffic_class=='all')&(paired.comparison=='degraded_minus_closed')
                &(paired.metric=='qualified_availability')]
    if len(diff)!=1:
        raise ValueError('Paired estimate selection is not unique')
    for suffix,key in [('', 'difference'),('Lo','lo'),('Hi','hi')]:
        name='MainQualifiedDelta'+suffix
        values[name]=100*float(diff.iloc[0][key])
        evidence[name]={'paired_row':diff.iloc[0].to_dict(),'field':key,
                        'raw_value':float(diff.iloc[0][key]),'display_value':f'{values[name]:.2f}'}
    OUT.mkdir(exist_ok=True)
    (OUT/'main_numbers.tex').write_text('\n'.join(
        f'\\newcommand{{\\{name}}}{{{number:.2f}}}' for name,number in values.items())+'\n',encoding='utf-8')
    lines=[r'\begin{tabular}{@{}lccc@{}}',r'\toprule',
           r'Class & Closed $Q$ & Fallback $A$ & Fallback $Q$\\',r'\midrule']
    for cls in ('C2','ISR','LOG'):
        c,d=row('FAIL_CLOSED',cls),row('FAIL_DEGRADED',cls)
        cells=[]
        for r,key in [(c,'qualified_availability'),(d,'availability'),(d,'qualified_availability')]:
            mean,lo,hi=[100*float(r[k]) for k in [key,key+'_lo',key+'_hi']]
            cells.append(r'\shortstack{'+f'{mean:.2f}'+r'\\'+f'({lo:.2f}, {hi:.2f})'+'}')
        lines.append(cls+' & '+' & '.join(cells)+r'\\[3pt]')
    lines += [r'\bottomrule',r'\end{tabular}']
    (OUT/'class_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'main_claim_ledger.json').write_text(_ledger_json(evidence),encoding='utf-8')
    learning_path=ROOT/'results/revision/learning_analysis/paired_differences.csv'
    if learning_path.exists():
        learning=pd.read_csv(learning_path)
        estimates=pd.read_csv(ROOT/'results/revision/learning_analysis/estimates.csv')
        def learned_pair(metric,cls='all',regime='full_robust'):
            selected=learning[(learning.treatment==regime)&(learning.control=='budget_greedy')
                              &(learning.condition_count==7)&(learning['class']==cls)
                              &(learning.metric==metric)]
            if len(selected)!=1 or selected.iloc[0]['status']!='defined':
                raise ValueError('Invalid or ambiguous learning manuscript estimate')
            return selected.iloc[0]
        def learned_absolute(policy,metric):
            selected=estimates[(estimates.policy==policy)&(estimates.condition_count==7)
                               &(estimates['class']=='all')&(estimates.metric==metric)]
            if len(selected)!=1 or selected.iloc[0]['status']!='defined':
                raise ValueError('Invalid learning absolute estimate')
            return selected.iloc[0]
        entries=[]
        for stem,metric,cls,scale,digits in [
            ('LearnUtilityDelta','utility','all',1,4),
            ('LearnQualifiedDelta','qualified_availability','all',100,2),
            ('LearnPayloadDelta','forced_payload_fraction','all',100,2),
            ('LearnISRDelta','qualified_availability','ISR',100,2),
            ('LearnCommandDelta','qualified_availability','C2',100,2),
            ('LearnLogisticsDelta','qualified_availability','LOG',100,2)]:
            r=learned_pair(metric,cls)
            for suffix,key in [('', 'mean'),('Lo','ci_low'),('Hi','ci_high')]:
                entries.append((stem+suffix,r,key,scale,digits))
        for name,policy in [('LearnPayloadGreedy','budget_greedy'),('LearnPayloadMulti','full_robust')]:
            entries.append((name,learned_absolute(policy,'forced_payload_fraction'),'mean',100,2))
        entries.append(('LearnISRLoss',learned_pair('qualified_availability','ISR'),'mean',-100,2))
        for name,regime in [('LearnShortDelta','short_nominal'),('LearnLongDelta','full_nominal')]:
            entries.append((name,learned_pair('utility',regime=regime),'mean',1,4))
        macros=[]
        ledger={}
        for name,r,key,scale,digits in entries:
            value=float(r[key])*scale
            text=f'{value:.{digits}f}'
            macros.append(f'\\newcommand{{\\{name}}}{{{text}}}')
            ledger[name]={'source_row':r.to_dict(),'field':key,'scale':scale,'display_value':text}
        (OUT/'learning_numbers.tex').write_text('\n'.join(macros)+'\n',encoding='utf-8')
        (OUT/'learning_claim_ledger.json').write_text(_ledger_json(ledger),encoding='utf-8')
    print('Exported main manuscript macros, class table and numerical claim ledger')
    if (DATA/'sensitivity_canonical_raw_metrics.csv').exists():
        export_remaining_results()
        print('Exported verified stock, cost, correlation, threshold, persistence and fallback numbers')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
