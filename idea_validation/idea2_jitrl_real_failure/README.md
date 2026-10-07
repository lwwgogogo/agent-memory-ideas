# Idea 2 Stage-8C — Real JitRL Agent Memory Failure Reproduction

This stage tests whether a memory item that was positive when written by the unmodified JitRL Jericho agent can reduce current-state outcome when the same item is retrieved later.

The fixed runtime is `conda env jitrl_runtime` (Python 3.10.21), JitRL commit `143d22185d95fbf633a0befe6861d5e8b732543b`, Jericho `library.z5`, and Ollama OpenAI-compatible backend with `qwen2.5:14b`. The vendored JitRL source is observed but not modified.

Protocol:

1. Lock preregistration and all formal Python scripts by SHA-256.
2. Run at least 20 preformal tests.
3. Run a two-episode technical pilot that is excluded from primary statistics.
4. Run exactly 20 formal episodes once, with one environment step per episode.
5. Log every native memory write and every native retrieval result.
6. For an eligible retrieved memory, compare a state-matched replay with the item present against a replay masking only that item.
7. Apply the preregistered G0–G9 gates and emit only `REAL_JITRL_MEMORY_FAILURE_GO`, `REAL_JITRL_MEMORY_FAILURE_NARROW`, or `REAL_JITRL_MEMORY_FAILURE_NO_GO`.

The environment lacks `faiss`, while the frozen Jericho implementation exposes no non-vector retrieval fallback. This is a preregistered feasibility boundary, not repaired by changing dependencies or JitRL code. Real JSONL memory writes remain observable. If native retrieval is unavailable, the formal run still executes and the result is a truthful NO_GO for this frozen runtime.

Commands (from this directory):

```bash
conda run -n jitrl_runtime python -B verify.py --lock
PYTHONDONTWRITEBYTECODE=1 conda run -n jitrl_runtime pytest -q -p no:cacheprovider tests
conda run -n jitrl_runtime python -B run_pilot.py
conda run -n jitrl_runtime python -B run_formal.py
conda run -n jitrl_runtime python -B analyze_failures.py
conda run -n jitrl_runtime python -B verify.py --final
```
