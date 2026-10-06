"""Independent evaluator: rational affine feasibility, no scipy/candidate geometry."""
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

def exact_membership(points,target):
    points=[tuple(Fraction(x) for x in p) for p in points]
    target=tuple(Fraction(x) for x in target)
    # Caratheodory in R^2: any feasible point has a witness of <=3 vertices.
    for size in range(1,min(3,len(points))+1):
        for indices in itertools.combinations(range(len(points)),size):
            matrix=[[Fraction(1) for _ in indices]+[Fraction(1)]]
            matrix += [[points[i][d] for i in indices]+[target[d]] for d in range(2)]
            pivots=[];row=0
            for col in range(size):
                pivot=next((r for r in range(row,3) if matrix[r][col]),None)
                if pivot is None: continue
                matrix[row],matrix[pivot]=matrix[pivot],matrix[row]
                divisor=matrix[row][col]
                matrix[row]=[v/divisor for v in matrix[row]]
                for r in range(3):
                    if r!=row:
                        factor=matrix[r][col]
                        matrix[r]=[v-factor*w for v,w in zip(matrix[r],matrix[row])]
                pivots.append(col);row+=1
            if any(all(v==0 for v in r[:size]) and r[size]!=0 for r in matrix): continue
            if len(pivots)!=size: continue
            weights=[Fraction(0)]*size
            for r,c in enumerate(pivots): weights[c]=matrix[r][size]
            if all(w>=0 for w in weights):
                return {"inside":True,"indices":list(indices),"weights":[str(w) for w in weights]}
    return {"inside":False,"indices":None,"weights":None}

def independent_counts(rows,source):
    groups={}
    for r in rows:
        e=r["era_id"] if source else "target"
        state=groups.setdefault(e,{}).setdefault(r["state"],{"A":[0,0],"B":[0,0]})
        state[r["action"]][0]+=1
        if source: state[r["action"]][1]+=r["outcome"]
    vectors={}
    valid=bool(groups)
    for e,states in groups.items():
        valid &= set(states)=={"S0","S1"}
        vectors[e]=[]
        for s in ("S0","S1"):
            cells=states[s];n=sum(cells[a][0] for a in ("A","B"))
            valid &= n==1000
            vectors[e].append(str(Fraction(cells["A"][0],n)))
            if source:
                for a,num in (("A",4),("B",2)):
                    valid &= cells[a][0]>0 and cells[a][1]*5==cells[a][0]*num
    return valid,vectors

def paired_checks(rows):
    pairs={p:{r["side"]:r for r in rows if r["pair"]==p} for p in ("P1","P2","P3","P4")}
    output={}
    for p,rs in pairs.items():
        a,b=rs["IN"],rs["OUT"]
        oa,ob=a["probe"],b["probe"]
        sa,sb=oa["source_summary"],ob["source_summary"]
        output[p]={"source_sha_equal":a["source_sha256"]==b["source_sha256"],
          "global_equal":oa["global"]==ob["global"],
          "source_summary_sha_equal":oa["source_summary_sha256"]==ob["source_summary_sha256"],
          "source_summary_canonical_equal":sa==sb,
          "provenance_sha_equal":oa["provenance_summary_sha256"]==ob["provenance_summary_sha256"],
          "utility_equal":sa["M1"]==sb["M1"],
          "counts_equal":all(sa[k]==sb[k] for k in ("total_observations","per_era_observation_counts")),
          "variance_equal":sa["variance_era_gap"]==sb["variance_era_gap"],
          "agreement_equal":all(sa[k]==sb[k] for k in ("C_pos","C_neg","C_conflict")),
          "diversity_equal":sa["D_policy"]==sb["D_policy"],
          "B0_equal":oa["baselines"]["B0"]==ob["baselines"]["B0"],
          "B1_equal":oa["baselines"]["B1"]==ob["baselines"]["B1"],
          "B3_equal":oa["baselines"]["B3"]==ob["baselines"]["B3"],
          "min_distance_equal":Fraction(oa["target_min_TV_exact"])==Fraction(ob["target_min_TV_exact"]),
          "min_distance_tolerance":abs(oa["target_min_TV"]-ob["target_min_TV"])<=1e-12,
          "global_both_prescriptive":all(o["global"]["status"]=="PRESCRIPTIVE" for o in (oa,ob)),
          "exact_membership_pair":a["independent_geometry"]["inside"] and not b["independent_geometry"]["inside"],
          "hull_pair":oa["target_in_convex_hull"] and not ob["target_in_convex_hull"],
          "transfer_pair":oa["transfer_decision"]=="TRANSFERABLE" and ob["transfer_decision"]=="OUT_OF_ENVELOPE"}
    return output

def compute_gates(rows,checks,oracle_free,scope_ok,lock_ok):
    def allkeys(p,keys): return all(checks[p][k] for k in keys.split())
    m1=all(r["probe"]["source_summary"]["M1"]=={"U_A":"4/5","U_B":"2/5","gap":"2/5"} for r in rows)
    g={}
    g["G0"]=all(r["data_integrity"] and r["descriptors_match"] for r in rows) and lock_ok
    g["G1"]=all(r["global_equivalence"] and r["probe"]["global"]["status"]=="PRESCRIPTIVE" for r in rows)
    g["G2"]=allkeys("P1","source_sha_equal global_equal agreement_equal utility_equal B0_equal B1_equal exact_membership_pair hull_pair transfer_pair")
    g["G3"]=allkeys("P2","source_sha_equal provenance_sha_equal B3_equal exact_membership_pair transfer_pair")
    g["G4"]=allkeys("P3","source_summary_sha_equal source_summary_canonical_equal utility_equal counts_equal variance_equal agreement_equal diversity_equal transfer_pair")
    g["G5"]=allkeys("P4","min_distance_equal min_distance_tolerance global_both_prescriptive exact_membership_pair hull_pair transfer_pair")
    g["G6"]=m1 and checks["P1"]["transfer_pair"] and checks["P3"]["transfer_pair"]
    g["G7"]=oracle_free
    g["G8"]=all(allkeys(p,"source_sha_equal source_summary_sha_equal source_summary_canonical_equal transfer_pair") for p in ("P1","P3"))
    g["G9"]=scope_ok
    return g

def verdict(gates,requires_target_outcome=False):
    if requires_target_outcome: return "TARGET_RELATIVE_ENVELOPE_NO_GO"
    if all(gates.values()): return "TARGET_RELATIVE_ENVELOPE_GO"
    if not any(gates[k] for k in ("G2","G3","G4","G5","G8")):
        return "TARGET_RELATIVE_ENVELOPE_NO_GO"
    return "TARGET_RELATIVE_ENVELOPE_NARROW"
