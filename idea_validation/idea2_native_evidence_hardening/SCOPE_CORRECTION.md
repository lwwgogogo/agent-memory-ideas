# Stage-4.1 证据范围加固说明

Stage-4 的 **POLICY_MEMORY_GO** verdict 不改，所有历史文件冻结。

Stage-4 的 JitRL action-level score 与 MemRL action-level bank-average score 包含我们在 adapter/evaluator 中的 aggregation。由这两类 score 得到的 PSI、PIUR 不作为本轮 primary evidence，也不进入任何 Gate。

Stage-4.1 将上游原生 get_top_episodes(...) 返回的 ranked episodes 和 ValueAwareSelector.select(...) 返回的 selected memories 作为 primary endpoint。SSP、Native-RCD、Native-PIUR、RWP 是我们的 evaluator 从这些原生返回 action metadata 与 rank 计算的统计量，不是系统自行输出的“因果价值”。

本轮保持 Stage-4 历史结论，并把待验证证据从 adapter-derived action score 加固到 native component selection output。完整 state-aware pipeline 若依赖不足则记 BLOCKED，禁止用模拟 embedding 替代，也不能把 component-level 结果说成 full-agent 结果。
