import json,pathlib,random,time,urllib.request,hashlib,datetime
P=pathlib.Path(__file__).resolve().parent
MODEL='qwq:32b';SEEDS=[17,43]
SYSTEM='你正在参与虚构低风险情境的判断实验。只输出一个 JSON 对象，且恰好包含 choice、confidence、reason。choice 只能为 H1 或 H0。confidence 明确定义为 H1 成立的概率，范围为 0 到 1，并非所选选项的概率。概率不少于 0.5 时选 H1，否则选 H0。reason 用一句简短中文说明。'
OPTIONS={'temperature':0,'seed':20261004,'num_predict':768,'num_ctx':4096}
def request(prompt):
 payload={'model':MODEL,'system':SYSTEM,'prompt':prompt,'stream':False,'format':{'type': 'object', 'properties': {'choice': {'type': 'string', 'enum': ['H1', 'H0']}, 'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1}, 'reason': {'type': 'string'}}, 'required': ['choice', 'confidence', 'reason'], 'additionalProperties': False},'options':OPTIONS,'keep_alive':'10m'}
 req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=240) as r:return json.load(r)
def parse(raw):
 def unique(pairs):
  d={}
  for k,v in pairs:
   if k in d:raise ValueError('duplicate key')
   d[k]=v
  return d
 x=json.loads(raw,object_pairs_hook=unique)
 assert isinstance(x,dict) and set(x)=={'choice','confidence','reason'}
 assert x['choice'] in ['H0','H1'] and type(x['confidence']) in [float,int] and 0<=x['confidence']<=1
 assert isinstance(x['reason'],str) and x['reason'].strip()
 assert x['choice']==('H1' if x['confidence']>=.5 else 'H0')
 return x
if __name__=='__main__':
 assert json.loads((P/'results/math_gate.json').read_text())['gate']=='PHASE_A_GO'
 cases=json.loads((P/'cases/cases.json').read_text())
 out=P/'results/llm_results.json';results=json.loads(out.read_text()) if out.exists() else []
 completed={(r['case_id'],r['condition'],r['order_seed']) for r in results}
 jobs=[(c,name,s) for c in cases if c['audit']['status']=='NO_NEW_INFORMATION' for name in c['conditions'] for s in SEEDS]
 random.Random(905).shuffle(jobs)
 (P/'results/config.json').write_text(json.dumps({'model':MODEL,'format':'strict_json_schema','formal_run':True,'options':OPTIONS,'order_seeds':SEEDS,'job_order_seed':905,'system':SYSTEM,'confidence_semantics':'P(H1)','bootstrap_seed':20261004,'bootstrap_samples':10000},ensure_ascii=False,indent=2))
 for c,name,s in jobs:
  key=(c['id'],name,s)
  if key in completed:continue
  memories=c['conditions'][name][:];random.Random(s).shuffle(memories)
  provenance='以下五条 memory 均由同一个原始 observation 派生，不是五个独立信息源。\n' if name=='ProvenanceAware5' else ''
  independent='本模拟明确设定：下面三条记录的采集过程在给定 H1 或 H0 时相互独立。\n' if name=='Independent3' else ''
  prompt='这是虚构场景。H1：'+c['hypothesis']+'。H0：该假设不成立。先验 P(H1)=0.5。请结合记录估计 H1 的概率。\n'+provenance+independent+'记忆记录：\n'+'\n'.join(str(i+1)+'. '+m for i,m in enumerate(memories))
  row={'case_id':c['id'],'family':c['family'],'condition':name,'order_seed':s,'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'timestamp':datetime.datetime.utcnow().isoformat()+'Z'}
  start=time.time()
  try:
   response=request(prompt);row['raw']=response.get('response','');row['provider_metadata']={k:v for k,v in response.items() if k not in ['response','context']}
   try:row['parsed']=parse(row['raw']);row['status']='OK'
   except Exception as e:row['status']='UNRESOLVED';row['parse_error']=type(e).__name__
  except Exception as e:row['status']='UNRESOLVED';row['transport_error']=str(e)
  row['elapsed_seconds']=time.time()-start;results.append(row)
  temp=out.with_suffix('.tmp');temp.write_text(json.dumps(results,ensure_ascii=False,indent=2));temp.replace(out)
  print(len(results),c['id'],name,s,row['status'],row.get('parsed',{}).get('confidence'),round(row['elapsed_seconds'],1),flush=True)
