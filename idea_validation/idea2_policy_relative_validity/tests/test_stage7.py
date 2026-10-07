import inspect
import json
from pathlib import Path
import sys

import pytest

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))

from baselines import (NoMemory,SimilarityMemory,HistoricalUtility,JitRLStyle,
                       OraclePolicyValidity,ProvenanceOnly,evaluate_baseline)
from mdp import DeterministicMDP
from memory import ExperienceMemory,MemoryBank,generate_source_memory
from policies import PI_A,PI_B,SharedPreferencePolicy
from run_experiment import run_f3,no_oracle_leakage,DISTINCTNESS_STATEMENT
from verify import history_match,make_manifest

def test_deterministic_transitions():
    mdp=DeterministicMDP()
    assert mdp.step("s0","a_L").next_state=="s1"
    assert mdp.step("s1","a_R").reward==2
    assert mdp.step("s1","a_L").reward==-2

def test_exact_q_computation():
    mdp=DeterministicMDP()
    assert mdp.q_value(PI_A,"s0","a_L")==2
    assert mdp.q_value(PI_B,"s0","a_L")==-2
    assert mdp.q_value(PI_A,"s0","a_R")==mdp.q_value(PI_B,"s0","a_R")==1

def test_required_q_reversal():
    mdp=DeterministicMDP()
    assert mdp.q_value(PI_A,"s0","a_L")>0
    assert mdp.q_value(PI_B,"s0","a_L")<0

def test_environment_reward_unchanged_by_policy():
    mdp=DeterministicMDP();fingerprint=mdp.fingerprint()
    mdp.q_value(PI_A,"s0","a_L");mdp.q_value(PI_B,"s0","a_L")
    assert mdp.fingerprint()==fingerprint
    assert mdp.transitions[("s0","a_L")].reward==0

def test_source_memory_provenance():
    memory,steps=generate_source_memory(DeterministicMDP())
    assert memory.to_dict()=={"state":"s0","action":"a_L","observed_return":2,
      "source_policy":"pi_A","trajectory_id":"traj_A_000","generation_step":0}
    assert steps[-1]["action"]=="a_R"

def test_same_policy_memory_valid_and_positive():
    mdp=DeterministicMDP();memory,_=generate_source_memory(mdp)
    assert mdp.q_value(PI_A,memory.state,memory.action)==2
    for baseline in (SimilarityMemory(),HistoricalUtility(),JitRLStyle()):
        result=evaluate_baseline(mdp,memory,baseline,"pi_A")
        assert result["memory_acceptance_rate"]==1
        assert result["average_return"]==2

def test_oracle_rejects_harmful_memory():
    mdp=DeterministicMDP();memory,_=generate_source_memory(mdp)
    result=evaluate_baseline(mdp,memory,OraclePolicyValidity(mdp),"pi_B")
    assert result["memory_acceptance_rate"]==0
    assert result["harmful_memory_use_rate"]==0
    assert result["average_return"]==1

def test_nonoracle_baselines_do_not_read_q():
    assert no_oracle_leakage()
    for cls in (NoMemory,SimilarityMemory,HistoricalUtility,JitRLStyle,ProvenanceOnly):
        source=inspect.getsource(cls)
        assert "q_value" not in source and "OraclePolicyValidity" not in source

def test_historical_success_trap():
    mdp=DeterministicMDP();memory,_=generate_source_memory(mdp)
    no=evaluate_baseline(mdp,memory,NoMemory(),"pi_B")
    assert no["average_return"]==1 and no["cumulative_regret"]==0
    for b in (SimilarityMemory(),HistoricalUtility(),JitRLStyle()):
        result=evaluate_baseline(mdp,memory,b,"pi_B")
        assert result["average_return"]==-2
        assert result["cumulative_regret"]==60
        assert result["harmful_memory_use_rate"]==1

def test_provenance_only_control():
    mdp=DeterministicMDP();memory,_=generate_source_memory(mdp)
    shifted=evaluate_baseline(mdp,memory,ProvenanceOnly(),"pi_B")
    same=evaluate_baseline(mdp,memory,ProvenanceOnly(),"pi_A")
    assert shifted["memory_acceptance_rate"]==0 and shifted["average_return"]==1
    assert same["memory_acceptance_rate"]==1 and same["average_return"]==2

def test_shared_preference_matches_policies():
    p=SharedPreferencePolicy(0)
    assert p.mapping()==PI_A
    memory,_=generate_source_memory(DeterministicMDP())
    p.apply_memory(memory)
    assert p.theta==2 and p.mapping()["s1"]==PI_B["s1"]
    assert p.mapping()["s0"]=="a_L"  # memory still recommends the original action

def test_f3_trace_fields_complete():
    memory,_=generate_source_memory(DeterministicMDP())
    trace,_=run_f3(DeterministicMDP(),memory,2)
    required={"iteration","policy_action_preference_before","policy_action_preference_after",
      "continuation_action_before","continuation_action_after","memory_used",
      "memory_source_policy","historical_utility","pre_use_target_Q","current_target_Q",
      "action","reward","valid_now","validity_flip","memory_bank_size"}
    assert required<=set(trace[0])

def test_f3_validity_flip_and_feedback():
    mdp=DeterministicMDP();memory,_=generate_source_memory(mdp)
    trace,flips=run_f3(mdp,memory,6)
    assert flips==1
    assert trace[0]["pre_use_target_Q"]==2 and trace[0]["current_target_Q"]==-2
    assert trace[0]["continuation_action_before"]=="a_R"
    assert trace[0]["continuation_action_after"]=="a_L"
    assert trace[-1]["memory_bank_size"]==7
    assert all(r["memory_trajectory_id"]=="traj_A_000" for r in trace)
    assert all(r["reward"]==-2 for r in trace)

def test_memory_bank_keeps_historical_success_top():
    source,_=generate_source_memory(DeterministicMDP())
    bank=MemoryBank([source,ExperienceMemory("s0","a_L",-2,"pi_B","bad",1)])
    assert bank.retrieve("s0")==source

def test_deterministic_repeatability():
    mdp=DeterministicMDP();memory,_=generate_source_memory(mdp)
    assert run_f3(mdp,memory,6)==run_f3(DeterministicMDP(),memory,6)
    assert evaluate_baseline(mdp,memory,JitRLStyle(),"pi_B")==evaluate_baseline(
        DeterministicMDP(),memory,JitRLStyle(),"pi_B")

def test_distinctness_is_feedback_not_static_only():
    assert all(x in DISTINCTNESS_STATEMENT for x in ("经典RL事实","旧policy产物","干预变量"))
    memory,_=generate_source_memory(DeterministicMDP())
    trace,_=run_f3(DeterministicMDP(),memory,1)
    assert trace[0]["memory_used"]
    assert trace[0]["policy_action_preference_before"]!=trace[0]["policy_action_preference_after"]
    assert trace[0]["written_memory_return"]<0

def test_history_unchanged_before_formal():
    assert history_match()

def test_manifest_covers_formal_files():
    manifest=make_manifest()
    assert set(manifest["files"])=={"preregistration.md","mdp.py","policies.py",
      "memory.py","baselines.py","run_experiment.py","verify.py"}
    assert all(len(v)==64 for v in manifest["files"].values())

def test_formal_guard_source_present():
    source=Path(__file__).resolve().parents[1].joinpath("run_experiment.py").read_text()
    assert 'formal_started.json").exists()' in source
    assert "formal run already started" in source
