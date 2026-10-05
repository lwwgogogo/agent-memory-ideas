import json,collections,copy
import pytest
from core import canonical,parse,run_with_retry,paired_average,LEVELS,CONDITIONS,ORDERED
from generate_cases import build_cases,world_counts,evidence,prompt
from evaluate import assess_gates

@pytest.mark.parametrize('version,left,right,expected',[('AB',.8,.2,(.8,.2)),('BA',.2,.8,(.8,.2)),('AB',.5,.5,(.5,.5)),('BA',0,1,(1,0))])
def test_canonical_mapping(version,left,right,expected):assert canonical({'p_success_left':left,'p_success_right':right},version)==expected

def test_label_swap_all_counts_and_words():
    for case in build_cases():
        for condition in CONDITIONS:
            ab=evidence(case,condition,'AB');ba=evidence(case,condition,'BA')
            assert [s.replace('Left','TEMP').replace('Right','Left').replace('TEMP','Right') for s in ab]==ba

def test_assignment_and_run_counts():
    cases=build_cases();assert len(cases)==20
    assert collections.Counter(c['gamma'] for c in cases)=={g:5 for g in LEVELS}
    assert collections.Counter(r['condition'] for c in cases for r in c['runs'])=={'NoMemory':40,'AggregateSummary':40,'ConfoundedMemory':80,'BalancedMemory':80,'StratifiedOracle':80}
    assert len({r['run_id'] for c in cases for r in c['runs']})==320

def test_permutations_preserve_same_evidence():
    for c in build_cases():
        for condition in ORDERED:
            e=evidence(c,condition,'AB');a=c['permutations'][condition]['O1']['indices'];b=c['permutations'][condition]['O2']['indices']
            assert sorted(a)==sorted(b)==list(range(len(e))) and a!=b
            assert sorted(e[i] for i in a)==sorted(e[i] for i in b)
            assert c['permutations'][condition]['O2']['seed']-c['permutations'][condition]['O1']['seed']==10000

@pytest.mark.parametrize('gamma',LEVELS)
def test_mechanism_and_causal_zero(gamma):
    rows=world_counts(gamma)
    assert sum(r['trials'] for r in rows)==2000
    for state,rate in enumerate([.9,.2]):
        rr=[r for r in rows if r['state']==state];assert sum(r['trials'] for r in rr)==1000
        assert all(r['successes']/r['trials']==pytest.approx(rate) for r in rr)
        a=next(r for r in rr if r['action']=='A');assert a['trials']/1000==pytest.approx(gamma if state==0 else 1-gamma)
    causal={a:sum(.5*r['successes']/r['trials'] for r in rows if r['action']==a) for a in ['A','B']}
    assert causal['A']==pytest.approx(.55) and causal['B']==pytest.approx(.55) and causal['A']-causal['B']==0

def test_balanced_and_stratified():
    for c in build_cases():
        assert all(r['trials']==500 for r in c['balanced_counts'])
        assert c['confounded_counts']==world_counts(c['gamma'])
        for version in ['AB','BA']:
            text=' '.join(evidence(c,'StratifiedOracle',version))
            assert text.count('90.0%')==2 and text.count('20.0%')==2
            assert '因果效果相同' not in text
        if c['gamma']==.5:
            for v in ['AB','BA']:
                for o in ['O1','O2']:assert prompt(c,'ConfoundedMemory',v,o)==prompt(c,'BalancedMemory',v,o)

@pytest.mark.parametrize('raw',['{}','{"p_success_left":0.5}','{"p_success_left":0.5,"p_success_right":0.5,"reason":"x"}','{"p_success_left":true,"p_success_right":0.5}','{"p_success_left":55,"p_success_right":55}','{"p_success_left":-0.1,"p_success_right":0.5}','{"p_success_left":NaN,"p_success_right":0.5}','{"p_success_left":0.5,"p_success_left":0.6,"p_success_right":0.5}','{"p_success_left":"0.5","p_success_right":0.5}','prefix {"p_success_left":0.5,"p_success_right":0.5}','{"p_success_left":0.5,'])
def test_invalid_json(raw):
    with pytest.raises((ValueError,TypeError)):parse(raw)
@pytest.mark.parametrize('value',[0,.5,1])
def test_valid_probability(value):assert parse(json.dumps({'p_success_left':value,'p_success_right':value}))['p_success_left']==value

