import datetime, json, sys, time
import requests
from core import ROOT, MODEL, OPTIONS, SYSTEM, SCHEMA, ensure_env, validate_parsed

def main():
    ensure_env()
    prompt = "This is a format-only capability probe. Return p_success_left=0.25 and p_success_right=0.75 as probabilities."
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t = time.time()
    session = requests.Session(); session.trust_env = False
    try:
        response = session.post("http://127.0.0.1:11434/api/chat", json={"model": MODEL, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], "format": SCHEMA, "options": OPTIONS, "stream": False, "keep_alive": "10m"}, timeout=(10, 180))
        response.raise_for_status(); data = response.json()
        raw = data.get("message", {}).get("content", "")
        parsed = json.loads(raw)
        supported, reason = validate_parsed(parsed)
        out = {"supported": bool(supported), "format": "schema", "probe_excluded": True, "model": MODEL, "options": OPTIONS, "started": started, "elapsed_seconds": time.time()-t, "raw": raw, "parsed": parsed, "provider_metadata": {k:v for k,v in data.items() if k != "message"}, "reason": reason}
    except Exception as exc:
        out = {"supported": False, "format": "schema", "probe_excluded": True, "model": MODEL, "options": OPTIONS, "started": started, "elapsed_seconds": time.time()-t, "error": repr(exc)}
    (ROOT / "results" / "capability_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out.get(k) for k in ["supported", "format", "probe_excluded", "model", "elapsed_seconds", "reason", "error"]}, ensure_ascii=False, indent=2))
    if not out["supported"]: raise SystemExit(1)

if __name__ == "__main__": main()

