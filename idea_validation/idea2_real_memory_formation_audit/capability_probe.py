from __future__ import annotations
import datetime,json,time,sys
import requests
from core import (ROOT,PRIMARY_WRITER,SECONDARY_WRITER,READER,OPTIONS_WRITER,OPTIONS_AUDIT,OPTIONS_READER,
                  FORMATION_SYSTEM,FORMATION_SCHEMA,FAITHFUL_SYSTEM,FAITHFUL_SCHEMA,RECOVERY_SYSTEM,RECOVERY_SCHEMA,
                  DOWNSTREAM_SYSTEM,DOWNSTREAM_SCHEMA,valid_formation,valid_faithfulness,valid_recovery,valid_downstream,save)
PROBES=[
("formation_primary",PRIMARY_WRITER,FORMATION_SYSTEM,FORMATION_SCHEMA,OPTIONS_WRITER,"Return a brief format-only test memory."),
("faithfulness_A",SECONDARY_WRITER,FAITHFUL_SYSTEM,FAITHFUL_SCHEMA,OPTIONS_AUDIT,"Return a schema-only probe with all four booleans false."),
("faithfulness_B",PRIMARY_WRITER,FAITHFUL_SYSTEM,FAITHFUL_SCHEMA,OPTIONS_AUDIT,"Return a schema-only probe with all four booleans false."),
("recovery_reader",READER,RECOVERY_SYSTEM,RECOVERY_SCHEMA,OPTIONS_READER,"Return null for every recovery field."),
("downstream_reader",READER,DOWNSTREAM_SYSTEM,DOWNSTREAM_SCHEMA,OPTIONS_READER,"Return p_success_left=0.25 and p_success_right=0.75.")
]
def valid(kind,x):
    return {"formation":valid_formation,"faithfulness":valid_faithfulness,"recovery":valid_recovery,"downstream":valid_downstream}[kind](x,512) if kind=="formation" else {"faithfulness":valid_faithfulness,"recovery":valid_recovery,"downstream":valid_downstream}[kind](x)
def main():
    session=requests.Session();session.trust_env=False;results=[]
    for name,model,system,schema,options,prompt in PROBES:
        t=time.time();row={"probe":name,"model":model,"options":options,"schema":schema,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"excluded_from_research":True}
        try:
            r=session.post("http://127.0.0.1:11434/api/chat",json={"model":model,"messages":[{"role":"system","content":system},{"role":"user","content":prompt}],"format":schema,"options":options,"stream":False},timeout=(10,240))
            r.raise_for_status();d=r.json();raw=d.get("message",{}).get("content","");parsed=json.loads(raw)
            kind="formation" if name.startswith("formation") else ("faithfulness" if name.startswith("faithfulness") else ("recovery" if name.startswith("recovery") else "downstream"))
            row.update(raw=raw,parsed=parsed,supported=valid(kind,parsed),provider_metadata={k:v for k,v in d.items() if k!="message"})
        except Exception as e:row.update(supported=False,error=repr(e))
        row["elapsed_seconds"]=time.time()-t;results.append(row);print(name,row["supported"],flush=True)
    save(ROOT/"results"/"capability_probes.json",results)
    if not all(x["supported"] for x in results):raise SystemExit("required schema probe failed")
if __name__=="__main__":main()
