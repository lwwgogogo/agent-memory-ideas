"""D1 grid diagnosis and D2 paired-prefix exploratory length diagnosis."""
import argparse
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from agent_memory.baselines import candidates,predict
from agent_memory.environment import generate
from agent_memory.online import model_average
from agent_memory.metrics import evaluate
from agent_memory.research_io import start_run,finish_run,write_csv,write_json,summarize,contrasts,recovery_fraction

METRICS=['accuracy','brier','false_update_rate','noise_overreaction','adaptation_delay_capped',
         'adaptation_censored_rate','stale_reuse_proxy']


def models(c):
    return {'online_bma':c['original_grid'], 'dense_bma':c['dense_grid'],
            'dense_prior_matched':c['dense_prior_matched']}


def d1(c,out):
    if set(c['validation_seeds']) & set(c['test_seeds']): raise ValueError('Seed leakage')
    cells=[(q,r) for q in c['q_values'] for r in c['r_values']]
    specs=candidates(); validation=[]; chosen={}
    for q,r in cells:
        score={s['name']:[] for s in specs}
        for seed in c['validation_seeds']:
            x,y=generate(q,r,c['steps'],seed)
            for s in specs:
                score[s['name']].append(float(np.mean((predict(y,s)[c['burn_in']:]>=.5)==x[c['burn_in']:])) )
        for m,v in score.items(): validation.append(dict(q=q,r=r,method=m,accuracy=float(np.mean(v))))
        chosen[q,r]=max(score,key=lambda m:np.mean(score[m]))
    global_best=max([s['name'] for s in specs],key=lambda m:np.mean([v['accuracy'] for v in validation if v['method']==m]))
    write_csv(out/'validation.csv',validation)
    write_json(out/'selection.json',dict(global_best=global_best,per_cell=[dict(q=q,r=r,method=m) for (q,r),m in chosen.items()]))
    rows=[]; diagnostics=[]
    for q,r in cells:
        for seed in c['test_seeds']:
            x,y=generate(q,r,c['steps'],seed)
            predictions={}
            for alias,name in [('selected_global',global_best),('selected_per_cell',chosen[q,r])]:
                predictions[alias]=predict(y,next(s for s in specs if s['name']==name))
            predictions['oracle_qr']=predict(y,dict(kind='bayes',q=q,r=r))
            for name,grid in models(c).items():
                predictions[name],diag=model_average(y,**grid)
                diagnostics.append(dict(q=q,r=r,seed=seed,method=name,**diag[-1]))
            for name,p in predictions.items():
                rows.append(dict(q=q,r=r,seed=seed,method=name,**evaluate(x,y,p,c['burn_in'])))
        print('D1 complete',q,r,flush=True)
    write_csv(out/'per_seed.csv',rows)
    write_csv(out/'posterior.csv',diagnostics)
    n=c['bootstrap_samples']
    write_csv(out/'summary.csv',summarize(rows,['q','r'],METRICS,n))
    write_csv(out/'overall.csv',summarize(rows,[],METRICS,n))
    write_csv(out/'contrasts.csv',contrasts(rows,['q','r'],METRICS,n))
    overall=contrasts(rows,[],METRICS,n)
    write_csv(out/'overall_contrasts.csv',overall)
    write_csv(out/'dense_improvement.csv',contrasts(rows,['q','r'],METRICS,n,reference='dense_bma'))
    improvement=contrasts(rows,[],METRICS,n,reference='dense_bma')
    fractions={m:recovery_fraction(rows,m,n) for m in models(c)}
    gap=next(r['mean'] for r in overall if r['method']=='dense_bma' and r['metric']=='accuracy')
    passed=fractions['dense_bma']['mean']>=.8 and gap<=.01
    result=dict(recovery_fraction=fractions,oracle_dense_gap=gap,
                stationary_mechanism_verdict='NO-GO' if passed else 'INCONCLUSIVE',
                stationary_threshold_met=bool(passed),dense_improvement=improvement)
    write_json(out/'decision.json',result)
    return result


def d2(c,out):
    rows=[]; windows=[]; posterior=[]
    ends=c['checkpoints']; longest=max(c['lengths'])
    for q,r in c['cells']:
        for seed in c['test_seeds']:
            # Original generator unchanged; one longest draw gives exact paired prefixes.
            x,y=generate(q,r,longest,seed)
            beliefs={'oracle_qr':predict(y,dict(kind='bayes',q=q,r=r))}
            diags={}
            for name,grid in models(c).items(): beliefs[name],diags[name]=model_average(y,**grid)
            for name,p in beliefs.items():
                for length in c['lengths']:
                    end_diag=diags[name][length-1] if name in diags else dict(q_mean=q,r_mean=r,effective_models=1)
                    rows.append(dict(q=q,r=r,seed=seed,method=name,length=length,
                                     **evaluate(x[:length],y[:length],p[:length],c['burn_in']),
                                     **{k:end_diag[k] for k in ['q_mean','r_mean','effective_models']}))
                start=c['burn_in']
                for end in ends:
                    windows.append(dict(q=q,r=r,seed=seed,method=name,start=start,end=end,
                                        **evaluate(x[:end],y[:end],p[:end],start)))
                    start=end
                for t in range(99,longest,100):
                    d=diags[name][t] if name in diags else dict(t=t,q_mean=q,r_mean=r,effective_models=1)
                    posterior.append(dict(q=q,r=r,seed=seed,method=name,step=t+1,**d))
        print('D2 complete',q,r,flush=True)
    n=c['bootstrap_samples']
    write_csv(out/'per_seed.csv',rows)
    write_csv(out/'windows.csv',windows)
    write_csv(out/'posterior.csv',posterior)
    write_csv(out/'summary.csv',summarize(rows,['q','r','length'],METRICS+['q_mean','r_mean','effective_models'],n))
    write_csv(out/'contrasts.csv',contrasts(rows,['q','r','length'],METRICS,n))
    write_csv(out/'window_summary.csv',summarize(windows,['q','r','start','end'],METRICS,n))
    write_csv(out/'window_contrasts.csv',contrasts(windows,['q','r','start','end'],METRICS,n))
    write_csv(out/'posterior_summary.csv',summarize(posterior,['q','r','step'],['q_mean','r_mean','effective_models'],n))
    return dict(exploratory=True,paired_prefix_length=longest)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['d1','d2'])
    parser.add_argument('--config',required=True)
    parser.add_argument('--output',required=True)
    a=parser.parse_args()
    c,out,meta,started=start_run(a.config,a.output)
    result=(d1 if a.phase=='d1' else d2)(c,out)
    finish_run(out,meta,started,result=result)
    print(result,flush=True)
