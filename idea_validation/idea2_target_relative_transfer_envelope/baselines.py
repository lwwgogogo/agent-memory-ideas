import hashlib
import json
from collections import Counter
from fractions import Fraction

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)
def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def m1(rows):
    stats={}
    for s in ("S0","S1"):
        for a in ("A","B"):
            cell=[r["outcome"] for r in rows if r["state"]==s and r["action"]==a]
            if not cell: raise ValueError("missing exposure")
            stats[s,a]=Fraction(sum(cell),len(cell))
    ua=sum((stats[s,"A"] for s in ("S0","S1")),Fraction(0))/2
    ub=sum((stats[s,"B"] for s in ("S0","S1")),Fraction(0))/2
    return {"U_A":str(ua),"U_B":str(ub),"gap":str(ua-ub)}

def source_summary(rows,global_result):
    utility=m1(rows)
    era_counts=dict(sorted(Counter(r["era_id"] for r in rows).items()))
    gaps=[]
    for e in era_counts:
        er=[r for r in rows if r["era_id"]==e]
        rates={a:Fraction(sum(r["outcome"] for r in er if r["action"]==a),
                          sum(r["action"]==a for r in er)) for a in ("A","B")}
        gaps.append(rates["A"]-rates["B"])
    mean=sum(gaps,Fraction(0))/len(gaps)
    variance=sum(((g-mean)**2 for g in gaps),Fraction(0))/len(gaps)
    return {"M1":utility,"total_observations":len(rows),"per_era_observation_counts":era_counts,
      "mean_era_gap":str(mean),"variance_era_gap":str(variance),
      "min_era_gap":str(min(gaps)),"max_era_gap":str(max(gaps)),
      "C_pos":global_result["C_pos"],"C_neg":global_result["C_neg"],
      "C_conflict":global_result["C_conflict"],"D_policy":global_result["D_policy"],
      "number_of_eras":len(era_counts),
      "effective_distinct_pairs":global_result["effective_distinct_policy_pairs"],
      "GlobalCertification":global_result["status"]}

def provenance(era_count):
    return {"source_type":"VERIFIED_RUNTIME_TRACE","trust_label":"VERIFIED",
            "validation_status":"SCHEMA_AND_COUNTS_VALIDATED","source_count":era_count,
            "era_count":era_count,"lineage_placeholder":"NOT_IMPLEMENTED"}

def baseline_outputs(summary,global_result,minimum_distance):
    invariant=(global_result["C_conflict"]==0 and
               len(set(global_result["sign_pattern"]))==1 and
               global_result["sign_pattern"][0] in ("+","-"))
    prov=provenance(summary["number_of_eras"])
    return {"B0":global_result["status"],"B1":"ALLOW" if invariant else "BLOCK",
            "B2":{"information_sha256":digest(summary),"decision":"NO_THRESHOLD_DEFINED"},
            "B3":{"information_sha256":digest(prov),"source_status":"VERIFIED_RUNTIME_TRACE"},
            "B4":{"nearest_TV_exact":str(minimum_distance),"decision":"NO_THRESHOLD_DEFINED"},
            "B5":summary["M1"]}
