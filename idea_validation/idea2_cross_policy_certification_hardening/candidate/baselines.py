def observed_baselines(cells,gaps,record_count,epsilon):
    return {"raw_support_count":record_count,"era_count":len(cells),
        "mean_observed_gap":sum(gaps.values())/len(gaps),
        "success_support":sum(cells[e][s]["A"][1] for e in cells if gaps[e]>epsilon for s in cells[e])}
