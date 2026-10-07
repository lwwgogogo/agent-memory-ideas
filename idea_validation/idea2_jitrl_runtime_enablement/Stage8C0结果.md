# Idea 2 Stage-8C0 结果

## 1. 当前阻塞

agentmem_lab 缺少 openai、jericho、tiktoken 和 python-dotenv。禁止安装依赖，因此官方 OpenAI Python client probe 与真实单回合 JitRL smoke 均不能执行。

## 2. Selected minimal task

Jericho / library。它是原生默认任务，本地已有 library.z5，且不需要 browser infrastructure。

## 3. Dependency audit

- REQUIRED_FOR_SELECTED_TASK：numpy（已安装）；openai、jericho、tiktoken、python-dotenv（缺失）
- OPTIONAL_FOR_OTHER_TASKS/PATHS：browsergym、faiss-cpu
- NOT_NEEDED：rank-bm25、torch
- MINIMAL_INSTALL_SET：openai、jericho、tiktoken、python-dotenv
- 本轮未安装任何依赖

## 4. OpenRouter code path

原生代码使用 openai.OpenAI，硬编码 base_url=https://openrouter.ai/api/v1，从 OPENAI_API_KEY 取 key，并调用 client.chat.completions.create。没有 OpenRouter-only headers、provider routing 或专属 response fields。动作请求使用严格 JSON schema，并总是请求 top_logprobs；verbalized mode 只消费 choices[0].message.content 中的 JSON，logit mode 才消费 response logprobs。usage、tools、streaming 均不使用。重试为标准 OpenAI SDK 异常，最多 5 次、间隔 20 秒。

Cross-episode embedding 另走 OpenAI SDK 默认 endpoint、OPENAI_API_KEY2 和 text-embedding-ada-002；本轮生成模型 probe 不覆盖该路径。

## 5. Ollama status

Ollama 0.5.12 可访问。选用已存在的最小文本生成模型 qwen2.5:14b；没有 pull 模型。

## 6. OpenAI-compatible probe

两次 raw HTTP 请求均为 HTTP 200。基础请求严格返回 OK，并有标准 choices 与 usage；字段请求支持严格 JSON schema，接受 logprobs/top_logprobs，但未返回 logprobs。由于 agentmem_lab 缺少 openai，未完成规定的 OpenAI Python client probe，G4 不通过。

## 7. Adapter fidelity

optional_backend_adapter.py 只替换 OpenAI constructor 的 base_url 与 api_key。没有修改 memory、retrieval、return、Q、advantage、normalization、action score、policy update 或 environment。

## 8. Smoke test

BLOCKED_BY_DEPENDENCY。真实 episode 数为 0；没有运行 benchmark 或 Stage-8C。

## 9. Gates

- G0 Integrity：PASS
- G1 Minimal Dependency Path Identified：PASS
- G2 Backend Contract Identified：PASS
- G3 Ollama Available：PASS
- G4 OpenAI Compatibility：FAIL
- G5 Adapter Fidelity：PASS
- G6 Smoke Runtime：BLOCKED_BY_DEPENDENCY

## 10. Verdict

RUNTIME_BLOCKED

最低成本路径仍需要安装四个 task-specific runtime 包，并重新验证官方 client 与一个真实 episode；这超出本轮未授权安装的范围，当前不值得继续自动推进。

## 11. 下一步所需的最小动作

若决定继续，单独授权在 agentmem_lab 安装 MINIMAL_INSTALL_SET，然后只重跑官方 OpenAI client probe 和一个 Jericho/library smoke episode。
