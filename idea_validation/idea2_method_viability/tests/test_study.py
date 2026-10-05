from fractions import Fraction as F
from dataclasses import fields
import inspect,statistics
import pytest
from build_worlds import generate,cells,true_mu,truth,worlds,RATES,TARGETS
from schema import Observation
from methods import m1,m2,m4,oracle,estimate,empirical_propensity
from metrics import pig,npe,tge,tsr,correction,rank,reversal,crossover,null_gate,signal_gate
from evaluate import verdict,no_leakage
from native_baselines import create_bank,select,support,native
from adapters import jitrl,memrl
from adapters.corrected_selector import CorrectedMemorySelector,apportion
def observed(rows):
 return [Observation(r['id'],r['state'],r['action'],r['outcome'],F(r['outcome'])) for r in rows]
def test_exact_truths():
 assert truth('A','T')=={'A':F(11,20),'B':F(11,20)}
 assert truth('B','T')=={'A':F(3,5),'B':F(1,2)}
 assert truth('C','T')=={'A':F(11,20),'B':F(11,20)}
 assert truth('C','T0')=={'A':F(19,25),'B':F(29,50)}
 assert truth('C','T1')=={'A':F(17,50),'B':F(13,25)}
@pytest.mark.parametrize('w',list(worlds()),ids=lambda w:w['id'])
def test_exposure_only_and_integer_cells(w):
 rows=generate(w['mechanism'],w['gamma'],w['policy']);c=cells(rows);mu=true_mu(w['gamma'],w['policy'])
 assert len(rows)==2000 and len({r['id'] for r in rows})==2000
 assert set(rows[0])=={'id','state','action','outcome'}
 for s in c:
  assert sum(c[s][a]['n'] for a in c[s])==1000
  for a in c[s]:
   assert c[s][a]['n']==1000*mu[s][a]
   assert F(c[s][a]['success'],c[s][a]['n'])==RATES[w['mechanism']][s][a]
@pytest.mark.parametrize('g',['0.50','0.70','0.85','0.95','0.99'])
def test_pq_exposure_reversal(g):
 p,q=[cells(generate('B',g,pol)) for pol in ('P','Q')]
 for s in p:
  assert p[s]['A']['n']==q[s]['B']['n']
  assert p[s]['B']['n']==q[s]['A']['n']
def test_m1_formula():
 rows=observed(generate('C','0.95','Q'))
 assert m1(rows,TARGETS['T0'])=={'A':F(19,25),'B':F(29,50)}
 assert m1(rows,TARGETS['T1'])=={'A':F(17,50),'B':F(13,25)}
def test_m2_exact_empirical_formula_and_clip():
 rows=observed(generate('A','0.99','P'));mu=empirical_propensity(rows)
 assert mu['S0']['A']==F(991,1002)
 assert mu['S1']['A']==F(11,1002)
 wa=1/mu['S0']['A'];wb=F(20)
 expected_A=(891*wa+2*wb)/(990*wa+10*wb)
 assert m2(rows,TARGETS['T'])['A']==expected_A
 assert m2(rows,TARGETS['T0'])==m2(rows,TARGETS['T1'])
def test_oracle_target_aware_snips():
 rows=observed(generate('C','0.95','Q'))
 assert oracle(rows,TARGETS['T0'],true_mu('0.95','Q'),TARGETS['T'])==truth('C','T0')
 assert oracle(rows,TARGETS['T1'],true_mu('0.95','Q'),TARGETS['T'])==truth('C','T1')
def test_jeffreys_shrinkage():
 rows=observed(generate('A','0.95','P'))
 assert m4(rows,TARGETS['T'])['A']==F(1,2)*(F(855*2+1,2*951)+F(10*2+1,2*51))
def test_missing_support_is_not_fabricated():
 rows=[Observation('a','S0','A',1,F(1))]
 with pytest.raises(ValueError):m1(rows,TARGETS['T'])
 assert m4(rows,TARGETS['T'])['B']==F(1,2)
