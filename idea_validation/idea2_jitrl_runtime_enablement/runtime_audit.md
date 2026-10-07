# Stage-8C0.2 runtime audit

## Baseline and corrected ROM

The run started from a clean repository at 58aa718f3d5a4c5eb35563fcc4bd14ac1f90ea24, equal to origin/main. jitrl_runtime used Python 3.10.21. The frozen JitRL checkout was clean.

The corrected ROM was found at:

idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl/Jericho/jericho-games/library.z5

The file existed and was 71 KB.

## Jericho load preflight

A direct FrotzEnv load/reset completed in 0.007903074030764401 seconds without an LLM call:

- ROM load: success
- reset: success
- initial observation present: yes
- initial observation characters: 2020
- initial score: 0

This establishes that the ROM itself is readable by the installed Jericho runtime.

## Single JitRL smoke attempt

Exactly one smoke episode was started with the corrected ROM path, qwen2.5:14b, Ollama at http://localhost:11434/v1, seed 0, temperature 0, and the previously validated transport-only adapter.

The JitRL JerichoEnv.reset path calls env.get_valid_actions(use_parallel=True). During that call the installed Jericho package detected that en_core_web_sm was missing and invoked spacy.cli.download("en_core_web_sm") from jericho/util.py lines 44-47.

Installing a new runtime dependency was prohibited in this stage and G0 required the runtime environment to remain unchanged. The same smoke process was therefore interrupted and terminated. It had not reached Ollama: /api/ps reported no loaded models and all GPUs were idle.

Observed smoke state:

- JitRL environment reset completed: no
- runner received initial observation: no
- LLM request: no
- response parse: no
- action generated/executed: no
- environment step: no
- trajectory: no
- memory write: no
- episode finished: no
- episode steps: 0
- reward: unavailable
- elapsed time: approximately 9 minutes before policy-preserving termination

No second episode was run. en-core-web-sm was confirmed absent after termination. The repository, runtime package set, and third-party checkout remained unchanged.

## Verdict

JERICHO_RUNTIME_BLOCKED

The minimal blocker is the undeclared-at-install-time spaCy language model required by Jericho valid-action enumeration.
