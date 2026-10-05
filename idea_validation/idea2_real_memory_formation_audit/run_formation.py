from __future__ import annotations
import datetime, json, sys, time
from pathlib import Path
import requests
from core import ROOT, WRITERS, OPTIONS_WRITER, FORMATION_TYPES, FORMATION_SCHEMA, FORMATION_SYSTEM, formation_prompt, valid_formation, load_source, save, sha, verify_frozen

def call(session, model, prompt):
    t=time.time()
    try:
        response=session.post("http://127.0.0.1:11434/api/chat",json={"model":model,"messages":[{"role":"system","content":FORMATION_SYSTEM},{"role":"user","content":prompt}],"format":FORMATION_SCHEMA,"options":OPTIONS_WRITER,"stream":False,"keep_alive":"10m"},timeout=(10,240))
        response.raise_for_status(); data=response.json()
        return {"raw":data.get("message",{}).get("content",""),"provider_metadata":{k:v for k,v in data.items() if k!="message"},"elapsed_seconds":time.time()-t,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    except requests.RequestException as e:
        return {"transport_error":repr(e),"elapsed_seconds":time.time()-t,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat()}

def main():
    tier=sys.argv[1] if len(sys.argv)>1 else "primary"
    if tier not in WRITERS: raise ValueError(tier)
    verify_frozen()
    cfg=json.loads((ROOT/"results"/"config.json").read_text())
    tests=json.loads((ROOT/"results"/"tests.json").read_text())
    assert tests["returncode"]==0
    for n,h in tests["source_sha256"].items(): assert sha(ROOT/n)==h,n
    worlds=load_source()["worlds"]; model=WRITERS[tier]
    jobs=[{"run_id":f"{tier}:{w['world_id']}:{f}","writer":tier,"model":model,"world_id":w["world_id"],"pair_id":w["pair_id"],"formation_type":f,"prompt":formation_prompt(w,f,cfg["memory_budget"])} for w in worlds for f in FORMATION_TYPES]
    out=ROOT/"results"/f"formation_{tier}.json"
    records=json.loads(out.read_text()) if out.exists() else []
    done={x["run_id"] for x in records}
    journal=ROOT/"results"/"formation_raw.jsonl"
    events=[json.loads(x) for x in journal.read_text().splitlines() if x] if journal.exists() else []
    starts={(x["run_id"],x["attempt"]) for x in events if x["event"]=="started"}
    results={(x["run_id"],x["attempt"]):x["response"] for x in events if x["event"]=="completed"}
    session=requests.Session();session.trust_env=False
    def append(item):
        with journal.open("a",encoding="utf-8") as f:f.write(json.dumps(item,ensure_ascii=False,allow_nan=False)+"\n");f.flush()
    for i,job in enumerate(jobs,1):
        if job["run_id"] in done:continue
        attempts=[]
        for attempt in [0,1]:
            key=(job["run_id"],attempt)
            if key in results:resp=results[key]
            elif key in starts:resp={"transport_error":"INTERRUPTED_REQUEST_OUTCOME_UNKNOWN; no reissue"}
            else:
                append({"event":"started","run_id":job["run_id"],"attempt":attempt,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"model":model,"condition":job["formation_type"],"world_id":job["world_id"],"request_metadata":{"options":OPTIONS_WRITER,"schema":FORMATION_SCHEMA,"prompt":job["prompt"]}})
                starts.add(key);resp=call(session,model,job["prompt"])
            parsed=None
            if "raw" in resp:
                try:parsed=json.loads(resp["raw"])
                except Exception:pass
            is_valid=valid_formation(parsed,cfg["memory_budget"])
            resp={**resp,"parsed":parsed,"valid":is_valid}
            append({"event":"completed","run_id":job["run_id"],"attempt":attempt,"response":resp,"model":model,"condition":job["formation_type"],"world_id":job["world_id"]})
            results[key]=resp;attempts.append(resp)
            if is_valid or "transport_error" in resp:break
        first=attempts[0]; last=attempts[-1]
        rec={**{k:v for k,v in job.items() if k!="prompt"},"prompt":job["prompt"],"first_attempt":first,"retry_attempt":attempts[1] if len(attempts)>1 else None,"final_status":"VALID" if last["valid"] else "INVALID","memory":last["parsed"]["memory"] if last.get("valid") else None,"memory_char_length":len(last["parsed"]["memory"]) if last.get("valid") else None}
        records.append(rec);save(out,records);done.add(job["run_id"])
        if rec["final_status"]=="VALID":
            safe_name=job["formation_type"]+"_"+job["world_id"]+".json"
            save(ROOT/"memories"/tier/safe_name,{"run_id":rec["run_id"],"world_id":rec["world_id"],"pair_id":rec["pair_id"],"formation_type":rec["formation_type"],"model":model,"memory":rec["memory"],"memory_char_length":rec["memory_char_length"]})
        print(f"{tier} {i}/160 {job['run_id']} {rec['final_status']} retry={len(attempts)>1}",flush=True)

if __name__=="__main__":main()
