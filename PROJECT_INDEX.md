# Agent Memory Ideas 项目索引

## 当前研究状态

本索引为当前研究入口；根 README 和历史备忘录保留当时语境，其中的旧 Idea 编号不等于当前 Idea Validation 编号。唯一主工作区为 imds 的 /home/liaoweiwen/projects/agent-memory-ideas。

### 1. Agent Memory Failure Discovery

目录：agent_memory_failure_discovery/。

状态：ARCHIVED_DIAGNOSTIC。

Mem0 96-case experiment 已完成，Harness 最终为 HARNESS_PARTIAL；96/96 没形成可见 Mem0 memory。后续 Formation Sanity 表明 infer=True 本地路径存在兼容 / structured-output 问题。不能用于 Agent Memory 科研 claim，不再作为当前主线。此前报告包含多个时间阶段，按最终 Harness 和 Formation 诊断阅读，不改写历史。

### 2. Formation Sanity

逻辑名称：formation_sanity/；服务器实际目录：agent_memory_failure_discovery/formation_sanity/。根目录没有 formation_sanity/，不创建替身、不移动目录。

状态：ARCHIVED_INFRASTRUCTURE_DIAGNOSTIC。

infer=False：12/12；qwen infer=True：0/12；qwq infer=True：0/12。qwen 原表有两个 ERROR 条目，0/12 表示未形成可见 memory，不代表所有调用正常返回。这是 infrastructure / compatibility 诊断，不是研究 Candidate。

### 3. Idea 1 — Evidence Double Counting

目录：idea_validation/idea1_evidence_double_counting/。

状态：NO_GO。最终：IDEA1_NO_GO。

严格完整场景主分析 N=10：OneSource=0.7400，Derived3=0.7560，Derived5=0.7700，Independent3=0.8600，ProvenanceAware5=0.6000。CI5 bootstrap 95% CI：[-0.015, 0.080]。未发现稳定的 derived-memory confidence inflation。

正式 JSON 结构均合法，29 条违反平局选择规则；20 场景原样概率的事后敏感性分析 CI5=0.010，区间 [-0.020, 0.040]，仍不支持稳定膨胀。不要继续救 Idea 1。

### 4. Idea 2 — Policy-Confounded Experience

目录：idea_validation/idea2_policy_confounding/。

状态：ACTIVE。本轮开始验证 Successful Experience ≠ Causal Evidence。先完成因果数学模型与测试，再用已有 qwq:32b 验证行为；不查文献、不设计方法。

## 环境与文档

- [专用研究环境](env/README.md)：agentmem_lab，Python 3.10，不与 Mem0 环境混用。
- [研究状态时间线](docs/RESEARCH_STATUS.md)
- [研究原则](docs/RESEARCH_PRINCIPLES.md)
- [文件清理建议](docs/FILE_CLEANUP_RECOMMENDATIONS.md)

## Idea 2 最终状态（2026-10-05 汇总）

状态：IDEA2_NO_GO（未达到预先固定的完整性门槛，不是无偏差结论）。2026-10-04 已完成 400 次固定调用，387 条合法；五条件完整场景 14/20，γ=0.70 档全部因分层条件越界概率被排除。

完整主分析 Confounded MIAB=0.133009，95% CI [0.063119, 0.203637]；Balanced correction=0.133009，Stratified correction=0.127652。有正偏差和纠正信号，不能写成“没有发现 action bias”。合法配对事后诊断 N=19，Δ_confounded=0.114388，95% CI [0.059638, 0.173566]，趋势随 γ 增加；但不替代预设的完整检验。13 条 UNRESOLVED 不修复、不补跑。

结果：[实验报告](idea_validation/idea2_policy_confounding/Idea2实验结果.md)、[最终结论](idea_validation/idea2_policy_confounding/最终结论.md)。本轮停止，不进入 Idea 3、不开展查重或方法设计。

## 2026-10-05：安全清理与确认性复现实验登记

安全审计确认 5 组字节相同文件均有引用风险，0 组 / 0 文件移动，16 个候选原位保留；见 archive/duplicates_20261005/MANIFEST.md。

Idea 2 Run 1 永久登记为 IDEA2_RUN1_NO_GO；原始 verdict 仍为 IDEA2_NO_GO，原因是完整性 Gate 未通过。原目录 idea_validation/idea2_policy_confounding/ 不修改。新的独立确认性复现位于 idea_validation/idea2_policy_confounding_confirmatory/，不覆盖或重判 Run 1。
