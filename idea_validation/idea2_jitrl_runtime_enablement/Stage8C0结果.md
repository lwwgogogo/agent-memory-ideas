# Idea 2 Stage-8C0.1 结果

## Runtime

成功从 agentmem_lab 克隆隔离环境 jitrl_runtime，Python 3.10.21。agentmem_lab 未修改。

## Dependencies

仅请求安装 openai、jericho、tiktoken、python-dotenv 及它们声明的必需依赖。最终版本分别为 3.26.0、3.3.1、0.14.0、1.2.4；numpy 保持 2.2.6。全部 import 通过，pip check 无破损依赖。未安装 browsergym、faiss-cpu、torch 或 rank-bm25。

## OpenAI → Ollama

官方 OpenAI Python client 指向 http://localhost:11434/v1，使用非空 dummy key 和 qwen2.5:14b。两次 standalone probe 均通过：

- text：严格返回 OK；
- JSON：严格解析为 {"status": "OK"}。

choices[0].message.content 契约成立，不依赖 OpenRouter-only response field。

## Adapter

adapter 只改变 base_url、api_key 和 client initialization；模型由外部配置为 qwen2.5:14b。JitRL 核心算法未修改，third-party checkout 干净。

## Smoke

唯一一次 Jericho/library episode 在 FrotzEnv 初始化时失败。wrapper 传入不存在的 Jericho/games/library.z5；实际 ROM 位于 Jericho/jericho-games/library.z5。

因此：

- environment initialized：NO
- LLM request：NO
- action generated：NO
- environment step：NO
- trajectory created：NO
- memory written：NO
- wall time：4.026174445985816 秒

没有运行第二个 episode。wrapper 已静态修正为 jericho-games，但未执行修正后的 smoke。

## Gates

- G0 PASS
- G1 PASS
- G2 PASS
- G3 PASS
- G4 PASS
- G5 PASS
- G6 FAIL

## Verdict

OLLAMA_CLIENT_COMPATIBLE_RUNTIME_BLOCKED

## Next

下一步最小动作是新开一次明确授权的单 episode smoke retry，使用已修正的 jericho-games/library.z5 路径；无需再安装依赖或重跑 standalone probes。
