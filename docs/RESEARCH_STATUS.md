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



## Idea 2 Stage-3 — Real Memory Formation Audit — 2026-10-05

独立目录：`idea_validation/idea2_real_memory_formation_audit/`。最终 verdict：**REAL_FORMATION_WEAK**。20 组/40 个 worlds 沿用 Stage-2 source（SHA256 `76fbd6c45e70a8737a6b81b220f480c8f95aa63b18d6d454b969cc8fda2ac148`）；未修改 Run1、Confirmatory 或 Stage-2 结果目录。

Primary qwen2.5:14b 和 Secondary qwq:32b 各完成 160/160 memory formation、320/320 双 faithfulness audit、160/160 recoverability、320/320 downstream calls；formal pipeline 无 retry。C1/C2 calibration 为 80/80 有效。Primary 严格双审计 faithfulness：GenericSummary 0/40、ReflectionLesson 0/40、StrategyMemory 0/40、ConsolidatedExperience 19/40。Secondary 分别为 6/40、2/40、5/40、40/40。Secondary ReflectionLesson 在 strict faithful cohort 中有 FBIR=0.50，但 cohort 仅 N=2；primary 的 FBIR 与 retention/regret、matched-pair gates 均未达到预设门槛。G0/G1/G7/G8 通过，G2–G6 未通过。C1 downstream control 有 1/80 label calls 因中断未知而保守记为 invalid，未重发；C1/C2 下游准确率分别 0.475/0.500，作为读者表现限制报告。

该结果是 partial formation signal，不支持 GO，也不足以称为无现象；严格按预注册规则判为 WEAK。只适用于本次固定 toy worlds、提示、模型与预算。运行环境 Python 3.10.21 / conda `agentmem_lab`；端末核验 GPU 为 4 张 RTX 4090，实验结束快照中 qwq:32b 位于 GPU 0。详见 Stage3 报告、最终结论、statistics 和 final_verification。Run1、Confirmatory、Stage-2 的历史 verdict 保持不变；本轮已停止。


## Idea 2 Stage-3 — Real Memory Formation Audit — 2026-10-05

独立目录：`idea_validation/idea2_real_memory_formation_audit/`。最终 verdict：**REAL_FORMATION_WEAK**。20 组/40 个 worlds 沿用 Stage-2 source（SHA256 `76fbd6c45e70a8737a6b81b220f480c8f95aa63b18d6d454b969cc8fda2ac148`）；未修改 Run1、Confirmatory 或 Stage-2 结果目录。

Primary qwen2.5:14b 和 Secondary qwq:32b 各完成 160/160 memory formation、320/320 双 faithfulness audit、160/160 recoverability、320/320 downstream calls；formal pipeline 无 retry。C1/C2 calibration 为 80/80 有效。Primary 严格双审计 faithfulness：GenericSummary 0/40、ReflectionLesson 0/40、StrategyMemory 0/40、ConsolidatedExperience 19/40。Secondary 分别为 6/40、2/40、5/40、40/40。Secondary ReflectionLesson 在 strict faithful cohort 中有 FBIR=0.50，但 cohort 仅 N=2；primary 的 FBIR 与 retention/regret、matched-pair gates 均未达到预设门槛。G0/G1/G7/G8 通过，G2–G6 未通过。C1 downstream control 有 1/80 label calls 因中断未知而保守记为 invalid，未重发；C1/C2 下游准确率分别 0.475/0.500，作为读者表现限制报告。

该结果是 partial formation signal，不支持 GO，也不足以称为无现象；严格按预注册规则判为 WEAK。只适用于本次固定 toy worlds、提示、模型与预算。运行环境 Python 3.10.21 / conda `agentmem_lab`；端末核验 GPU 为 4 张 RTX 4090，实验结束快照中 qwq:32b 位于 GPU 0。详见 Stage3 报告、最终结论、statistics 和 final_verification。Run1、Confirmatory、Stage-2 的历史 verdict 保持不变；本轮已停止。

## Idea 2 Stage-4 — Policy-Conditioned Experience Memory Audit — 2026-10-05

新目录 `idea_validation/idea2_policy_conditioned_memory_audit/`，不修改 Run1、Confirmatory、Stage-2、Stage-3 结果。预注册 SHA256 核验通过；5/5 官方仓库 clone 成功，Memento 无可确认官方代码。JitRL episode ranker 与 MemRL value selector 的原生组件动态审计均出现 P/Q policy-aligned score preference flip，BAL gap reduction 约 97.8%。静态 blind spot 5/5；完整 agent E2E 和 state-matched query 未执行/接口不支持。按锁定 gate 得 **POLICY_MEMORY_GO（仅限已测试 native ranking/value-selection 组件及 aggregate experience utility）**。详见 Stage4实验结果.md、最终结论.md 与 `results/`。Idea 2 各阶段历史 verdict 保持独立且冻结；Stage-4 已停止。

