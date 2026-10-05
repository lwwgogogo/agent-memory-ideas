from dataclasses import dataclass
from fractions import Fraction as F
@dataclass(frozen=True,slots=True)
class Observation:
 id:str
 state:str
 action:str
 outcome:int
 native_utility:F
 def __post_init__(self):
  assert self.state in ('S0','S1') and self.action in ('A','B')
  assert self.outcome in (0,1)
def validate_rho(rho):
 assert set(rho)=={'S0','S1'}
 rho={s:F(v) for s,v in rho.items()}
 assert sum(rho.values())==1 and min(rho.values())>=0
 return rho
