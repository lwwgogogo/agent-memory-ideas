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


## Idea 2 Confirmatory Replication — 2026-10-05 完成

独立确认性复现实验结论：**IDEA2_CONFIRM_GO**，预注册 G0—G7 全部通过。固定 320/320 个正式运行有效，0 次重试、0 个无效；20/20 个主场景完整，每个 gamma 均为 5/5。运行前测试 46 passed / 0 failed。

场景级 MIAB：NoMemory 0.000000；Confounded 0.199256（95% bootstrap CI [0.105587, 0.287052]）；Balanced 0.015938；Stratified 0.008750；Aggregate 0.350000（次要结果）。Balanced/Stratified 纠正比例为 92.001506% / 95.608670%；gamma 单调递增，四点 Spearman rho=1.0。Confounded 标签 AB/BA 均值 0.155275 / 0.243238，顺序 O1/O2 均值 0.196113 / 0.202400。

Run 1 永久保留 **IDEA2_RUN1_NO_GO**（原始标记 **IDEA2_NO_GO**）：因完整率门槛未通过，其历史文件及结论均不修改。此次 GO 仅适用于 qwq:32b、固定机制与预注册输入协议，不代表新颖性或现实长期 Agent 泛化。正式推理已结束；不自动开展文献查重、方法设计或 Idea 3。

证据目录：`idea_validation/idea2_policy_confounding_confirmatory/`。详见其中 `preregistration.md`、`Confirmatory结果.md`、`最终结论.md`、`results/statistics.json`、`results/raw_outputs.jsonl` 和 `plots/`。


## Idea 2 Stage-2 — Causal Sufficiency of Experience Memory — 2026-10-05

独立 Stage-2 目录：idea_validation/idea2_causal_sufficiency/。未修改 Idea 2 Run 1（IDEA2_RUN1_NO_GO / 原始 IDEA2_NO_GO）或确认性复现（IDEA2_CONFIRM_GO）的任何结果。

Phase A 使用确定性的整数枚举搜索出 20 组 matched-world pairs（40 worlds）：每对 g_lossy 的 aggregate exposure/success 整数统计逐项相同，g_preserve 的 state-conditioned 统计不同，target-policy 最优动作严格相反；Fraction 精确检查通过，Phase A verdict 为 CAUSAL_SUFFICIENCY_MATH_GO。

Phase B 固定每个 world 的 X,A,Y experience dataset，仅改变 memory representation。800/800 正式调用有效，0 retry，40/40 worlds 完整。R2 FaithfulLossySummary 在每对的相同 label/order 下逐字节相同，而真实最优动作相反，representation-level non-identifiability 检查通过。模型级结果：R1 StatePreservingSummary accuracy=0.643750，regret=0.074479；R2 accuracy=0.500000，regret=0.102083；R3 CausalSufficientCompact accuracy=0.631250，regret=0.077604；R0 RawEpisodic 为 secondary，accuracy=0.781250。由于 R1/R3 未达到预注册的高 accuracy、bootstrap、regret 和控制门槛，最终 verdict 为 **CAUSAL_SUFFICIENCY_WEAK**，不是 GO。结果仅限固定 qwq:32b、固定提示/seed、toy worlds 与本次协议。无论文检索、无 Mem0、无方法设计、未进入 Idea 3；正式推理已停止。



## Idea 2 Stage-3 — Real Memory Formation Audit — 2026-10-05

独立目录：`idea_validation/idea2_real_memory_formation_audit/`。最终 verdict：**REAL_FORMATION_WEAK**。20 组/40 个 worlds 沿用 Stage-2 source（SHA256 `76fbd6c45e70a8737a6b81b220f480c8f95aa63b18d6d454b969cc8fda2ac148`）；未修改 Run1、Confirmatory 或 Stage-2 结果目录。

