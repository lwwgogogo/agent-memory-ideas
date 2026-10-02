"""Frozen A2 plots with CSV provenance and paired-seed intervals."""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read(p):
    with p.open(encoding='utf-8') as f:return list(csv.DictReader(f))


def main(root):
    figdir=root/'figures';figdir.mkdir(exist_ok=False)
    curves=read(root/'curve_summary.csv');summary=read(root/'summary.csv');gaps=read(root/'contrasts.csv')
    methods=['selected_global','online_bma','dense_bma','selected_forgetting','selected_window','oracle_qr']
    for filename,scenarios in [('q_change',['q_increase','q_decrease']),('r_change',['r_increase','r_decrease']),
                               ('temporary_corruption',['temporary_corruption'])]:
        fig,axes=plt.subplots(1,len(scenarios),figsize=(7*len(scenarios),4.5),constrained_layout=True,squeeze=False)
        for ax,scenario in zip(axes[0],scenarios):
            for m in methods:
                rows=sorted([r for r in curves if r['scenario']==scenario and r['method']==m and r['metric']=='error'],key=lambda r:int(r['offset']))
                ax.plot([int(r['offset'])+12.5 for r in rows],[float(r['mean'])*100 for r in rows],label=m,linewidth=1.3)
            ax.axvline(0,color='black',linestyle='--',linewidth=1)
            if scenario=='temporary_corruption':ax.axvspan(0,100,color='grey',alpha=.12,label='corruption')
            ax.set(title=scenario,xlabel='Steps relative to parameter change',ylabel='25-step mean tracking error (%)')
            ax.legend(fontsize=7,ncol=2)
        fig.suptitle('A2 held-out seed mean; curve_summary.csv (CIs available in CSV)')
        fig.savefig(figdir/f'{filename}.png',dpi=160);plt.close(fig)
    scenarios=['q_increase','q_decrease','r_increase','r_decrease','temporary_corruption']
    plotted=['online_bma','selected_forgetting','selected_window','selected_deployable','oracle_qr']
    fig,ax=plt.subplots(figsize=(12,5),constrained_layout=True)
    for i,m in enumerate(plotted):
        rows=[next(r for r in summary if r['scenario']==s and r['method']==m and r['metric']=='recovery_delay') for s in scenarios]
        a=np.array([float(r['mean']) for r in rows]);lo=np.array([float(r['ci_low']) for r in rows]);hi=np.array([float(r['ci_high']) for r in rows])
        ax.errorbar(np.arange(5)+(i-2)*.12,a,yerr=[a-lo,hi-a],fmt='o',capsize=2,label=m)
    ax.set_xticks(range(5),scenarios,rotation=15)
    ax.set(ylabel='Steps to completed 10-correct streak (capped)',xlabel='Scenario',title='A2 recovery delay; 95% seed bootstrap; summary.csv')
    ax.legend(fontsize=8)
    fig.savefig(figdir/'recovery_delay.png',dpi=160);plt.close(fig)
    scenarios+=['control_low_q','control_high_q','control_clean','control_noisy']
    fig,ax=plt.subplots(figsize=(12,5),constrained_layout=True)
    for i,m in enumerate(['online_bma','dense_bma','selected_forgetting','selected_window','selected_deployable']):
        rows=[next(r for r in gaps if r['scenario']==s and r['method']==m and r['metric']=='accuracy') for s in scenarios]
        a=np.array([float(r['mean'])*100 for r in rows]);lo=np.array([float(r['ci_low'])*100 for r in rows]);hi=np.array([float(r['ci_high'])*100 for r in rows])
        ax.errorbar(np.arange(len(scenarios))+(i-2)*.12,a,yerr=[a-lo,hi-a],fmt='o',capsize=2,label=m)
    ax.axhline(2,color='black',linestyle='--',label='2 pp research threshold')
    ax.set_xticks(range(len(scenarios)),scenarios,rotation=25,ha='right')
    ax.set(ylabel='Oracle minus method accuracy (pp)',xlabel='Scenario',title='A2 Oracle gap; paired seed 95% CI; contrasts.csv')
    ax.legend(fontsize=7,ncol=3)
    fig.savefig(figdir/'oracle_gap_by_scenario.png',dpi=160);plt.close(fig)
    # Validation-only forgetting trade-off; never select from test.
    data=read(root/'validation_summary.csv')
    fig,ax=plt.subplots(figsize=(10,5),constrained_layout=True)
    for scenario in scenarios:
        rows=[r for r in data if r['scenario']==scenario and r['method'].startswith('forget_') and r['metric']=='accuracy']
        rows.sort(key=lambda r:float(r['method'].split('_')[1]))
        ax.plot([1/(1-float(r['method'].split('_')[1])) for r in rows],[float(r['mean'])*100 for r in rows],'o-',label=scenario)
    ax.set(xscale='log',xlabel='1 / (1 - rho), nominal weight horizon (steps)',ylabel='Validation accuracy (%)',
           title='Forgetting-rate trade-off; validation_summary.csv only')
    ax.legend(fontsize=7,ncol=2)
    fig.savefig(figdir/'validation_forgetting_tradeoff.png',dpi=160);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();main(Path(a.directory))
