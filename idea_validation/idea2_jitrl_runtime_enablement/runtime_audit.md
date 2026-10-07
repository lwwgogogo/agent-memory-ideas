# Stage-8C0.1 runtime audit

## Isolation

The repository baseline was clean at 77e9313c57309948b334641884a2c1a26a2395ca and matched origin/main. Home had 364 GB available.

jitrl_runtime was created successfully with:

conda create -n jitrl_runtime --clone agentmem_lab -y

The clone retained Python 3.10.21 and numpy 2.2.6. agentmem_lab was not modified.

## Minimal installation

Only openai, jericho, tiktoken, and python-dotenv were requested from pip. The resolver added their declared dependencies, including spaCy from Jericho. It did not downgrade existing packages or install browsergym, faiss-cpu, torch, rank-bm25, or WebArena dependencies.

Installed top-level versions:

- openai 3.26.0
- jericho 3.3.1
- tiktoken 0.14.0
- python-dotenv 1.2.4
- numpy remained 2.2.6

All required imports passed and pip check reported no broken requirements.

## Official client compatibility

Two and only two standalone requests were made with openai.OpenAI, base_url http://localhost:11434/v1, a non-empty dummy key, and qwen2.5:14b.

The text request returned exactly OK. The structured request returned JSON parsed as {"status": "OK"}. Both responses exposed choices[0].message.content, finish_reason, model, and usage. No OpenRouter-only response field was required.

## Single smoke attempt

Exactly one JitRL evaluation run was attempted with one environment step, seed 0, temperature 0, verbalized confidence, and cross-episode memory disabled for the transport/runtime smoke.

The attempt failed in Jericho FrotzEnv construction before any LLM request or environment step:

- configured ROM: Jericho/games/library.z5
- actual ROM: Jericho/jericho-games/library.z5
- exception: FileNotFoundError
- wall time: 4.026174445985816 seconds

No trajectory or memory write occurred. No second episode was run. The external smoke wrapper now points to jericho-games for a future explicitly authorized retry, but this correction was not executed.

## Integrity

The adapter changes only client base_url and api_key. JitRL source, memory, retrieval, return, advantage, action selection, environment, and reward logic were not changed. The frozen JitRL checkout is clean.