Primary qwen2.5:14b 和 Secondary qwq:32b 各完成 160/160 memory formation、320/320 双 faithfulness audit、160/160 recoverability、320/320 downstream calls；formal pipeline 无 retry。C1/C2 calibration 为 80/80 有效。Primary 严格双审计 faithfulness：GenericSummary 0/40、ReflectionLesson 0/40、StrategyMemory 0/40、ConsolidatedExperience 19/40。Secondary 分别为 6/40、2/40、5/40、40/40。Secondary ReflectionLesson 在 strict faithful cohort 中有 FBIR=0.50，但 cohort 仅 N=2；primary 的 FBIR 与 retention/regret、matched-pair gates 均未达到预设门槛。G0/G1/G7/G8 通过，G2–G6 未通过。C1 downstream control 有 1/80 label calls 因中断未知而保守记为 invalid，未重发；C1/C2 下游准确率分别 0.475/0.500，作为读者表现限制报告。

该结果是 partial formation signal，不支持 GO，也不足以称为无现象；严格按预注册规则判为 WEAK。只适用于本次固定 toy worlds、提示、模型与预算。运行环境 Python 3.10.21 / conda `agentmem_lab`；端末核验 GPU 为 4 张 RTX 4090，实验结束快照中 qwq:32b 位于 GPU 0。详见 Stage3 报告、最终结论、statistics 和 final_verification。Run1、Confirmatory、Stage-2 的历史 verdict 保持不变；本轮已停止。


## Idea 2 Stage-3 — Real Memory Formation Audit — 2026-10-05

独立目录：`idea_validation/idea2_real_memory_formation_audit/`。最终 verdict：**REAL_FORMATION_WEAK**。20 组/40 个 worlds 沿用 Stage-2 source（SHA256 `76fbd6c45e70a8737a6b81b220f480c8f95aa63b18d6d454b969cc8fda2ac148`）；未修改 Run1、Confirmatory 或 Stage-2 结果目录。

Primary qwen2.5:14b 和 Secondary qwq:32b 各完成 160/160 memory formation、320/320 双 faithfulness audit、160/160 recoverability、320/320 downstream calls；formal pipeline 无 retry。C1/C2 calibration 为 80/80 有效。Primary 严格双审计 faithfulness：GenericSummary 0/40、ReflectionLesson 0/40、StrategyMemory 0/40、ConsolidatedExperience 19/40。Secondary 分别为 6/40、2/40、5/40、40/40。Secondary ReflectionLesson 在 strict faithful cohort 中有 FBIR=0.50，但 cohort 仅 N=2；primary 的 FBIR 与 retention/regret、matched-pair gates 均未达到预设门槛。G0/G1/G7/G8 通过，G2–G6 未通过。C1 downstream control 有 1/80 label calls 因中断未知而保守记为 invalid，未重发；C1/C2 下游准确率分别 0.475/0.500，作为读者表现限制报告。

该结果是 partial formation signal，不支持 GO，也不足以称为无现象；严格按预注册规则判为 WEAK。只适用于本次固定 toy worlds、提示、模型与预算。运行环境 Python 3.10.21 / conda `agentmem_lab`；端末核验 GPU 为 4 张 RTX 4090，实验结束快照中 qwq:32b 位于 GPU 0。详见 Stage3 报告、最终结论、statistics 和 final_verification。Run1、Confirmatory、Stage-2 的历史 verdict 保持不变；本轮已停止。

## Idea 2 Stage-4 — Policy-Conditioned Experience Memory Audit — 2026-10-05

独立目录：`idea_validation/idea2_policy_conditioned_memory_audit/`。预注册门槛结果为 **POLICY_MEMORY_GO（限定范围）**。六个目标系统纳入静态审计，五个官方 repo 成功 clone，Memento 标记 `OFFICIAL_CODE_NOT_FOUND`。五个可审 repo 均未发现 behavior-policy/propensity 记录或 exposure correction，结构性 blind spot 5/5。

JitRL 原生 episode ranking helper 与 MemRL 原生 Q-value selector 在合成 P/Q exposure 反转下均出现 policy-aligned preference flip（PIUR=1），BAL 后 score gap reduction 各约 97.8%。此为隔离的 native ranking/value-selection component 证据，不是完整 agent 端到端结果。state-matched query API 不支持；JitRL 完整 state/history embedding retrieval 未运行，解释收窄至 aggregate/native selector 路径。G0–G4、G6 PASS，G5 为 NARROW。详见 Stage4 报告和逐系统 JSON；本阶段结束，不启动新 Idea。
