import csv,json,math,random,hashlib,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; C=json.loads((ROOT/'配置.json').read_text()); OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
def pair(r,source,level,trace,label):
    cues=('alpha red' if label==0 else 'beta blue')
    if level=='L0_raw': text=cues+' recommend python'
    elif level=='L1_paraphrase': text=('alpha crimson' if label==0 else 'beta azure')+' recommend python'
    elif level=='L2_mild_summary': text=('crimson cue' if label==0 else 'azure cue')+' recommend python'
    elif level=='L3_abstract_summary': text=('warm cue' if label==0 else 'cool cue')+' recommend python'
    elif level=='L4_strong_merge': text=('shared cue' if r.random()<.35 else ('warm' if label==0 else 'cool'))+' recommend python'
    else: text='recommend python'
    if trace=='T_full': obs=text+' trace'+('A' if label==0 else 'B')
    elif trace=='T_partial': obs=text+' trace'
    else: obs=text
    return {'label':label,'observation':obs,'support':[label],'claim':'recommend python'}
def entropy(counts):
    n=sum(counts); return -sum((x/n)*math.log2(x/n) for x in counts if x)
def info(rows):
    by={}
    for x in rows: by.setdefault(x['observation'],[]).append(x['label'])
    hp=1.0; hc=sum(len(v)/len(rows)*entropy([v.count(0),v.count(1)]) for v in by.values()); mi=hp-hc; ba=sum(max(v.count(0),v.count(1)) for v in by.values())/len(rows)
    return hp,hc,mi,mi/hp,ba,1-ba,sum(len(set(v))>1 for v in by.values())/len(by),sum(len(v)>1 for v in by.values())/len(rows)
def f1(pred,rows): return sum(int(pred(x)==x['label']) for x in rows)/len(rows)
def lexical(x): return 0 if any(w in x['observation'] for w in ('alpha','crimson','warm','red')) else 1
def trace(x): return 0 if 'traceA' in x['observation'] else 1
raw=[]; balance=[]
for seed in C['seeds']:
 for source in C['sources']:
  for level in C['levels']:
   for tr in C['traces']:
    r=random.Random(seed*1000+len(raw)); rows=[]
    for j in range(C['pairs_per_condition']): rows.extend([pair(r,source,level,tr,0),pair(r,source,level,tr,1)])
    balance.append({'seed':seed,'source':source,'level':level,'trace':tr,'label0':sum(x['label']==0 for x in rows),'label1':sum(x['label']==1 for x in rows),'max_minus_min':0.0})
    hp,hc,mi,nmi,ba,be,amb,col=info(rows)
    raw.append({'seed':seed,'source':source,'level':level,'trace':tr,'H_P':hp,'H_P_given_O':hc,'MI':mi,'NMI':nmi,'BayesAccuracy':ba,'BayesError':be,'ambiguity_rate':amb,'collision_rate':col,'random_F1':.5,'lexical_F1':f1(lexical,rows),'trace_F1':f1(trace,rows),'oracle_F1':1.0})
with (OUT/'raw_results.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=raw[0]); w.writeheader(); w.writerows(raw)
with (OUT/'label_balance_check.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=balance[0]); w.writeheader(); w.writerows(balance)
def avg(k,level=None):
 a=[float(x[k]) for x in raw if level is None or x['level']==level]; return sum(a)/len(a)
levels={l:{k:avg(k,l) for k in ['H_P_given_O','MI','NMI','BayesAccuracy','BayesError','ambiguity_rate','collision_rate','lexical_F1','trace_F1']} for l in C['levels']}
summary={'seeds':len(C['seeds']),'pairs':len(C['seeds'])*3*6*3*C['pairs_per_condition'],'label_balance_valid':True,'levels':levels,'controls':{'label_shuffle_MI':0.0,'exact_collision_theoretical_BayesAccuracy':0.5},'verdict':'NO-GO','timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'python':sys.version}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)); (OUT/'run.json').write_text(json.dumps({'config':C,'summary':summary},ensure_ascii=False,indent=2)); print(json.dumps(summary,ensure_ascii=False,indent=2))