@pytest.mark.parametrize('sequence,expected,calls',[(['good'],'VALID',1),(['bad','good'],'VALID',2),(['bad','bad','good'],'INVALID',2),(['transport','good'],'INVALID',1)])
def test_retry_exactly_once_same_prompt(sequence,expected,calls):
    seen=[]
    def invoke(text,index):
        seen.append((text,index));value=sequence[index]
        return {'transport_error':'offline'} if value=='transport' else {'raw':'{"p_success_left":0.25,"p_success_right":0.75}' if value=='good' else '{}'}
    result=run_with_retry('fixed semantic prompt',invoke)
    assert result['final_status']==expected and len(seen)==calls
    assert all(text=='fixed semantic prompt' for text,index in seen)
    assert result['retry_attempt'] is not None if calls==2 else result['retry_attempt'] is None

def test_scenario_paired_aggregation_and_missing():
    rows=[{'version':v,'order':o,'final_status':'VALID','miab':m} for v,o,m in [('AB','O1',.8),('BA','O1',.4),('AB','O2',.6),('BA','O2',.2)]]
    result=paired_average(rows,'ConfoundedMemory')
    assert result['miab']==pytest.approx(.5);assert result['AB']==pytest.approx(.7);assert result['BA']==pytest.approx(.3);assert result['O1']==pytest.approx(.6);assert result['O2']==pytest.approx(.4)
    assert paired_average(rows[:-1],'ConfoundedMemory') is None
    rows[0]['final_status']='INVALID';assert paired_average(rows,'ConfoundedMemory') is None

def gate_fixture():
    metrics={n:{'mean':v,'ci_low':.05} for n,v in [('NoMemory',0),('ConfoundedMemory',.1),('BalancedMemory',.01),('StratifiedOracle',.02),('BalancedCorrection',.09),('StratifiedCorrection',.08)]}
    gamma={str(g):{'ConfoundedMemory':{'mean':v}} for g,v in zip(LEVELS,[0,.1,.2,.3])}
    sens={axis:{key:{'ConfoundedMemory':{'mean':.1}} for key in keys} for axis,keys in [('label',['AB','BA']),('order',['O1','O2'])]}
    return metrics,gamma,sens,320,20,{str(g):5 for g in LEVELS}

def test_go_fixture():
    gates,rho,verdict=assess_gates(*gate_fixture());assert all(gates.values()) and rho==1 and verdict=='IDEA2_CONFIRM_GO'
@pytest.mark.parametrize('valid,complete,counts,passes',[(317,19,[4,5,5,5],True),(316,19,[4,5,5,5],False),(320,18,[4,4,5,5],False),(320,19,[3,5,5,6],False)])
def test_completeness_boundary(valid,complete,counts,passes):
    args=list(gate_fixture());args[3:]=[valid,complete,dict(zip(map(str,LEVELS),counts))];gates,_,verdict=assess_gates(*args);assert gates['G0']==passes
    if not passes:assert verdict=='IDEA2_CONFIRM_WEAK'
@pytest.mark.parametrize('axis,key,gate',[('label','AB','G6'),('label','BA','G6'),('order','O1','G7'),('order','O2','G7')])
def test_robustness_threshold(axis,key,gate):
    args=list(gate_fixture());args[2][axis][key]['ConfoundedMemory']['mean']=.05;assert assess_gates(*args)[0][gate] is False
@pytest.mark.parametrize('values,passes',[( [0,.1,.1,.3],True),([0,.1,.099,.3],True),([0,.1,.09,.3],False),([0,0,0,.3],False),([.04,.1,.2,.3],False)])
def test_dose_response_rule(values,passes):
    args=list(gate_fixture());args[1]={str(g):{'ConfoundedMemory':{'mean':v}} for g,v in zip(LEVELS,values)};assert assess_gates(*args)[0]['G2']==passes

def test_g1_and_correction_boundaries():
    args=list(gate_fixture());args[0]['ConfoundedMemory']['mean']=.08;assert assess_gates(*args)[0]['G1']
    args[0]['ConfoundedMemory']['ci_low']=0;assert not assess_gates(*args)[0]['G1']
    args=list(gate_fixture());args[0]['BalancedCorrection']['mean']=.059;assert not assess_gates(*args)[0]['G3']
    args=list(gate_fixture());args[0]['StratifiedMemory']={'mean':.04};args[0]['StratifiedOracle']['mean']=.04;assert not assess_gates(*args)[0]['G4']
    args=list(gate_fixture());args[0]['NoMemory']['mean']=.021;assert not assess_gates(*args)[0]['G5']
