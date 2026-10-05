#!/usr/bin/env python3
"""Generate fixed-seed selected experiences for P/Q and equal-exposure BAL."""
from __future__ import annotations
import json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SEED=20261005;N=2000
OUTCOME={'S0':0.9,'S1':0.2}
def generate():
 rng=random.Random(SEED);out={}
 for policy in ['P','Q']:
  rows=[]
  for i in range(N):
   s='S0' if rng.random()<0.5 else 'S1'
   pa={'P':{'S0':0.95,'S1':0.05},'Q':{'S0':0.05,'S1':0.95}}[policy][s]
   a='A' if rng.random()<pa else 'B'
   y=int(rng.random()<OUTCOME[s])
   rows.append({'episode_id':f'{policy}-{i:04d}','policy_id':policy,'state':s,'action':a,'outcome':y,'reward':y,'action_propensity':pa if a=='A' else 1-pa,'state_probability':0.5})
  out[policy]=rows
 rows=[]
 cells=[(s,a) for s in ['S0','S1'] for a in ['A','B']]
 for s,a in cells:
  for j in range(N//4):
   y=int(rng.random()<OUTCOME[s]);rows.append({'episode_id':f'BAL-{s}-{a}-{j:03d}','policy_id':'BAL','state':s,'action':a,'outcome':y,'reward':y,'action_propensity':0.5,'state_probability':0.5})
 rng.shuffle(rows)
 for i,r in enumerate(rows):r['episode_id']=f'BAL-{i:04d}'
 out['BAL']=rows
 return out
def values(rows):
 ans={}
 for s in ['S0','S1']:
  for a in ['A','B']:
   c=[r for r in rows if r['state']==s and r['action']==a]
   ans[f'{s}:{a}']={'n':len(c),'successes':sum(r['outcome'] for r in c),'rate':sum(r['outcome'] for r in c)/len(c)}
 return ans
def main():
 banks=generate();dest=ROOT/'results'/'synthetic_logs';dest.mkdir(parents=True,exist_ok=True)
 for name,rows in banks.items():
  with (dest/f'D_{name}.jsonl').open('w') as f:
   for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
 meta={'seed':SEED,'n_per_bank':N,'outcome_model':OUTCOME,'target_state_distribution':{'S0':0.5,'S1':0.5},
 'true_target_values':{'A':0.55,'B':0.55},'cells':{k:values(v) for k,v in banks.items()}}
 (dest/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
