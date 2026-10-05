"""Minimal interface; implementations must delegate to unmodified upstream code."""
from abc import ABC,abstractmethod
class MemoryAuditAdapter(ABC):
 name='abstract';level='L0'
 @abstractmethod
 def reset(self):...
 @abstractmethod
 def ingest(self,experiences):...
 def score_action(self,state,action):return None
 def retrieve(self,query_state,k):return None
 def summarize_action_preference(self,query_state):
  a=self.score_action(query_state,'A');b=self.score_action(query_state,'B')
  return None if a is None or b is None else {'A':a,'B':b}
