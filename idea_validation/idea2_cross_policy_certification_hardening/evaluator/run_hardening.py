import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from evaluator.verify_isolation import (REPO,FIELDS,ENV,sha,write_json,history_snapshot,inspect_sources,
    check_input,launch,negative_checks,metadata_checks,read_denial_probe,verify_lock)
from evaluator.compute_gates import reproduction,legacy_science_check,compute_gates

def test_count():
    root=ET.parse(BASE/"results/preformal_tests.xml").getroot()
    suites=list(root.iter("testsuite"))
    count=sum(int(s.get("tests","0")) for s in suites)
    errors=sum(int(s.get(k,"0")) for s in suites for k in ("failures","errors","skipped"))
    if count<32 or errors: raise RuntimeError("pre-formal tests not complete")
    return count

def main():
    result=BASE/"results"
    if (result/"formal_started.json").exists(): raise RuntimeError("formal execution already started")
    count=test_count(); lock=verify_lock()
    before=json.loads((result/"history_before.json").read_text())
    if before!=history_snapshot():raise RuntimeError("historical bytes changed before formal run")
    write_json(result/"formal_started.json",{"formal_run_count":1,"formal_restart":False,"python":sys.version,"executable":sys.executable})
    events=[]
    private_path=result/"private/world_manifest.json"
    subprocess.run([sys.executable,"-B",str(BASE/"generator/private_generate.py"),
       "--output-dir",str(BASE/"export"),"--private-manifest",str(private_path)],check=True)
    events.append("generator_finished")
    inputs=[]; outputs={}; runs=[]; out_manifest=[]
    for path in sorted((BASE/"export").glob("case_*.jsonl")):
        inputs.append(check_input(path))
        out=result/"candidate_outputs"/(path.stem+".json")
        run=launch(path,out)
        if run["returncode"]!=0:raise RuntimeError(run["stderr"])
        outputs[path.name]=run["output"]
        runs.append({k:v for k,v in run.items() if k not in ("output_bytes","output")})
        out_manifest.append({"path":str(out.relative_to(BASE)),"sha256":sha(out),"input_sha256":run["input_sha256"]})
        events.append("candidate_finished:"+path.name)
    write_json(result/"candidate_input_manifest.json",{"inputs":inputs,"schema_fields":sorted(FIELDS)})
    write_json(result/"candidate_output_manifest.json",{"outputs":out_manifest})
    # Private metadata is read only after every scientific candidate process has exited.
    private=json.loads(private_path.read_text());events.append("evaluator_private_read")
    rep=reproduction(outputs,private)
    write_json(result/"reproduction.json",rep)
    input_path=BASE/"export/case_008.jsonl"
    negatives=negative_checks(input_path)
    metamorphic=metadata_checks(input_path,result/"private/metamorphic")
    write_json(result/"metamorphic_test.json",metamorphic)
    meta_inputs=[check_input(p) for p in sorted((result/"private/metamorphic").glob("input_*.jsonl"))]
    meta_outputs=[{"path":str(p.relative_to(BASE)),"sha256":sha(p)}
                  for p in sorted((result/"private/metamorphic").glob("output_*.json"))]
    write_json(result/"candidate_input_manifest.json",{"inputs":inputs,"metamorphic_inputs":meta_inputs,"schema_fields":sorted(FIELDS)})
    write_json(result/"candidate_output_manifest.json",{"outputs":out_manifest,"metamorphic_outputs":meta_outputs})
    probe=read_denial_probe()
    audit=inspect_sources()
    audit.update({
      "schema_fields":sorted(FIELDS),"formal_cli_args":[r["formal_cli_args"] for r in runs],
      "candidate_environment_variable_whitelist":sorted(ENV),"formal_runs":runs,"negative_checks":negatives,
      "filesystem_read_denial_probe":probe,"execution_order":events,
      "schema_whitelist_pass":len(inputs)==11 and all(x["schema_whitelist_pass"] for x in inputs),
      "anonymous_era_id_pass":len(inputs)==11 and all(x["anonymous_era_id_pass"] for x in inputs)
              and all(x["rejected"] for x in negatives if x["probe"].startswith("semantic_")),
      "forbidden_field_rejection_pass":sum(x["probe"].startswith("extra_") for x in negatives)==6
              and all(x["rejected"] for x in negatives if x["probe"].startswith("extra_")),
      "missing_field_rejection_pass":sum(x["probe"].startswith("missing_") for x in negatives)==4
              and all(x["rejected"] for x in negatives if x["probe"].startswith("missing_")),
      "subprocess_isolation_pass":len(runs)==11 and all(x["subprocess_isolation_pass"] for x in runs),
      "filesystem_isolation_pass":len(runs)==11 and all(x["filesystem_isolation_pass"] and x["source_copy_hash_match"] for x in runs) and probe["blocked"],
      "environment_isolation_pass":len(runs)==11 and all(x["environment_isolation_pass"] for x in runs),
      "metadata_invariance_pass":metamorphic["private_metadata_mutations_tested"]>=5 and metamorphic["input_sha_equality"]
              and metamorphic["output_bitwise_equality"] and metamorphic["canonical_output_equality"] and metamorphic["all_isolated"],
      "candidate_output_reproduction_pass":rep["all_match"] and rep["ratio_match"],
    })
    required=["schema_whitelist_pass","forbidden_field_rejection_pass","candidate_import_isolation_pass",
      "forbidden_string_audit_pass","anonymous_era_id_pass","subprocess_isolation_pass",
      "filesystem_isolation_pass","metadata_invariance_pass","candidate_output_reproduction_pass",
      "missing_field_rejection_pass","environment_isolation_pass"]
    audit["G5"]=all(audit[k] for k in required)
    audit["G5_required_subchecks"]=required
    write_json(result/"oracle_boundary_audit.json",audit)
    after=history_snapshot()
    history={"history_file_count":len(before),"history_hash_match":before==after}
    science=legacy_science_check();write_json(result/"science_equivalence.json",science)
    lock=verify_lock()
    gates=compute_gates(history,rep,audit,metamorphic,science,all(lock.values()))
    write_json(result/"gate_results.json",gates)
    write_json(result/"final_verification.json",{**history,"preformal_tests_passed":count,
      "preregistration_hash_match":all(lock.values()),"formal_run_count":1,"formal_restart":False,
      "historical_verdict_retained":"CROSS_POLICY_CERT_NARROW","G5":audit["G5"],
      "verdict":gates["verdict"],"environment":{"python":sys.version,"executable":sys.executable},
      "output_hashes":{p.name:sha(p) for p in sorted(result.glob("*.json")) if p.name!="final_verification.json"}})
    from evaluator.render_report import render
    render()
    print(json.dumps({"tests":count,"G5":audit["G5"],"gates":gates,"history":history},indent=2))
if __name__=="__main__":main()
