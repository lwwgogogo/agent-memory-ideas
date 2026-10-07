"""Frozen Stage-7 MDP evaluation around the source-extracted JitRL native path."""
from __future__ import annotations

import importlib.util
import inspect
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jitrl_adapter import STAGE_DIR, native_decision

STAGE7_DIR = STAGE_DIR.parent / "idea2_policy_relative_validity"
STAGE7_MDP_SHA256 = "8c2e51bdaa29c57da5d2208885bbbe11815de2b639969036e488b909b8242181"
STAGE7_POLICIES_SHA256 = "52aaaf4e1b3325de4dfea7d7e818ae18367b96b1ad20bba36539926d887c1166"
SOURCE_POLICY = "pi_A"
HISTORICAL_ACTION = "a_L"
FORMAL_SEED = 0
B3_EPISODES = 20
CLOSED_LOOP_STATUS = "NOT_TESTABLE"
CLOSED_LOOP_REASON = (
    "The no-LLM source-extracted harness executes native storage, retrieval, advantage, "
    "and score correction, but JitRL episode scoring/text generation needs the excluded "
    "LLM runtime and exposes no standalone native policy-update rule. Adding one would be invented."
)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_stage7() -> Tuple[Any, Dict[str, Dict[str, str]]]:
    mdp_mod = _load_module("stage8_frozen_stage7_mdp", STAGE7_DIR / "mdp.py")
    policy_mod = _load_module("stage8_frozen_stage7_policies", STAGE7_DIR / "policies.py")
    return mdp_mod.DeterministicMDP(), policy_mod.POLICIES


def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def q_table(target_policy: str) -> Dict[str, float]:
    mdp, policies = load_stage7()
    policy = policies[target_policy]
    return {
        action: float(mdp.q_value(policy, "s0", action))
        for action in ("a_L", "a_R")
    }


def oracle_quantities(target_policy: str) -> Dict[str, Any]:
    qs = q_table(target_policy)
    mean_q = sum(qs.values()) / len(qs)
    advantages = {action: value - mean_q for action, value in qs.items()}
    optimal_action = max(qs, key=qs.get)
    return {
        "target_q_left": qs["a_L"],
        "target_q_right": qs["a_R"],
        "target_advantage_left": advantages["a_L"],
        "target_advantage_right": advantages["a_R"],
        "optimal_action": optimal_action,
        "optimal_return": qs[optimal_action],
    }


def action_return(target_policy: str, action: str) -> float:
    mdp, policies = load_stage7()
    _, total = mdp.rollout(policies[target_policy], initial_action=action)
    return float(total)


def probe_case(target_policy: str) -> Dict[str, Any]:
    # native_decision has no Q/oracle input; oracle quantities are joined only after action selection.
    native = native_decision(target_policy, seed=FORMAL_SEED)
    oracle = oracle_quantities(target_policy)
    source_oracle = oracle_quantities(SOURCE_POLICY)
    chosen_return = action_return(target_policy, native["chosen_action"])
    mismatch = sign(native["native_signal"]) != sign(oracle["target_advantage_left"])
    return {
        "condition": "B1_same_policy" if target_policy == SOURCE_POLICY else "B2_policy_shift",
        "source_policy": SOURCE_POLICY,
        "target_policy": target_policy,
        "historical_action": HISTORICAL_ACTION,
        "historical_return": native["historical_return"],
        "historical_q_source": source_oracle["target_q_left"],
        "historical_advantage_source": source_oracle["target_advantage_left"],
        "retrieved": native["retrieved"],
        "retrieved_count": native["retrieved_count"],
        "retrieval_score": native["retrieval_score"],
        "native_memory_signal": native["native_signal"],
        "native_raw_advantage": native["native_raw_advantage"],
        "target_q": oracle["target_q_left"],
        "target_advantage": oracle["target_advantage_left"],
        "target_q_right": oracle["target_q_right"],
        "signal_sign_match": not mismatch,
        "sign_mismatch": mismatch,
        "positive_historical_negative_target": (
            native["native_signal"] > 0 and oracle["target_advantage_left"] < 0
        ),
        "base_action": native["base_action"],
        "chosen_action": native["chosen_action"],
        "optimal_action": oracle["optimal_action"],
        "left_base_score": native["left_base_score"],
        "right_base_score": native["right_base_score"],
        "left_corrected_score": native["left_corrected_score"],
        "right_corrected_score": native["right_corrected_score"],
        "policy_bias_applied": native["policy_bias_applied"],
        "chosen_return": chosen_return,
        "regret": oracle["optimal_return"] - chosen_return,
        "harmful_memory_use": (
            native["memory_read"]
            and native["chosen_action"] == HISTORICAL_ACTION
            and oracle["target_q_left"] < oracle["target_q_right"]
        ),
        "harmful_policy_bias": (
            native["policy_bias_applied"]
            and chosen_return < action_return(target_policy, native["base_action"])
        ),
        "memory_read": native["memory_read"],
        "oracle_read": native["oracle_read"],
    }


