# Idea 2 Stage-8C0.3: Completed Local JitRL Ollama Smoke Runtime

This directory records the final single-episode runtime smoke for the corrected Jericho/library path.

## Outcome

- Runtime: jitrl_runtime, Python 3.10.21.
- spaCy: 3.8.16.
- Authorized model installed: en_core_web_sm 3.8.0, with no dependency upgrades.
- ROM: Jericho/jericho-games/library.z5.
- Backend: Ollama at http://localhost:11434/v1.
- Model: qwen2.5:14b.
- Episodes run in this stage: exactly one.
- JitRL runner initialized Jericho and obtained the initial observation.
- JitRL constructed its prompt and completed a real Ollama request.
- The response parsed successfully.
- Generated action: west.
- The action was in Jericho's valid-action set and was executed.
- One environment step and one trajectory/log record completed.
- Episode completed at the one-step smoke limit with reward 0.
- Cross-episode memory was intentionally disabled for this runtime smoke, so no memory write occurred.
- Frozen third-party JitRL remains clean.
- Final verdict: OLLAMA_SMOKE_PASS.

This establishes only that local Ollama can serve as the inference transport for the current controlled JitRL runtime path.
