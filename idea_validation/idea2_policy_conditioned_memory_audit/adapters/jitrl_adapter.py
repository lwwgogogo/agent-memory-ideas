"""Adapter around the unmodified JitRL episode-ranker helper."""
import importlib,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def _load_native():
 path=ROOT/'third_party'/'jitrl'/'Jericho'
 sys.path.insert(0,str(path))
 # Optional provider packages are stubbed only to import the pure ranking helper;
 # this adapter never invokes an LLM, embedding API, or changes JitRL source.
 if 'openai' not in sys.modules:
  m=types.ModuleType('openai')
  class E(Exception):pass
  m.OpenAI=type('OpenAI',(),{'__init__':lambda self,*a,**k:None})
  m.RateLimitError=m.APIError=m.OpenAIError=E
  sys.modules['openai']=m
 if 'tiktoken' not in sys.modules:
  m=types.ModuleType('tiktoken');m.get_encoding=lambda name: type('Enc',(),{'encode':lambda self,x:list(x.encode()),'decode':lambda self,x:bytes(x).decode(errors='ignore')})()
  sys.modules['tiktoken']=m
 if 'dotenv' not in sys.modules:
  m=types.ModuleType('dotenv');m.load_dotenv=lambda **kwargs:None;sys.modules['dotenv']=m
 return importlib.import_module('src.prompt_update_with_history').get_top_episodes
class JitRLAdapter:
 name='jitrl';level='L2';query_state_supported=False
 def reset(self):self.rows=[]
 def ingest(self,experiences):
  self.rows=[{'episode_id':r['episode_id'],'final_score':float(r['outcome']),'success':bool(r['outcome']),
              'steps':[{'state':r['state'],'action':r['action'],'reward':r['outcome']}]} for r in experiences]
 def retrieve(self,query_state='TARGET',k=20):
  get_top=_load_native()
  return get_top(self.rows,k)
 def score_action(self,query_state='TARGET'):
  out={}
  for a in ['A','B']:
   xs=[r['final_score'] for r in self.rows if r['steps'][0]['action']==a]
   out[a]=sum(xs)/len(xs)
  return out
