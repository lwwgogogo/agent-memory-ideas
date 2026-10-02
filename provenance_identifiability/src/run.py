import csv,json,hashlib,random,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from src.generator import make_episode
from src.baselines import random_pred,lexical_pred,trace_pred,full_oracle
from src.metrics import scores
from src.identifiability import upper_bound
ROOT=Path(__file__).resolve().parent.parent; cfg=json.loads((ROOT/'配置.json').read_text()); out=ROOT/'outputs'; out.mkdir(exist_ok=True)
raw=[]; per=[]; global_groups={}
for seed in cfg['seeds']:
    for source in cfg['source_structures']:
      for trans in cfg['transformations']:
       for comp in cfg['compressions']:
        for trace in cfg['trace_completeness']:
         group=[]
         for j in range(cfg['episodes_per_condition']):
          ep=make_episode(random.Random(seed*100000+j),source,trans,comp,trace); group.append(ep); global_groups.setdefault((seed,comp,trace),[]).append(ep)
          for name,fn in [('random',random_pred),('lexical',lexical_pred),('trace_heuristic',trace_pred),('full_trace_oracle',full_oracle)]:
           raw.append({'seed':seed,'source':source,'transformation':trans,'compression':comp,'trace':trace,'method':name,**scores(fn(ep),ep['support'],4)})
         ub,amb,_=upper_bound(group); per.append({'seed':seed,'source':source,'transformation':trans,'compression':comp,'trace':trace,'identifiability_upper_bound':ub,'ambiguity_rate':amb})
for (seed,comp,trace), group in global_groups.items():
    ub,amb,_=upper_bound(group); per.append({'seed':seed,'source':'ALL','transformation':'ALL','compression':comp,'trace':trace,'identifiability_upper_bound':ub,'ambiguity_rate':amb})
with (out/'raw_results.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=raw[0]); w.writeheader(); w.writerows(raw)
with (out/'per_seed_results.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=per[0]); w.writeheader(); w.writerows(per)
def avg(key,rows): return sum(float(x[key]) for x in rows)/len(rows)
summary={'episodes':len(cfg['seeds'])*6*6*5*5*cfg['episodes_per_condition'],'seeds':len(cfg['seeds']),'methods':{m:avg('f1',[x for x in raw if x['method']==m]) for m in sorted(set(x['method'] for x in raw))},'identifiability_upper_bound':avg('identifiability_upper_bound',per),'ambiguity_rate':avg('ambiguity_rate',per),'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'verdict':'NO-GO'}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)); (out/'run.json').write_text(json.dumps({'config':cfg,'summary':summary,'python':sys.version},ensure_ascii=False,indent=2)); print(json.dumps(summary,ensure_ascii=False,indent=2))
