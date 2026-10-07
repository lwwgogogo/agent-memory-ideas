# Idea 2 Stage-8C0.2: Corrected Jericho Smoke Runtime

This directory records the single permitted smoke retry with the corrected library ROM path.

## Outcome

- Repository baseline: clean at 58aa718f3d5a4c5eb35563fcc4bd14ac1f90ea24, equal to origin/main.
- Runtime: jitrl_runtime, Python 3.10.21.
- ROM: Jericho/jericho-games/library.z5, present at 71 KB.
- Direct Jericho FrotzEnv load/reset: PASS; initial observation contained 2020 characters.
- JitRL smoke attempts in this stage: exactly one.
- The runner blocked in Jericho valid-action enumeration before the LLM request.
- Jericho attempted to download and install en_core_web_sm because it was absent.
- The run was stopped to preserve the explicit no-install/runtime-unchanged constraint.
- en-core-web-sm was not installed, Ollama was not called, and no second episode was run.
- Frozen third-party JitRL remains clean.
- Final verdict: JERICHO_RUNTIME_BLOCKED.

No dependency, ROM, model, cache, credential, conda environment, or third-party change is committed.
