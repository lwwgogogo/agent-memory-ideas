import json
import os
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
import pytest
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from generator.private_worlds import CASES, NULL, INVARIANT, generate_cells, observed_records
from generator.private_generate import generate
from candidate.schema import FIELDS,validate
from candidate.policy_profile import reconstruct,distance,pair_distances,diversity
from candidate.certification import certify,lifecycle,sign
from evaluator.verify_isolation import (ENV,launch,check_input,inspect_sources,negative_checks,
                                       metadata_checks,read_denial_probe)
from evaluator.compute_gates import legacy_science_check,m1_from_observations,EXPECTED_CONFIG

@pytest.fixture(scope="session")
def generated():
    (BASE/"runtime").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="test_data_",dir=BASE/"runtime") as directory:
        root=Path(directory)
        generate(root/"export",root/"private.json")
        yield root

@pytest.fixture(scope="session")
def outputs(generated):
    out={}
    for index,(name,_,_) in enumerate(CASES,1):
        run=launch(generated/"export"/f"case_{index:03d}.jsonl")
        assert run["returncode"]==0,run["stderr"]
        out[name]=run
    return out

@pytest.fixture(scope="session")
def rejected(generated):
    return {r["probe"]:r["rejected"] for r in negative_checks(generated/"export/case_008.jsonl")}

@pytest.fixture(scope="session")
def metamorphic(generated):
    return metadata_checks(generated/"export/case_008.jsonl")

@pytest.mark.parametrize("case",CASES,ids=[c[0] for c in CASES])
def test_exact_stage6a_cells(case):
    _,table,policies=case;cells=list(generate_cells(table,policies))
    assert len(cells)==4*len(policies)
    for cell in cells:
        assert type(cell["n"]) is int and type(cell["success"]) is int
        assert Fraction(cell["success"],cell["n"])==table[cell["state"]][cell["action"]]
    for i in range(len(policies)):
        for s in ("S0","S1"):
            assert sum(c["n"] for c in cells if c["era_id"]==f"e{i:03d}" and c["state"]==s)==1000

@pytest.mark.parametrize("table,expected",[(NULL,{"A":Fraction(11,20),"B":Fraction(11,20)}),
                                           (INVARIANT,{"A":Fraction(4,5),"B":Fraction(2,5)})])
def test_fraction_truth(table,expected):
    assert {a:sum(Fraction(1,2)*table[s][a] for s in table) for a in ("A","B")}==expected

def test_schema_exact_whitelist():
    assert FIELDS=={"era_id","state","action","outcome"}
    validate({"era_id":"e000","state":"S0","action":"A","outcome":1})

@pytest.mark.parametrize("field",["gamma","policy_name","world","true_utility","ground_truth","expected_status"])
def test_forbidden_field_rejected_in_subprocess(field,rejected):
    assert rejected["extra_"+field]

@pytest.mark.parametrize("field",sorted(FIELDS))
def test_missing_field_rejected_in_subprocess(field,rejected):
    assert rejected["missing_"+field]

@pytest.mark.parametrize("index",[0,1])
def test_semantic_era_rejected_in_subprocess(index,rejected):
    assert rejected["semantic_era_"+str(index)]

@pytest.mark.parametrize("era",["e000","e123","e12345"])
def test_anonymous_era_valid(era):
    validate({"era_id":era,"state":"S1","action":"B","outcome":0})

@pytest.mark.parametrize("outcome",[True,False,1.0,"1",2,-1,None])
def test_outcome_strict_integer(outcome):
    with pytest.raises(ValueError):validate({"era_id":"e000","state":"S0","action":"A","outcome":outcome})

def test_candidate_imports_safe():
    audit=inspect_sources()
    assert audit["candidate_import_isolation_pass"] and not audit["forbidden_imports"]

def test_candidate_forbidden_strings_absent():
    assert inspect_sources()["forbidden_string_audit_pass"]

def test_private_metadata_invariance(metamorphic):
    assert metamorphic["private_metadata_mutations_tested"]>=5 and metamorphic["all_isolated"]

def test_same_input_bitwise_output(metamorphic):
    assert metamorphic["input_sha_equality"] and metamorphic["output_bitwise_equality"]
    assert metamorphic["canonical_output_equality"]

def test_cli_only_input_output(outputs):
    for run in outputs.values():
        assert run["formal_cli_args"][-3:]==["cli.py","input.jsonl","output.json"]

@pytest.mark.parametrize("extra",[[],["input.jsonl"],["input.jsonl","output.json","W3"]])
def test_cli_rejects_wrong_arg_count(extra):
    r=subprocess.run([sys.executable,"-I","-S","-B",str(BASE/"candidate/cli.py"),*extra],
                     cwd=BASE/"candidate",env=ENV,capture_output=True,text=True)
    assert r.returncode!=0 and "exactly two fixed anonymous" in r.stderr

def test_filesystem_copy_and_read_audit(outputs):
    assert all(r["filesystem_isolation_pass"] and r["source_copy_hash_match"] for r in outputs.values())

def test_external_file_read_blocked():
    assert read_denial_probe()["blocked"]

def test_independent_process(outputs):
    assert all(r["child_pid"]!=r["parent_pid"] and r["subprocess_isolation_pass"] for r in outputs.values())

