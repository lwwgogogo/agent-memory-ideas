"""Bounded Stage-8C0 JitRL smoke runner.

Default behavior audits dependencies. --run permits at most one Jericho
episode with one environment step.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import runpy
import sys
import tempfile
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
        "stage": "Idea 2 Stage-8C0",
        "task": "Jericho/library",
        "status": "BLOCKED_BY_DEPENDENCY",
        "required_dependencies": state,
        "missing_dependencies": sorted(name for name, present in state.items() if not present),
        "episode_attempted": False,
        "episode_count": 0,
        "environment_initialized": False,
        "action_generated": False,
        "runner_completed": False,
        "trajectory_log_created": False,
        "model": backend_settings()["model"],
        "temperature": 0,
        "seed": 0,
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
    try:
        with tempfile.TemporaryDirectory(prefix="jitrl_stage8c0_") as tmp:
            sys.path.insert(0, str(JERICHO_DIR))
            settings = backend_settings()
            sys.argv = [
                str(JERICHO_DIR / "main.py"),
                "--game_name", "library",
                "--rom_path", str(JERICHO_DIR / "games"),
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
            payload = {
                "stage": "Idea 2 Stage-8C0",
                "task": "Jericho/library",
                "status": "PASS" if exit_code == 0 else "FAIL",
                "required_dependencies": state,
                "missing_dependencies": [],
                "episode_attempted": True,
                "episode_count": 1,
                "environment_initialized": bool(logs),
                "action_generated": "[CHOSEN_ACTION]" in log_text,
                "runner_completed": exit_code == 0,
                "trajectory_log_created": bool(logs),
                "model": settings["model"],
                "temperature": 0,
                "seed": 0,
                "exit_code": exit_code,
            }
    except Exception as exc:
        payload = {
            "stage": "Idea 2 Stage-8C0",
            "task": "Jericho/library",
            "status": "FAIL",
            "episode_attempted": True,
            "episode_count": 1,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
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
