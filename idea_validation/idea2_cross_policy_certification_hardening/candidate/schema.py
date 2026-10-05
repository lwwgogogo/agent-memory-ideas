import json
import re

FIELDS = frozenset({"era_id","state","action","outcome"})

def validate(record):
    if type(record) is not dict or set(record)!=FIELDS:
        raise ValueError("record fields must exactly match the whitelist")
    if type(record["era_id"]) is not str or re.fullmatch(r"e[0-9]{3,}",record["era_id"]) is None:
        raise ValueError("era identifier must be anonymous")
    if record["state"] not in ("S0","S1") or record["action"] not in ("A","B"):
        raise ValueError("unsupported observation category")
    if type(record["outcome"]) is not int or record["outcome"] not in (0,1):
        raise ValueError("outcome must be an integer zero or one")

def unique_object(items):
    out={}
    for key,value in items:
        if key in out:
            raise ValueError("duplicate field")
        out[key]=value
    return out

def read_records(path):
    count=0
    with open(path,encoding="utf-8") as f:
        for line in f:
            record=json.loads(line,object_pairs_hook=unique_object)
            validate(record); count+=1
            yield record
    if count==0:
        raise ValueError("empty observations")
