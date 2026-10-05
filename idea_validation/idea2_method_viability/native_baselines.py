"""Unmodified upstream imports, native update and native selection, Stage-4.1 protocol."""
import importlib.util,sys,types,inspect,random,json,statistics
from functools import lru_cache
from fractions import Fraction as F
from config import ROOT,UPSTREAM,OLD41,SEEDS,sources,sha,save
sys.dont_write_bytecode=True
def forbidden_provider(*a,**k):raise RuntimeError('LLM helper is outside component protocol')
def execute(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
@lru_cache(None)
def native(system):
 sources()
 if system=='jitrl':
  path=UPSTREAM/'jitrl/Jericho/src'
  pkg=types.ModuleType('mv_jitrl');pkg.__path__=[str(path)];sys.modules[pkg.__name__]=pkg
  helper=types.ModuleType('mv_jitrl.openai_helpers');helper.claude_completion_with_retries=forbidden_provider
  sys.modules[helper.__name__]=helper
  return execute('mv_jitrl.prompt_update_with_history',path/'prompt_update_with_history.py')
 names=['memos','memos.mem_os','memos.mem_os.main'];old={n:sys.modules.get(n) for n in names}
 try:
  for n in names:
   m=types.ModuleType(n);m.__path__=[];sys.modules[n]=m
  sys.modules[names[-1]].MOS=type('MOSImportBoundary',(),{})
  return execute('mv_memrl',UPSTREAM/'memrl/memrl/service/value_driven.py')
 finally:
  for n in names:
   if old[n] is None:sys.modules.pop(n,None)
   else:sys.modules[n]=old[n]
class Item:
 def __init__(self,id,memory,metadata):self.id=id;self.memory=memory;self.metadata=metadata
class Store:
 def __init__(self):self.items={}
 def get(self,id):return self.items[id]
 def update(self,id,payload):self.items[id]=Item(id,payload['memory'],payload['metadata'])
class MOSBoundary:
 def __init__(self):self.mem_cubes={'audit':types.SimpleNamespace(text_mem=Store())}
def create_bank(system,rows):
 n=native(system)
 if system=='jitrl':
  return [{'episode_id':r['id'],'final_score':r['outcome'],'success':bool(r['outcome']),
           'steps':[{'state':r['state'],'action':r['action'],'reward':r['outcome']}]} for r in rows]
 mos=MOSBoundary();store=mos.mem_cubes['audit'].text_mem;cfg=n.RLConfig(epsilon=0.0)
 updater=n.QValueUpdater(mos,'audit',cfg,default_cube_id='audit')
 for r in rows:
  store.items[r['id']]=Item(r['id'],f"state={r['state']} action={r['action']} outcome={r['outcome']}",{'state':r['state'],'action':r['action']})
  updater.update(r['id'],cfg.success_reward if r['outcome'] else cfg.failure_reward)
 return [{'memory_id':r['id'],'state':r['state'],'action':r['action'],
          'metadata':dict(store.items[r['id']].metadata),'similarity':.5} for r in rows]
def select(system,bank,seed,k=20):
 items=list(bank);random.Random(seed).shuffle(items);n=native(system)
 if system=='jitrl':return n.get_top_episodes(items,top_k=k)
 random.seed(seed)
 return n.ValueAwareSelector(n.RLConfig(epsilon=0)).select(items,top_k=k)['selected']
def action(system,x):return x['steps'][0]['action'] if system=='jitrl' else x['metadata']['action']
def identity(system,x):return x['episode_id'] if system=='jitrl' else x['memory_id']
def support(system,selected):
 return {a:F(sum(action(system,x)==a for x in selected),len(selected)) for a in ('A','B')}
def provenance():
 out={}
 for s in ('jitrl','memrl'):
  n=native(s);fs=[n.get_top_episodes] if s=='jitrl' else [n.QValueUpdater.update,n.ValueAwareSelector.select]
  out[s]=[{'file':inspect.getsourcefile(f),'symbol':f.__qualname__,'line':f.__code__.co_firstlineno,
           'sha256':sha(__import__('pathlib').Path(inspect.getsourcefile(f)).read_bytes())} for f in fs]
 return out
def reproduce():
 from build_worlds import generate
 from config import ready
 ready();out={}
 for s in ('jitrl','memrl'):
  old=[json.loads(l) for l in (OLD41/f'results/{s}_native_raw.jsonl').read_text().splitlines()]
  ix={(r['policy'],r['seed']):r for r in old if r['gamma']=='0.95' and r['k']==20}
  result={};records=[];identical=True
  for p in ('P','Q'):
   bank=create_bank(s,generate('A','0.95',p))
   for seed in SEEDS:
    ret=select(s,bank,seed);u=support(s,ret);result[p,seed]=u
    ids=[identity(s,x) for x in ret];oldids=[x['id'] for x in ix[p,seed]['parsed_selection']]
    identical &= ids==oldids
    records.append({'policy':p,'seed':seed,'native_selected':ret,'support':{a:str(v) for a,v in u.items()}})
  rev=[];rcd=[]
  for seed in SEEDS:
   p,q=result['P',seed],result['Q',seed];sp=p['A']-p['B'];sq=q['A']-q['B']
   rev.append(sp>F(1,10) and sq<-F(1,10));rcd.append(abs(p['A']-q['A']))
  rate=sum(rev)/20;med=statistics.median(rcd)
  out[s]={'reversal_rate':rate,'median_native_RCD':float(med),'stage41_selected_ids_identical':identical,
          'pass':rate>=.8 and med>=F(3,10) and identical,'records':records}
 passed=all(d['pass'] for d in out.values())
 save(ROOT/'results/native_reproduction.json',{'pass':passed,'systems':out,'provenance':provenance(),
      'M0_utility_semantics':'selection support f_A/f_B, not success probability'})
 if not passed:raise RuntimeError('G0 FAIL: STOP before candidate experiment')
 return passed
if __name__=='__main__':print('G0',reproduce())
