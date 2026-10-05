"""Adapter uses MemRL's unchanged QValueUpdater and ValueAwareSelector."""
import importlib.util,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Item:
 def __init__(self,ident,memory,metadata=None):self.id=ident;self.memory=memory;self.metadata=metadata or {}
class TextMemory:
 def __init__(self):self.items={}
 def get(self,ident):return self.items[ident]
 def update(self,ident,payload):self.items[ident]=Item(ident,payload.get('memory',''),payload.get('metadata',{}))
class Cube:
 def __init__(self):self.text_mem=TextMemory()
class FakeMOS:
 def __init__(self):self.mem_cubes={'audit':Cube()}
class MemRLAdapter:
 name='memrl';level='L2';query_state_supported=False
 def __init__(self):self.native=None
 def _load(self):
  if self.native:return self.native
  # MOS is used only as a type/import boundary in this module; its updater
  # operates on the duck-typed text_mem object below. No MemOS algorithm runs.
  for modname in ['memos','memos.mem_os','memos.mem_os.main']:
   if modname not in sys.modules:
    m=types.ModuleType(modname);m.__path__=[];sys.modules[modname]=m
  sys.modules['memos.mem_os.main'].MOS=type('MOS',(),{})
  path=ROOT/'third_party'/'memrl'/'memrl'/'service'/'value_driven.py'
  spec=importlib.util.spec_from_file_location('pcm_memrl_value_driven',path);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
  self.native=mod;return mod
 def reset(self):
  mod=self._load();self.mos=FakeMOS()
  cfg=mod.RLConfig(alpha=.1,gamma=0.0,epsilon=0.0,q_init_pos=0.0,q_init_neg=0.0)
  self.cfg=cfg;self.updater=mod.QValueUpdater(self.mos,'audit',cfg,default_cube_id='audit')
  self.selector=mod.ValueAwareSelector(cfg);self.rows=[]
 def ingest(self,experiences):
  text=self.mos.mem_cubes['audit'].text_mem
  for r in experiences:
   ident=r['episode_id'];item=Item(ident,f"state={r['state']} action={r['action']} outcome={r['outcome']}",{})
   text.items[ident]=item
   # Upstream MemRL update consumes reward feedback; propensity is never passed.
   self.updater.update(ident,1.0 if r['outcome'] else -1.0)
   self.rows.append({'memory_id':ident,'action':r['action'],'state':r['state'],
                     'metadata':dict(text.items[ident].metadata),'similarity':0.5})
 def score_action(self,query_state='TARGET'):
  return {a:sum(x['metadata']['q_value'] for x in self.rows if x['action']==a)/sum(x['action']==a for x in self.rows) for a in ['A','B']}
 def retrieve(self,query_state='TARGET',k=20):
  # ValueAwareSelector is the native top-k reranker; upstream semantic
  # candidate retrieval is intentionally not replaced or simulated here.
  return self.selector.select(self.rows,k)['selected']
