"""Thin, source-extracted adapter for the fixed upstream WebArena JitRL path."""
from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import os
import random
import subprocess
import sys
import types
from pathlib import Path
from types import MethodType, SimpleNamespace
from typing import Any, Dict, List, Optional

import numpy as np

STAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = STAGE_DIR.parents[1]
JITRL_ROOT = REPO_ROOT / "idea_validation" / "idea2_policy_conditioned_memory_audit" / "third_party" / "jitrl"
AGENT_REL = Path("WebArena/memory_agents/jitrl_agent.py")
MEMORY_REL = Path("WebArena/memory_agents/utils/cross_episode_memory.py")
AGENT_SOURCE = JITRL_ROOT / AGENT_REL
MEMORY_SOURCE = JITRL_ROOT / MEMORY_REL
EXPECTED_COMMIT = "143d22185d95fbf633a0befe6861d5e8b732543b"
EXPECTED_SHA256 = {
    AGENT_REL.as_posix(): "e4f1b2143ed412833d0bbe592dd5123f669d6cbc5631e55dcc969662c40849e1",
    MEMORY_REL.as_posix(): "e93c382d30bee83f5248397c475280e9e060317971f8a5aefa2cc53c01e507cc",
}
MEMORY_METHODS = (
    "_store_step_in_vector_db",
    "retrieve_similar_with_vector",
    "_tokenize",
    "_get_ngrams",
    "_jaccard",
)
AGENT_METHODS = ("update_scores",)

