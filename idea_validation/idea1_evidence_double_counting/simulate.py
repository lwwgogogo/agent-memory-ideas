import csv,json,math,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=pathlib.Path(__file__).resolve().parent
rows=[]
for lam in [1.5,2,3,5]:
 for k in range(1,21):
  posterior=1/(1+math.exp(-k*math.log(lam)))
  oracle=lam/(1+lam)
  rows.append(dict(lambda_=lam,k=k,independent_posterior=posterior,derived_oracle_posterior=oracle,naive_derived_posterior=posterior,confidence_inflation=posterior-oracle,effective_evidence_ratio=k))
for r in rows:r['lambda']=r.pop('lambda_')
with (P/'results/simulation.csv').open('w') as f:
 w=csv.DictWriter(f,lineterminator='\n',fieldnames=['lambda','k','independent_posterior','derived_oracle_posterior','naive_derived_posterior','confidence_inflation','effective_evidence_ratio']);w.writeheader();w.writerows(rows)
checks=[]
for lam in [1.5,2,3,5]:
 rr=[r for r in rows if r['lambda']==lam]
 checks.extend([abs(rr[0]['confidence_inflation'])<1e-12,all(b['confidence_inflation']>a['confidence_inflation'] for a,b in zip(rr,rr[1:])),all(abs(r['naive_derived_posterior']-lam**r['k']/(1+lam**r['k']))<1e-12 for r in rr),all(abs(r['derived_oracle_posterior']-lam/(1+lam))<1e-12 for r in rr)])
for k in range(1,21):
 pp=[r['naive_derived_posterior'] for r in rows if r['k']==k];checks.append(all(b>a for a,b in zip(pp,pp[1:])))
for field,name,ylabel in [('naive_derived_posterior','posterior_vs_k','Posterior P(H=1)'),('confidence_inflation','inflation_vs_k','Naive minus oracle'),('effective_evidence_ratio','effective_evidence_ratio','Assumed / true evidence count')]:
 plt.figure(figsize=(8,5))
 for lam in [1.5,2,3,5]:
  rr=[r for r in rows if r['lambda']==lam]
  line,=plt.plot([r['k'] for r in rr],[r[field] for r in rr],label=('Independent = naive, LR = ' if name=='posterior_vs_k' else 'LR = ')+str(lam))
  if name=='posterior_vs_k':plt.plot([r['k'] for r in rr],[r['derived_oracle_posterior'] for r in rr],linestyle='--',color=line.get_color(),alpha=.7,label='Oracle, LR = '+str(lam))
 plt.xlabel('Memory count k');plt.ylabel(ylabel);plt.legend();plt.grid(alpha=.2);plt.tight_layout();plt.savefig(P/('plots/'+name+'.png'),dpi=180);plt.close()
gate='PHASE_A_GO' if all(checks) else 'IDEA1_MATH_NO_GO'
(P/'results/math_gate.json').write_text(json.dumps({'gate':gate,'checks':len(checks),'all_passed':all(checks)},indent=2))
print(gate)
