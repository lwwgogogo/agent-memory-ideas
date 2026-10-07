# Idea 2 Stage-8C0.2 结果

## ROM

修正路径为：

idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl/Jericho/jericho-games/library.z5

文件存在，约 71 KB。

## Jericho load

直接使用 jitrl_runtime 中的 FrotzEnv load/reset 成功。初始 observation 存在，长度 2020 字符，初始 score 为 0。

## Single episode smoke

本轮只启动了 1 个 episode，没有启动第二个。

真实 JitRL runner 在 JerichoEnv.reset 的 valid-action 枚举阶段阻塞。安装版 Jericho 在缺少 en_core_web_sm 时调用 spacy.cli.download("en_core_web_sm")。本轮禁止重新安装依赖且要求 runtime unchanged，因此中止并终止该进程。

中止前尚未到达 Ollama：

- environment initialized：NO
- initial observation returned to runner：NO
- LLM request：NO
- response parse：NO
- action generated：NO
- action valid：NO
- environment step：NO
- trajectory created：NO
- memory written：NO
- episode finished：NO
- steps：0
- reward：N/A
- wall time：约 9 分钟

中止后确认 en-core-web-sm 未安装，Ollama 无加载模型，runtime package set 未变化，third-party checkout 干净。

## Gates

- G0 PASS
- G1 PASS
- G2 PASS
- G3 PASS
- G4 FAIL
- G5 FAIL
- G6 FAIL
- G7 PASS

## Verdict

JERICHO_RUNTIME_BLOCKED

## Next

下一步最小动作是单独授权在 jitrl_runtime 中安装 Jericho 所需的 en-core-web-sm 3.8.0；安装后再新开一次、且仅一次 smoke episode。
