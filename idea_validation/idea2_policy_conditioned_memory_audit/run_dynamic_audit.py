#!/usr/bin/env python3
import json,statistics
from pathlib import Path
from adapters.jitrl_adapter import JitRLAdapter
from adapters.memrl_adapter import MemRLAdapter
from evaluate import psi,tv,preference,piur
ROOT=Path(__file__).resolve().parent
def dist(items):
 c={'A':0,'B':0}
 for x in items:
  a=x.get('action') or (x.get('steps') or [{}])[0].get('action')
  if a in c:c[a]+=1
 n=sum(c.values())
 return {k:v/n for k,v in c.items()} if n else {'A':0.0,'B':0.0}
def load_banks():
 d=ROOT/'results'/'synthetic_logs'
 return {n:[json.loads(l) for l in (d/f'D_{n}.jsonl').read_text().splitlines()] for n in ['P','Q','BAL']}
def run_one(factory,banks,name):
 condition={}
 for policy,rows in banks.items():
  a=factory();a.reset();a.ingest(rows)
  condition[policy]={'score':a.score_action('TARGET'),'retrieved':a.retrieve('TARGET',20)}
  # State matched queries are attempted through the same native query API.
  condition[policy]['state_queries']={s:dist(a.retrieve(s,20)) for s in ['S0','S1']}
  condition[policy]['retrieved_distribution']=dist(condition[policy]['retrieved'])
 p,q,b=(condition[x] for x in ['P','Q','BAL'])
 pscore,qscore,bscore=(p['score'],q['score'],b['score'])
 rcd=tv(p['retrieved_distribution'],q['retrieved_distribution'])
 denom=(abs(pscore['A']-pscore['B'])+abs(qscore['A']-qscore['B']))/2
 delta_bal=abs(bscore['A']-bscore['B'])
 return {'system':name,'audit_level':'L2','conditions':condition,
  'PSI':psi(pscore,qscore),'RCD':rcd,'PIUR':piur(pscore,qscore),
  'policy_delta_P':pscore['A']-pscore['B'],'policy_delta_Q':qscore['A']-qscore['B'],
  'balanced_reduction':None if denom==0 else 1-delta_bal/denom,
  'state_matched_effect':'UNSUPPORTED_BY_NATIVE_QUERY_API',
  'query_state_supported':False,
  'notes':'Native top-k ranker/value selector exercised over source-derived experience items; full end-to-end agent and embedding candidate generation not run.'}
def main():
 banks=load_banks();results=[]
 for factory,name in [(JitRLAdapter,'jitrl'),(MemRLAdapter,'memrl')]:
  try:results.append(run_one(factory,banks,name))
  except Exception as e:results.append({'system':name,'audit_level':'L0','dynamic_status':'DEPENDENCY_BLOCKED','error':type(e).__name__+': '+str(e)})
 out={'n_per_policy':{k:len(v) for k,v in banks.items()},'systems':results}
 p=ROOT/'results'/'dynamic'/'real_systems.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
