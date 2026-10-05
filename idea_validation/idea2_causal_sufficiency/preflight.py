import json, subprocess, sys
from core import ROOT, sha

def main():
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT, capture_output=True, text=True)
    (ROOT / "results" / "pytest_output.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    source_files = ["core.py", "generate_cases.py", "phase_a_search.py", "preflight.py", "capability_probe.py", "run_llm_test.py", "evaluate.py", "tests/test_stage2.py", "preregistration.md", "cases/cases.json", "results/identifiability_checks.json"]
    hashes = {name: sha(ROOT / name) for name in source_files}
    value = {"returncode": result.returncode, "source_sha256": hashes, "python": sys.executable, "version": sys.version, "phase_a_verdict": json.loads((ROOT / "results" / "identifiability_checks.json").read_text())["verdict"]}
    (ROOT / "results" / "tests.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"returncode": result.returncode, "tests": result.stdout.strip(), "python": sys.version.split()[0]}, indent=2))
    if result.returncode: raise SystemExit(result.returncode)

if __name__ == "__main__": main()

