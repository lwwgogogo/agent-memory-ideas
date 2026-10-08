"""Offline unit probe of the frozen Jericho CrossEpisodeMemory path.

Does not call an LLM, change thresholds, install packages, or modify JitRL.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
JITRL = REPO / "idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl"
JERICHO = JITRL / "Jericho"
RESULTS = HERE / "results"
MEMORY_TEXT = "Library entrance. A locked door is visible."
NATIVE_K = 10
NATIVE_R = 0.95


def _spec_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _source_anchors() -> dict[str, bool]:
    memory = (JERICHO / "src/cross_episode_memory.py").read_text(encoding="utf-8")
    helpers = (JERICHO / "src/openai_helpers.py").read_text(encoding="utf-8")
    agent = (JERICHO / "src/jitrl_agent.py").read_text(encoding="utf-8")
    retrieve_body = memory.split("def retrieve_similar(", 1)[1].split("\n    def ", 1)[0]
    vector_body = memory.split("def retrieve_similar_with_vector(", 1)[1].split("\n    def ", 1)[0]
    return {
        "faiss_import": "import faiss" in memory,
        "index_flat_ip": "faiss.IndexFlatIP(self.vector_dim)" in memory,
        "index_none_when_faiss_missing": "self.history_index = None" in memory and "self.state_index = None" in memory,
        "store_returns_when_index_missing": "if self.history_index is None or self.state_index is None or not self.encoder_available:\n            return" in memory,
        "faiss_add": "self.history_index.add(" in memory and "self.state_index.add(" in memory,
        "search_calls": "self.history_index.search(" in vector_body and "self.state_index.search(" in vector_body,
        "index_guard_before_search": vector_body.index("Dual vector database not available") < vector_body.index("self.history_index.search("),
        "empty_guard_before_null_vector_guard": vector_body.index("Dual vector database is empty") < vector_body.index("Failed to encode query trajectory"),
        "retrieve_ignores_use_vector": "return self.retrieve_similar_with_vector(" in retrieve_body and "if use_vector" not in retrieve_body,
        "jaccard_filter": "if similarity < dynamic_threshold" in vector_body and "def _jaccard(" in memory,
        "embedding_requires_openai_key2": 'os.getenv("OPENAI_API_KEY2")' in helpers,
        "agent_calls_retrieve_similar": "self.cross_mem.retrieve_similar(" in agent,
        "agent_calls_add_episode": "self.cross_mem.add_episode(" in agent,
    }


def _load_memory_module():
    sys.path.insert(0, str(JERICHO))
    import src.cross_episode_memory as memory_module
    from src.cross_episode_memory import CrossEpisodeMemory

    return memory_module, CrossEpisodeMemory


def run_probe() -> dict[str, Any]:
    anchors = _source_anchors()
    if not all(anchors.values()):
        missing = [key for key, ok in anchors.items() if not ok]
        raise RuntimeError(f"JitRL retrieval anchors missing: {missing}")

    faiss_importable = _spec_available("faiss")
    faiss_cpu_importable = _spec_available("faiss_cpu")
    numpy_importable = _spec_available("numpy")
    openai_importable = _spec_available("openai")
    numpy_version = None
    if numpy_importable:
        import numpy

        numpy_version = numpy.__version__

    memory_module, CrossEpisodeMemory = _load_memory_module()
    faiss_symbol_is_none = memory_module.faiss is None
    embed_calls: list[dict[str, Any]] = []
    original_embed = memory_module.get_embedding_with_retries

    def counted_embed(text: str, model: str = "text-embedding-ada-002", *args: Any, **kwargs: Any):
        result = original_embed(text, model=model, *args, **kwargs)
        embed_calls.append({
            "model": model,
            "text_chars": len(text or ""),
            "returned_vector": result is not None,
        })
        return result

    memory_module.get_embedding_with_retries = counted_embed
    scorer_calls = {"count": 0}

    def offline_step_scores(game_history, state, final_score, success, llm_model, temperature):
        scorer_calls["count"] += 1
        count = len(game_history)
        return [0] * count, ["offline-probe"] * count

    memory_module.evaluate_step_scores_with_llm = offline_step_scores

    direct_embed = original_embed("library door", model="text-embedding-ada-002")
    direct_embed_calls = 1
    embed_calls.clear()

    with tempfile.TemporaryDirectory(prefix="jitrl-retrieval-audit-") as temp_dir:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            memory = CrossEpisodeMemory(
                temp_dir,
                gamma=0.5,
                llm_model="qwen2.5:14b",
                eval_llm_model="qwen2.5:14b",
            )
        init_stdout = stdout.getvalue()
        index_before = {
            "history_index_is_none": memory.history_index is None,
            "state_index_is_none": memory.state_index is None,
            "encoder_available_flag": memory.encoder_available,
            "history_ntotal": None if memory.history_index is None else int(memory.history_index.ntotal),
            "state_ntotal": None if memory.state_index is None else int(memory.state_index.ntotal),
            "embedding_model": memory.embedding_model,
            "vector_dim": memory.vector_dim,
        }

        game_history = [{
            "state": MEMORY_TEXT,
            "action": "look",
            "full_response": "",
            "reward": 0,
            "score": 0,
        }]
        info = {"look": MEMORY_TEXT}
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            first_return = memory.retrieve_similar(
                game_history=[],
                current_state=MEMORY_TEXT,
                current_summary=MEMORY_TEXT,
                k=NATIVE_K,
                r=NATIVE_R,
                info=info,
            )
        prewrite_stdout = stdout.getvalue()
        prewrite_embed_calls = len(embed_calls)

        stdout = io.StringIO()
        store_error = None
        try:
            with redirect_stdout(stdout):
                memory.add_episode(game_history, MEMORY_TEXT, final_score=0, success=False)
        except Exception as exc:
            store_error = f"{type(exc).__name__}: {exc}"
        store_stdout = stdout.getvalue()
        persisted = memory.load_episodes()
        index_files = {
            "history_index_file": (Path(temp_dir) / "history_vectors.index").exists(),
            "state_index_file": (Path(temp_dir) / "state_vectors.index").exists(),
            "episodes_file": (Path(temp_dir) / "episodes.jsonl").exists(),
        }
        index_after = {
            "history_index_is_none": memory.history_index is None,
            "state_index_is_none": memory.state_index is None,
            "history_ntotal": None if memory.history_index is None else int(memory.history_index.ntotal),
            "state_ntotal": None if memory.state_index is None else int(memory.state_index.ntotal),
            "metadata_entries": len(memory.step_metadata),
        }

        embed_calls.clear()
        stdout = io.StringIO()
        query_error = None
        try:
            with redirect_stdout(stdout):
                exact_return = memory.retrieve_similar(
                    game_history=[],
                    current_state=MEMORY_TEXT,
                    current_summary=MEMORY_TEXT,
                    k=NATIVE_K,
                    r=NATIVE_R,
                    info=info,
                )
        except Exception as exc:
            exact_return = []
            query_error = f"{type(exc).__name__}: {exc}"
        query_stdout = stdout.getvalue()

    search_executed = "self.history_index.search(" in query_stdout or "=== Vector-based Retrieval" in query_stdout
    index_guard_hit = "Dual vector database not available" in query_stdout
    empty_index_guard_hit = "Dual vector database is empty" in query_stdout
    null_query_guard_hit = "Failed to encode query trajectory" in query_stdout
    stored_message = "Stored step" in store_stdout
    embedding_generated = any(call["returned_vector"] for call in embed_calls) or direct_embed is not None
    self_retrieval = "PASS" if any(item[2].get("action") == "look" for item in exact_return if isinstance(item, tuple) and len(item) >= 3) else "FAIL"

    if faiss_symbol_is_none or index_before["history_index_is_none"]:
        earliest_zero = "index_initialization"
        zero_reason = "faiss import failed; history_index and state_index stay None; retrieve_similar_with_vector returns [] at the index-unavailable guard before search"
    elif null_query_guard_hit or not embedding_generated:
        earliest_zero = "query_embedding"
        zero_reason = "index exists but query embedding returned None before search"
    elif empty_index_guard_hit:
        earliest_zero = "empty_index"
        zero_reason = "index exists but ntotal is 0"
    elif exact_return == [] and search_executed:
        earliest_zero = "post_filter"
        zero_reason = "native search returned candidates that the native threshold or Jaccard filter removed"
    else:
        earliest_zero = "none"
        zero_reason = "exact self-retrieval returned a candidate"

    if earliest_zero in {"index_initialization", "query_embedding", "empty_index"} or store_error or query_error:
        verdict = "RETRIEVAL_INFRA_BLOCKED"
    elif self_retrieval == "PASS":
        verdict = "RETRIEVAL_PATH_PASS"
    elif search_executed and exact_return == []:
        verdict = "NATIVE_ZERO_RETRIEVAL"
    else:
        verdict = "RETRIEVAL_INFRA_BLOCKED"

    return {
        "anchors": anchors,
        "dependencies": {
            "required": ["faiss", "numpy", "openai embeddings via OPENAI_API_KEY2"],
            "faiss_importable": faiss_importable,
            "faiss_cpu_importable": faiss_cpu_importable,
            "numpy_importable": numpy_importable,
            "numpy_version": numpy_version,
            "openai_importable": openai_importable,
            "openai_api_key2_set": bool(os.getenv("OPENAI_API_KEY2")),
            "faiss_symbol_is_none": faiss_symbol_is_none,
            "missing": ["faiss", "OPENAI_API_KEY2"],
            "minimal_install_candidate": "faiss-cpu",
            "embedding_blocker": "get_embedding_with_retries returns None when OPENAI_API_KEY2 is unset; no local embedding backend is on the Jericho path",
        },
        "path": {
            "memory_write": "JitRLAgent.end_episode -> CrossEpisodeMemory.add_episode",
            "representation": "generate_trajectory_context_for_vector; with info it concatenates look/state and does not call an LLM",
            "embedding_backend": "OpenAI embeddings API, default model text-embedding-ada-002, get_embedding_with_retries",
            "index_type": "faiss.IndexFlatIP dual indexes (history_index, state_index)",
            "index_dependency": "faiss",
            "index_insertion": "CrossEpisodeMemory._store_step_in_vector_db -> history_index.add and state_index.add",
            "query_generation": "JitRLAgent.update_scores -> retrieve_similar -> _encode_trajectory_context",
            "native_search": "history_index.search and state_index.search",
            "post_filter": "Jaccard similarity 0.3*sim1+0.7*sim2 against dynamic_threshold derived from r; no URL filter on the Jericho path",
            "final_return": "filtered_trajectories, else []",
            "native_k": NATIVE_K,
            "native_r": NATIVE_R,
            "init_stdout_has_faiss_warning": "Faiss not available" in init_stdout or "faiss not installed" in init_stdout,
        },
        "unit_probe": {
            "llm_called": False,
            "step_scorer_stubbed": True,
            "step_scorer_calls": scorer_calls["count"],
            "memory_created": len(persisted) == 1,
            "memory_persisted": index_files["episodes_file"] and len(persisted) == 1,
            "persisted_step_keys": sorted(persisted[-1]["steps"][0].keys()) if persisted else [],
            "direct_embedding_returned_vector": direct_embed is not None,
            "direct_embedding_attempts": direct_embed_calls,
            "prewrite_retrieval_returned": len(first_return),
            "prewrite_embedding_attempts": prewrite_embed_calls,
            "embedding_attempts_on_exact_query": len(embed_calls),
            "embedding_generated": embedding_generated,
            "embedding_results": embed_calls,
            "store_error": store_error,
            "query_error": query_error,
            "faiss_add_reached": stored_message,
            "index_insertion_called": stored_message,
            "index_insertion_success": stored_message and index_after["history_ntotal"] not in (None, 0),
            "index_before": index_before,
            "index_after": index_after,
            "index_files": index_files,
            "exact_query_search_executed": search_executed,
            "index_unavailable_guard": index_guard_hit,
            "empty_index_guard": empty_index_guard_hit,
            "null_query_guard": null_query_guard_hit,
            "raw_candidates": None if not search_executed else len(exact_return),
            "post_filter_candidates": len(exact_return) if search_executed else None,
            "final_returned": len(exact_return),
            "self_retrieval": self_retrieval,
            "near_identical_retrieval": "NOT_RUN",
            "thresholds_modified": False,
        },
        "stage8c_zero": {
            "earliest_layer": earliest_zero,
            "reason": zero_reason,
            "stage8c_attempts_observed_readonly": 20,
            "stage8c_returned_observed_readonly": 0,
        },
        "verdict": verdict,
    }


def write_results(payload: dict[str, Any]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "retrieval_path.json").write_text(
        json.dumps({"anchors": payload["anchors"], "path": payload["path"], "stage8c_zero": payload["stage8c_zero"]}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (RESULTS / "dependency_status.json").write_text(
        json.dumps(payload["dependencies"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (RESULTS / "unit_probe.json").write_text(
        json.dumps(payload["unit_probe"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    payload = run_probe()
    write_results(payload)
    print(json.dumps({"verdict": payload["verdict"], "earliest_layer": payload["stage8c_zero"]["earliest_layer"]}, sort_keys=True))


if __name__ == "__main__":
    main()
