from __future__ import annotations
import datetime,json,sys,time
from pathlib import Path
import requests
from core import ROOT,load_source,downstream_prompt,replace_action_labels,DOWNSTREAM_SCHEMA,DOWNSTREAM_SYSTEM,valid_downstream,save,verify_frozen

MODEL="qwq:32b"
OPTIONS={"temperature":0,"top_p":1.0,"seed":20261005,"num_ctx":8192,"num_predict":256}

def call(session,prompt):
    t=time.time()
    try:
        r=session.post("http://127.0.0.1:11434/api/chat",json={"model":MODEL,"messages":[{"role":"system","content":DOWNSTREAM_SYSTEM},{"role":"user","content":prompt}],"format":DOWNSTREAM_SCHEMA,"options":OPTIONS,"stream":False,"keep_alive":"10m"},timeout=(10,240))
        r.raise_for_status();d=r.json()
        return {"raw":d.get("message",{}).get("content",""),"metadata":{k:v for k,v in d.items() if k!="message"},"elapsed_seconds":time.time()-t,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    except requests.RequestException as e:return {"transport_error":repr(e),"elapsed_seconds":time.time()-t}

def main():
    verify_frozen()
    mode=sys.argv[1] if len(sys.argv)>1 else "controls"
    if mode=="controls":
        worlds=load_source()["worlds"];jobs=[]
        from core import oracle_summary,aggregate_summary
        for w in worlds:
            for c,render in [("C1_StatePreservingOracle",oracle_summary),("C2_FaithfulLossyAggregate",aggregate_summary)]:
                m=render(w)
                for version in ["AB","BA"]:
                    mem=replace_action_labels(m,version)
                    jobs.append({"run_id":f"downstream:{c}:{w['world_id']}:{version}","world_id":w["world_id"],"pair_id":w["pair_id"],"condition":c,"version":version,"writer":"deterministic","memory":mem,"prompt":downstream_prompt(mem)})
        output=ROOT/"results"/"downstream_controls.json"
    else:
        forms=json.loads((ROOT/"results"/f"formation_{mode}.json").read_text());jobs=[]
        for f in forms:
            if f["final_status"]!="VALID":continue
            for version in ["AB","BA"]:
                mem=replace_action_labels(f["memory"],version)
                jobs.append({"run_id":f"downstream:{f['run_id']}:{version}","world_id":f["world_id"],"pair_id":f["pair_id"],"condition":f["formation_type"],"version":version,"writer":mode,"formation_run_id":f["run_id"],"memory":mem,"prompt":downstream_prompt(mem)})
        output=ROOT/"results"/f"downstream_{mode}.json"
    results=json.loads(output.read_text()) if output.exists() else [];done={x["run_id"] for x in results}
    journal=ROOT/"results"/"downstream_raw.jsonl"
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
                append({"event":"started","run_id":j["run_id"],"attempt":attempt,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"model":MODEL,"condition":j["condition"],"world_id":j["world_id"],"request_metadata":{"options":OPTIONS,"schema":DOWNSTREAM_SCHEMA,"prompt":j["prompt"]}})
                started.add(key);r=call(session,j["prompt"])
            parsed=None
            if "raw" in r:
                try:parsed=json.loads(r["raw"])
                except Exception:pass
            valid=valid_downstream(parsed);r={**r,"parsed":parsed,"valid":valid}
            append({"event":"completed","run_id":j["run_id"],"attempt":attempt,"response":r,"model":MODEL,"condition":j["condition"],"world_id":j["world_id"]})
            completed[key]=r;at.append(r)
            if valid or "transport_error" in r:break
        last=at[-1];item={k:v for k,v in j.items() if k!="prompt"};item.update(prompt=j["prompt"],first_attempt=at[0],retry_attempt=at[1] if len(at)>1 else None,final_status="VALID" if last["valid"] else "INVALID",prediction=last.get("parsed"))
        results.append(item);save(output,results);done.add(j["run_id"])
        print(f"{mode} downstream {i}/{len(jobs)} {j['run_id']} {item['final_status']} retry={len(at)>1}",flush=True)
if __name__=="__main__":main()
