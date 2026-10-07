# Runtime audit

## Frozen baseline

The audit started from a clean main branch with HEAD equal to origin/main at 7a3f15538efcb213ce9badf4922c551e416278bb. The frozen JitRL checkout is at 143d22185d95fbf633a0befe6861d5e8b732543b. Python is 3.10.21 in conda environment agentmem_lab. The prior Phase A gate is JITRL_NATIVE_FAILURE_GO.

No frozen JitRL file or earlier Idea 2 result was changed.

## Selected task

Jericho library was selected because it is the native main.py default, games/library.z5 exists locally, and it requires no browser infrastructure. WebArena would require browsergym plus external browser and website services. A single-step episode is sufficient to exercise environment initialization, action generation, runner flow, and trajectory logging.

## Actual import path

main.py -> src.evaluation.GameEvaluator -> src.jitrl_agent.JitRLAgent and src.env.JerichoEnv.

| Component | Classification | Current state | Role |
|---|---|---:|---|
| numpy | required | installed, 2.2.6 | evaluator and arrays |
| openai | required | missing | chat client and exception types |
| jericho | required | missing | FrotzEnv runtime |
| tiktoken | required | missing | imported and initialized at module load |
| python-dotenv | required | missing | load_dotenv at module load |
| faiss-cpu | optional for smoke | missing | guarded vector-index import |
| browsergym | not needed | missing | WebArena only |
| rank-bm25 | not needed | missing | WebArena path |
| torch | not needed | missing | absent from selected import path |

The no-episode command PYTHONDONTWRITEBYTECODE=1 conda run -n agentmem_lab python -B main.py --help exited 1 at src/openai_helpers.py with ModuleNotFoundError: No module named 'openai'. It failed before argument parsing or environment initialization.

## Bounded smoke design

smoke_test.py permits at most one evaluation run and one environment step with seed 0, qwen2.5:14b, temperature 0, verbalized confidence, and a temporary output directory outside the repository. Cross-episode vector memory is disabled only for this transport/runtime smoke. The script would verify environment initialization, one action call, runner completion, and an episode log.

It was not run because required packages are missing and installation was forbidden.
