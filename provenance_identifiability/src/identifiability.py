from collections import defaultdict,Counter

def classes(rows):
    d=defaultdict(list)
    for x in rows:
        d[x['observation']].append(tuple(x['support']))
    return d

def upper_bound(rows):
    d=classes(rows); total=sum(len(v) for v in d.values()); correct=sum(Counter(v).most_common(1)[0][1] for v in d.values())
    amb=sum(len(set(v))>1 for v in d.values())/len(d) if d else 0
    return correct/total if total else 1.0,amb,d
