"""Candidate entry point; receives only anonymous source/target observations."""
import json
import math
import os
import sys
from pathlib import Path

def compute(source,target,config):
    from global_candidate.policy_profile import reconstruct,pair_distances,diversity
    from global_candidate.certification import certify
    from global_candidate.baselines import observed_baselines
    from policy_geometry import source_descriptors,descriptor,nearest,membership,decision
    from baselines import source_summary,provenance,digest,baseline_outputs
    cells,profiles,gaps,count=reconstruct(source)
    pairs=pair_distances(profiles);div=diversity(pairs)
    global_result={**div,**certify(profiles,gaps,pairs,div,config),
                   **observed_baselines(cells,gaps,count,config["epsilon"]),
                   "profile":profiles,"gaps":gaps,"cells":cells}
    vectors=source_descriptors(source);target_vector=descriptor(target)
    dominant=1 if global_result["C_pos"]>=global_result["C_neg"] else -1
    supporting=[e for e in sorted(vectors) if dominant*gaps[e]>config["epsilon"]]
    points=[vectors[e] for e in supporting]
    geometry=membership(points,target_vector) if points else {
        "inside":False,"weights":None,"residual":None,"solver_status":"NO_SUPPORT"}
    minimum=nearest(list(vectors.values()),target_vector)
    summary=source_summary(source,global_result)
    weights=geometry["weights"]
    return {"global":global_result,"source_summary":summary,
      "source_summary_sha256":digest(summary),
      "provenance_summary":provenance(len(vectors)),
      "provenance_summary_sha256":digest(provenance(len(vectors))),
      "source_policy_vectors":{e:[str(v) for v in b] for e,b in vectors.items()},
      "target_policy_vector":[str(v) for v in target_vector],
      "supporting_eras":supporting,"target_min_TV_exact":str(minimum),
      "target_min_TV":float(minimum),"target_in_convex_hull":geometry["inside"],
      "convex_weights":None if weights is None else dict(zip(supporting,weights)),
      "linprog_residual":geometry["residual"],"solver_status":geometry["solver_status"],
      "transfer_decision":decision(global_result["status"],geometry["inside"]),
      "interpolation_diagnostic":"INTERPOLATION" if geometry["inside"] else "EXTRAPOLATION",
      "max_lambda":None if weights is None else max(weights),
      "lambda_entropy":None if weights is None else -sum(w*math.log(w) for w in weights if w>0),
      "baselines":baseline_outputs(summary,global_result,minimum)}

def main():
    if sys.argv[1:]!=["source.jsonl","target.jsonl","output.json"]:
        raise ValueError("fixed anonymous arguments required")
    root=Path(__file__).resolve().parent
    if Path.cwd().resolve()!=root: raise ValueError("unexpected cwd")
    sys.path.insert(0,str(root))
    # Import scientific libraries before the file boundary; no observations/private
    # experiment metadata are read during import. Runtime I/O is audited below.
    import policy_geometry
    import baselines
    import schema
    from global_candidate import policy_profile,certification
    from global_candidate import baselines as global_baselines
    from boundary import install
    reads=install(root,"output.json")
    config=json.loads((root/"global_config.json").read_text())
    source=schema.read_records("source.jsonl",True)
    target=schema.read_records("target.jsonl",False)
    result=compute(source,target,config)
    result["execution_audit"]={"environment_keys":sorted(os.environ),
        "initial_files":sorted(p.name for p in root.iterdir()),"read_paths":sorted(reads)}
    Path("output.json").write_text(json.dumps(result,sort_keys=True,separators=(",",":"),
                                             allow_nan=False)+"\n")
if __name__=="__main__": main()
