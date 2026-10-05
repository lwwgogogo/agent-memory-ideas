"""Secondary quota prototype; primary endpoint is estimate_action_utility."""
import math
from fractions import Fraction as F
from methods import estimate
from schema import validate_rho
from adapters import jitrl,memrl
def apportion(n,weights):
 keys=sorted(weights);total=sum(weights.values())
 raw={a:n*weights[a]/total for a in keys}
 out={a:math.floor(raw[a]) for a in keys}
 for a in sorted(keys,key=lambda a:(-(raw[a]-out[a]),a))[:n-sum(out.values())]:out[a]+=1
 return out
class CorrectedMemorySelector:
 def __init__(self,system,method='M1'):
  assert method in ('M1','M2','M4')
  self.reader={'jitrl':jitrl,'memrl':memrl}[system];self.method=method
 def fit(self,memory_items):
  self.items=self.reader.observations(memory_items);return self
 def estimate_action_utility(self,target_context_distribution):
  return estimate(self.method,self.items,target_context_distribution)
 def select(self,candidates,k,target_context_distribution):
  if self.method not in ('M1','M4'):raise ValueError('secondary protocol only M1/M4')
  rho=validate_rho(target_context_distribution)
  utility=self.estimate_action_utility(rho)
  states=apportion(k,rho)
  soft={a:math.exp(float(v)) for a,v in utility.items()} # fixed T=1
  obs=self.reader.observations(candidates);selected=[]
  for s,n in states.items():
   if not n:continue
   if n<4:raise ValueError('state quota insufficient for two slots per action')
   allocation=apportion(n-4,soft)
   for a in ('A','B'):
    count=2+allocation[a]
    pool=[(x,o) for x,o in zip(candidates,obs) if o.state==s and o.action==a]
    if len(pool)<count:raise ValueError('insufficient observed support; no duplication')
    # Preserve insertion order within state/action; do not favor successful outcomes.
    selected.extend(x for x,o in pool[:count])
  assert len(selected)==k
  return selected
