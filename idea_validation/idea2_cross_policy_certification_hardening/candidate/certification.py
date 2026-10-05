def sign(value,epsilon):
    return int(value>epsilon)-int(value< -epsilon)

def lifecycle(eras,pairs,diversity,positive,negative,conflict,total,config):
    if total<=config["epsilon"]:
        return "DESCRIPTIVE"
    if (eras>=config["min_eras"] and pairs>=config["min_effective_pairs"]
        and diversity>=config["min_diversity"]
        and max(positive,negative)>=config["min_agreement"]
        and conflict<=config["max_conflict"]):
        return "PRESCRIPTIVE"
    return "PROVISIONAL"

def certify(profiles,gaps,pairs,diversity,config):
    total=pos=neg=conflict=0.
    epsilon=config["epsilon"]
    for i,j,weight in pairs:
        si=sign(gaps[i],epsilon); sj=sign(gaps[j],epsilon)
        total+=weight
        if si>0 and sj>0: pos+=weight
        elif si<0 and sj<0: neg+=weight
        elif si*sj<0: conflict+=weight
    if total<=epsilon: cp=cn=cc=0.
    else: cp,cn,cc=pos/total,neg/total,conflict/total
    effective=sum(weight>epsilon for _,_,weight in pairs)
    status=lifecycle(len(profiles),effective,diversity["D_policy"],cp,cn,cc,total,config)
    return {"C_pos":cp,"C_neg":cn,"C_conflict":cc,
        "effective_distinct_policy_pairs":effective,"status":status,
        "diagnostic":"NO_EFFECTIVE_POLICY_DIVERSITY" if total<=epsilon else
                     "POLICY_CONDITIONED" if cc>epsilon else "CROSS_POLICY_SUPPORT",
        "sign_pattern":["+" if sign(gaps[e],epsilon)>0 else "-" if sign(gaps[e],epsilon)<0 else "0"
                        for e in sorted(gaps)]}
