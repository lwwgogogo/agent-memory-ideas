# Idea 2 Stage-8C0.1: Local JitRL Ollama Runtime

This directory records the isolated runtime setup, official OpenAI Python client probes, and the single permitted Jericho/library smoke attempt.

## Outcome

- Isolated conda environment: jitrl_runtime, cloned from agentmem_lab.
- Python: 3.10.21.
- Installed minimal requested packages: openai 3.26.0, jericho 3.3.1, tiktoken 0.14.0, python-dotenv 1.2.4.
- pip check: no broken requirements.
- Official openai.OpenAI text probe: PASS.
- Official openai.OpenAI strict JSON probe: PASS.
- One JitRL smoke episode was attempted and failed before environment initialization because the wrapper supplied Jericho/games/library.z5 while the ROM is under Jericho/jericho-games/library.z5.
- No second episode was run.
- The external wrapper is statically corrected for a future authorized retry.
- Frozen third-party JitRL remains clean.
- Final verdict: OLLAMA_CLIENT_COMPATIBLE_RUNTIME_BLOCKED.

No conda environment, cache, model, credential, or third-party change is committed.
