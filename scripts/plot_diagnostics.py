"""D1/D2 publication-style PNGs from underlying CSV; never reruns inference."""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read(path):
    with path.open(encoding='utf-8') as f: return list(csv.DictReader(f))


def d1(root):
    data=read(root/'summary.csv'); gaps=read(root/'contrasts.csv')
    qs=sorted({float(r['q']) for r in data}); rs=sorted({float(r['r']) for r in data})
    for name,records,methods in [('accuracy_heatmap',data,['online_bma','dense_bma','oracle_qr']),
                                  ('gap_heatmap',gaps,['online_bma','dense_bma','dense_prior_matched'])]:
        arrays=[]
        for method in methods:
            lookup={(float(r['q']),float(r['r'])):float(r['mean']) for r in records if r['method']==method and r['metric']=='accuracy'}
            arrays.append(np.array([[lookup[q,r] for r in rs] for q in qs]))
        is_gap='gap' in name
        fig,axes=plt.subplots(1,3,figsize=(14,4),constrained_layout=True)
        lim=max(abs(a).max() for a in arrays) if is_gap else 1
        for ax,m,a in zip(axes,methods,arrays):
            im=ax.imshow(a*100,origin='lower',aspect='auto',cmap='RdBu' if is_gap else 'viridis',
                         vmin=-lim*100 if is_gap else 50,vmax=lim*100)
            ax.set(title=m,xlabel='R (flip probability)',ylabel='Q (change probability)')
            ax.set_xticks(range(len(rs)),[str(v) for v in rs]); ax.set_yticks(range(len(qs)),[str(v) for v in qs])
        fig.colorbar(im,ax=axes,label='Oracle minus method (pp)' if is_gap else 'Accuracy (%)')
        fig.suptitle('D1: held-out seed mean, T=2000; source: '+('contrasts.csv' if is_gap else 'summary.csv'))
        fig.savefig(root/'figures'/f'{name}.png',dpi=160); plt.close(fig)


def d2(root):
    data=read(root/'contrasts.csv'); post=read(root/'posterior_summary.csv')
    fig,axes=plt.subplots(1,2,figsize=(12,4),constrained_layout=True)
    for ax,q in zip(axes,[.001,.01]):
        for m in ['online_bma','dense_bma','dense_prior_matched']:
            rows=sorted([r for r in data if float(r['q'])==q and r['method']==m and r['metric']=='accuracy'],key=lambda r:int(r['length']))
            x=[int(r['length']) for r in rows]; y=np.array([float(r['mean'])*100 for r in rows])
            ax.plot(x,y,'o-',label=m)
            ax.fill_between(x,[float(r['ci_low'])*100 for r in rows],[float(r['ci_high'])*100 for r in rows],alpha=.15)
        ax.set(title=f'Q={q}, R=0.45',xlabel='Sequence length (observations)',ylabel='Oracle accuracy minus method (pp)')
        ax.legend(fontsize=8)
    fig.suptitle('D2 exploratory: paired-prefix trajectories, 95% seed bootstrap; contrasts.csv')
    fig.savefig(root/'figures'/'gap_vs_length.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
    for i,q in enumerate([.001,.01]):
        for j,metric in enumerate(['q_mean','r_mean']):
            ax=axes[i,j]
            for m in ['online_bma','dense_bma','dense_prior_matched']:
                rows=sorted([r for r in post if float(r['q'])==q and r['method']==m and r['metric']==metric],key=lambda r:int(r['step']))
                ax.plot([int(r['step']) for r in rows],[float(r['mean']) for r in rows],label=m)
            ax.axhline(q if metric=='q_mean' else .45,color='black',linestyle='--',label='true parameter')
            ax.set(title=f'{metric}, true Q={q}, R=.45',xlabel='Observed steps',ylabel='Posterior mean probability')
            ax.legend(fontsize=8)
    fig.suptitle('D2 exploratory: seed-mean parameter estimates; posterior_summary.csv')
    fig.savefig(root/'figures'/'posterior_convergence.png',dpi=160);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['d1','d2']);p.add_argument('directory')
    a=p.parse_args();root=Path(a.directory);(root/'figures').mkdir(exist_ok=False)
    (d1 if a.phase=='d1' else d2)(root)
