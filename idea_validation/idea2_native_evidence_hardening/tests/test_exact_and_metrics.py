from collections import Counter
from fractions import Fraction
import math
import pytest
from common import GAMMAS,SEEDS,KS
from build_exact_logs import generate,target_value,counts,ordered,multiset_hash,order_hash,RATES,success_pool
from native_metrics import parse,selection,native_piur,rcd,balanced_reduction,ties
from evaluate import dose,k_consistency,reversal_gate,decide
def metric(na,n=20):
    return selection([{'action':'A' if i<na else 'B'} for i in range(n)])
def test_exact_target():
    assert target_value('A')==target_value('B')==Fraction(11,20)
@pytest.mark.parametrize('gamma',GAMMAS)
@pytest.mark.parametrize('policy',['P','Q'])
def test_exact_cells(gamma,policy):
    rows=generate(gamma,policy);c=counts(rows)
    assert len(rows)==2000 and len({r['id'] for r in rows})==2000
    for state in ('S0','S1'):
        pa=Fraction(gamma) if state=='S0' else 1-Fraction(gamma)
        if policy=='Q':pa=1-pa
        for a,p in [('A',pa),('B',1-pa)]:
            assert c[f'{state}/{a}']['exposure']==1000*p
            assert c[f'{state}/{a}']['success']==1000*p*RATES[state]
@pytest.mark.parametrize('gamma',GAMMAS)
def test_pq_exposure_reversal(gamma):
    p,q=[counts(generate(gamma,policy)) for policy in ['P','Q']]
    for s in RATES:
        assert p[s+'/A']==q[s+'/B'] and p[s+'/B']==q[s+'/A']
def test_bal_identity_and_exposure():
    p,q=[generate('0.50',pol) for pol in ('P','Q')]
    assert p==q
    assert {c['exposure'] for c in counts(p).values()}=={500}
    assert counts(p)['S0/A']['success']==450
    assert counts(p)['S1/A']['success']==100
@pytest.mark.parametrize('gamma',GAMMAS)
@pytest.mark.parametrize('policy',['P','Q'])
def test_20_multiset_replicates_only_order_changes(gamma,policy):
    rows=generate(gamma,policy);original=list(rows);h=multiset_hash(rows)
    identities=Counter(tuple(sorted(r.items())) for r in rows)
    shuffled=[ordered(rows,seed) for seed in SEEDS]
    assert rows==original
    assert all(Counter(tuple(sorted(r.items())) for r in r2)==identities for r2 in shuffled)
    assert all(multiset_hash(r2)==h for r2 in shuffled)
    assert len({order_hash(r2) for r2 in shuffled})==20
    assert shuffled[0]==ordered(rows,SEEDS[0])
def test_success_pool_exact_mechanism():
    p=success_pool(generate('0.95','P'));q=success_pool(generate('0.95','Q'))
    assert p['size']==q['size']==1100
    assert p['counts']=={'A':865,'B':235}
    assert q['counts']=={'A':235,'B':865}
def test_ssp():
    assert metric(15)['SSP']==.5
    assert metric(0)['SSP']==-1 and metric(20)['SSP']==1
    assert metric(10)['SSP']==0
def test_rcd():
    assert rcd(metric(15),metric(5))==.5
    assert rcd(metric(5),metric(15))==.5
    assert rcd(metric(5),metric(5))==0
def test_piur_strict_boundaries():
    assert native_piur(metric(11),metric(9))==0
    assert native_piur(metric(12),metric(8))==1
    assert native_piur(metric(8),metric(12))==1
    assert native_piur(metric(12),metric(13))==0
def test_bal_reduction_and_na():
    assert balanced_reduction(metric(15),metric(5),metric(10))==1
    assert balanced_reduction(metric(14),metric(6),metric(12))==.5
    assert balanced_reduction(metric(10),metric(10),metric(10)) is None
    assert balanced_reduction(metric(12),metric(8),metric(20))<0
def test_rwp_rank_sensitive_and_bounded():
    vals=[{'action':'A'},{'action':'B'}]
    expected=(1-1/math.log2(3))/(1+1/math.log2(3))
    assert selection(vals)['RWP']==pytest.approx(expected)
    assert selection(list(reversed(vals)))['RWP']==pytest.approx(-expected)
    assert selection([{'action':'A'}]*50)['RWP']==1
def test_tie_statistics():
    t=ties([1,1,0],[1,1,1,0,0])
    assert t['selected_unique_score_count']==2
    assert t['selected_tie_fraction']==pytest.approx(2/3)
    assert t['selected_duplicate_score_fraction']==pytest.approx(1/3)
    assert t['top_score_candidate_pool_size']==3
    assert ties([1,0],[1,0])['selected_tie_fraction']==0
def test_dose_thresholds_and_rho():
    d=dose(dict(zip(GAMMAS,[0,.2,.4,.6])))
    assert d['thresholds_pass'] and d['spearman_rho']==1
    assert not dose(dict(zip(GAMMAS,[0,.1,.15,.2])))['thresholds_pass']
    assert not dose(dict(zip(GAMMAS,[0,.5,.4,.4])))['thresholds_pass']
    assert dose(dict(zip(GAMMAS,[0,0,0,0])))['spearman_rho']==0
def test_k_3_of_4_boundary():
    s={k:{'median_SSP_P':.4,'median_SSP_Q':-.4,'median_RCD':.4,'reversal_rate':.8} for k in KS}
    s[5]['median_SSP_Q']=.1
    assert k_consistency(s)['pass']
    s[10]['median_SSP_Q']=.1
    assert not k_consistency(s)['pass']
def test_reversal_gate_boundaries():
    assert reversal_gate({'reversal_rate':.8,'median_RCD':.3})
    assert not reversal_gate({'reversal_rate':.75,'median_RCD':.7})
    assert not reversal_gate({'reversal_rate':1,'median_RCD':.2999})
def test_verdict_boundaries():
    g={f'G{i}':{'pass':True} for i in range(8)}
    p={s:{'median_BAL_reduction':.5} for s in ('jitrl','memrl')}
    assert decide(g,p)=='NATIVE_EVIDENCE_GO'
    g['G6']['pass']=False
    assert decide(g,p)=='NATIVE_EVIDENCE_NARROW'
    g['G2']['pass']=False;g['G3']['pass']=False
    assert decide(g,p)=='NATIVE_EVIDENCE_NO_GO'
    g['G2']['pass']=True;g['G0']['pass']=False
    assert decide(g,p)=='NATIVE_EVIDENCE_NO_GO'
def test_empty_or_unknown_output_fails():
    with pytest.raises(ValueError):selection([])
    with pytest.raises(ValueError):parse('not_a_system',[{}])
