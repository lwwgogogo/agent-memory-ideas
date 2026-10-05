# Idea 2 Stage-3：真实记忆形成审计

本目录检验常见 Agent 风格的经验记忆生成，是否会自然形成“事实忠实，但无法恢复完整 state-conditioned 结构”的 memory。

输入直接复用 Stage-2 的 20 组 matched pairs / 40 个 worlds，SHA256 记录于 cases/source_manifest.json。每个自然 formation writer × world × archetype 只调用一次。Primary 为 qwen2.5:14b，Secondary robustness 为 qwq:32b，仅在 Primary 流程全部结束后运行；恢复结构与 downstream reader 均为 qwq:32b。模型参数、schema、retry、MEMORY_BUDGET 和 gates 见 preregistration.md。

C1/C2 recovery calibration 先行。若校准不通过，结果将判为 STAGE3_RECOVERY_PIPELINE_INVALID 并停止。模型原始请求与响应、各阶段 parsed results、逐 memory 文件、统计、图表和哈希清单均保存在本目录。

Stage-2 的 CAUSAL_SUFFICIENCY_WEAK、Confirmatory 的 IDEA2_CONFIRM_GO、Run 1 的 IDEA2_RUN1_NO_GO 均为冻结历史，未在此目录修改。
