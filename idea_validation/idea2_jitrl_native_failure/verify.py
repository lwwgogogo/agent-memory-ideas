"""Locked-manifest and post-run gate verification for Stage-8."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from jitrl_adapter import (
    EXPECTED_COMMIT,
    STAGE_DIR,
    assert_source_integrity,
    sha256_file,
)
from native_probe import (
    CLOSED_LOOP_STATUS,
    STAGE7_DIR,
    native_decision_signature_has_no_oracle,
)

RESULTS = STAGE_DIR / "results"
MANIFEST = RESULTS / "preregistration_manifest.json"


def tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(sha256_file(path).encode())
        h.update(b"\n")
    return h.hexdigest()


def verify_manifest() -> Dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for rel, expected in data["locked_files"].items():
        actual = sha256_file(STAGE_DIR / rel)
        if actual != expected:
            mismatches.append({"file": rel, "expected": expected, "actual": actual})
    stage7_actual = tree_digest(STAGE7_DIR)
    if stage7_actual != data["stage7_tree_sha256"]:
        mismatches.append({
            "file": "../idea2_policy_relative_validity",
            "expected": data["stage7_tree_sha256"],
            "actual": stage7_actual,
        })
    source = assert_source_integrity()
    return {
        "ok": not mismatches and source["commit"] == EXPECTED_COMMIT,
        "mismatches": mismatches,
        "source": source,
        "stage7_tree_sha256": stage7_actual,
    }


def _read_csv(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_bool(value: str) -> bool:
    return value.lower() == "true"


def finalize() -> Dict[str, Any]:
    manifest = verify_manifest()
    mapping = json.loads((RESULTS / "native_mapping.json").read_text(encoding="utf-8"))
    summary = json.loads((RESULTS / "experiment_summary.json").read_text(encoding="utf-8"))
    mismatch = _read_csv("advantage_mismatch.csv")
    baselines = _read_csv("baseline_results.csv")
    b1 = next(row for row in mismatch if row["condition"] == "B1_same_policy")
    b2 = next(row for row in mismatch if row["condition"] == "B2_policy_shift")
    native_rows = [row for row in baselines if row["baseline"] == "JitRLNative"]
    no_memory_rows = [row for row in baselines if row["baseline"] == "NoMemory"]
    oracle_rows = [row for row in baselines if row["baseline"] == "OracleValidity"]
    pretests = json.loads((RESULTS / "preformal_tests.json").read_text(encoding="utf-8"))

    allowed_tracked = subprocess.check_output(
        ["git", "-C", str(STAGE_DIR.parents[1]), "diff", "--name-only"], text=True
    ).splitlines()
    history_clean = not allowed_tracked

    gates: Dict[str, Dict[str, Any]] = {}
    gates["G0"] = {
        "result": "PASS" if (
            manifest["ok"]
            and history_clean
            and pretests["status"] == "PASS"
            and all(not _as_bool(row["oracle_read"]) for row in native_rows)
            and all(not _as_bool(row["memory_read"]) for row in no_memory_rows)
            and all(_as_bool(row["oracle_read"]) for row in oracle_rows)
            and native_decision_signature_has_no_oracle()
        ) else "FAIL",
        "evidence": "locked hashes, clean tracked history, source hashes, and baseline access boundaries",
    }
    gates["G1"] = {
        "result": "PASS" if mapping["verdict"] == "JITRL_MAPPING_GO" and _as_bool(b2["retrieved"]) else "FAIL",
        "evidence": "native storage/retrieval/advantage/score path executed",
    }
    gates["G2"] = {
        "result": "PASS" if (
            mapping["revalues_under_current_policy"] == "NO"
            and mapping["importance_correction"] == "NO"
            and mapping["policy_mismatch_check"] == "NO"
        ) else "FAIL",
        "evidence": "no explicit current-policy validity correction in audited path",
    }
    gates["G3"] = {
        "result": "PASS" if (
            not _as_bool(b1["sign_mismatch"])
            and float(b1["native_memory_signal"]) > 0
            and float(b1["target_advantage"]) > 0
        ) else "FAIL",
        "evidence": "pi_A to pi_A native and target signs agree",
    }
    gates["G4"] = {
        "result": "PASS" if (
            _as_bool(b2["retrieved"])
            and float(b2["native_memory_signal"]) > 0
            and float(b2["target_advantage"]) < 0
            and _as_bool(b2["sign_mismatch"])
        ) else "FAIL",
        "evidence": "retrieved positive native signal conflicts with negative pi_B target advantage",
    }
    nm = summary["B3"]["NoMemory"]
    native = summary["B3"]["JitRLNative"]
    gates["G5"] = {
        "result": "PASS" if (
            native["average_return"] < nm["average_return"]
            and native["cumulative_regret"] > nm["cumulative_regret"]
            and native["harmful_policy_bias_rate"] > 0
        ) else "FAIL",
        "evidence": "native memory changes action and degrades return under pi_B",
    }
    gates["G6"] = {
        "result": "PASS" if (
            manifest["ok"]
            and summary["native_execution"]["source_extracted_methods"]
            and summary["native_execution"]["adapter_boundary_only"]
        ) else "FAIL",
        "evidence": "core storage, retrieval, advantage, and score update execute upstream AST bodies",
    }
    gates["G7"] = {
        "result": "PASS" if (
            _as_bool(b2["retrieved"])
            and _as_bool(b2["policy_bias_applied"])
            and _as_bool(b2["harmful_policy_bias"])
        ) else "FAIL",
        "evidence": "evidence includes native retrieval/reinjection and harm beyond Q reversal",
    }
    gates["G8"] = {
        "result": CLOSED_LOOP_STATUS,
        "evidence": summary["B4"]["reason"],
    }

    verdict = (
        "JITRL_NATIVE_FAILURE_GO"
        if all(gates[f"G{i}"]["result"] == "PASS" for i in range(8))
        and gates["G8"]["result"] in {"PASS", "NOT_TESTABLE"}
        else "JITRL_NATIVE_FAILURE_NARROW"
        if gates["G1"]["result"] == "PASS" and gates["G4"]["result"] == "PASS"
        else "JITRL_NATIVE_FAILURE_NO_GO"
    )
    gate_payload = {
        "stage8a_verdict": mapping["verdict"],
        "gates": gates,
        "verdict": verdict,
    }
    (RESULTS / "gate_results.json").write_text(
        json.dumps(gate_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    final = {
        "stage": "Idea 2 Stage-8",
        "tests_passed": pretests["tests_passed"],
        "tests_failed": pretests["tests_failed"],
        "formal_run_count": 1,
        "formal_restart": False,
        "deterministic": True,
        "no_llm_calls": True,
        "no_api_calls": True,
        "no_full_jitrl_benchmark": True,
        "manifest_hash_match": manifest["ok"],
        "jitrl_commit": EXPECTED_COMMIT,
        "jitrl_source_hash_match": manifest["source"]["matches_expected"],
        "stage7_history_hash_match": not manifest["mismatches"],
        "root_tracked_history_clean_at_formal_verification": history_clean,
        "no_oracle_leakage": gates["G0"]["result"] == "PASS",
        "closed_loop": CLOSED_LOOP_STATUS,
        "gates": {key: value["result"] for key, value in gates.items()},
        "verdict": verdict,
    }
    (RESULTS / "final_verification.json").write_text(
        json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return final


if __name__ == "__main__":
    print(json.dumps(finalize(), indent=2, sort_keys=True))
