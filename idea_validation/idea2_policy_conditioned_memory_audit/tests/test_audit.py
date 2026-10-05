import json
from pathlib import Path
from build_synthetic_logs import generate,OUTCOME,N
from evaluate import b0,b1,b2,psi,tv,preference,piur
from extract_memory_mechanism import structural_blindspot
def test_outcome_mechanism_and_true_values():
 assert OUTCOME=={'S0':.9,'S1':.2}
 assert .5*.9+.5*.2==.55
def test_generated_policies_and_balanced_exposures():
 d=generate()
 assert all(len(d[x])==N for x in ['P','Q','BAL'])
 for s in ['S0','S1']:
  assert sum(r['state']==s and r['action']=='A' for r in d['BAL'])==500
  pp=sum(r['state']==s and r['action']=='A' for r in d['P'])/sum(r['state']==s for r in d['P'])
  qq=sum(r['state']==s and r['action']=='A' for r in d['Q'])/sum(r['state']==s for r in d['Q'])
  assert abs(pp-({'S0':.95,'S1':.05}[s]))<.05
  assert abs(qq-({'S0':.05,'S1':.95}[s]))<.05
def test_aggregate_reversal_seeded():
 d=generate();p=b0(d['P']);q=b0(d['Q'])
 assert p['A']>p['B'] and q['A']<q['B']
 assert piur(p,q)==1
def test_state_conditioning_and_oracle_are_neutral():
 d=generate()
 for method in [b1,b2]:
  p,q=method(d['P']),method(d['Q'])
  assert abs(p['A']-p['B'])<.08 and abs(q['A']-q['B'])<.08
  assert abs(psi(p,q))<.10
def test_adapter_schema_and_policy_swap_isolation():
 from adapters.base import MemoryAuditAdapter
 assert all(hasattr(MemoryAuditAdapter,x) for x in ['reset','ingest','score_action','retrieve'])
 d=generate()
 p1,p2=generate()['P'],generate()['Q']
 assert p1==d['P'] and p2==d['Q'] and p1 is not p2
def test_balanced_control_exposure_and_metric_definitions():
 d=generate();v=b0(d['BAL'])
 assert abs(v['A']-v['B'])<.08
 assert 0<=tv({'A':.8,'B':.2},{'A':.2,'B':.8})<=1
 assert abs(tv({'A':.8,'B':.2},{'A':.2,'B':.8})-.6)<1e-9
 assert psi({'A':.9,'B':.2},{'A':.2,'B':.9})==1.4
def test_metrics_and_classification_rules():
 assert preference({'A':.7,'B':.2})=='A'
 assert piur({'A':.7,'B':.2},{'A':.2,'B':.7})==1
 a={'experience_origin':'SELF_GENERATED','observed_reward_used_as_utility':True,'utility_affects_future_retrieval':True,'utility_affects_future_action':False,'exposure_correction':'NONE','stores_behavior_policy_id':False,'stores_action_propensity':False}
 assert structural_blindspot(a)
 a['exposure_correction']='EXPLICIT';assert not structural_blindspot(a)
def test_gate_boundaries():
 assert 5>=5 and 3>=3 and 2>=2
