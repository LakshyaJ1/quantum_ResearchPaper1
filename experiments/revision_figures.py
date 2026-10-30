"""Publication figures generated only from completed revision evidence."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.revision_analyze import load_phase,canonicalize_records
from revision.metrics import mean_interval
from revision.scenarios import Case

FIG=ROOT/'figures/revision'
ANALYSIS=ROOT/'results/revision/analysis'
BLUE,ORANGE,GREEN,PURPLE='#0072B2','#D55E00','#009E73','#8B4B9E'
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],
                     'font.size':8,'axes.labelsize':8,'axes.titlesize':8,
                     'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,
                     'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white',
                     'axes.spines.top':False,'axes.spines.right':False,
                     'axes.linewidth':.6,'lines.linewidth':1.3})


def save(fig,name,inputs):
    FIG.mkdir(parents=True,exist_ok=True)
    fig.savefig(FIG/f'{name}.pdf',bbox_inches='tight',pad_inches=.025)
    fig.savefig(FIG/f'{name}.png',dpi=300,bbox_inches='tight',pad_inches=.025)
    (FIG/f'{name}.provenance.json').write_text(json.dumps({
        'figure':name,'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in inputs}},indent=2),encoding='utf-8')
    plt.close(fig)
    print(f'Created figures/revision/{name}.pdf',flush=True)


def main_outcomes():
    verify=ANALYSIS/'main_verification.json'
    if not verify.exists():
        raise RuntimeError('Run main evidence analysis first')
    source=ANALYSIS/'main_summary.csv'
    data=pd.read_csv(source)
    data=data[(data.traffic_class=='all') & (data.attack_budget==data.cut_cost)]
    order=['formation','ring','grid','parallel3','parallel4']
    labels=['Formation','Ring','Grid','3 parallel paths','4 parallel paths']
    fig,axes=plt.subplots(1,2,figsize=(3.48,2.2),sharey=True)
    for mode,color,offset,label in [('FAIL_CLOSED',BLUE,-.13,'Fail closed'),
                                    ('FAIL_DEGRADED',ORANGE,.13,'Fail degraded')]:
        frame=data[data.fail_mode==mode].set_index('topology').loc[order]
        for ax,metric in zip(axes,['availability','qualified_availability']):
            values=frame[metric].to_numpy()*100
            lo=frame[f'{metric}_lo'].to_numpy()*100
            hi=frame[f'{metric}_hi'].to_numpy()*100
            ax.errorbar(values,np.arange(len(order))+offset,
                        xerr=np.vstack([values-lo,hi-values]),fmt='o',markersize=3,
                        capsize=2,color=color,label=label,elinewidth=.9)
    axes[0].set_yticks(range(5),labels)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0,103)
    axes[0].set_xticks([0,50,100])
    axes[1].set_xlim(0,15)
    axes[1].set_xticks([0,5,10,15])
    axes[0].set_title('(a) Timely service')
    axes[1].set_title('(b) Floor-compliant service')
    for ax in axes:
        ax.grid(axis='x',alpha=.2,linewidth=.5)
        ax.set_xlabel('Arriving requests (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=2,frameon=False,
               bbox_to_anchor=(.61,1.025),columnspacing=1.1)
    fig.subplots_adjust(left=.275,right=.99,bottom=.2,top=.80,wspace=.24)
    save(fig,'fig1_comparable_service',[source,verify])


def reserve_horizon():
    manifest,runs=load_phase('sensitivity')
    manifest,runs,_=canonicalize_records(manifest,runs)
    fig,axes=plt.subplots(1,2,figsize=(3.48,2.12),sharey=True)
    colors={.02:ORANGE,.1:BLUE,1.:GREEN}
    for ax,topology in zip(axes,('formation','parallel3')):
        for fill in (.02,.1,1.):
            expected=asdict(Case(topology=topology,attack_budget=2 if topology=='formation' else 3,
                                initial_spendable_fraction=fill))
            selected=[run for run in runs if run['case']==expected]
            if len(selected)!=len(manifest['seed_ids']):
                raise RuntimeError(f'Nonunique or incomplete reserve cells {topology}/{fill}: {len(selected)}')
            matrix=np.array([[h['forced_entitled_fraction'] for h in r['hourly']] for r in selected])
            stats=np.array([mean_interval(matrix[:,i]) for i in range(matrix.shape[1])])*100
            hours=np.arange(matrix.shape[1])+.5
            ax.plot(hours,stats[:,0],color=colors[fill],label=f'{fill*100:g}% usable stock',
                    linestyle='--' if fill==1 else '-')
            ax.fill_between(hours,stats[:,1],stats[:,2],color=colors[fill],alpha=.15,linewidth=0)
        ax.set_title('Formation' if topology=='formation' else '3 parallel paths')
        ax.set_xticks([0,6,12,18,24])
        ax.set_xlim(0,24)
        ax.set_ylim(-3,103)
        ax.set_xlabel('Hours since suppression')
        ax.grid(alpha=.18,linewidth=.5)
    axes[0].set_ylabel('Entitled requests downgraded (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=3,frameon=False,
               bbox_to_anchor=(.55,1.03),columnspacing=.6,handlelength=1.4)
    fig.subplots_adjust(left=.14,right=.99,bottom=.21,top=.77,wspace=.18)
    save(fig,'fig2_reserve_horizon',[ROOT/'results/revision/manifest_sensitivity.json'])


def learning_outcomes(conditions=False):
    source=ROOT/'results/revision/learning_analysis/paired_differences.csv'
    freeze=ROOT/'results/revision/learning_policy_freeze.json'
    frame=pd.read_csv(source)
    frame=frame[(frame.control=='budget_greedy')&(frame['class']=='all')]
    regimes=['short_nominal','full_nominal','full_robust']
    if conditions:
        order=['nominal','attack2','overload_isr1','rate_half','correlated_weather',
               'unseen_ring','unseen_parallel3_attack3']
        labels=['Nominal','Generation cut','ISR overload','Half key rate',
                'Correlated outages','Unseen ring','Unseen 3-path cut']
        fig,ax=plt.subplots(figsize=(3.48,2.9))
        for regime,color,offset,label in zip(regimes,[BLUE,PURPLE,GREEN],[-.19,0,.19],
                                            ['6h nominal','24h nominal','24h multi-condition']):
            group=frame[(frame.treatment==regime)&(frame.metric=='utility')].set_index('condition').loc[order]
            v,lo,hi=[group[k].to_numpy()*1000 for k in ['mean','ci_low','ci_high']]
            ax.errorbar(v,np.arange(7)+offset,xerr=np.vstack([v-lo,hi-v]),fmt='o',
                        markersize=2.7,capsize=1.8,color=color,label=label,elinewidth=.8)
        ax.set_yticks(range(7),labels)
        ax.invert_yaxis()
        ax.axvline(0,color='.45',linestyle='--',linewidth=.7)
        ax.set_xlabel(r'Change in utility $J$ ($\times10^{-3}$)')
        ax.grid(axis='x',alpha=.15)
        ax.legend(frameon=False,loc='lower left',bbox_to_anchor=(-.55,1.01),ncol=1)
        fig.subplots_adjust(left=.34,right=.98,bottom=.17,top=.74)
        save(fig,'supp_learning_conditions',[source,freeze])
        return
    frame=frame[frame.condition=='fixed_seven_condition_average']
    fig,axes=plt.subplots(1,2,figsize=(3.48,1.85),sharey=True)
    for ax,metric,scale,color in zip(axes,['utility','forced_payload_fraction'],[1000,100],[BLUE,ORANGE]):
        group=frame[frame.metric==metric].set_index('treatment').loc[regimes]
        v,lo,hi=[group[k].to_numpy()*scale for k in ['mean','ci_low','ci_high']]
        ax.errorbar(v,np.arange(3),xerr=np.vstack([v-lo,hi-v]),fmt='o',markersize=3.2,
                    capsize=2.5,color=color,elinewidth=1)
        ax.axvline(0,color='.45',linestyle='--',linewidth=.7)
        ax.grid(axis='x',alpha=.15)
    axes[0].set_yticks(range(3),['6h nominal','24h nominal','24h multi-condition'])
    axes[0].invert_yaxis()
    axes[0].set_xlim(-6.5,3)
    axes[0].set_xticks([-6,-3,0,3])
    axes[1].set_xlim(-2.5,2.5)
    axes[1].set_xticks([-2,0,2])
    axes[0].set_title('(a) Utility')
    axes[1].set_title('(b) Below-ITS payload')
    axes[0].set_xlabel(r'$\Delta J$ ($\times10^{-3}$)')
    axes[1].set_xlabel(r'$\Delta F_B$ (percentage points)')
    fig.subplots_adjust(left=.31,right=.99,bottom=.29,top=.82,wspace=.24)
    save(fig,'fig3_learning_tradeoff',[source,freeze])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--figure',choices=['main','reserve','learning','learning-conditions'],default='main')
    args=parser.parse_args()
    if args.figure=='main':
        main_outcomes()
    elif args.figure=='reserve':
        reserve_horizon()
    else:
        learning_outcomes(conditions=args.figure=='learning-conditions')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