TASK_GOAL = "stage7 policy relative task"
QUERY_CONTEXT = "s0 start branch"
SECOND_CONTEXT = "s1 continuation outcome different"
TOY_URL = "toy://stage7"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_status() -> Dict[str, Any]:
    commit = subprocess.check_output(
        ["git", "-C", str(JITRL_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    diff = subprocess.run(
        [
            "git", "-C", str(JITRL_ROOT), "diff", "--quiet", "--",
            AGENT_REL.as_posix(), MEMORY_REL.as_posix(),
        ],
        check=False,
    )
    hashes = {
        AGENT_REL.as_posix(): sha256_file(AGENT_SOURCE),
        MEMORY_REL.as_posix(): sha256_file(MEMORY_SOURCE),
    }
    return {
        "commit": commit,
        "hashes": hashes,
        "tracked_diff_clean": diff.returncode == 0,
        "matches_expected": (
            commit == EXPECTED_COMMIT
            and hashes == EXPECTED_SHA256
            and diff.returncode == 0
        ),
    }


def assert_source_integrity() -> Dict[str, Any]:
    status = source_status()
    if not status["matches_expected"]:
        raise RuntimeError(f"Fixed JitRL source integrity failed: {status}")
    return status


def _method_nodes(source: Path, class_name: str, method_names: tuple[str, ...]) -> List[ast.FunctionDef]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    found = {
        node.name: node
        for node in cls.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in method_names
    }
    missing = set(method_names) - set(found)
    if missing:
        raise RuntimeError(f"Missing upstream methods in {source}: {sorted(missing)}")
    return [found[name] for name in method_names]


def native_method_ast_hashes() -> Dict[str, str]:
    specs = [
        (MEMORY_SOURCE, "CrossEpisodeMemory", MEMORY_METHODS),
        (AGENT_SOURCE, "BrowserGymJitRLAgent", AGENT_METHODS),
    ]
    out: Dict[str, str] = {}
    for source, class_name, names in specs:
        for node in _method_nodes(source, class_name, names):
            payload = ast.dump(node, annotate_fields=True, include_attributes=False).encode()
            out[f"{source.relative_to(JITRL_ROOT).as_posix()}:{class_name}.{node.name}"] = hashlib.sha256(payload).hexdigest()
    return out


def normalize_action(action: str, state: str) -> Dict[str, str]:
    # Boundary adapter only: the toy action names are already canonical.
    return {
        "raw_action": action,
        "normalized_action": action,
        "semantic_action": action,
    }


def calculate_action_similarity(*args: Any, **kwargs: Any) -> float:
    return 1.0


def denormalize_action(action: str, state: str) -> str:
    return action


def _install_relative_import_boundary() -> None:
    package = sys.modules.setdefault("stage8_nativeprobe", types.ModuleType("stage8_nativeprobe"))
    package.__path__ = []
    utils_package = sys.modules.setdefault(
        "stage8_nativeprobe.utils", types.ModuleType("stage8_nativeprobe.utils")
    )
    utils_package.__path__ = []
    module = types.ModuleType("stage8_nativeprobe.utils.utils")
    module.normalize_action = normalize_action
    module.calculate_action_similarity = calculate_action_similarity
    module.denormalize_action = denormalize_action
    sys.modules["stage8_nativeprobe.utils.utils"] = module


def _compile_native_class(
    source: Path,
    upstream_class: str,
    method_names: tuple[str, ...],
    harness_name: str,
) -> type:
    _install_relative_import_boundary()
    methods = _method_nodes(source, upstream_class, method_names)
    class_node = ast.ClassDef(
        name=harness_name,
        bases=[],
        keywords=[],
        body=methods,
        decorator_list=[],
    )
    module_node = ast.Module(body=[class_node], type_ignores=[])
    ast.fix_missing_locations(module_node)
    env: Dict[str, Any] = {
        "__name__": f"stage8_nativeprobe.{harness_name.lower()}",
        "__package__": "stage8_nativeprobe",
        "Any": Any,
        "Dict": Dict,
        "List": List,
        "Optional": Optional,
        "BM25Okapi": None,
        "json": json,
        "np": np,
        "os": os,
        "random": random,
        "normalize_action": normalize_action,
    }
    exec(compile(module_node, str(source), "exec"), env)
    return env[harness_name]


def load_native_classes() -> tuple[type, type]:
    assert_source_integrity()
    memory_class = _compile_native_class(
        MEMORY_SOURCE, "CrossEpisodeMemory", MEMORY_METHODS, "NativeMemoryHarness"
    )
    agent_class = _compile_native_class(
        AGENT_SOURCE, "BrowserGymJitRLAgent", AGENT_METHODS, "NativeAgentHarness"
    )
    return memory_class, agent_class


def _materialized_encoder(
    self: Any,
    states: List[str],
    actions: List[str],
    current_step: int,
    current_summary: Optional[str] = None,
    task_goal: Optional[str] = None,
    urls: Optional[List[str]] = None,
    screenshots_dir: Optional[str] = None,
) -> tuple[str, str, str]:
    # Replaces only the unavailable LLM text encoder. Retrieval/value/policy code is upstream.
    return current_summary or QUERY_CONTEXT, "stage7 deterministic mdp", TOY_URL


def _recording_retrieve(self: Any, **kwargs: Any) -> List[Any]:
    result = self.retrieve_similar_with_vector(**kwargs)
    self.last_retrieval = result
    return result


def build_native_memory() -> Any:
    memory_class, _ = load_native_classes()
    memory = memory_class()
    memory.gamma = 1.0  # Frozen Stage-7 MDP discount, not an effect-tuned setting.
    memory.current_episode_number = 1
    memory.task_similarity_threshold = 0.27
    memory.step_metadata = []
    memory.bm25_corpus = []
    memory.bm25_index = None
    memory.step_summaries = []
    memory.step_context_cache = [
        (QUERY_CONTEXT, "stage7 deterministic mdp", TOY_URL),
        (SECOND_CONTEXT, "stage7 deterministic mdp", TOY_URL),
    ]
    memory._encode_trajectory_context = MethodType(_materialized_encoder, memory)
    memory.retrieve_similar = MethodType(_recording_retrieve, memory)

    episode = {
        "timestamp": "frozen_probe",
        "final_score": 2,
        "success": True,
        "task_goal": TASK_GOAL,
        "steps": [
            {
                "step_num": 0,
                "state": "s0",
                "action": "a_L",
                "normalized_action": "a_L",
                "llm_step_score": 0,
                "reward": 0,
                "url": TOY_URL,
                "step_summary": QUERY_CONTEXT,
            },
            {
                "step_num": 1,
                "state": "s1",
                "action": "a_R",
                "normalized_action": "a_R",
                "llm_step_score": 2,
                "reward": 2,
                "url": TOY_URL,
                "step_summary": SECOND_CONTEXT,
            },
        ],
    }
    with contextlib.redirect_stdout(io.StringIO()):
        memory._store_step_in_vector_db(["s0", "s1"], ["a_L", "a_R"], 0, episode)
        memory._store_step_in_vector_db(["s0", "s1"], ["a_L", "a_R"], 1, episode)
    return memory


def policy_options(target_policy: str) -> Dict[int, Dict[str, Any]]:
    if target_policy not in {"pi_A", "pi_B"}:
        raise ValueError(target_policy)
    selected = "a_L" if target_policy == "pi_A" else "a_R"
    return {
        1: {
            "action": "a_L",
            "normalized_action": "a_L",
            "normalized_prob": 1.0 if selected == "a_L" else 0.0,
            "token": "1",
        },
        2: {
            "action": "a_R",
            "normalized_action": "a_R",
            "normalized_prob": 1.0 if selected == "a_R" else 0.0,
            "token": "2",
        },
    }


def choose_base_action(target_policy: str) -> str:
    options = policy_options(target_policy)
    return max(options.values(), key=lambda row: row["normalized_prob"])["action"]


def native_decision(target_policy: str, seed: int = 0) -> Dict[str, Any]:
    """Execute the exact extracted retrieval/value/policy functions without oracle inputs."""
    memory = build_native_memory()
    _, agent_class = load_native_classes()
    agent = agent_class()
    agent.enable_cross_mem = True
    agent.cross_mem = memory
    agent.game_history = []
    options = policy_options(target_policy)
    state_node = SimpleNamespace(state=QUERY_CONTEXT, instruction=TASK_GOAL)
    random.seed(seed)
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        updated = agent.update_scores(
            state_node,
            options,
            k=10,
            r=0.8,
            memory_text=QUERY_CONTEXT,
            current_url=TOY_URL,
            screenshots_dir=None,
        )
    if not updated:
        raise RuntimeError("Native JitRL update returned no options")
    choice_num, choice = max(
        updated.items(), key=lambda item: item[1].get("corrected_logprob", float("-inf"))
    )
    retrieved = memory.last_retrieval
    historical = next(row for row in retrieved if row[2]["normalized_action"] == "a_L")
    left = next(row for row in updated.values() if row["normalized_action"] == "a_L")
    right = next(row for row in updated.values() if row["normalized_action"] == "a_R")
    return {
        "target_policy": target_policy,
        "base_action": choose_base_action(target_policy),
        "chosen_action": choice["action"],
        "choice_option": choice_num,
        "retrieved": bool(retrieved),
        "retrieved_count": len(retrieved),
        "retrieval_score": float(historical[0]),
        "historical_return": float(historical[1]),
        "native_signal": float(left["normalized_advantage"]),
        "native_raw_advantage": float(left["raw_advantage"]),
        "left_base_score": float(left["normalized_prob"]),
        "right_base_score": float(right["normalized_prob"]),
        "left_corrected_score": float(left["corrected_logprob"]),
        "right_corrected_score": float(right["corrected_logprob"]),
        "policy_bias_applied": choice["action"] != choose_base_action(target_policy),
        "memory_read": True,
        "oracle_read": False,
        "native_log": capture.getvalue(),
    }


def adapter_mapping() -> Dict[str, str]:
    return {
        "storage": "WebArena/memory_agents/utils/cross_episode_memory.py:CrossEpisodeMemory._store_step_in_vector_db",
        "retrieval": "WebArena/memory_agents/utils/cross_episode_memory.py:CrossEpisodeMemory.retrieve_similar_with_vector",
        "value_and_advantage": "WebArena/memory_agents/jitrl_agent.py:BrowserGymJitRLAgent.update_scores",
        "policy_influence": "WebArena/memory_agents/jitrl_agent.py:BrowserGymJitRLAgent.update_scores and generate_action argmax",
        "adapter_boundary": "pre-materialized trajectory text and canonical toy action normalization only",
    }
