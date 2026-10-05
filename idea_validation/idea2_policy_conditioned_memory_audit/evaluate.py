#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def mean(xs):return statistics.mean(xs) if xs else None
def psi(p,q):return abs(p['A']-q['A'])+abs(p['B']-q['B'])
def tv(p,q):return 0.5*sum(abs(p.get(k,0)-q.get(k,0)) for k in set(p)|set(q))
def preference(scores,eps=.01):
 if scores is None:return None
 d=scores['A']-scores['B']
 return 'A' if d>eps else ('B' if d< -eps else 'TIE')
def piur(p,q,eps=.01):
 a,b=preference(p,eps),preference(q,eps)
 return int(a in {'A','B'} and b in {'A','B'} and a!=b)
def score_tables(rows):
 out={}
 for a in ['A','B']:
  c=[r for r in rows if r['action']==a];out[a]=sum(r['outcome'] for r in c)/len(c)
 return out
def state_scores(rows,s):
 out={}
 for a in ['A','B']:
  c=[r for r in rows if r['state']==s and r['action']==a];out[a]=sum(r['outcome'] for r in c)/len(c)
 return out
def b0(rows):return score_tables(rows)
def b1(rows):return {a:0.5*state_scores(rows,'S0')[a]+0.5*state_scores(rows,'S1')[a] for a in ['A','B']}
def b2(rows):
 # Propensity-weighted direct standardization: normalize inverse action-propensity
 # weights within each state, then average the state estimates under target P(X).
 out={}
 for a in ['A','B']:
  state_est=[]
  for state in ['S0','S1']:
   cell=[r for r in rows if r['state']==state and r['action']==a]
   weights=[1/r['action_propensity'] for r in cell]
   state_est.append(sum(w*r['outcome'] for w,r in zip(weights,cell))/sum(weights))
  out[a]=0.5*sum(state_est)
 return out
def summarize():
 dest=ROOT/'results'/'synthetic_logs';out={}
 for name in ['P','Q','BAL']:
  rows=[json.loads(l) for l in (dest/f'D_{name}.jsonl').read_text().splitlines()]
  out[name]={m:f(rows) for m,f in [('B0',b0),('B1',b1),('B2',b2)]}
 for m in ['B0','B1','B2']:
  p,q,b=(out[z][m] for z in ['P','Q','BAL'])
  delta=lambda x:x['A']-x['B']
  out.setdefault('metrics',{})[m]={
   'PSI':psi(p,q),'PIUR':piur(p,q),
   'policy_delta_P':delta(p),'policy_delta_Q':delta(q),'policy_induced_delta_gap':abs(delta(p)-delta(q)),
   'balanced_reduction':None if (abs(delta(p))+abs(delta(q)))==0 else 1-abs(delta(b))/((abs(delta(p))+abs(delta(q)))/2),
   'state_matched_delta_gap':{s:abs((state_scores([json.loads(l) for l in (dest/'D_P.jsonl').read_text().splitlines()],s)['A']-state_scores([json.loads(l) for l in (dest/'D_P.jsonl').read_text().splitlines()],s)['B'])-(state_scores([json.loads(l) for l in (dest/'D_Q.jsonl').read_text().splitlines()],s)['A']-state_scores([json.loads(l) for l in (dest/'D_Q.jsonl').read_text().splitlines()],s)['B'])) for s in ['S0','S1']}
  }
 (ROOT/'results'/'dynamic'/'synthetic_baselines.json').write_text(json.dumps(out,indent=2)+'\n')
 return out
def main():
 z=summarize();print(json.dumps(z.get('metrics'),indent=2))
if __name__=='__main__':main()
