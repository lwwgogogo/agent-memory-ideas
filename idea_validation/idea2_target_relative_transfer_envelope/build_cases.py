"""Private deterministic generator. Never copied into candidate directory."""
import json
from pathlib import Path
from fractions import Fraction

BASE_SOURCE=((20,20),(80,20),(50,80))
P4_IN=((30,40),(70,40),(50,70))
P4_OUT=((30,50),(10,90),(10,10))
CASES=(
("P1","IN",BASE_SOURCE,(50,40)),("P1","OUT",BASE_SOURCE,(50,95)),
("P2","IN",BASE_SOURCE,(50,40)),("P2","OUT",BASE_SOURCE,(50,95)),
("P3","IN",BASE_SOURCE,(50,40)),("P3","OUT",BASE_SOURCE,(50,95)),
("P4","IN",P4_IN,(50,50)),("P4","OUT",P4_OUT,(50,50)))

def source_records(points):
    rows=[]
    for i,point in enumerate(points):
        for si,percent in enumerate(point):
            for action,n,numerator in (("A",percent*10,4),("B",1000-percent*10,2)):
                successes=Fraction(n*numerator,5)
                if successes.denominator!=1: raise ValueError("noninteger cell")
                for j in range(n):
                    rows.append(dict(era_id=f"e{i:03d}",state=f"S{si}",action=action,outcome=int(j<successes)))
    return rows

def target_records(point):
    return [{"state":f"S{si}","action":action}
            for si,percent in enumerate(point)
            for action,n in (("A",percent*10),("B",1000-percent*10))
            for _ in range(n)]

def encode(rows):
    return "".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in rows).encode()

def build(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for i,(pair,side,source,target) in enumerate(CASES,1):
        tag=f"case_{i:03d}"
        sf=output/(tag+"_source.jsonl");tf=output/(tag+"_target.jsonl")
        sf.write_bytes(encode(source_records(source)));tf.write_bytes(encode(target_records(target)))
        manifest.append(dict(anonymous_id=tag,pair=pair,side=side,
                             source_file=sf.name,target_file=tf.name,
                             construction_source_percent=source,construction_target_percent=target))
    return manifest