def test_no_oracle_leakage_api():
 assert no_leakage()
 assert {f.name for f in fields(Observation)}=={'id','state','action','outcome','native_utility'}
 for fn in [m1,m2,m4]:assert tuple(inspect.signature(fn).parameters)==('items','rho')
 rows=observed(generate('B','0.70','P'))
 with pytest.raises(KeyError):estimate('M3',rows,TARGETS['T'])
 with pytest.raises(TypeError):m1(rows,TARGETS['T'],gamma=.7)
 with pytest.raises((AttributeError,TypeError)):setattr(rows[0],'gamma',.7)
def test_metrics_exact():
 p={'A':F(7,10),'B':F(3,10)};q={'A':F(3,10),'B':F(7,10)}
 assert pig(p,q)==F(4,5) and npe(p)==F(2,5)
 assert tge(p,F(1,10))==F(3,10)
 assert tsr(p)==4 and tsr(q) is None
 assert correction(F(1,10),F(1,2))==F(4,5)
 assert correction(F(0),F(0)) is None
 assert reversal(p,q) and not reversal(p,p)
 assert crossover(p,q) and not crossover(q,p)
 assert rank({'A':F(1,2),'B':F(1,2)})=='TIE'
def test_gate_boundaries():
 assert null_gate(F(4,5),F(3,100),F(3,100))
 assert not null_gate(F(799,1000),F(0),F(0))
 assert not null_gate(F(1),F(31,1000),F(0))
 assert signal_gate(['A']*6,[F(7,10)]*6)
 assert signal_gate(['A']*6,[F(13,10)]*6)
 assert not signal_gate(['A']*6,[F(131,100)]*6)
 assert not signal_gate(['A']*5+['B'],[F(1)]*6)
 assert not signal_gate(['A']*6,[None]*6)
def test_verdict_boundaries():
 g={f'G{i}':True for i in range(10)};p={'M1':{f'G{i}':True for i in range(1,10)}}
 assert verdict(g,p)=='METHOD_VIABILITY_GO'
 g['G9']=False
 assert verdict(g,p)=='METHOD_VIABILITY_WEAK'
 g['G0']=False
 assert verdict(g,p)=='METHOD_VIABILITY_NO_GO'
def small_rows():
 return [{'id':f'{s}-{a}','state':s,'action':a,'outcome':int(s=='S0')} for s in ('S0','S1') for a in ('A','B')]
def test_native_adapter_mapping_and_real_calls():
 rows=small_rows()
 j,m=[create_bank(s,rows) for s in ('jitrl','memrl')]
 oj,om=jitrl.observations(j),memrl.observations(m)
 assert [(x.id,x.state,x.action,x.outcome) for x in oj]==[(x.id,x.state,x.action,x.outcome) for x in om]
 assert oj[0].native_utility==1 and om[0].native_utility==F(1,10)
 assert native('jitrl').get_top_episodes.__code__.co_firstlineno==22
 for s,bank in [('jitrl',j),('memrl',m)]:
  ret=select(s,bank,20261005,k=2)
  assert len(ret)==2 and support(s,ret)=={'A':F(1,2),'B':F(1,2)}
@pytest.mark.parametrize('system',['jitrl','memrl'])
@pytest.mark.parametrize('method',['M1','M4'])
def test_secondary_wrapper_support(system,method):
 bank=create_bank(system,generate('C','0.99','P'))
 wrapper=CorrectedMemorySelector(system,method).fit(bank)
 for t in ['T','T0','T1']:
  selected=wrapper.select(bank,20,TARGETS[t])
  parsed=wrapper.reader.observations(selected)
  assert len({r.id for r in parsed})==20
  for s in ('S0','S1'):
   assert sum(r.state==s for r in parsed)==20*TARGETS[t][s]
   for a in ('A','B'):assert sum(r.state==s and r.action==a for r in parsed)>=2
 assert wrapper.estimate_action_utility(TARGETS['T0'])['A']>wrapper.estimate_action_utility(TARGETS['T0'])['B']
 assert wrapper.estimate_action_utility(TARGETS['T1'])['A']<wrapper.estimate_action_utility(TARGETS['T1'])['B']
def test_fixed_apportionment():
 assert apportion(20,TARGETS['T0'])=={'S0':16,'S1':4}
 assert apportion(6,{'A':1,'B':1})=={'A':3,'B':3}
