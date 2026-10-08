"""Integrity checks and gate report for the retrieval-path audit."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
JITRL = REPO / "idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl"
STAGE8C = REPO / "idea_validation/idea2_jitrl_real_failure"
RESULTS = HERE / "results"
EXPECTED_COMMIT = "143d22185d95fbf633a0befe6861d5e8b732543b"
EXPECTED_VERDICT = "REAL_JITRL_FAILURE_NO_GO"


def git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()


def main() -> None:
    from retrieval_probe import run_probe, write_results

    jitrl_head = git(JITRL, "rev-parse", "HEAD")
    jitrl_status = git(JITRL, "status", "--short")
    stage8c_status = git(REPO, "status", "--short", "--", "idea_validation/idea2_jitrl_real_failure")
    stage8c_diff = git(REPO, "diff", "--", "idea_validation/idea2_jitrl_real_failure")
    recorded = json.loads((STAGE8C / "results/final_verification.json").read_text(encoding="utf-8"))
    payload = run_probe()
    write_results(payload)

    g0 = (
        jitrl_head == EXPECTED_COMMIT
        and jitrl_status == ""
        and stage8c_status == ""
        and stage8c_diff == ""
        and recorded.get("final_verdict") == EXPECTED_VERDICT
    )
    g1 = all(payload["anchors"].values())
    deps = payload["dependencies"]
    g2 = deps["faiss_importable"] is False and deps["numpy_importable"] is True and "faiss" in deps["missing"]
    probe = payload["unit_probe"]
    g3 = probe["index_after"]["history_index_is_none"] and probe["index_insertion_called"] is False
    g4 = probe["exact_query_search_executed"] is False and probe["index_unavailable_guard"] is True
    g5 = probe["self_retrieval"] == "PASS"
    g6 = payload["stage8c_zero"]["earliest_layer"] == "index_initialization"
    gates = {
        "G0": "PASS" if g0 else "FAIL",
        "G1": "PASS" if g1 else "FAIL",
        "G2": "PASS" if g2 else "FAIL",
        "G3": "PASS" if g3 else "FAIL",
        "G4": "PASS" if g4 else "FAIL",
        "G5": "PASS" if g5 else "FAIL",
        "G6": "PASS" if g6 else "FAIL",
        "verdict": payload["verdict"],
        "frozen": {
            "jitrl_head": jitrl_head,
            "jitrl_status_clean": jitrl_status == "",
            "stage8c_status_clean": stage8c_status == "",
            "stage8c_verdict": recorded.get("final_verdict"),
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "gate_results.json").write_text(json.dumps(gates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    final = {
        "stage": "Idea 2 Stage-8C1",
        "verdict": payload["verdict"],
        "stage8c_verdict_retained": recorded.get("final_verdict"),
        "earliest_zero_layer": payload["stage8c_zero"]["earliest_layer"],
        "self_retrieval": probe["self_retrieval"],
        "near_identical_retrieval": probe["near_identical_retrieval"],
        "gates": {key: gates[key] for key in ("G0", "G1", "G2", "G3", "G4", "G5", "G6")},
    }
    (RESULTS / "final_verification.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if payload["verdict"] != "RETRIEVAL_INFRA_BLOCKED":
        raise SystemExit(f"unexpected verdict: {payload['verdict']}")
    if not all(gates[key] == ("FAIL" if key == "G5" else "PASS") for key in ("G0", "G1", "G2", "G3", "G4", "G5", "G6")):
        raise SystemExit(f"unexpected gates: {gates}")
    print(json.dumps({"verdict": payload["verdict"], "gates": final["gates"]}, sort_keys=True))


if __name__ == "__main__":
    main()
