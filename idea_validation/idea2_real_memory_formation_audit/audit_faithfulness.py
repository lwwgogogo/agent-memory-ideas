from __future__ import annotations
import datetime,json,sys,time
from pathlib import Path
import requests
from core import ROOT,load_source,source_text,faithful_prompt,FAITHFUL_SCHEMA,FAITHFUL_SYSTEM,valid_faithfulness,save,sha,verify_frozen

AUDITORS={"A":"qwq:32b","B":"qwen2.5:14b"}
OPTIONS={"temperature":0,"top_p":1.0,"seed":20261005,"num_ctx":8192,"num_predict":512}

def call(session,model,prompt):
    t=time.time()
    try:
        r=session.post("http://127.0.0.1:11434/api/chat",json={"model":model,"messages":[{"role":"system","content":FAITHFUL_SYSTEM},{"role":"user","content":prompt}],"format":FAITHFUL_SCHEMA,"options":OPTIONS,"stream":False,"keep_alive":"10m"},timeout=(10,240))
        r.raise_for_status();d=r.json()
        return {"raw":d.get("message",{}).get("content",""),"metadata":{k:v for k,v in d.items() if k!="message"},"elapsed_seconds":time.time()-t,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    except requests.RequestException as e:return {"transport_error":repr(e),"elapsed_seconds":time.time()-t}

def main():
    verify_frozen()
    tier=sys.argv[1] if len(sys.argv)>1 else "primary"
    input_path=ROOT/"results"/f"formation_{tier}.json"
    formations=json.loads(input_path.read_text())
    worlds={w["world_id"]:w for w in load_source()["worlds"]}
    jobs=[]
    for f in formations:
        if f["final_status"]!="VALID":continue
        for auditor,model in AUDITORS.items():
            jobs.append({"run_id":f"audit:{tier}:{f['world_id']}:{f['formation_type']}:{auditor}","formation_run_id":f["run_id"],"writer":tier,"model":model,"auditor":auditor,"world_id":f["world_id"],"formation_type":f["formation_type"],"prompt":faithful_prompt(worlds[f["world_id"]],f["memory"])})
    output=ROOT/"results"/f"faithfulness_{tier}.json"
    results=json.loads(output.read_text()) if output.exists() else [];done={x["run_id"] for x in results}
    journal=ROOT/"results"/"faithfulness_raw.jsonl"
    ev=[json.loads(x) for x in journal.read_text().splitlines() if x] if journal.exists() else []
    started={(x["run_id"],x["attempt"]) for x in ev if x["event"]=="started"};completed={(x["run_id"],x["attempt"]):x["response"] for x in ev if x["event"]=="completed"}
    session=requests.Session();session.trust_env=False
    def append(x):
        with journal.open("a",encoding="utf-8") as f:f.write(json.dumps(x,ensure_ascii=False,allow_nan=False)+"\n");f.flush()
    for i,j in enumerate(jobs,1):
        if j["run_id"] in done:continue
        at=[]
        for attempt in [0,1]:
            key=(j["run_id"],attempt)
            if key in completed:r=completed[key]
            elif key in started:r={"transport_error":"INTERRUPTED_REQUEST_OUTCOME_UNKNOWN; no reissue"}
            else:
                append({"event":"started","run_id":j["run_id"],"attempt":attempt,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"model":j["model"],"condition":j["formation_type"],"world_id":j["world_id"],"request_metadata":{"options":OPTIONS,"schema":FAITHFUL_SCHEMA,"prompt":j["prompt"]}})
                started.add(key);r=call(session,j["model"],j["prompt"])
            parsed=None
            if "raw" in r:
                try:parsed=json.loads(r["raw"])
                except Exception:pass
            valid=valid_faithfulness(parsed)
            r={**r,"parsed":parsed,"valid":valid}
            append({"event":"completed","run_id":j["run_id"],"attempt":attempt,"response":r,"model":j["model"],"condition":j["formation_type"],"world_id":j["world_id"]})
            completed[key]=r;at.append(r)
            if valid or "transport_error" in r:break
        last=at[-1]
        item={k:v for k,v in j.items() if k!="prompt"};item.update(prompt=j["prompt"],first_attempt=at[0],retry_attempt=at[1] if len(at)>1 else None,final_status="VALID" if last["valid"] else "INVALID",audit=last.get("parsed"))
        results.append(item);save(output,results);done.add(j["run_id"])
        print(f"{tier} audit {i}/{len(jobs)} {j['run_id']} {item['final_status']} retry={len(at)>1}",flush=True)

if __name__=="__main__":main()
