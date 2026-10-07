from pathlib import Path
import inspect
import json
import sys

import pytest

STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE))

import jitrl_adapter as ja
import native_probe as npb
import verify


@pytest.fixture(scope="module")
def b1():
    return npb.probe_case("pi_A")


@pytest.fixture(scope="module")
def b2():
    return npb.probe_case("pi_B")


@pytest.fixture(scope="module")
def rows():
    return npb.baseline_records(3)


def test_01_jitrl_source_located():
    assert ja.AGENT_SOURCE.is_file() and ja.MEMORY_SOURCE.is_file()


def test_02_jitrl_commit_fixed():
    assert ja.source_status()["commit"] == ja.EXPECTED_COMMIT


def test_03_native_source_hashes_fixed():
    assert ja.source_status()["hashes"] == ja.EXPECTED_SHA256


def test_04_native_tracked_files_clean():
    assert ja.source_status()["tracked_diff_clean"]


def test_05_native_methods_extracted():
    hashes = ja.native_method_ast_hashes()
    assert len(hashes) == 6
    assert any(key.endswith("update_scores") for key in hashes)


def test_06_adapter_maps_exact_core_functions():
    mapping = ja.adapter_mapping()
    assert "_store_step_in_vector_db" in mapping["storage"]
    assert "retrieve_similar_with_vector" in mapping["retrieval"]
    assert "update_scores" in mapping["value_and_advantage"]


def test_07_native_memory_schema_and_no_policy_field():
    memory = ja.build_native_memory()
    metadata = memory.step_metadata[0]
    assert {"step_data", "future_rewards", "trajectory_context", "episode_number"} <= set(metadata)
    forbidden = {"source_policy", "behavior_policy", "propensity", "policy_version", "checkpoint"}
    assert not (forbidden & set(metadata))
    assert not (forbidden & set(metadata["step_data"]))


def test_08_native_retrieval_selects_s0_only():
    decision = ja.native_decision("pi_A")
    assert decision["retrieved"] and decision["retrieved_count"] == 1
    assert decision["retrieval_score"] == pytest.approx(1.0)


def test_09_native_discounted_return_matches_stage7():
    assert ja.native_decision("pi_A")["historical_return"] == pytest.approx(2.0)


def test_10_stage7_exact_q_values():
    assert npb.q_table("pi_A") == {"a_L": 2.0, "a_R": 1.0}
    assert npb.q_table("pi_B") == {"a_L": -2.0, "a_R": 1.0}


def test_11_same_policy_native_signal_sane(b1):
    assert b1["native_memory_signal"] > 0
    assert b1["target_advantage"] > 0
    assert not b1["sign_mismatch"]


def test_12_policy_shift_mismatch_computable(b2):
    assert b2["native_memory_signal"] > 0
    assert b2["target_advantage"] < 0
    assert b2["sign_mismatch"]


def test_13_no_memory_never_reads_memory(rows):
    subset = [row for row in rows if row["baseline"] == "NoMemory"]
    assert subset and all(not row["memory_read"] for row in subset)


def test_14_jitrl_native_does_not_read_oracle(rows):
    subset = [row for row in rows if row["baseline"] == "JitRLNative"]
    assert subset and all(not row["oracle_read"] for row in subset)
    assert npb.native_decision_signature_has_no_oracle()


def test_15_oracle_is_only_oracle_reader(rows):
    for row in rows:
        assert row["oracle_read"] == (row["baseline"] == "OracleValidity")


def test_16_historical_provenance_in_experiment_ledger(b1, b2):
    assert b1["source_policy"] == "pi_A"
    assert b2["source_policy"] == "pi_A"
    assert b2["target_policy"] == "pi_B"


def test_17_deterministic_repeatability():
    first = ja.native_decision("pi_B")
    second = ja.native_decision("pi_B")
    keys = ["chosen_action", "historical_return", "native_signal", "left_corrected_score", "right_corrected_score"]
    assert {key: first[key] for key in keys} == {key: second[key] for key in keys}


def test_18_result_schema_complete(b2):
    required = {
        "source_policy", "target_policy", "historical_return", "historical_q_source",
        "native_memory_signal", "target_q", "target_advantage", "retrieval_score",
        "retrieved", "sign_mismatch", "policy_bias_applied", "chosen_action",
        "chosen_return", "regret",
    }
    assert required <= set(b2)


def test_19_native_source_unchanged_after_probe():
    before = ja.source_status()
    ja.native_decision("pi_B")
    after = ja.source_status()
    assert before == after and after["matches_expected"]


def test_20_native_policy_shift_changes_action_and_harms(b2):
    assert b2["base_action"] == "a_R"
    assert b2["chosen_action"] == "a_L"
    assert b2["policy_bias_applied"] and b2["harmful_policy_bias"]


def test_21_baseline_returns_and_regret(rows):
    summary = npb.summarize_baselines(rows)
    assert summary["NoMemory"]["average_return"] == 1.0
    assert summary["JitRLNative"]["average_return"] == -2.0
    assert summary["OracleValidity"]["average_return"] == 1.0
    assert summary["JitRLNative"]["cumulative_regret"] == 9.0


def test_22_closed_loop_is_explicitly_not_testable():
    assert npb.CLOSED_LOOP_STATUS == "NOT_TESTABLE"
    assert "invented" in npb.CLOSED_LOOP_REASON


def test_23_preregistration_manifest_matches():
    check = verify.verify_manifest()
    assert check["ok"], check["mismatches"]
