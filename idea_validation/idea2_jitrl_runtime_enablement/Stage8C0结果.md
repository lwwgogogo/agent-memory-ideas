# Idea 2 Stage-8C0.3 结果

## spaCy

- spaCy：3.8.16
- en_core_web_sm：3.8.0
- load/tokenization：PASS
- 安装方式：官方 wheel，--no-deps
- 其他核心包升级：无
- pip check：PASS

## Runtime

- 环境：jitrl_runtime
- Python：3.10.21
- ROM：Jericho/jericho-games/library.z5
- 模型：qwen2.5:14b
- Backend：Ollama / http://localhost:11434/v1

## Single episode smoke

本轮只运行 1 个 episode：

- runner initialization：PASS
- initial observation：PASS
- prompt constructed：PASS
- LLM request：PASS
- LLM response：PASS
- response parse：PASS
- action generated：west
- action valid：PASS
- environment step：PASS
- trajectory created：PASS
- memory written：NO（runtime smoke 明确关闭 cross-episode memory）
- episode finished：PASS
- steps：1
- reward：0
- score：0
- wall time：10.01150385197252 秒
- exception：NONE

reward 为 0 不影响 runtime gate。没有运行第二个 episode，也没有进入 Stage-8C formal experiment。

## Gates

- G0 PASS
- G1 PASS
- G2 PASS
- G3 PASS
- G4 PASS
- G5 PASS
- G6 PASS
- G7 PASS
- G8 PASS
- G9 PASS

## Verdict

OLLAMA_SMOKE_PASS

本地 Ollama 已可作为当前 JitRL 受控 Stage-8C 实验的 inference transport。

## Next

下一步最小动作是返回 Stage-8C real failure reproduction；本轮到此停止。
