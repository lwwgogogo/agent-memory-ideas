import json
import re
from collections import Counter

SOURCE_FIELDS=frozenset({"era_id","state","action","outcome"})
TARGET_FIELDS=frozenset({"state","action"})

def validate(record, source):
    fields=SOURCE_FIELDS if source else TARGET_FIELDS
    if type(record) is not dict or set(record)!=fields:
        raise ValueError("fields must exactly match whitelist")
    if type(record["state"]) is not str or record["state"] not in ("S0","S1"):
        raise ValueError("state")
    if type(record["action"]) is not str or record["action"] not in ("A","B"):
        raise ValueError("action")
    if source:
        if type(record["era_id"]) is not str or re.fullmatch(r"e[0-9]{3,}",record["era_id"]) is None:
            raise ValueError("anonymous era required")
        if type(record["outcome"]) is not int or record["outcome"] not in (0,1):
            raise ValueError("binary integer outcome required")

def unique_object(items):
    result={}
    for k,v in items:
        if k in result: raise ValueError("duplicate JSON field")
        result[k]=v
    return result

def read_records(path, source):
    rows=[]
    with open(path,encoding="utf-8") as f:
        for line in f:
            row=json.loads(line,object_pairs_hook=unique_object)
            validate(row,source);rows.append(row)
    validate_counts(rows,source)
    return rows

def validate_counts(rows,source):
    if not rows: raise ValueError("empty data")
    counts=Counter()
    for r in rows:
        validate(r,source)
        counts[(r["era_id"] if source else "target",r["state"])]+=1
    eras={e for e,s in counts}
    if any(counts[(e,s)]!=1000 for e in eras for s in ("S0","S1")):
        raise ValueError("exactly 1000 observations per state required")
