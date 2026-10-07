from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

from paired_intervention import (
    PAIRED_COLUMNS, RETRIEVAL_COLUMNS, SOURCE_COLUMNS, BudgetExceeded, BudgetGuard,
    behavior_confirmed, canonical_json, choose_action, delta_current,
    deterministic_confirmed, is_candidate, is_historically_positive,
    mask_only_target, pair_inputs_match, repeated_confirmed, result_memory_id,
    retrieval_discounted_return, retrieval_result_dict, retrieval_similarity,
    sha256_json, state_hash,
)
from runtime_runner import BACKEND, JITRL, JITRL_COMMIT, MODEL, ROM_DIR, SEED, make_args
from verify import HERE, RESULTS, verify_lock


def sample(ep=1, step=0, signal=2):
    return {
        "episode_number": ep, "step_num": step, "state": "room", "action": "look",
        "reward": 0, "score": 0, "delta_score": 0, "llm_step_score": signal,
    }


def test_01_expected_commit():
    head = subprocess.check_output(["git", "-C", str(JITRL), "rev-parse", "HEAD"], text=True).strip()
    assert head == JITRL_COMMIT


def test_02_jitrl_clean():
    assert subprocess.check_output(["git", "-C", str(JITRL), "status", "--short"], text=True).strip() == ""


def test_03_rom_exists():
    assert (ROM_DIR / "library.z5").is_file()


def test_04_faiss_absent():
    assert importlib.util.find_spec("faiss") is None


def test_05_frozen_model_backend_seed():
    assert (MODEL, BACKEND, SEED) == ("qwen2.5:14b", "http://localhost:11434/v1", 20261008)


def test_06_args_frozen(tmp_path):
    args = make_args(tmp_path, 20)
    assert (args.eval_runs, args.env_step_limit, args.llm_temperature) == (20, 1, 0.0)
    assert (args.gamma, args.retrieval_top_k, args.retrieval_threshold) == (0.5, 10, 0.95)


def test_07_cross_memory_enabled(tmp_path):
    args = make_args(tmp_path, 2)
    assert args.enable_cross_mem and not args.update_guiding_prompt and args.use_valid_actions


def test_08_canonical_json_order():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})


def test_09_sha_stable():
    assert sha256_json({"x": 1}) == sha256_json({"x": 1})


def test_10_state_hash_sensitive():
    assert state_hash("a") != state_hash("b")


def test_11_memory_id_stable():
    assert result_memory_id(sample()) == result_memory_id(dict(sample()))


def test_12_memory_id_signal_sensitive():
    assert result_memory_id(sample(signal=1)) != result_memory_id(sample(signal=2))


def test_13_retrieval_tuple_parse():
    item = (0.9, 1.2, sample())
    assert retrieval_result_dict(item)["action"] == "look"
    assert retrieval_similarity(item) == 0.9
    assert retrieval_discounted_return(item) == 1.2


def test_14_retrieval_mapping_parse():
    item = dict(sample(), similarity_score=0.5, discounted_reward=-2)
    assert retrieval_similarity(item) == 0.5
    assert retrieval_discounted_return(item) == -2


def test_15_mask_exact_target():
    a, b = sample(ep=1), sample(ep=2)
    items = [(0.8, 1, a), (0.7, 2, b)]
    masked = mask_only_target(items, result_memory_id(a))
    assert len(masked) == 1 and result_memory_id(retrieval_result_dict(masked[0])) == result_memory_id(b)


def test_16_mask_missing_rejected():
    with pytest.raises(ValueError):
        mask_only_target([(0.8, 1, sample())], "missing")


def test_17_mask_does_not_mutate():
    item = (0.8, 1, sample())
    items = [item, (0.7, 0, sample(ep=2))]
    before = json.dumps(items)
    mask_only_target(items, result_memory_id(sample()))
    assert json.dumps(items) == before


def test_18_choose_action_corrected():
    options = {1: {"action": "a", "corrected_logprob": 0.1}, 2: {"action": "b", "corrected_logprob": 0.2}}
    assert choose_action(options) == "b"


def test_19_delta_definition():
    assert delta_current(-1, 2) == -3


def test_20_historical_positive_strict():
    assert is_historically_positive(0.01)
    assert not is_historically_positive(0)
    assert not is_historically_positive(-1)
    assert not is_historically_positive("nan")


def test_21_candidate_requires_all_conditions():
    assert is_candidate(1, -1, True)
    assert not is_candidate(0, -1, True)
    assert not is_candidate(1, 0, True)
    assert not is_candidate(1, -1, False)


def test_22_deterministic_confirmation():
    assert deterministic_confirmed([-1, -2])
    assert not deterministic_confirmed([-1, 0])


def test_23_repeated_confirmation():
    assert repeated_confirmed([-1, -1, 1])
    assert not repeated_confirmed([-1, 1, 1])
    assert not repeated_confirmed([-1, -1])


def test_24_behavior_confirmation():
    assert behavior_confirmed([True, True, False])
    assert not behavior_confirmed([True, False, False])


def test_25_pair_state_match():
    snapshot = {"env": "bytes", "rng": [1, 2]}
    assert pair_inputs_match(snapshot, dict(snapshot))
    assert not pair_inputs_match(snapshot, {"env": "changed", "rng": [1, 2]})


def test_26_budget_guard():
    guard = BudgetGuard(2)
    guard.charge(); guard.charge()
    assert guard.calls == 2
    with pytest.raises(BudgetExceeded):
        guard.charge()


def test_27_schemas_unique():
    for columns in (SOURCE_COLUMNS, RETRIEVAL_COLUMNS, PAIRED_COLUMNS):
        assert len(columns) == len(set(columns))


def test_28_preregistration_has_verdicts():
    text = (HERE / "preregistration.md").read_text(encoding="utf-8")
    for verdict in ("REAL_JITRL_MEMORY_FAILURE_GO", "REAL_JITRL_MEMORY_FAILURE_NARROW", "REAL_JITRL_MEMORY_FAILURE_NO_GO"):
        assert verdict in text


def test_29_lock_exists_and_matches():
    ok, problems = verify_lock()
    assert ok, problems


def test_30_no_formal_before_tests():
    assert not (RESULTS / "formal_started.json").exists()
