"""Lock and verify the Stage-8C preregistration and formal artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = HERE / "results"
JITRL = REPO / "idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl"
EXPECTED_COMMIT = "143d22185d95fbf633a0befe6861d5e8b732543b"
EXPECTED_PYTHON = "3.10.21"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_files() -> list[Path]:
    return [HERE / "preregistration.md", *sorted(HERE.glob("*.py"))]


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(JITRL), *args], text=True).strip()


def verify_lock() -> tuple[bool, list[str]]:
    path = RESULTS / "preregistration_manifest.json"
    if not path.exists():
        return False, ["missing preregistration_manifest.json"]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    expected = manifest.get("files", {})
    current_names = {p.name for p in locked_files()}
    if set(expected) != current_names:
        problems.append("locked file set changed")
    for file in locked_files():
        if expected.get(file.name) != sha256(file):
            problems.append(f"hash mismatch: {file.name}")
    return not problems, problems


def lock() -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    target = RESULTS / "preregistration_manifest.json"
    if target.exists():
        raise RuntimeError("lock already exists")
    manifest = {
        "locked_before_formal": not (RESULTS / "formal_started.json").exists(),
        "files": {p.name: sha256(p) for p in locked_files()},
        "expected_jitrl_commit": EXPECTED_COMMIT,
        "python": platform.python_version(),
    }
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def final() -> dict[str, Any]:
    lock_ok, lock_problems = verify_lock()
    tests_path = RESULTS / "preformal_tests.json"
    tests = json.loads(tests_path.read_text(encoding="utf-8")) if tests_path.exists() else {}
    formal_path = RESULTS / "formal_summary.json"
    formal = json.loads(formal_path.read_text(encoding="utf-8")) if formal_path.exists() else {}
    required = [
        "formal_source_memories.csv", "formal_retrieval_attempts.json",
        "formal_retrieval_events.csv", "formal_native_episodes.jsonl",
        "paired_interventions.csv", "failure_candidates.csv", "confirmed_failures.csv",
        "metrics.json", "gate_results.json", "experiment_summary.json",
    ]
    checks = {
        "locked_hashes": lock_ok,
        "python_3_10_21": platform.python_version() == EXPECTED_PYTHON,
        "jitrl_commit": git("rev-parse", "HEAD") == EXPECTED_COMMIT,
        "jitrl_clean": not bool(git("status", "--short")),
        "preformal_tests_at_least_20": tests.get("passed", 0) >= 20 and tests.get("failed", 1) == 0,
        "formal_exactly_20": formal.get("episodes_completed") == 20,
        "formal_call_budget": formal.get("model_calls", 10**9) <= 160,
        "formal_not_restarted": json.loads((RESULTS / "formal_started.json").read_text()).get("restart_count") == 0 if (RESULTS / "formal_started.json").exists() else False,
        "required_outputs": all((RESULTS / name).exists() for name in required),
    }
    report = {"ok": all(checks.values()), "checks": checks, "lock_problems": lock_problems}
    (RESULTS / "final_verification.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if not report["ok"]:
        raise RuntimeError(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lock", action="store_true")
    group.add_argument("--final", action="store_true")
    args = parser.parse_args()
    print(json.dumps(lock() if args.lock else final(), indent=2, sort_keys=True))
