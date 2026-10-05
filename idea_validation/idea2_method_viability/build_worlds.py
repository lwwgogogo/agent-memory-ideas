"""Exact integer worlds. Truth and logging metadata stay outside practical inputs."""
from fractions import Fraction as F
from config import ROOT,GAMMAS,canonical,sha,save
RATES={'A':{'S0':{'A':F(9,10),'B':F(9,10)},'S1':{'A':F(1,5),'B':F(1,5)}},
       'B':{'S0':{'A':F(9,10),'B':F(4,5)},'S1':{'A':F(3,10),'B':F(1,5)}},
       'C':{'S0':{'A':F(9,10),'B':F(3,5)},'S1':{'A':F(1,5),'B':F(1,2)}}}
TARGETS={'T':{'S0':F(1,2),'S1':F(1,2)},'T0':{'S0':F(4,5),'S1':F(1,5)},'T1':{'S0':F(1,5),'S1':F(4,5)}}
def true_mu(gamma,policy):
 g=F(gamma);pa={'S0':g,'S1':1-g}
 if policy=='Q':pa={s:1-p for s,p in pa.items()}
 return {s:{'A':p,'B':1-p} for s,p in pa.items()}
def truth(mechanism,target):
 return {a:sum(TARGETS[target][s]*RATES[mechanism][s][a] for s in ('S0','S1')) for a in ('A','B')}
def generate(mechanism,gamma,policy):
 rows=[];mu=true_mu(gamma,policy)
 for s in ('S0','S1'):
  for a in ('A','B'):
   n=1000*mu[s][a];success=n*RATES[mechanism][s][a]
   assert n.denominator==success.denominator==1
   for y,count in [(1,int(success)),(0,int(n-success))]:
    for i in range(count):
     rows.append({'id':f'{s}-{a}-{y}-{i:04d}','state':s,'action':a,'outcome':y})
 return rows
def worlds():
 for family,mechanisms,gammas in [('A',['A'],GAMMAS),('B',['B'],GAMMAS),('C',['C'],GAMMAS),('D',['A','B','C'],('0.95','0.99'))]:
  for mechanism in mechanisms:
   for gamma in gammas:
    for policy in ('P','Q'):
     yield {'id':f'{family}_{mechanism}_{gamma}_{policy}','family':family,'mechanism':mechanism,
            'gamma':gamma,'policy':policy,'targets':['T','T0','T1'] if mechanism=='C' else ['T']}
def cells(rows):
 return {s:{a:{'n':sum(r['state']==s and r['action']==a for r in rows),
                   'success':sum(r['outcome'] for r in rows if r['state']==s and r['action']==a)}
            for a in ('A','B')} for s in ('S0','S1')}
def build():
 out=[]
 for w in worlds():
  rows=generate(w['mechanism'],w['gamma'],w['policy']);p=ROOT/f"results/worlds/{w['id']}.jsonl"
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(canonical(r)+'\n' for r in rows))
  out.append(dict(w,n=2000,cells=cells(rows),file=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),
                  truth={t:{a:str(v) for a,v in truth(w['mechanism'],t).items()} for t in w['targets']}))
 save(ROOT/'results/world_manifest.json',{'worlds':out,'outcome_sampling':False,'N_per_state':1000,'D_scope':'A/B/C mechanisms at .95 and .99; sensitivity only at .99'})
 return out
if __name__=='__main__':print('exact banks:',len(build()))
