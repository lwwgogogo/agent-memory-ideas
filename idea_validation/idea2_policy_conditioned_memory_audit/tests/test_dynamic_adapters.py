import json
from pathlib import Path
from adapters.jitrl_adapter import JitRLAdapter
from adapters.memrl_adapter import MemRLAdapter
ROOT=Path(__file__).resolve().parents[1]
def banks():
 p=ROOT/'results'/'synthetic_logs'
 return {k:[json.loads(l) for l in (p/f'D_{k}.jsonl').read_text().splitlines()] for k in ['P','Q','BAL']}
def test_jitrl_native_ranker_and_policy_swap():
 d=banks();a=JitRLAdapter();a.reset();a.ingest(d['P']);x=a.retrieve(k=20)
 b=JitRLAdapter();b.reset();b.ingest(d['Q']);y=b.retrieve(k=20)
 assert len(x)==len(y)==20
 assert x[0]['final_score']>=x[-1]['final_score']
 assert a.score_action()['A']>a.score_action()['B']
 assert b.score_action()['A']<b.score_action()['B']
def test_memrl_native_q_update_and_topk():
 d=banks();a=MemRLAdapter();a.reset();a.ingest(d['P']);x=a.retrieve(k=20)
 b=MemRLAdapter();b.reset();b.ingest(d['Q']);y=b.retrieve(k=20)
 assert len(x)==len(y)==20
 assert a.score_action()['A']>a.score_action()['B']
 assert b.score_action()['A']<b.score_action()['B']
 assert all(z['metadata']['q_visits']==1 for z in x)
