import pathlib,sys,json,subprocess,datetime
import requests
from core import ROOT,MODEL,OPTIONS,SYSTEM,SCHEMA,ensure_env,save,sha,parse

def main():
    ensure_env()
    test=subprocess.run([sys.executable,'-m','pytest','-q','tests'],cwd=ROOT,text=True,capture_output=True)
    (ROOT/'results/pytest_output.txt').write_text(test.stdout+test.stderr)
    source={str(f.relative_to(ROOT)):sha(f) for f in ROOT.rglob('*.py')}
    save(ROOT/'results/tests.json',{'returncode':test.returncode,'source_sha256':source,'python':sys.executable,'version':sys.version,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print(test.stdout,flush=True)
    if test.returncode:raise SystemExit(test.returncode)
    path=ROOT/'results/capability_probe.json'
    if not path.exists():
        session=requests.Session();session.trust_env=False
        environment={'python':sys.executable,'version':sys.version,'git_start':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'ollama_version':session.get('http://127.0.0.1:11434/api/version',timeout=10).json(),'models':session.get('http://127.0.0.1:11434/api/tags',timeout=10).json(),'gpu_before':subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,memory.used,utilization.gpu','--format=csv'],text=True)}
        assert any(m['name']==MODEL for m in environment['models']['models'])
        save(ROOT/'results/environment.json',environment)
        prompt='这是输出格式协议测试，不是研究场景。请返回 Left 成功概率 0.25、Right 成功概率 0.75，严格使用指定的两个字段和 0 到 1 的小数。'
        payload={'model':MODEL,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],'format':SCHEMA,'options':OPTIONS,'stream':False,'keep_alive':'10m'}
        attempts=[];mode='schema'
        response=session.post('http://127.0.0.1:11434/api/chat',json=payload,timeout=(10,180))
        attempts.append({'format':mode,'http_status':response.status_code,'response':response.text})
        if response.status_code==400 and ('schema' in response.text.lower() or 'format' in response.text.lower()):
            mode='json';payload['format']='json';response=session.post('http://127.0.0.1:11434/api/chat',json=payload,timeout=(10,180));attempts.append({'format':mode,'http_status':response.status_code,'response':response.text})
        supported=False;error=None
        try:response.raise_for_status();parsed=parse(response.json()['message']['content']);supported=True
        except (ValueError,KeyError,requests.RequestException) as e:error=str(e)
        save(path,{'supported':supported,'format':mode,'attempts':attempts,'semantic_prompt':prompt,'model':MODEL,'options':OPTIONS,'schema':SCHEMA,'error':error,'excluded_from_experiment':True})
    result=json.loads(path.read_text());print('Format support:',result['supported'],result['format'],flush=True)
    if not result['supported']:raise SystemExit('Format capability probe failed; no formal inference')
if __name__=='__main__':main()
