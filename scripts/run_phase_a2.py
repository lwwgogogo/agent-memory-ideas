"""Frozen nonstationary baseline evaluation; validation-only selection."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from agent_memory.baselines import candidates,predict
from agent_memory.online import model_average
from agent_memory.window import sliding_bma
from agent_memory.nonstationary import generate_scenario,oracle_filter,event_metrics
from agent_memory.metrics import evaluate
from agent_memory.research_io import start_run,finish_run,write_json,write_csv,summarize,contrasts

METRICS=['accuracy','brier','false_update_rate','noise_overreaction','adaptation_delay_capped',
         'adaptation_censored_rate','stale_reuse_proxy','error_50','error_100','error_300',
         'recovery_delay','recovery_censored','corruption_error','post_corruption_error_100',
         'post_corruption_error_remaining','post_corruption_recovery','post_corruption_censored',
         'useful_memory_retention_proxy']


def method_specs(c):
    specs=[dict(s,family='fixed') for s in candidates()]
    specs += [dict(name='online_bma',kind='bma',family='stationary',grid='original_grid'),
              dict(name='dense_bma',kind='bma',family='stationary',grid='dense_grid')]
    specs += [dict(name=f'forget_{rho}',kind='bma',family='forget',grid='dense_grid',forgetting=rho)
              for rho in c['forgetting_rates']]
    specs += [dict(name=f'window_bma_{w}',kind='window_bma',family='window',window=w)
              for w in c['window_sizes']]
    return specs


def belief(y,s,c):
    if s['kind']=='bma':
        return model_average(y,**c[s['grid']],forgetting=s.get('forgetting',1.))[0]
    if s['kind']=='window_bma':return sliding_bma(y,**c['dense_grid'],window=s['window'])
    return predict(y,s)


def worker(job):
    c,scenario,seed,specs,aliases,trace=job
    x,y,q,r,events=generate_scenario(scenario,c['steps'],seed,c['start_range'])
    rows=[];curves=[]
    ps={s['name']:belief(y,s,c) for s in specs}
    if trace:ps['oracle_qr']=oracle_filter(y,q,r)
    ps.update({alias:ps[name] for alias,name in aliases.items()})
    for name,p in ps.items():
        rows.append(dict(scenario=scenario['name'],category=scenario['kind'],seed=seed,method=name,
                         change=events['change'],corruption_end=events['corruption_end'],
                         **evaluate(x,y,p,c['burn_in']),**event_metrics(x,p,events)))
        if trace:
            # Align controls at a nominal 1200 solely for drawing; no model sees this.
            origin=events['change'] if events['change'] is not None else 1200
            for offset in range(-400,800,25):
                a=origin+offset;b=a+25
                curves.append(dict(scenario=scenario['name'],seed=seed,method=name,offset=offset,
                                   end_offset=offset+25,error=float(np.mean((p[a:b]>=.5)!=x[a:b])),
                                   brier=float(np.mean((p[a:b]-x[a:b])**2))))
    return rows,curves


def main(c,out):
    if set(c['validation_seeds']) & set(c['test_seeds']):raise ValueError('Seed leakage')
    specs=method_specs(c);validation=[]
    jobs=[(c,scenario,seed,specs,{},False) for scenario in c['scenarios'] for seed in c['validation_seeds']]
    with ProcessPoolExecutor(max_workers=c['workers']) as pool:
        for i,(rows,_) in enumerate(pool.map(worker,jobs)):
            validation.extend(rows)
            if (i+1)%20==0:print('validation',i+1,'/',len(jobs),flush=True)
    write_csv(out/'validation_per_seed.csv',validation)
    score={s['name']:float(np.mean([r['accuracy'] for r in validation if r['method']==s['name']])) for s in specs}
    selected={}
    for family,alias in [('fixed','selected_global'),('forget','selected_forgetting'),('window','selected_window')]:
        selected[alias]=max([s['name'] for s in specs if s['family']==family],key=lambda n:score[n])
    selected['selected_deployable']=max(score,key=score.get)
    # Freeze one global choice per family before any test simulation.
    write_json(out/'selection.json',dict(selected=selected,validation_accuracy=score,
                                       rule='equal scenario-weighted accuracy; deterministic candidate-order ties'))
    write_csv(out/'validation_summary.csv',summarize(validation,['scenario'],METRICS,c['bootstrap_samples']))
    names=set(selected.values())|{'online_bma','dense_bma'}
    test_specs=[s for s in specs if s['name'] in names]
    rows=[];curves=[]
    jobs=[(c,scenario,seed,test_specs,selected,True) for scenario in c['scenarios'] for seed in c['test_seeds']]
    with ProcessPoolExecutor(max_workers=c['workers']) as pool:
        for i,(batch,curve) in enumerate(pool.map(worker,jobs)):
            rows.extend(batch);curves.extend(curve)
            if (i+1)%40==0:print('test',i+1,'/',len(jobs),flush=True)
    write_csv(out/'per_seed.csv',rows);write_csv(out/'curves.csv',curves)
    n=c['bootstrap_samples']
    summary=summarize(rows,['scenario'],METRICS,n)
    comparisons=contrasts(rows,['scenario'],METRICS,n)
    write_csv(out/'summary.csv',summary);write_csv(out/'contrasts.csv',comparisons)
    write_csv(out/'curve_summary.csv',summarize(curves,['scenario','offset','end_offset'],['error','brier'],n))
    checks=[];eligible_categories=set()
    for scenario in c['scenarios']:
        name=scenario['name']
        lookup={r['metric']:r for r in comparisons if r['scenario']==name and r['method']=='selected_deployable'}
        if scenario['kind']!='control':
            meets=lookup['accuracy']['mean']>=.02 and all(lookup[f'error_{w}']['mean']<0 for w in [50,100,300])
            if meets:eligible_categories.add(scenario['kind'])
            checks.append(dict(scenario=name,category=scenario['kind'],gap=lookup['accuracy'],meets=bool(meets)))
    control_rows=[r for r in rows if r['category']=='control']
    declines=[]
    for reference in ['dense_bma','selected_global']:
        comp=contrasts(control_rows,['scenario'],['accuracy'],n,reference)
        declines.extend([r for r in comp if r['method']=='selected_deployable'])
    degradation=any(r['mean']>.01 and r['ci_low']>0 for r in declines)
    go=len(eligible_categories)>=2 and not degradation
    decision=dict(verdict='GO' if go else 'NO-GO',selected=selected,scenario_checks=checks,
                  eligible_categories=sorted(eligible_categories),control_degradation=bool(degradation),
                  control_comparisons=declines,thresholds=c['decision_rule'])
    write_json(out/'decision.json',decision)
    return decision


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    p.add_argument('--diagnostics-d1',required=True);p.add_argument('--diagnostics-d2',required=True)
    a=p.parse_args()
    import json,hashlib
    d1=json.loads((Path(a.diagnostics_d1)/'run.json').read_text())
    d2=json.loads((Path(a.diagnostics_d2)/'run.json').read_text())
    if d1['status']!='complete' or d2['status']!='complete' or not d1['result']['stationary_threshold_met']:
        raise SystemExit('Diagnostics gate not passed. Do not run A2.')
    c,out,meta,started=start_run(a.config,a.output)
    meta['prerequisites']={str(Path(v)/'run.json'):hashlib.sha256((Path(v)/'run.json').read_bytes()).hexdigest()
                           for v in [a.diagnostics_d1,a.diagnostics_d2]}
    decision=main(c,out)
    finish_run(out,meta,started,result=decision)
    print(decision,flush=True)
