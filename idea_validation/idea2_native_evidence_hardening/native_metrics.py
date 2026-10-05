"""Evaluator statistics derived from returned native objects, never used for ranking."""
from collections import Counter
from math import log2,fsum
from fractions import Fraction
def parse(system,native_return):
    if system not in ('jitrl','memrl'):raise ValueError(system)
    selected=native_return if system=='jitrl' else native_return['selected']
    out=[]
    for rank,item in enumerate(selected,1):
        if system=='jitrl':
            assert len(item['steps'])==1
            a=item['steps'][0]['action'];state=item['steps'][0]['state']
            score=item['final_score'];ident=item['episode_id'];sim=None
        elif system=='memrl':
            a=item['action'];state=item['state'];ident=item['memory_id']
            score=item['metadata']['q_value'];sim=item.get('similarity')
            assert item['metadata']['action']==a and item['metadata']['state']==state
        else:raise ValueError(system)
        assert a in ('A','B')
        out.append({'id':ident,'action':a,'state':state,'native_score':score,
                    'rank':rank,'similarity':sim})
    return out
def selection(items):
    n=len(items)
    if not n:raise ValueError('empty native selection')
    na=sum(x['action']=='A' for x in items);nb=n-na
    weights=[1/log2(i+1) for i in range(1,n+1)]
    return {'n':n,'n_A':na,'n_B':nb,'f_A':na/n,'f_B':nb/n,'SSP':(na-nb)/n,
            'SSP_exact':str(Fraction(na-nb,n)),
            'RWP':fsum(w*(1 if x['action']=='A' else -1) for w,x in zip(weights,items))/fsum(weights)}
def native_piur(p,q):
    # Strict +/- 0.10 tested on integer counts: equality at threshold is not a reversal.
    sp=Fraction(p['n_A']-p['n_B'],p['n']);sq=Fraction(q['n_A']-q['n_B'],q['n'])
    e=Fraction(1,10)
    return int((sp>e and sq<-e) or (sp<-e and sq>e))
def rcd(p,q):return abs(p['f_A']-q['f_A'])
def balanced_reduction(p,q,bal):
    den=(abs(p['SSP'])+abs(q['SSP']))/2
    return None if den==0 else 1-abs(bal['SSP'])/den
def ties(selected_scores,candidate_scores):
    sc=Counter(selected_scores);cc=Counter(candidate_scores)
    if not sc or not cc:raise ValueError('empty tie audit')
    return {'selected_unique_score_count':len(sc),
            'selected_tie_fraction':sum(n for n in sc.values() if n>1)/sum(sc.values()),
            'selected_duplicate_score_fraction':1-len(sc)/sum(sc.values()),
            'candidate_unique_score_count':len(cc),
            'candidate_tie_fraction':sum(n for n in cc.values() if n>1)/sum(cc.values()),
            'top_score_candidate_pool_size':cc[max(cc)],
            'top_native_score':max(cc)}
