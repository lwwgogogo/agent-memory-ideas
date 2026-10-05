# 研究状态时间线

| 时间 | 方向 | 当前决策与证据边界 |
|---|---|---|
| 2026-09-24 起 | Agent Memory idea exploration | 形成 Noise / Change、Contextual Inhibition、Revision Inertia 等旧编号探索；历史备忘录保留 |
| 2026-09-29 | Noise vs Change | NO-GO；停止复杂 updater 路线，见 execution_phase_a2_20260929.md |
| 历史阶段，精确日期未在本轮核实 | Structured Revision | Novelty NO-GO；沿用已记录的 Candidate 01 决策，不开展新查重 |
| 2026-09-30 前后 | Provenance Identifiability v1/v2 | 当前项目管理决策 NO-GO；v1 原报告 NO-GO，v2 原报告为 BORDERLINE 且未通过 GO，不改写原文，不再推进 |
| 2026-10-02 | Mem0 Failure Discovery / Formation Sanity | diagnostic only；HARNESS_PARTIAL，96/96 无可见形成，infer=False 12/12，两个 infer=True writer 均 0/12 |
| 2026-10-04 | Idea 1 Evidence Double Counting | NO-GO；主分析与全量概率敏感性分析均无稳定膨胀，不继续救 |
| 2026-10-04 | Idea 2 Policy-Confounded Experience | ACTIVE；使用新建 agentmem_lab 环境做数学与最小行为验证 |

历史目录不移动、不重命名、不删除。以上表格区分当前管理决策与原报告措辞。

## 2026-10-05：Idea 2 最终状态

IDEA2_NO_GO，原因是预设完整性门槛未达，而非未观察到偏差。400 次调用中 387 条合法，完整场景 14/20；γ=0.70 的完整主检验缺失。主分析 Confounded MIAB=0.133009，95% CI [0.063119, 0.203637]，两个 correction 为正。事后合法配对 N=19 仍见正偏差与上升趋势，保留为描述性诊断，不据此修改原定判定。停止，不调整提示救结果、不进入 Idea 3。其余历史状态不变。


## Idea 2 Confirmatory Replication — 2026-10-05 完成

独立确认性复现实验结论：**IDEA2_CONFIRM_GO**，预注册 G0—G7 全部通过。固定 320/320 个正式运行有效，0 次重试、0 个无效；20/20 个主场景完整，每个 gamma 均为 5/5。运行前测试 46 passed / 0 failed。

场景级 MIAB：NoMemory 0.000000；Confounded 0.199256（95% bootstrap CI [0.105587, 0.287052]）；Balanced 0.015938；Stratified 0.008750；Aggregate 0.350000（次要结果）。Balanced/Stratified 纠正比例为 92.001506% / 95.608670%；gamma 单调递增，四点 Spearman rho=1.0。Confounded 标签 AB/BA 均值 0.155275 / 0.243238，顺序 O1/O2 均值 0.196113 / 0.202400。

Run 1 永久保留 **IDEA2_RUN1_NO_GO**（原始标记 **IDEA2_NO_GO**）：因完整率门槛未通过，其历史文件及结论均不修改。此次 GO 仅适用于 qwq:32b、固定机制与预注册输入协议，不代表新颖性或现实长期 Agent 泛化。正式推理已结束；不自动开展文献查重、方法设计或 Idea 3。

证据目录：`idea_validation/idea2_policy_confounding_confirmatory/`。详见其中 `preregistration.md`、`Confirmatory结果.md`、`最终结论.md`、`results/statistics.json`、`results/raw_outputs.jsonl` 和 `plots/`。


## Idea 2 Stage-2 — Causal Sufficiency of Experience Memory — 2026-10-05

独立 Stage-2 目录：idea_validation/idea2_causal_sufficiency/。未修改 Idea 2 Run 1（IDEA2_RUN1_NO_GO / 原始 IDEA2_NO_GO）或确认性复现（IDEA2_CONFIRM_GO）的任何结果。

Phase A 使用确定性的整数枚举搜索出 20 组 matched-world pairs（40 worlds）：每对 g_lossy 的 aggregate exposure/success 整数统计逐项相同，g_preserve 的 state-conditioned 统计不同，target-policy 最优动作严格相反；Fraction 精确检查通过，Phase A verdict 为 CAUSAL_SUFFICIENCY_MATH_GO。

Phase B 固定每个 world 的 X,A,Y experience dataset，仅改变 memory representation。800/800 正式调用有效，0 retry，40/40 worlds 完整。R2 FaithfulLossySummary 在每对的相同 label/order 下逐字节相同，而真实最优动作相反，representation-level non-identifiability 检查通过。模型级结果：R1 StatePreservingSummary accuracy=0.643750，regret=0.074479；R2 accuracy=0.500000，regret=0.102083；R3 CausalSufficientCompact accuracy=0.631250，regret=0.077604；R0 RawEpisodic 为 secondary，accuracy=0.781250。由于 R1/R3 未达到预注册的高 accuracy、bootstrap、regret 和控制门槛，最终 verdict 为 **CAUSAL_SUFFICIENCY_WEAK**，不是 GO。结果仅限固定 qwq:32b、固定提示/seed、toy worlds 与本次协议。无论文检索、无 Mem0、无方法设计、未进入 Idea 3；正式推理已停止。