def select_oracle_validity(target_policy: str) -> Dict[str, Any]:
    oracle = oracle_quantities(target_policy)
    base_action = oracle["optimal_action"]
    if oracle["target_advantage_left"] < 0:
        return {
            "chosen_action": base_action,
            "memory_read": False,
            "oracle_read": True,
            "policy_bias_applied": False,
            "rejected_native_influence": True,
        }
    native = native_decision(target_policy, seed=FORMAL_SEED)
    return {
        "chosen_action": native["chosen_action"],
        "memory_read": True,
        "oracle_read": True,
        "policy_bias_applied": native["policy_bias_applied"],
        "rejected_native_influence": False,
    }


def baseline_records(episodes: int = B3_EPISODES) -> List[Dict[str, Any]]:
    target_policy = "pi_B"
    oracle = oracle_quantities(target_policy)
    rows: List[Dict[str, Any]] = []
    for episode in range(1, episodes + 1):
        base_action = oracle["optimal_action"]
        native = native_decision(target_policy, seed=FORMAL_SEED)
        oracle_choice = select_oracle_validity(target_policy)
        decisions = {
            "NoMemory": {
                "chosen_action": base_action,
                "memory_read": False,
                "oracle_read": False,
                "policy_bias_applied": False,
            },
            "JitRLNative": native,
            "OracleValidity": oracle_choice,
        }
        for baseline, decision in decisions.items():
            chosen = decision["chosen_action"]
            value = action_return(target_policy, chosen)
            base_value = action_return(target_policy, base_action)
            rows.append({
                "condition": "B3_policy_shift",
                "episode": episode,
                "baseline": baseline,
                "source_policy": SOURCE_POLICY,
                "target_policy": target_policy,
                "chosen_action": chosen,
                "optimal_action": oracle["optimal_action"],
                "return": value,
                "reward": value,
                "regret": oracle["optimal_return"] - value,
                "memory_read": bool(decision["memory_read"]),
                "oracle_read": bool(decision["oracle_read"]),
                "policy_bias_applied": bool(decision["policy_bias_applied"]),
                "harmful_memory_use": bool(
                    decision["memory_read"]
                    and chosen == HISTORICAL_ACTION
                    and oracle["target_q_left"] < oracle["target_q_right"]
                ),
                "harmful_policy_bias": bool(
                    decision["policy_bias_applied"] and value < base_value
                ),
            })
    return rows


def summarize_baselines(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for baseline in ("NoMemory", "JitRLNative", "OracleValidity"):
        subset = [row for row in rows if row["baseline"] == baseline]
        n = len(subset)
        out[baseline] = {
            "n": n,
            "average_return": sum(row["return"] for row in subset) / n,
            "cumulative_regret": sum(row["regret"] for row in subset),
            "harmful_memory_use_rate": sum(row["harmful_memory_use"] for row in subset) / n,
            "harmful_policy_bias_rate": sum(row["harmful_policy_bias"] for row in subset) / n,
        }
    return out


def native_decision_signature_has_no_oracle() -> bool:
    names = set(inspect.signature(native_decision).parameters)
    return not any(token in name for name in names for token in ("oracle", "target_q", "advantage"))
