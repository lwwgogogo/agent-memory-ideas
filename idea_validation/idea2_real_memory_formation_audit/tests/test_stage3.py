from __future__ import annotations
import json, math, pytest
from core import (ROOT,STAGE2,load_source,source_sha,oracle_summary,valid_formation,valid_faithfulness,valid_recovery,recovery_accuracy,full_structure_retained,canonical_probabilities,regret,pair_resolution,bootstrap_mean_ci,final_verdict)

def test_source_sha_and_world_pair_integrity():
    meta=json.loads((ROOT/"cases"/"source_manifest.json").read_text())
    assert source_sha()==meta["source_sha256"]
    from core import sha
    assert sha(ROOT/"cases"/"source_worlds.json")==meta["source_sha256"]
    data=load_source();checks=json.loads((STAGE2/"results"/"identifiability_checks.json").read_text())
    assert len(data["pairs"])==20 and len(data["worlds"])==40 and checks["verdict"]=="CAUSAL_SUFFICIENCY_MATH_GO"
    for p in checks["pairs"]:assert p["lossy_equal"] and not p["g_preserve_equal"] and p["exact_opposite"]

def test_oracle_budget_fits_all_worlds():
    meta=json.loads((ROOT/"cases"/"source_manifest.json").read_text())
    assert meta["memory_budget"]==max(512,math.ceil(1.25*meta["max_oracle_char_length"]))
    assert all(len(oracle_summary(w))<=meta["memory_budget"] for w in load_source()["worlds"])

def test_formation_faithfulness_recovery_schemas():
    assert valid_formation({"memory":"x"},512)
    assert not valid_formation({"memory":"x","reason":"no"},512)
    assert not valid_formation({"memory":"x"*513},512)
    good={"contradiction":False,"unsupported_specific_claim":False,"numeric_error":False,"faithful":True}
    assert valid_faithfulness(good) and not valid_faithfulness({**good,"extra":True})
    missing={k:None for k in ["s0_action_a_success","s0_action_a_exposure","s0_action_b_success","s0_action_b_exposure","s1_action_a_success","s1_action_a_exposure","s1_action_b_success","s1_action_b_exposure"]}
    assert valid_recovery(missing)
    assert not valid_recovery({**missing,"s0_action_a_success":-1})

def test_null_cra_and_full_retention():
    world=load_source()["worlds"][0]
    nulls={k:None for k in ["s0_action_a_success","s0_action_a_exposure","s0_action_b_success","s0_action_b_exposure","s1_action_a_success","s1_action_a_exposure","s1_action_b_success","s1_action_b_exposure"]}
    assert recovery_accuracy(nulls,world)==0.0 and not full_structure_retained(nulls,world)
    exact={}
    for s in ["S0","S1"]:
        for a in ["A","B"]:
            cell=world["cells"][s][a];prefix=f"{s.lower()}_action_{a.lower()}"
            exact[prefix+"_success"]=cell["success"];exact[prefix+"_exposure"]=cell["n"]
    assert recovery_accuracy(exact,world)==1.0 and full_structure_retained(exact,world)

def test_ab_ba_mapping_and_regret():
    parsed={"p_success_left":0.8,"p_success_right":0.2}
    assert canonical_probabilities(parsed,"AB")==(.8,.2)
    assert canonical_probabilities(parsed,"BA")==(.2,.8)
    world=load_source()["worlds"][0]
    correct=0.2 if world["optimal_action"]=="A" else -0.2
    assert regret(correct,world)==pytest.approx(0)
    assert regret(-correct,world)>0

def test_pair_resolution_and_bootstrap_reproducibility():
    assert pair_resolution("A","B","A","B")
    assert not pair_resolution("A","A","A","B")
    assert bootstrap_mean_ci([1,2,3])==bootstrap_mean_ci([1,2,3])

def test_go_gate_boundaries():
    assert final_verdict({"a":True,"b":True})=="REAL_FORMATION_GO"
    assert final_verdict({"a":True,"b":False})=="REAL_FORMATION_WEAK"
    assert final_verdict({"a":False},pipeline_invalid=True)=="STAGE3_RECOVERY_PIPELINE_INVALID"

def test_r2_r4_budget_and_stage2_readonly():
    meta=json.loads((ROOT/"cases"/"source_manifest.json").read_text())
    assert meta["pairs"]==20 and meta["worlds"]==40 and meta["memory_budget"]>=512
