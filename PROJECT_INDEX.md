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
