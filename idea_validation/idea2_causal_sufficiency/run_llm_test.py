import datetime, json, random, sys, time
from pathlib import Path
import requests
from core import ROOT, MODEL, OPTIONS, SYSTEM, SCHEMA, CONDITIONS, ensure_env, save, sha, canonical, run_with_retry, parse

def request_model(session, prompt):
    started = time.time()
    try:
        response = session.post("http://127.0.0.1:11434/api/chat", json={"model": MODEL, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], "format": SCHEMA, "options": OPTIONS, "stream": False, "keep_alive": "10m"}, timeout=(10, 180))
        response.raise_for_status(); data = response.json()
        return {"raw": data.get("message", {}).get("content", ""), "provider_metadata": {k: v for k, v in data.items() if k != "message"}, "elapsed_seconds": time.time() - started, "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    except requests.RequestException as exc:
        return {"transport_error": repr(exc), "elapsed_seconds": time.time() - started, "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}

def main():
    ensure_env()
    tests = json.loads((ROOT / "results" / "tests.json").read_text())
    if tests["returncode"] != 0: raise RuntimeError("tests did not pass")
    for name, expected in tests["source_sha256"].items():
        if sha(ROOT / name) != expected: raise RuntimeError("frozen source changed: " + name)
    capability = json.loads((ROOT / "results" / "capability_probe.json").read_text())
    if not capability.get("supported"): raise RuntimeError("structured JSON capability probe failed")
    cases = json.loads((ROOT / "cases" / "cases.json").read_text())
    jobs = list(cases["runs"])
    if len(jobs) != 800: raise AssertionError(len(jobs))
    config = {"model": MODEL, "options": OPTIONS, "system": SYSTEM, "format": SCHEMA, "planned_runs": 800, "retry_max": 1, "job_order_seed": 20261005, "case_sha256": sha(ROOT / "cases" / "cases.json"), "preregistration_sha256": sha(ROOT / "preregistration.md"), "source_sha256": tests["source_sha256"], "python": sys.executable}
    config_path = ROOT / "results" / "config.json"
    if config_path.exists():
        if json.loads(config_path.read_text()) != config: raise RuntimeError("frozen config mismatch")
    else: save(config_path, config)
    random.Random(20261005).shuffle(jobs)
    result_path = ROOT / "results" / "llm_results.json"
    results = json.loads(result_path.read_text()) if result_path.exists() else []
    finished = {row["run_id"] for row in results}
    journal = ROOT / "results" / "raw_outputs.jsonl"
    started, completed = set(), {}
    if journal.exists():
        for line in journal.read_text().splitlines():
            if not line: continue
            event = json.loads(line); key = (event["run_id"], event["attempt"])
            if event["event"] == "started": started.add(key)
            elif event["event"] == "completed": completed[key] = event["response"]
    session = requests.Session(); session.trust_env = False
    def append(event):
        with journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n"); stream.flush()
    for index, spec in enumerate(jobs, 1):
        if spec["run_id"] in finished: continue
        def invoke(prompt, attempt):
            key = (spec["run_id"], attempt)
            if key in completed: return completed[key]
            if key in started:
                response = {"transport_error": "INTERRUPTED_REQUEST_OUTCOME_UNKNOWN; no reissue"}
            else:
                append({"event": "started", "run_id": key[0], "attempt": key[1], "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}); started.add(key)
                response = request_model(session, prompt)
            append({"event": "completed", "run_id": key[0], "attempt": key[1], "response": response}); completed[key] = response
            return response
        outcome = run_with_retry(spec["prompt"], invoke)
        row = dict(spec); row.update(outcome)
        if row["final_status"] == "VALID":
            p_a, p_b = canonical(row["parsed"], spec["version"])
            row.update(p_success_A=p_a, p_success_B=p_b, predicted_difference=p_a-p_b, offline_decision="A" if p_a > p_b else ("B" if p_b > p_a else "TIE"))
        results.append(row); save(result_path, results); finished.add(spec["run_id"])
        print(f"{index}/800 {spec['run_id']} {row['final_status']} retry={row['retry_attempt'] is not None}", flush=True)

if __name__ == "__main__": main()

