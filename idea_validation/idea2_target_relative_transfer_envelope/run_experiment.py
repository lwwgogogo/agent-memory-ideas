"""One-shot evaluator orchestration. No private metadata enters candidate processes."""
import csv
import json
import sys
from pathlib import Path
from fractions import Fraction
import scipy
from build_cases import build
from launcher import launch,success,sha,denial_probe,CANDIDATE_FILES,LEGACY
from schema import read_records
from evaluate import independent_counts,exact_membership,paired_checks,compute_gates,verdict
from integrity import history_matches,check_lock
from render_report import render,scope_ok,SCOPE

BASE=Path(__file__).resolve().parent
def write(name,value):
    p=BASE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n")
def scientific(output):
    return {k:v for k,v in output.items() if k!="execution_audit"}
def main():
    results=BASE/"results"
    if (results/"formal_started.json").exists(): raise RuntimeError("formal run already started; no overwrite")
    tests=json.loads((results/"preformal_tests.json").read_text())
    if tests["tests_passed"]<28 or not tests["success"]: raise RuntimeError("preformal tests not passed")
    lock=json.loads((results/"preregistration_manifest.json").read_text())
    if not check_lock(lock) or not history_matches(): raise RuntimeError("lock/history mismatch before run")
    write("results/formal_started.json",{"formal_run_count":1,"formal_restart":False,
         "python":sys.version,"scipy":scipy.__version__,"tests_passed":tests["tests_passed"]})
    manifest=build(BASE/"export")
    write("results/case_manifest.json",manifest)
    raw_outputs={};audit=[];events=["generator_completed"]
    # Candidate processes receive anonymous observations, not this manifest.
    for i in range(1,9):
        tag=f"case_{i:03d}"
        sf=BASE/"export"/(tag+"_source.jsonl");tf=BASE/"export"/(tag+"_target.jsonl")
        official_run=launch(sf.read_bytes(),official=True)
        official=scientific(success(official_run))
        probe_run=launch(sf.read_bytes(),tf.read_bytes())
        probe=success(probe_run)
        raw_outputs[tag]=(official,probe)
        write("results/candidate_outputs/"+tag+".json",probe)
        audit.append({"anonymous_id":tag,
          "official":{k:v for k,v in official_run.items() if k!="output"},
          "probe":{k:v for k,v in probe_run.items() if k!="output"},
          "candidate_execution_audit":probe["execution_audit"]})
        events.append("candidate_finished:"+tag)
    events.append("evaluator_private_manifest_read")
    private=json.loads((results/"case_manifest.json").read_text())
    rows=[]
    for m in private:
        sf=BASE/"export"/m["source_file"];tf=BASE/"export"/m["target_file"]
        source=read_records(sf,True);target=read_records(tf,False)
        valid_s,vectors=independent_counts(source,True)
        valid_t,tv=independent_counts(target,False)
        official,probe=raw_outputs[m["anonymous_id"]]
        expected=exact_membership(list(vectors.values()),tv["target"])
        row={**m,"source_sha256":sha(sf),"target_sha256":sha(tf),
          "probe":scientific(probe),"independent_geometry":expected,
          "data_integrity":valid_s and valid_t,
          "descriptors_match":vectors==probe["source_policy_vectors"] and tv["target"]==probe["target_policy_vector"],
          "global_equivalence":official==probe["global"]}
        rows.append(row)
    checks=paired_checks(rows)
    forbidden_modules=("build_cases","evaluate","run_experiment","case_manifest")
    code_clean=all(not any(token in (BASE/name).read_text() for token in forbidden_modules)
                   for name in CANDIDATE_FILES)
    allowed_files=set(CANDIDATE_FILES)|{"boundary.py","global_config.json","global_candidate","source.jsonl","target.jsonl"}
    isolated=all(set(a["candidate_execution_audit"]["initial_files"])==allowed_files and
      all(a[k]["environment_isolation_pass"] and a[k]["filesystem_isolation_pass"] and a[k]["source_copy_hash_match"]
          for k in ("official","probe")) for a in audit)
    denial=denial_probe()
    negative_names=["test_target_outcome_rejected","test_gamma_rejected","test_policy_name_rejected",
                    "test_expected_status_rejected","test_cli_extra_rejected","test_private_read_denied"]
    negatives=all(n in tests["passed_names"] for n in negative_names)
    oracle=isolated and code_clean and denial and negatives
    write("results/oracle_boundary_audit.json",{"pass":oracle,"isolated_runs":isolated,
          "candidate_dependency_audit":code_clean,"outside_read_denied":denial,
          "negative_schema_checks_pass":negatives,"execution_order":events,"runs":audit,
          "scope":"Audited candidate path; not malicious-code OS sandbox"})
    gates=compute_gates(rows,checks,oracle,scope_ok(),check_lock(lock))
    label=verdict(gates)
    write("results/source_profiles.json",{r["anonymous_id"]:r["probe"]["source_policy_vectors"] for r in rows})
    write("results/target_profiles.json",{r["anonymous_id"]:r["probe"]["target_policy_vector"] for r in rows})
    write("results/pair_checks.json",checks)
    for pair,name in [("P1","invariance"),("P2","provenance"),("P3","confidence"),("P4","nearest_distance")]:
        write("results/"+name+"_reduction.json",{"pair":pair,"checks":checks[pair],
            "cases":[r for r in rows if r["pair"]==pair],
            "claim_scope":"Only the specified source-only / nearest-scalar information projection"})
    csv_rows=[]
    for r in rows:
        o=r["probe"];s=o["source_summary"]
        csv_rows.append({"case":r["anonymous_id"],"pair":r["pair"],"side":r["side"],
          "source_sha256":r["source_sha256"],"source_summary_sha256":o["source_summary_sha256"],
          "provenance_summary_sha256":o["provenance_summary_sha256"],
          "source_policy_vectors":json.dumps(o["source_policy_vectors"],sort_keys=True),
          "target_policy_vector":json.dumps(o["target_policy_vector"]),
          "global_certification":o["global"]["status"],"M1_U_A":s["M1"]["U_A"],
          "M1_U_B":s["M1"]["U_B"],"M1_gap":s["M1"]["gap"],
          "C_pos":s["C_pos"],"C_conflict":s["C_conflict"],"D_policy":s["D_policy"],
          "target_min_TV":o["target_min_TV"],"target_min_TV_exact":o["target_min_TV_exact"],
          "target_in_convex_hull":o["target_in_convex_hull"],
          "convex_weights":json.dumps(o["convex_weights"],sort_keys=True),
          "linprog_residual":o["linprog_residual"],"transfer_decision":o["transfer_decision"],
          "baseline_decisions":json.dumps(o["baselines"],sort_keys=True),
          "independent_membership":r["independent_geometry"]["inside"]})
    with (results/"paired_results.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(csv_rows[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(csv_rows)
    write("results/gate_results.json",{"gates":{k:"PASS" if v else "FAIL" for k,v in gates.items()},"verdict":label})
    write("results/scope_review.json",{"G9":gates["G9"],"scope_statement":SCOPE,
          "no_performance_or_novelty_claim":True})
    render(BASE,rows,gates,label)
    required=["README.md","theory.md","preregistration.md","TransferEnvelope机制说明.md",
      "Stage6C实验结果.md","最终结论.md","results/case_manifest.json","results/source_profiles.json",
      "results/target_profiles.json","results/paired_results.csv","results/invariance_reduction.json",
      "results/provenance_reduction.json","results/confidence_reduction.json","results/nearest_distance_reduction.json",
      "results/gate_results.json","plots/policy_geometry_pairs.png","plots/target_inside_outside.png",
      "plots/nearest_distance_counterexample.png","plots/reduction_summary.png"]
    missing=[p for p in required if not (BASE/p).is_file()]
    write("results/final_verification.json",{
       "tests_passed":tests["tests_passed"],"formal_run_count":1,"formal_restart":False,
       "history_hash_match":history_matches(),
       "history_file_count":len(json.loads((results/"history_before.json").read_text())),
       "preregistration_hash_match":check_lock(lock),
       "global_cert_equivalence":all(r["global_equivalence"] for r in rows),
       "all_pair_constraints_match":all(gates[k] for k in ("G2","G3","G4","G5","G6","G8")),
       "G0-G9":{k:"PASS" if v else "FAIL" for k,v in gates.items()},
       "verdict":label,"required_files_present":not missing,"missing_files":missing,
       "historical_stage6b":"STAGE6B_NARROW","candidate_processes":8,"official_global_cli_calls":8,
       "no_target_outcome":True,"no_llm_calls":True,"no_literature_search":True})
    if missing or not history_matches() or not check_lock(lock):
        raise RuntimeError("final integrity failed")
    print(json.dumps({"gates":gates,"verdict":label,"tests":tests["tests_passed"]},indent=2))
if __name__=="__main__": main()
