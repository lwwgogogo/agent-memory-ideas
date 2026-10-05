"""Integer-count experience construction; no outcome sampling or native algorithms."""
from fractions import Fraction
import json, random
from collections import Counter
from common import ROOT,GAMMAS,SEEDS,sha,canonical,save
RATES={'S0':Fraction(9,10),'S1':Fraction(1,5)}
N_PER_STATE=1000
def target_value(action):
    assert action in ('A','B')
    return sum(Fraction(1,2)*r for r in RATES.values())
def generate(gamma,policy):
    assert policy in ('P','Q')
    gamma=Fraction(gamma);rows=[]
    assert gamma in map(Fraction,GAMMAS)
    for state in ('S0','S1'):
        pa=gamma if state=='S0' else 1-gamma
        if policy=='Q':pa=1-pa
        for action,prop in [('A',pa),('B',1-pa)]:
            n=prop*N_PER_STATE;assert n.denominator==1
            s=n*RATES[state];assert s.denominator==1
            for outcome,count in [(1,int(s)),(0,int(n-s))]:
                for i in range(count):
                    rows.append({'id':f'{state}-{action}-{outcome}-{i:04d}',
                                 'state':state,'action':action,'outcome':outcome})
    return rows
def multiset_hash(rows):
    return sha(('\n'.join(sorted(canonical(r) for r in rows))+'\n').encode())
def order_hash(rows):
    return sha(('\n'.join(canonical(r) for r in rows)+'\n').encode())
def ordered(rows,seed):
    rows=list(rows);random.Random(seed).shuffle(rows);return rows
def counts(rows):
    out={}
    for state in RATES:
        for action in ('A','B'):
            cell=[r for r in rows if r['state']==state and r['action']==action]
            out[f'{state}/{action}']={'exposure':len(cell),'success':sum(r['outcome'] for r in cell)}
    return out
def success_pool(rows):
    c=Counter(r['action'] for r in rows if r['outcome']==1)
    n=sum(c.values())
    return {'size':n,'counts':dict(c),'fractions':{a:str(Fraction(c[a],n)) for a in ('A','B')}}
def build():
    manifest={'target_values':{a:str(target_value(a)) for a in ('A','B')},
              'n_per_state':N_PER_STATE,'conditions':[],'outcomes_sampled':False}
    for g in GAMMAS:
        for p in ('P','Q'):
            rows=generate(g,p);h=multiset_hash(rows)
            path=ROOT/f'results/exact_logs/gamma_{g}_{p}.jsonl'
            path.write_text(''.join(canonical(r)+'\n' for r in rows))
            reps=[{'seed':s,'multiset_sha256':multiset_hash(ordered(rows,s)),
                   'order_sha256':order_hash(ordered(rows,s))} for s in SEEDS]
            assert all(z['multiset_sha256']==h for z in reps)
            manifest['conditions'].append({'gamma':g,'policy':p,'file':str(path.relative_to(ROOT)),
                'n':len(rows),'cells':counts(rows),'multiset_sha256':h,
                'success_pool':success_pool(rows),'replicates':reps})
    manifest['all_multiset_checks_passed']=True
    save(ROOT/'results/exact_logs/manifest.json',manifest)
    return manifest
def load(gamma,policy,seed):
    p=ROOT/f'results/exact_logs/gamma_{gamma}_{policy}.jsonl'
    return ordered([json.loads(x) for x in p.read_text().splitlines()],seed)
if __name__=='__main__':
    print(canonical(build()))
