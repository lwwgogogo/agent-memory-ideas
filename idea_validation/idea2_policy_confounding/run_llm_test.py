import json,math,random,time,datetime,sys,subprocess
import requests
from common import ROOT,CONDITIONS,ensure_environment,save_json,digest
from generate_cases import make_prompt
MODEL='qwq:32b'
OPTIONS={'temperature':0,'seed':20261004,'num_ctx':4096,'num_predict':768}
SYSTEM='请判断虚构系统的未来成功概率。只能输出一个 JSON 对象，包含 p_success_A、p_success_B、choice、confidence、reason。两个 p_success 分别对应提示中 Action A 和 Action B 的未来成功概率。choice 可以是 A、B 或 TIE；confidence 是你对该选择的把握程度，取 0 到 1。不要将 confidence 当作成功率。reason 用一句简短中文解释。'
SCHEMA={'type':'object','properties':{'p_success_A':{'type':'number','minimum':0,'maximum':1},'p_success_B':{'type':'number','minimum':0,'maximum':1},'choice':{'type':'string','enum':['A','B','TIE']},'confidence':{'type':'number','minimum':0,'maximum':1},'reason':{'type':'string'}},'required':['p_success_A','p_success_B','choice','confidence','reason'],'additionalProperties':False}

def parse(raw):
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise ValueError('duplicate key')
            d[k]=v
        return d
    x=json.loads(raw,object_pairs_hook=unique)
    if not isinstance(x,dict) or set(x)!=set(SCHEMA['required']):raise ValueError('fields')
    for key in ['p_success_A','p_success_B','confidence']:
        if type(x[key]) not in [float,int] or not math.isfinite(x[key]) or not 0<=x[key]<=1:raise ValueError('probability')
    if x['choice'] not in ['A','B','TIE'] or not isinstance(x['reason'],str) or not x['reason'].strip():raise ValueError('choice/reason')
    return x

def normalized_bias(parsed,swap):return (parsed['p_success_A']-parsed['p_success_B'])*(-1 if swap else 1)

def main():
    ensure_environment()
    if json.loads((ROOT/'results/math_gate.json').read_text())['gate']!='PHASE_A_GO':raise RuntimeError('Math gate failed')
    cases=json.loads((ROOT/'cases/cases.json').read_text())
    config={'model':MODEL,'options':OPTIONS,'schema':SCHEMA,'system':SYSTEM,'endpoint':'http://127.0.0.1:11434/api/chat','order_seeds':[17,43],'label_swaps':[0,1],'job_order_seed':20261005,'planned_calls':400,'case_sha256':digest(ROOT/'cases/cases.json'),'protocol_sha256':digest(ROOT/'README.md'),'python':sys.executable,'version':sys.version,'source_sha256':{f.name:digest(f) for f in ROOT.glob('*.py')}}
    config_path=ROOT/'results/config.json'
    if config_path.exists():
        old=json.loads(config_path.read_text())
        if old!=config:raise RuntimeError('Resume configuration differs; refusing mixed protocol')
    else:save_json(config_path,config)
    out=ROOT/'results/llm_results.json';rows=json.loads(out.read_text()) if out.exists() else []
    completed={(r['case_id'],r['condition'],r['label_swap'],r['order_seed']) for r in rows}
    jobs=[(c,v,n) for c in cases for v in c['variants'] for n in CONDITIONS];random.Random(20261005).shuffle(jobs)
    session=requests.Session();session.trust_env=False
    for c,v,name in jobs:
        key=(c['id'],name,v['label_swap'],v['order_seed'])
        if key in completed:continue
        prompt=make_prompt(c,v,name)
        row={'case_id':c['id'],'family':c['family'],'gamma':c['gamma'],'condition':name,'label_swap':v['label_swap'],'order_seed':v['order_seed'],'prompt':prompt,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        start=time.time()
        try:
            response=session.post(config['endpoint'],json={'model':MODEL,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],'format':SCHEMA,'options':OPTIONS,'stream':False,'keep_alive':'10m'},timeout=(10,240))
            response.raise_for_status();data=response.json();row['raw']=data.get('message',{}).get('content','');row['provider_metadata']={k:val for k,val in data.items() if k!='message'}
            if data.get('message',{}).get('thinking'):row['provider_thinking']=data['message']['thinking']
            try:
                x=parse(row['raw']);row['parsed']=x;row['status']='OK';row['miab']=normalized_bias(x,v['label_swap'])
                row['choice_probability_consistent']=(x['choice']=='TIE' and abs(x['p_success_A']-x['p_success_B'])<1e-9) or (x['choice']=='A' and x['p_success_A']>=x['p_success_B']) or (x['choice']=='B' and x['p_success_B']>=x['p_success_A'])
            except (ValueError,TypeError,KeyError) as error:row['status']='UNRESOLVED';row['parse_error']=str(error)
        except requests.RequestException as error:row['status']='UNRESOLVED';row['transport_error']=str(error)
        row['elapsed_seconds']=time.time()-start;rows.append(row);save_json(out,rows)
        print(len(rows),c['id'],name,'swap',v['label_swap'],'order',v['order_seed'],row['status'],row.get('miab'),round(row['elapsed_seconds'],2),flush=True)
if __name__=='__main__':main()
