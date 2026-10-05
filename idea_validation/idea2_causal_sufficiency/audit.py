import datetime, json, math, re, subprocess, sys
from pathlib import Path
from core import ROOT

def main():
    repo = ROOT.parent.parent
    journal = ROOT / "results" / "raw_outputs.jsonl"
    lines = [json.loads(x) for x in journal.read_text(encoding="utf-8").splitlines() if x]
    rows = json.loads((ROOT / "results" / "llm_results.json").read_text(encoding="utf-8"))
    starts = [x for x in lines if x["event"] == "started"]; completes = [x for x in lines if x["event"] == "completed"]
    assert len(rows) == 800 and len(lines) == 1600 and len(starts) == len(completes) == 800
    assert len({x["run_id"] for x in starts}) == len({x["run_id"] for x in completes}) == 800
    assert all(x["attempt"] == 0 for x in lines)
    assert all(r["final_status"] == "VALID" and r["retry_attempt"] is None for r in rows)
    completed_map = {(x["run_id"], x["attempt"]): x["response"] for x in completes}
    for row in rows:
        response = completed_map[(row["run_id"], 0)]
        assert row["first_attempt"]["raw"] == response["raw"]
        assert json.loads(response["raw"]) == row["parsed"]
        assert set(row["parsed"]) == {"p_success_left", "p_success_right"}
        assert all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and 0 <= v <= 1 for v in row["parsed"].values())
    checks = json.loads((ROOT / "results" / "identifiability_checks.json").read_text())
    assert checks["verdict"] == "CAUSAL_SUFFICIENCY_MATH_GO" and checks["search"]["pairs"] == 20
    assert all(x["lossy_equal"] and not x["g_preserve_equal"] and x["exact_opposite"] for x in checks["pairs"])
    stats = json.loads((ROOT / "results" / "statistics.json").read_text())
    assert stats["verdict"] == "CAUSAL_SUFFICIENCY_WEAK" and stats["complete_worlds"] == 40
    assert stats["matched_pair_identity"]["all_identical"] and stats["matched_pair_identity"]["all_opposite"]
    assert stats["length_checks"]["all_equal"] and stats["length_checks"]["r2_chars"] == [256]
    credential = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16}")
    listed = subprocess.check_output(["git", "-C", str(repo), "ls-files", "--others", "--exclude-standard", "-z", str(ROOT.relative_to(repo))]).decode().split("\0")
    files = [repo / x for x in listed if x]
    for f in files:
        assert f.stat().st_size < 5_000_000, (f, f.stat().st_size)
        assert f.suffix.lower() not in {".pem", ".key", ".gguf", ".pt", ".bin"}
        if f.suffix.lower() in {".json", ".jsonl", ".csv", ".md", ".py", ".txt"}:
            assert not credential.search(f.read_text(encoding="utf-8", errors="ignore")), f
    old = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", "c029f3b", "--", "idea_validation/idea2_policy_confounding", "idea_validation/idea2_policy_confounding_confirmatory"]).returncode
    assert old == 0
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip().splitlines()
    environment = {"python": sys.version, "executable": sys.executable, "model": "qwq:32b", "ollama_endpoint": "http://127.0.0.1:11434/api/chat", "gpu": gpu, "formal_calls": 800, "retries": 0, "capability_probe_excluded": True}
    (ROOT / "results" / "environment.json").write_text(json.dumps(environment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verification = {"timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "phase_a": "PASS", "journal_records": 1600, "unique_formal_runs": 800, "all_first_attempt": True, "raw_matches_parsed_results": "PASS", "complete_worlds": 40, "r2_pair_identity": "PASS", "r2_r4_length_equal_256": "PASS", "historical_idea2_dirs_unchanged": "PASS", "credential_and_artifact_scan": "PASS", "verdict": stats["verdict"]}
    (ROOT / "results" / "final_verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()

