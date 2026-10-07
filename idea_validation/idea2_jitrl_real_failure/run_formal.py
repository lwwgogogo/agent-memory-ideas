"""Execute the single preregistered 20-episode formal run."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from paired_intervention import PAIRED_COLUMNS
from runtime_runner import HERE, JITRL, RESULTS, execute_run, write_csv, write_json


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(JITRL), *args], text=True).strip()


if __name__ == "__main__":
    marker = RESULTS / "formal_started.json"
    if marker.exists():
        raise RuntimeError("formal run already started; preregistration forbids restart")
    write_json(marker, {"started_unix": time.time(), "episodes": 20, "restart_count": 0})
    summary = execute_run("formal", episodes=20, max_calls=160)
    write_csv(RESULTS / "paired_interventions.csv", PAIRED_COLUMNS, [])
    write_csv(RESULTS / "failure_candidates.csv", PAIRED_COLUMNS, [])
    write_csv(RESULTS / "confirmed_failures.csv", PAIRED_COLUMNS, [])
    manifest = {
        "jitrl_commit": git_output("rev-parse", "HEAD"),
        "jitrl_clean": not bool(git_output("status", "--short")),
        "formal_summary": summary,
        "paired_intervention_note": (
            "No paired replay is possible without a returned native retrieval item; "
            "the frozen runtime returned zero items when native vector retrieval was unavailable."
        ),
    }
    write_json(RESULTS / "run_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
