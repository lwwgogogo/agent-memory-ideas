# Stage-8C0.3 runtime audit

## Baseline

The repository started clean at 67a68f4a3bd19e2132428a92d1d25aac4f625304, equal to origin/main. The runtime was jitrl_runtime with Python 3.10.21. The corrected 71 KB ROM existed at:

idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl/Jericho/jericho-games/library.z5

The frozen JitRL checkout was clean.

## Authorized spaCy model installation

spaCy 3.8.16 was installed but had no language models. Loading en_core_web_sm produced E050, confirming that the only missing resource was the model.

The official en_core_web_sm 3.8.0 wheel was dry-run with --no-deps. The plan contained only en_core_web_sm 3.8.0. It was then installed with --no-deps, so spaCy, numpy, openai, jericho, tiktoken, and python-dotenv were not upgraded.

Validation passed:

- model name: core_web_sm
- model version: 3.8.0
- tokens for "You are in a library.": ["You", "are", "in", "a", "library", "."]
- pip check: no broken requirements

## Final single-episode smoke

Exactly one episode was run with:

- task: Jericho/library
- ROM: jericho-games/library.z5
- backend: Ollama, http://localhost:11434/v1
- model: qwen2.5:14b
- seed: 0
- temperature: 0
- evaluation runs: 1
- environment step limit: 1
- external runner time guard: 360 seconds
- transport-only adapter
- cross-episode memory disabled for the runtime smoke

Observed chain:

1. JitRL created and reset JerichoEnv.
2. The runner obtained the initial observation and valid actions.
3. JitRL constructed the action prompt.
4. The OpenAI-compatible client sent a real request to Ollama.
5. A response was received and parsed.
6. JitRL selected west.
7. west was present in the valid-action set.
8. Jericho executed the action.
9. One environment step completed with reward 0 and score 0.
10. A real episode log/trajectory record was created.
11. The evaluator completed successfully.

Wall time was 10.01150385197252 seconds. The model output contained 818 characters. Token usage was not exposed by the JitRL runner. No second episode was started.

## Integrity

No JitRL core, memory, retrieval, value, advantage, action-selection, environment, or reward logic was changed. The third-party checkout remained clean.

## Verdict

OLLAMA_SMOKE_PASS

Local Ollama can serve as the inference transport for the current controlled JitRL Stage-8C runtime path.
