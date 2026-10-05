import json,random,time,datetime,sys,subprocess
import requests
from core import ROOT,RUN1,MODEL,OPTIONS,SYSTEM,SCHEMA,ensure_env,save,sha,canonical,run_with_retry

def request_model(session,prompt,format_value):
    start=time.time()
    try:
        response=session.post('http://127.0.0.1:11434/api/chat',json={'model':MODEL,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],'format':format_value,'options':OPTIONS,'stream':False,'keep_alive':'10m'},timeout=(10,180))
        response.raise_for_status();data=response.json()
        return {'raw':data.get('message',{}).get('content',''),'provider_metadata':{k:v for k,v in data.items() if k!='message'},'elapsed_seconds':time.time()-start,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    except requests.RequestException as e:return {'transport_error':str(e),'elapsed_seconds':time.time()-start}

def main():
    ensure_env();tests=json.loads((ROOT/'results/tests.json').read_text())
    if tests['returncode']!=0:raise RuntimeError('Tests did not pass')
    for n,h in tests['source_sha256'].items():
        if sha(ROOT/n)!=h:raise RuntimeError('Code changed since tests: '+n)
    capability=json.loads((ROOT/'results/capability_probe.json').read_text())
    if not capability['supported']:raise RuntimeError('No valid structured JSON support')
    format_value=SCHEMA if capability['format']=='schema' else 'json'
    config={'model':MODEL,'options':OPTIONS,'system':SYSTEM,'format':format_value,'planned_runs':320,'retry_max':1,'job_order_seed':20261005,'case_sha256':sha(ROOT/'cases/cases.json'),'preregistration_sha256':sha(ROOT/'preregistration.md'),'source_sha256':tests['source_sha256'],'run1_cases_sha256':sha(RUN1/'cases/cases.json'),'python':sys.executable}
    cfg=ROOT/'results/config.json'
    if cfg.exists():
        if json.loads(cfg.read_text())!=config:raise RuntimeError('Frozen config mismatch')
    else:save(cfg,config)
    cases=json.loads((ROOT/'cases/cases.json').read_text());jobs=[(c,r) for c in cases for r in c['runs']];assert len(jobs)==320
    random.Random(20261005).shuffle(jobs)
    out=ROOT/'results/llm_results.json';results=json.loads(out.read_text()) if out.exists() else [];finished={r['run_id'] for r in results}
    journal=ROOT/'results/raw_outputs.jsonl';started=set();completed={}
    if journal.exists():
        for line in journal.read_text().splitlines():
            event=json.loads(line);key=(event['run_id'],event['attempt'])
            if event['event']=='started':started.add(key)
            else:completed[key]=event['response']
    session=requests.Session();session.trust_env=False
    def append(event):
        with journal.open('a',encoding='utf-8') as stream:stream.write(json.dumps(event,ensure_ascii=False,allow_nan=False)+'\n');stream.flush()
    for case,spec in jobs:
        if spec['run_id'] in finished:continue
        def invoke(semantic_prompt,index):
            key=(spec['run_id'],index)
            if key in completed:return completed[key]
            if key in started:
                response={'transport_error':'INTERRUPTED_REQUEST_OUTCOME_UNKNOWN; no reissue'}
            else:
                append({'event':'started','run_id':key[0],'attempt':index,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()});started.add(key)
                response=request_model(session,semantic_prompt,format_value)
            append({'event':'completed','run_id':key[0],'attempt':index,'response':response});completed[key]=response
            return response
        attempts=run_with_retry(spec['prompt'],invoke)
        row={**spec,'case_id':case['id'],'family':case['family'],'gamma':case['gamma'],**attempts}
        if row['final_status']=='VALID':
            a,b=canonical(row['parsed'],spec['version']);row.update(p_success_A=a,p_success_B=b,miab=a-b,offline_decision='A' if a>b else ('B' if b>a else 'TIE'))
        results.append(row);save(out,results);finished.add(spec['run_id'])
        print(len(results),spec['run_id'],row['final_status'],'retry',row['retry_attempt'] is not None,flush=True)
if __name__=='__main__':main()