def test_parent_environment_poison_not_inherited(generated,monkeypatch):
    for key in ("WORLD","GAMMA","POLICY","GROUND_TRUTH","PYTHONPATH"):
        monkeypatch.setenv(key,"synthetic_poison")
    run=launch(generated/"export/case_008.jsonl")
    assert run["returncode"]==0 and run["environment_isolation_pass"]
    assert run["output"]["execution_audit"]["environment_keys"]==sorted(ENV)

def test_schema_export_manifest(generated):
    item=check_input(generated/"export/case_008.jsonl")
    assert item["record_count"]==6000 and item["schema_fields"]==sorted(FIELDS) and item["anonymous_era_id_pass"]

@pytest.mark.parametrize("k",[1,2,5,10,20])
def test_w1_reproduction(k,outputs):
    out=outputs[f"W1_K{k}"]["output"]
    assert out["raw_support_count"]==2000*k and out["D_policy"]==0 and out["status"]=="DESCRIPTIVE"
    assert out["diagnostic"]=="NO_EFFECTIVE_POLICY_DIVERSITY"

def test_w2_reproduction(outputs):
    out=outputs["W2_PQPQ"]["output"]
    assert out["sign_pattern"]==["+","-","+","-"] and abs(out["D_policy"]-.6)<1e-12
    assert out["C_conflict"]==1 and out["status"]=="PROVISIONAL" and out["diagnostic"]=="POLICY_CONDITIONED"

def test_w3_reproduction(outputs):
    out=outputs["W3"]["output"]
    assert out["sign_pattern"]==["+","+","+"] and abs(out["D_policy"]-.6)<1e-12
    assert out["C_pos"]==1 and out["C_conflict"]==0 and out["status"]=="PRESCRIPTIVE"

def test_w4_reproduction(outputs):
    out=outputs["W4"]["output"];other=outputs["W3"]["output"]
    assert abs(out["D_policy"]-1/30)<1e-12 and abs(other["D_policy"]/out["D_policy"]-18)<1e-12
    assert out["era_count"]==other["era_count"]==3 and out["status"]!="PRESCRIPTIVE"

@pytest.mark.parametrize("filename",["case_010.jsonl","case_011.jsonl"])
def test_m1_gap_from_observed_records(filename,generated):
    u=m1_from_observations(generated/"export"/filename)
    assert u["exact"]=={"A":"4/5","B":"2/5"} and u["gap"]==.4

def test_echo_diverse_certification_difference(outputs):
    assert outputs["M1_ECHO"]["output"]["status"]=="DESCRIPTIVE"
    assert outputs["M1_DIVERSE"]["output"]["status"]=="PRESCRIPTIVE"

def test_scientific_constants_equal_old_stage():
    assert legacy_science_check()["pass"]

def test_public_thresholds_equal_frozen():
    assert json.loads((BASE/"public_config.json").read_text())==EXPECTED_CONFIG

def test_tv_formula():
    left={"S0":.95,"S1":.05};right={"S0":.05,"S1":.95}
    assert abs(distance(left,right)-.9)<1e-12
    assert distance(left,left)==0

def test_pairwise_mean_formula():
    p={"e000":{"S0":.95,"S1":.05},"e001":{"S0":.05,"S1":.95},"e002":{"S0":.5,"S1":.5}}
    assert abs(diversity(pair_distances(p))["D_policy"]-.6)<1e-12

@pytest.mark.parametrize("gaps,expected",[
 ({"e000":1,"e001":1},(1.,0.,0.)),({"e000":-1,"e001":-1},(0.,1.,0.)),
 ({"e000":1,"e001":-1},(0.,0.,1.)),({"e000":0,"e001":1},(0.,0.,0.))])
def test_weighted_direction_and_conflict(gaps,expected):
    p={"e000":{"S0":.95,"S1":.05},"e001":{"S0":.05,"S1":.95}};pairs=pair_distances(p)
    c=certify(p,gaps,pairs,diversity(pairs),EXPECTED_CONFIG)
    assert (c["C_pos"],c["C_neg"],c["C_conflict"])==expected

@pytest.mark.parametrize("field,value",[
 ("eras",2),("pairs",1),("diversity",.2-1e-9),("positive",.8-1e-9),("conflict",.1+1e-9)])
def test_lifecycle_gate_below_boundary(field,value):
    args={"eras":3,"pairs":2,"diversity":.2,"positive":.8,"negative":0,"conflict":.1,"total":1}
    assert lifecycle(**args,config=EXPECTED_CONFIG)=="PRESCRIPTIVE"
    args[field]=value
    assert lifecycle(**args,config=EXPECTED_CONFIG)=="PROVISIONAL"

def test_lifecycle_zero_weight():
    assert lifecycle(20,0,0,0,0,0,0,EXPECTED_CONFIG)=="DESCRIPTIVE"

def test_epsilon_tie():
    assert sign(1e-12,1e-12)==0 and sign(-1e-12,1e-12)==0

def test_deterministic_rerun(generated,outputs):
    rerun=launch(generated/"export/case_008.jsonl")
    assert rerun["output_bytes"]==outputs["W3"]["output_bytes"]

def test_no_m1_output_in_candidate(outputs):
    assert all(not any("M1" in k for k in r["output"]) for r in outputs.values())