## Idea 2 Stage-4.1 — Native Evidence Hardening — 2026-10-05

独立目录：idea_validation/idea2_native_evidence_hardening/。最终 **NATIVE_EVIDENCE_GO**，G0–G7 全 PASS，G8 BLOCKED。两个固定 commit 的原生组件各完成 640 条返回；20 个 order replicates 在 exact integer logs 上执行，不改变 outcome/exposure。gamma=.95/k=20 时 JitRL 与 MemRL 均 20/20 reversal，SSP 中位数 P=+.60/Q=−.60，RCD=.625，BAL reduction=.794737。四个 gamma 的 median RCD=0/.275/.525/.625，rho=1；4/4 k 中位方向一致。

Stage-4.1 scope correction：旧 adapter action-level score/bank-average score 不进入新 Gate；新 primary 只依赖 upstream returned ranking/selection。两个组件原生 selected IDs 完全一致，不作为独立统计重复；大量同分成功项是机制本身，shuffle 排除单一 insertion order 特例。当前完整 JitRL state-aware 路径缺 OpenAI/FAISS 等依赖与必要环境配置，严格记 BLOCKED，没有模拟 embedding；MemRL full candidate retrieval 未运行。加固仅限 native component selection，不能外推完整 agent。

永久保留历史：IDEA2_RUN1_NO_GO、IDEA2_CONFIRM_GO、CAUSAL_SUFFICIENCY_WEAK、REAL_FORMATION_WEAK、POLICY_MEMORY_GO。现象证据加固完成，可以进入方法设计阶段；本轮到此停止。

## Idea 2 Stage-5 — Method Viability Study — 2026-10-05

独立目录 idea_validation/idea2_method_viability/。最终 **METHOD_VIABILITY_GO**，候选 **M1**。G0原生复现先通过，57项测试与SHA256锁定均在正式运行前；36个exact bank、720条method结果、1440条native selections、4800条secondary selections完成，G0–G9通过。

M1在两adapter上得到相同观察输入，无true propensity/gamma；null PIG=NPE=0，真实gap=.10全部保留、TSR=1，context T0/T1全部正确翻转。M4在常规support通过但仍有小幅strict false reversal与.99 shrinkage limitation。M2的题述global SNIPS缺rho适配，crossover失败且.99 clipping留大偏差；M3为oracle classical reference，永不候选。M0 primary proxy是native selection fraction中位数，报告明确它不等于成功概率。

M1与经典direct standardization/g-computation相同，不声明novelty；下一步应做方法新颖性/差异化审计，本轮不自动执行。Exact离散state结果不外推finite-sample/连续context/full-agent。六个历史目录与verdict冻结，不回写结果。

## Idea 2 Stage-6A — Cross-Policy Memory Certification — 2026-10-06
独立目录 idea_validation/idea2_cross_policy_certification/。W1 same-policy echo 保持 D_policy=0、DESCRIPTIVE；W2 识别交替方向与 C_conflict=1；W3 invariant profile 为 PRESCRIPTIVE；W4 false-diversity D=.0333 对比 true-diversity D=.60；M1 utility 在 echo/diverse 下同为 gap=.4，但 lifecycle 不同。最终 **CROSS_POLICY_CERT_NARROW**：G0–G4、G6–G9 通过；G5 因运行器未充分隔离生成器与 candidate 输入而失败，故不声称完成 oracle-free 执行认证。24 项测试通过，正式 deterministic run 一次，未调阈值。Stage-6A 已停止。

## Idea 2 Stage-6A.1 — Oracle-Free Boundary Hardening — 2026-10-06

独立目录：idea_validation/idea2_cross_policy_certification_hardening/。本轮结论 **ORACLE_FREE_HARDENING_GO**，H0–H9 全 PASS，G5 由真实的 schema、拒绝、AST、字符串、进程、文件、环境、metadata invariance 与数值复现检查组合计算。77 项预运行测试通过；正式运行一次，无 restart。

候选仅在临时目录读取匿名逐条观测与冻结公开阈值；11 个固定配置复现 Stage-6A，5 种私有元数据变换得到逐字节相同的输出。M1 ECHO/DIVERSE gap 均 .40，认证分别 DESCRIPTIVE/PRESCRIPTIVE。1,956 个历史文件及链接核验一致。Stage-6A 的 **CROSS_POLICY_CERT_NARROW** 永久保留，未回写历史结果。新增证据仅限受审计代码路径的执行边界，不等同于 OS 级恶意代码隔离，也不扩大 synthetic/exact-count 研究结论。本轮已停止，未进入后续阶段。
