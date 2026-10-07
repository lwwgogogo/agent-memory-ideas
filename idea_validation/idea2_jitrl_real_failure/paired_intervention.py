"""Pure definitions for Stage-8C logging and paired causal checks."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

SOURCE_COLUMNS = [
    "run_kind", "episode", "step", "memory_id", "state", "action", "reward",
    "score", "delta_score", "llm_step_score", "source_policy_identity",
]
RETRIEVAL_COLUMNS = [
    "run_kind", "episode", "step", "attempt_id", "rank", "memory_id",
    "similarity", "discounted_return", "historical_signal", "historically_positive",
    "source_action", "current_state_hash",
]
PAIRED_COLUMNS = [
    "pair_id", "episode", "step", "memory_id", "repeat", "state_hash_with",
    "state_hash_without", "inputs_match", "action_with", "action_without",
    "outcome_with", "outcome_without", "delta_current", "historical_signal",
    "historically_positive", "behavior_changed", "candidate", "confirmed",
]

class BudgetExceeded(RuntimeError):
    pass

@dataclass
class BudgetGuard:
    max_calls: int
    calls: int = 0

    def charge(self, n: int = 1) -> None:
        if n < 0 or self.calls + n > self.max_calls:
            raise BudgetExceeded(f"model-call budget exceeded: {self.calls + n}>{self.max_calls}")
        self.calls += n


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def state_hash(state: Any) -> str:
    return sha256_json(state)


def result_memory_id(result: Mapping[str, Any]) -> str:
    """Stable ID from fields persisted by native Jericho episodes.jsonl."""
    value = {
        "episode_number": result.get("episode_number", result.get("episode", "UNAVAILABLE")),
        "step_num": result.get("step_num", result.get("step", "UNAVAILABLE")),
        "state": result.get("state", ""),
        "action": result.get("action", ""),
        "reward": result.get("reward", 0),
        "score": result.get("score", 0),
        "delta_score": result.get("delta_score", 0),
        "llm_step_score": result.get("llm_step_score", 0),
    }
    return sha256_json(value)


def retrieval_result_dict(item: Any) -> Mapping[str, Any]:
    if isinstance(item, (tuple, list)) and len(item) >= 3 and isinstance(item[2], Mapping):
        return item[2]
    if isinstance(item, Mapping):
        return item
    raise TypeError("unsupported native retrieval item")


def retrieval_similarity(item: Any) -> float | None:
    if isinstance(item, (tuple, list)) and item:
        try:
            return float(item[0])
        except (TypeError, ValueError):
            return None
    value = retrieval_result_dict(item).get("similarity_score")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def retrieval_discounted_return(item: Any) -> float | None:
    if isinstance(item, (tuple, list)) and len(item) > 1:
        try:
            return float(item[1])
        except (TypeError, ValueError):
            pass
    value = retrieval_result_dict(item).get("discounted_reward")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mask_only_target(items: Sequence[Any], target_memory_id: str) -> list[Any]:
    masked = []
    removed = 0
    for item in items:
        if result_memory_id(retrieval_result_dict(item)) == target_memory_id and removed == 0:
            removed += 1
            continue
        masked.append(copy.deepcopy(item))
    if removed != 1:
        raise ValueError(f"expected exactly one target, removed {removed}")
    return masked


def choose_action(updated_options: Mapping[int, Mapping[str, Any]]) -> str:
    if not updated_options:
        return ""
    key = max(updated_options, key=lambda k: (updated_options[k].get("corrected_logprob", updated_options[k].get("normalized_prob", 0)), -int(k)))
    return str(updated_options[key].get("action", ""))


def delta_current(outcome_with: float, outcome_without: float) -> float:
    return float(outcome_with) - float(outcome_without)


def is_historically_positive(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0


def is_candidate(historical_signal: Any, delta: Any, behavior_changed: bool) -> bool:
    try:
        d = float(delta)
    except (TypeError, ValueError):
        return False
    return is_historically_positive(historical_signal) and math.isfinite(d) and d < 0 and bool(behavior_changed)


def deterministic_confirmed(deltas: Iterable[float]) -> bool:
    values = [float(x) for x in deltas]
    return bool(values) and all(math.isfinite(x) and x < 0 for x in values)


def repeated_confirmed(deltas: Iterable[float]) -> bool:
    values = [float(x) for x in deltas]
    return len(values) == 3 and all(math.isfinite(x) for x in values) and sum(values) / 3 < 0 and sum(x < 0 for x in values) >= 2


def behavior_confirmed(changed: Iterable[bool]) -> bool:
    values = [bool(x) for x in changed]
    return bool(values) and (all(values) if len(values) < 3 else sum(values) >= 2)


def pair_inputs_match(with_snapshot: Any, without_snapshot: Any) -> bool:
    return state_hash(with_snapshot) == state_hash(without_snapshot)
