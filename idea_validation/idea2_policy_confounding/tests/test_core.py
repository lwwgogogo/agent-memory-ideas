import json,pytest
from simulate import numerical,analytic,GAMMAS
from generate_cases import build_cases,counts,render,make_prompt
from run_llm_test import parse,normalized_bias

def test_unconfounded_zero():assert numerical(.5)['observational_gap']==pytest.approx(0,abs=1e-12)
def test_monotonic():
    gaps=[numerical(g)['observational_gap'] for g in GAMMAS]
    assert all(b>a for a,b in zip(gaps,gaps[1:]))
@pytest.mark.parametrize('gamma',GAMMAS)
def test_causal_zero(gamma):
    r=numerical(gamma);assert r['causal_gap']==0;assert r['causal_success_A']==pytest.approx(.55);assert r['causal_success_B']==pytest.approx(.55)
@pytest.mark.parametrize('gamma',GAMMAS+[.85])
def test_joint_matches_analytic(gamma):
    r=numerical(gamma);a,b,gap=analytic(gamma)
    assert r['observational_success_A']==pytest.approx(a);assert r['observational_success_B']==pytest.approx(b);assert r['observational_gap']==pytest.approx(gap)
@pytest.mark.parametrize('gamma',[.5,.7,.85,.95])
def test_experience_counts(gamma):
    rows=counts(gamma);assert sum(r['trials'] for r in rows)==2000
    for state,rate in enumerate([.9,.2]):
        rr=[r for r in rows if r['state']==state];assert sum(r['trials'] for r in rr)==1000
        assert all(r['successes']/r['trials']==pytest.approx(rate) for r in rr)
    rates=[sum(r['successes'] for r in rows if r['action']==a)/sum(r['trials'] for r in rows if r['action']==a) for a in ['A','B']]
    assert rates[0]-rates[1]==pytest.approx(analytic(gamma)[2])

def test_design_and_information_integrity():
    cases=build_cases();assert len(cases)==20 and len({c['family'] for c in cases})==5
    for c in cases:
        assert len(c['variants'])==4 and len({(v['label_swap'],v['order_seed']) for v in c['variants']})==4
        for v in c['variants']:
            assert v['memories']['NoMemory']==[]
            assert len(v['memories']['ConfoundedMemory'])==4
            assert len(v['memories']['StratifiedOracle'])==2
            assert len(v['memories']['AggregateSummary'])==2
            assert '因果效果相同' not in make_prompt(c,v,'StratifiedOracle')
        if c['gamma']==.5:
            for v in c['variants']:assert v['memories']['ConfoundedMemory']==v['memories']['BalancedMemory']

def test_order_changes_only_order():
    rows=counts(.85)
    for style in ['ConfoundedMemory','AggregateSummary']:
        a=render(rows,['Q7','M4'],0,17,style);b=render(rows,['Q7','M4'],0,43,style)
        assert sorted(a)==sorted(b) and a!=b

def test_swap_normalization():
    assert normalized_bias({'p_success_A':.8,'p_success_B':.2},0)==pytest.approx(.6)
    assert normalized_bias({'p_success_A':.2,'p_success_B':.8},1)==pytest.approx(.6)

@pytest.mark.parametrize('raw',['{}','not json','{"p_success_A":NaN,"p_success_B":0.5,"choice":"A","confidence":0.5,"reason":"x"}','{"p_success_A":true,"p_success_B":0.5,"choice":"A","confidence":0.5,"reason":"x"}','{"p_success_A":1.1,"p_success_B":0.5,"choice":"A","confidence":0.5,"reason":"x"}','{"p_success_A":0.5,"p_success_A":0.8,"p_success_B":0.5,"choice":"A","confidence":0.5,"reason":"x"}'])
def test_reject_invalid(raw):
    with pytest.raises((ValueError,TypeError)):parse(raw)
@pytest.mark.parametrize('choice',['A','B','TIE'])
def test_ties_never_exclude_valid_probabilities(choice):
    x={'p_success_A':.5,'p_success_B':.5,'choice':choice,'confidence':.5,'reason':'没有差异'}
    assert parse(json.dumps(x))==x
