"""Run the frozen native JitRL Jericho evaluator with observation-only hooks."""
from __future__ import annotations

import csv
import json
import os
import random
import shutil
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from paired_intervention import (
    BudgetGuard, RETRIEVAL_COLUMNS, SOURCE_COLUMNS, is_historically_positive,
    result_memory_id, retrieval_discounted_return, retrieval_result_dict,
    retrieval_similarity, state_hash,
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
JITRL = REPO / "idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl"
JERICHO = JITRL / "Jericho"
ROM_DIR = JERICHO / "jericho-games"
RESULTS = HERE / "results"
MODEL = "qwen2.5:14b"
BACKEND = "http://localhost:11434/v1"
SEED = 20261008
JITRL_COMMIT = "143d22185d95fbf633a0befe6861d5e8b732543b"


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


class Tracker:
    def __init__(self, run_kind: str, episodes: int, max_calls: int):
        self.run_kind = run_kind
        self.episodes = episodes
        self.guard = BudgetGuard(max_calls)
        self.current_episode = -1
        self.retrieval_attempts: list[dict[str, Any]] = []
        self.retrieval_events: list[dict[str, Any]] = []
        self.source_rows: list[dict[str, Any]] = []
        self.memory_writes = 0
        self.request_log: list[dict[str, Any]] = []

    def call_record(self, kwargs: dict[str, Any], response: Any) -> None:
        self.guard.charge()
        usage = getattr(response, "usage", None)
        self.request_log.append({
            "call": self.guard.calls,
            "episode": self.current_episode,
            "model": kwargs.get("model"),
            "temperature": kwargs.get("temperature"),
            "max_tokens": kwargs.get("max_tokens"),
            "response_format": bool(kwargs.get("response_format")),
            "prompt_chars": sum(len(str(x.get("content", ""))) for x in kwargs.get("messages", [])),
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
        })


def make_args(output_path: Path, episodes: int) -> SimpleNamespace:
    return SimpleNamespace(
        rom_path=str(ROM_DIR), game_name="library", output_path=str(output_path),
        env_step_limit=1, seed=SEED, llm_model=MODEL, top_actions=3,
        llm_temperature=0.0, max_memory=30, gamma=0.5,
        max_trajectory_window=5, exploration_rate=0.65, exploration_alpha=1.0,
        use_history_prompt=True, debug_info=False, track_valid_changes=False,
        agent_type="jitrl", eval_runs=episodes, evol_temperature=0.8,
        retrieval_top_k=10, retrieval_threshold=0.95,
        evolution_llm_model=MODEL, enable_cross_mem=True,
        update_guiding_prompt=False, use_valid_actions=True,
        confidence_mode="verbalized", eval_llm_model=MODEL,
    )


def execute_run(run_kind: str, episodes: int, max_calls: int) -> dict[str, Any]:
    if episodes < 1:
        raise ValueError("episodes must be positive")
    RESULTS.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS / f"native_output_{run_kind}"
    if output_path.exists():
        raise RuntimeError(f"refusing to overwrite existing run output: {output_path}")
    output_path.mkdir(parents=True)

    tracker = Tracker(run_kind, episodes, max_calls)
    random.seed(SEED)
    os.environ["PYTHONHASHSEED"] = str(SEED)
    os.environ.pop("OPENAI_API_KEY2", None)

    import dotenv
    dotenv.load_dotenv = lambda *args, **kwargs: False
    import openai
    original_openai = openai.OpenAI

    class CompletionProxy:
        def __init__(self, inner: Any):
            self.inner = inner

        def create(self, **kwargs: Any) -> Any:
            if tracker.guard.calls >= tracker.guard.max_calls:
                tracker.guard.charge()
            forced = dict(kwargs)
            forced["model"] = MODEL
            forced["temperature"] = 0.0
            response = self.inner.create(**forced)
            tracker.call_record(forced, response)
            return response

    class ChatProxy:
        def __init__(self, inner: Any):
            self.completions = CompletionProxy(inner.completions)

    class LocalOpenAI:
        def __init__(self, *args: Any, **kwargs: Any):
            inner = original_openai(api_key="ollama", base_url=BACKEND, timeout=180.0)
            self.chat = ChatProxy(inner.chat)
            self.embeddings = inner.embeddings

    openai.OpenAI = LocalOpenAI
    sys.path.insert(0, str(JERICHO))

    from src.cross_episode_memory import CrossEpisodeMemory
    from src.evaluation import GameEvaluator
    from src.jitrl_agent import JitRLAgent

    original_start = JitRLAgent.start_episode
    original_retrieve = CrossEpisodeMemory.retrieve_similar
    original_add = CrossEpisodeMemory.add_episode

    def tracked_start(agent: Any) -> Any:
        tracker.current_episode += 1
        return original_start(agent)

    def tracked_retrieve(memory: Any, *args: Any, **kwargs: Any) -> Any:
        episode = tracker.current_episode
        current_state = kwargs.get("current_state", args[1] if len(args) > 1 else "")
        step = len(kwargs.get("game_history", args[0] if args else []))
        attempt_id = f"{run_kind}-e{episode:03d}-s{step:03d}"
        returned = original_retrieve(memory, *args, **kwargs)
        tracker.retrieval_attempts.append({
            "run_kind": run_kind, "episode": episode, "step": step,
            "attempt_id": attempt_id, "current_state_hash": state_hash(current_state),
            "returned_count": len(returned), "history_index_available": memory.history_index is not None,
            "state_index_available": memory.state_index is not None,
        })
        for rank, item in enumerate(returned, start=1):
            result = retrieval_result_dict(item)
            signal = result.get("llm_step_score")
            tracker.retrieval_events.append({
                "run_kind": run_kind, "episode": episode, "step": step,
                "attempt_id": attempt_id, "rank": rank,
                "memory_id": result_memory_id(result),
                "similarity": retrieval_similarity(item),
                "discounted_return": retrieval_discounted_return(item),
                "historical_signal": signal,
                "historically_positive": is_historically_positive(signal),
                "source_action": result.get("action", ""),
                "current_state_hash": state_hash(current_state),
            })
        return returned

    def tracked_add(memory: Any, *args: Any, **kwargs: Any) -> Any:
        result = original_add(memory, *args, **kwargs)
        episodes_data = memory.load_episodes()
        if not episodes_data:
            raise RuntimeError("native add_episode returned without persisted episode")
        native_episode = episodes_data[-1]
        episode_index = tracker.current_episode
        tracker.memory_writes += 1
        for step in native_episode.get("steps", []):
            identity_record = dict(step)
            identity_record["episode_number"] = memory.current_episode_number
            tracker.source_rows.append({
                "run_kind": run_kind, "episode": episode_index,
                "step": step.get("step_num"), "memory_id": result_memory_id(identity_record),
                "state": step.get("state", ""), "action": step.get("action", ""),
                "reward": step.get("reward"), "score": step.get("score"),
                "delta_score": step.get("delta_score"),
                "llm_step_score": step.get("llm_step_score"),
                "source_policy_identity": "UNAVAILABLE",
            })
        return result

    JitRLAgent.start_episode = tracked_start
    CrossEpisodeMemory.retrieve_similar = tracked_retrieve
    CrossEpisodeMemory.add_episode = tracked_add

    started = time.time()
    try:
        evaluator = GameEvaluator(make_args(output_path, episodes))
        native_result = evaluator.run_evaluation()
    finally:
        openai.OpenAI = original_openai
        JitRLAgent.start_episode = original_start
        CrossEpisodeMemory.retrieve_similar = original_retrieve
        CrossEpisodeMemory.add_episode = original_add
    elapsed = time.time() - started

    write_csv(RESULTS / f"{run_kind}_source_memories.csv", SOURCE_COLUMNS, tracker.source_rows)
    write_csv(RESULTS / f"{run_kind}_retrieval_events.csv", RETRIEVAL_COLUMNS, tracker.retrieval_events)
    write_json(RESULTS / f"{run_kind}_retrieval_attempts.json", tracker.retrieval_attempts)
    with (RESULTS / f"{run_kind}_request_trace.jsonl").open("w", encoding="utf-8") as handle:
        for row in tracker.request_log:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    native_episode_files = list(output_path.rglob("episodes.jsonl"))
    if len(native_episode_files) != 1:
        raise RuntimeError(f"expected one native episodes.jsonl, found {len(native_episode_files)}")
    shutil.copyfile(native_episode_files[0], RESULTS / f"{run_kind}_native_episodes.jsonl")

    summary = {
        "run_kind": run_kind, "episodes_requested": episodes,
        "episodes_completed": len(native_result.get("individual_scores", [])),
        "scores": native_result.get("individual_scores", []),
        "memory_writes": tracker.memory_writes,
        "source_memory_steps": len(tracker.source_rows),
        "retrieval_attempts": len(tracker.retrieval_attempts),
        "retrieval_events": len(tracker.retrieval_events),
        "model_calls": tracker.guard.calls, "max_model_calls": max_calls,
        "elapsed_seconds": elapsed,
        "model": MODEL, "backend": BACKEND, "seed": SEED,
        "temperature": 0.0, "env_step_limit": 1,
        "faiss_available": False,
        "native_success": bool(native_result.get("success")),
    }
    write_json(RESULTS / f"{run_kind}_summary.json", summary)
    return summary
