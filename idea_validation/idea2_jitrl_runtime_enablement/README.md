# Idea 2 Stage-8C0: JitRL Runtime Enablement and Ollama Compatibility Audit

This directory is a technical runtime audit only. It contains no Stage-8C experiment, benchmark, or method change.

## Outcome

- Selected native task: Jericho library.
- Frozen JitRL source: idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl at commit 143d22185d95fbf633a0befe6861d5e8b732543b.
- Ollama 0.5.12 served the existing qwen2.5:14b model through /v1/chat/completions.
- Exactly two standalone requests were made. No JitRL episode was run.
- agentmem_lab is missing openai, jericho, tiktoken, and python-dotenv.
- Final verdict: RUNTIME_BLOCKED.

## Minimal dependency set reported, not installed

Required for the selected Jericho runner: openai, jericho, tiktoken, and python-dotenv. numpy 2.2.6 is installed. faiss-cpu is optional for this bounded smoke when cross-episode memory is disabled, but is needed for the vector-memory path. browsergym, rank-bm25, and torch are not needed for Jericho.

smoke_test.py defaults to dependency audit. It requires --run to attempt the bounded one-episode, one-step smoke and refuses to run while required packages are missing.
