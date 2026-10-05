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
