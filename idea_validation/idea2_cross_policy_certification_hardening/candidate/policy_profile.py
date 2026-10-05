from itertools import combinations
from statistics import median

def reconstruct(records):
    cells={}
    count=0
    for record in records:
        era=cells.setdefault(record["era_id"],{})
        state=era.setdefault(record["state"],{})
        cell=state.setdefault(record["action"],[0,0])
        cell[0]+=1; cell[1]+=record["outcome"]; count+=1
    if not cells:
        raise ValueError("empty observations")
    profiles={}; gaps={}
    for era in sorted(cells):
        states=cells[era]
        if set(states)!={"S0","S1"} or any(set(states[s])!={"A","B"} for s in states):
            raise ValueError("both states and actions must have exposure")
        profiles[era]={s:states[s]["A"][0]/sum(states[s][a][0] for a in ("A","B"))
                       for s in ("S0","S1")}
        rate={a:sum(states[s][a][1] for s in ("S0","S1"))/
                   sum(states[s][a][0] for s in ("S0","S1")) for a in ("A","B")}
        gaps[era]=rate["A"]-rate["B"]
    return cells,profiles,gaps,count

def distance(left,right):
    return sum(abs(left[s]-right[s]) for s in ("S0","S1"))/2

def pair_distances(profiles):
    return [(i,j,distance(profiles[i],profiles[j])) for i,j in combinations(sorted(profiles),2)]

def diversity(pairs):
    values=[p[2] for p in pairs]
    return {"D_policy":sum(values)/len(values) if values else 0.,
            "D_min":min(values) if values else 0.,
            "D_median":median(values) if values else 0.,
            "D_max":max(values) if values else 0.}
