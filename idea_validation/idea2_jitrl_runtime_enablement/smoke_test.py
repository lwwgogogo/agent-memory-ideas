"""Bounded Stage-8C0.1 JitRL smoke runner.

Default behavior audits dependencies. --run permits at most one Jericho
episode with one environment step.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import runpy
import sys
import tempfile
import time
import traceback
from pathlib import Path

from optional_backend_adapter import backend_settings, patch_openai_constructor

STAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = STAGE_DIR.parent.parent
JERICHO_DIR = REPO_ROOT / "idea_validation" / "idea2_policy_conditioned_memory_audit" / "third_party" / "jitrl" / "Jericho"
RESULT_PATH = STAGE_DIR / "results" / "smoke_test.json"
REQUIRED_IMPORTS = {
    "openai": "openai",
    "jericho": "jericho",
    "tiktoken": "tiktoken",
    "python-dotenv": "dotenv",
    "numpy": "numpy",
}


def dependency_state() -> dict[str, bool]:
    return {name: importlib.util.find_spec(module) is not None for name, module in REQUIRED_IMPORTS.items()}


def write_result(payload: dict) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def blocked_payload(state: dict[str, bool]) -> dict:
    return {
        "stage": "Idea 2 Stage-8C0.1",
        "task": "Jericho/library",
        "status": "BLOCKED_BY_DEPENDENCY",
        "required_dependencies": state,
        "missing_dependencies": sorted(name for name, present in state.items() if not present),
        "episode_attempted": False,
        "episode_count": 0,
        "environment_initialized": False,
        "llm_request_success": False,
        "response_parse_success": False,
        "action_generated": False,
        "action_in_valid_actions": None,
        "environment_step_success": False,
        "trajectory_created": False,
        "memory_written_if_any": False,
        "exception": None,
        "model": backend_settings()["model"],
        "backend": backend_settings()["base_url"],
        "temperature": 0,
        "seed": 0,
        "wall_time_seconds": 0.0,
        "prompt_tokens": None,
        "completion_tokens": None,
        "output_characters": 0,
    }


def extract_observations(log_text: str) -> dict:
    raw_match = re.search(r"\[RAW_LLM_OUTPUT\] (.*?)\n\[CHOSEN_ACTION\] (.*?)\n", log_text, re.DOTALL)
    raw_output = raw_match.group(1).strip() if raw_match else ""
    chosen_action = raw_match.group(2).strip() if raw_match else ""
    cleaned = re.sub(r"^~~~(?:json)?\s*", "", raw_output)
    cleaned = re.sub(r"\s*~~~$", "", cleaned)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    response_parse_success = False
    if cleaned:
        try:
            json.loads(cleaned)
            response_parse_success = True
        except json.JSONDecodeError:
            response_parse_success = False

    valid_match = re.search(r"\[VALID_ACTIONS\] (.*?)\n", log_text)
    action_in_valid_actions = None
    if valid_match and chosen_action:
        try:
            valid_actions = ast.literal_eval(valid_match.group(1))
            action_in_valid_actions = chosen_action in valid_actions
        except (ValueError, SyntaxError):
            action_in_valid_actions = None

    return {
        "raw_output": raw_output,
        "chosen_action": chosen_action,
        "response_parse_success": response_parse_success,
        "action_in_valid_actions": action_in_valid_actions,
    }


def run_one_episode() -> dict:
    state = dependency_state()
    if not all(state.values()):
        payload = blocked_payload(state)
        write_result(payload)
        return payload

    original_openai = patch_openai_constructor()
    import openai

    old_argv = sys.argv[:]
    old_path = sys.path[:]
    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix="jitrl_stage8c01_") as tmp:
            sys.path.insert(0, str(JERICHO_DIR))
            settings = backend_settings()
            sys.argv = [
                str(JERICHO_DIR / "main.py"),
                "--game_name", "library",
                "--rom_path", str(JERICHO_DIR / "jericho-games"),
                "--output_path", tmp,
                "--env_step_limit", "1",
                "--seed", "0",
                "--llm_model", settings["model"],
                "--eval_llm_model", settings["model"],
                "--llm_temperature", "0",
                "--eval_runs", "1",
                "--agent_type", "jitrl",
                "--no-enable_cross_mem",
                "--no-update_guiding_prompt",
                "--confidence_mode", "verbalized",
            ]
            exit_code = 0
            try:
                runpy.run_path(str(JERICHO_DIR / "main.py"), run_name="__main__")
            except SystemExit as exc:
                exit_code = int(exc.code or 0)

            logs = list(Path(tmp).rglob("episode_*.txt"))
            log_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in logs)
            observed = extract_observations(log_text)
            elapsed = time.perf_counter() - started
            action_generated = bool(observed["chosen_action"])
            step_success = "[REWARD]" in log_text and "[CUM_REWARD]" in log_text
            payload = {
                "stage": "Idea 2 Stage-8C0.1",
                "task": "Jericho/library",
                "status": "PASS" if exit_code == 0 and action_generated and step_success and logs else "FAIL",
                "required_dependencies": state,
                "missing_dependencies": [],
                "episode_attempted": True,
                "episode_count": 1,
                "environment_initialized": bool(logs),
                "llm_request_success": bool(observed["raw_output"]),
                "response_parse_success": observed["response_parse_success"],
                "action_generated": action_generated,
                "action": observed["chosen_action"],
                "action_in_valid_actions": observed["action_in_valid_actions"],
                "environment_step_success": step_success,
                "trajectory_created": bool(logs),
                "trajectory_log_count": len(logs),
                "memory_written_if_any": False,
                "memory_mode": "disabled_for_transport_runtime_smoke",
                "exception": None,
                "model": settings["model"],
                "backend": settings["base_url"],
                "temperature": 0,
                "seed": 0,
                "wall_time_seconds": elapsed,
                "prompt_tokens": None,
                "completion_tokens": None,
                "output_characters": len(observed["raw_output"]),
                "exit_code": exit_code,
            }
    except Exception as exc:
        payload = {
            "stage": "Idea 2 Stage-8C0.1",
            "task": "Jericho/library",
            "status": "FAIL",
            "episode_attempted": True,
            "episode_count": 1,
            "environment_initialized": False,
            "llm_request_success": False,
            "response_parse_success": False,
            "action_generated": False,
            "action_in_valid_actions": None,
            "environment_step_success": False,
            "trajectory_created": False,
            "memory_written_if_any": False,
            "exception": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
            "model": backend_settings()["model"],
            "backend": backend_settings()["base_url"],
            "temperature": 0,
            "seed": 0,
            "wall_time_seconds": time.perf_counter() - started,
            "prompt_tokens": None,
            "completion_tokens": None,
            "output_characters": 0,
        }
    finally:
        openai.OpenAI = original_openai
        sys.argv = old_argv
        sys.path[:] = old_path

    write_result(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="Permit the bounded one-episode smoke.")
    args = parser.parse_args()
    state = dependency_state()
    payload = run_one_episode() if args.run else blocked_payload(state)
    write_result(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] in {"PASS", "BLOCKED_BY_DEPENDENCY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
