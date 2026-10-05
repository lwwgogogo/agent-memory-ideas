from fractions import Fraction as F
from schema import Observation
def observations(items):
 result=[]
 for x in items:
  md=x['metadata'];r=F(str(md['last_reward']))
  assert r in (-1,1)
  # Fixed documented native feedback coding +1/-1, not a propensity or truth field.
  y=(r+1)/2
  result.append(Observation(x['memory_id'],md['state'],md['action'],int(y),F(str(md['q_value']))))
 return result
def identity(x):return x['memory_id']
