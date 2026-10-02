import random

def make_episode(r, structure, transformation, compression, trace):
    evidence=[{'id':f'e{i}','text':f'{"shared" if structure=="S6_overlap" else "source"+str(i)} fact{i} topic{i%2}','source':f's{i}'} for i in range(4)]
    if structure=='S1_single': support=frozenset({0})
    elif structure in ('S2_multi','S3_redundant','S6_overlap'): support=frozenset({0,1})
    elif structure in ('S4_alternative','S5_conflicting'): support=frozenset({0 if r.random()<.5 else 1})
    else: support=frozenset({0})
    kept=[e['text'] for e in evidence if e['id'] in {f'e{i}' for i in support} or r.random()>compression*.8]
    if transformation in ('T2_summary','T3_merge','T4_rewrite','T5_multistep'):
        kept=[x.replace('source','s').replace('fact','f') for x in kept]
    if compression>=.4: kept=[x.replace('topic0','topic') for x in kept]
    memory=' '.join(sorted(kept)) or 'generic memory'; hidden=[f'support:{i}' for i in sorted(support)]
    visible=hidden if trace>=.99 else hidden[:max(0,int(len(hidden)*trace))]
    return {'candidate_evidence':[e['text'] for e in evidence],'support':sorted(support),'chain':[transformation,compression],'visible_trace':visible,'hidden_trace':hidden,'memory':memory,'claim':'claim topic0','observation':f'claim topic0|{memory}|{" ".join(visible)}'}
