"""Fixed estimators. Practical APIs receive only typed observed records and target rho."""
from fractions import Fraction as F
from schema import Observation,validate_rho
PRACTICAL=('M1','M2','M4')
def stats(items):
 out={s:{a:[0,0] for a in ('A','B')} for s in ('S0','S1')}
 for x in items:
  assert isinstance(x,Observation)
  out[x.state][x.action][0]+=1;out[x.state][x.action][1]+=x.outcome
 return out
def m1(items,rho):
 rho=validate_rho(rho);c=stats(items);out={}
 for a in ('A','B'):
  out[a]=F(0)
  for s,p in rho.items():
   if p==0:continue
   n,y=c[s][a]
   if not n:raise ValueError('positivity failure')
   out[a]+=p*F(y,n)
 return out
def empirical_propensity(items):
 c=stats(items)
 return {s:{a:F(c[s][a][0]+1,sum(c[s][b][0] for b in ('A','B'))+2) for a in ('A','B')} for s in c}
def m2(items,rho):
 # Literal preregistered global empirical SNIPS: rho deliberately not used.
 validate_rho(rho);mu=empirical_propensity(items);num={a:F(0) for a in ('A','B')};den=num.copy()
 for x in items:
  w=1/max(mu[x.state][x.action],F(1,20))
  num[x.action]+=w*x.outcome;den[x.action]+=w
 if min(den.values())==0:raise ValueError('no action support')
 return {a:num[a]/den[a] for a in den}
def m4(items,rho):
 rho=validate_rho(rho);c=stats(items)
 return {a:sum(p*F(2*c[s][a][1]+1,2*(c[s][a][0]+1)) for s,p in rho.items()) for a in ('A','B')}
def aggregate(items,rho):
 validate_rho(rho)
 return {a:F(sum(x.outcome for x in items if x.action==a),sum(x.action==a for x in items)) for a in ('A','B')}
def oracle(items,rho,mu,state_distribution):
 # ORACLE / NOT CANDIDATE METHOD. Target-aware classical SNIPS.
 rho=validate_rho(rho);num={a:F(0) for a in ('A','B')};den=num.copy()
 for x in items:
  w=rho[x.state]/state_distribution[x.state]/mu[x.state][x.action]
  num[x.action]+=w*x.outcome;den[x.action]+=w
 return {a:num[a]/den[a] for a in num}
def estimate(method,items,rho):
 return {'M1':m1,'M2':m2,'M4':m4,'A1':aggregate}[method](items,rho)
