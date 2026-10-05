from fractions import Fraction as F
from schema import Observation
def observations(items):
 result=[]
 for x in items:
  assert len(x['steps'])==1
  st=x['steps'][0];reward=st['reward']
  assert reward in (0,1) and x['final_score']==reward
  result.append(Observation(x['episode_id'],st['state'],st['action'],int(reward),F(x['final_score'])))
 return result
def identity(x):return x['episode_id']
