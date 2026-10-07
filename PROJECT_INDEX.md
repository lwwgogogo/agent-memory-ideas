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

## Idea 2 Stage-4.1 — Native Evidence Hardening — 2026-10-05

独立目录：idea_validation/idea2_native_evidence_hardening/。新增 verdict：**NATIVE_EVIDENCE_GO**。正式前 37 tests 全部通过，预注册与实现 SHA256 锁定；JitRL/MemRL 各 640 条正式 native return。精确整数日志的 target V(A)=V(B)=.55，20 个顺序复本只有顺序不同。primary gamma=.95、k=20：两个系统均 reversal rate=1.00、median SSP P/Q=+.60/−.60、median Native-RCD=.625、median BAL reduction=.794737。D_gamma=0/.275/.525/.625，四点 rho=1；4/4 k 中位方向一致。G0–G7 全 PASS。

证据只来自 JitRL 原生 get_top_episodes 与 MemRL 原生 QValueUpdater/ValueAwareSelector 的返回选择；不再以旧 adapter 全 bank action-average score 为 Gate。所有 selected 项在成功池内同分，20 次 shuffle 后偏移仍随 P/Q 稳定变化。两个组件 selected IDs 一致，属于同一固定机制的两个实现，不应视为独立统计重复。JitRL exact state-aware path 被依赖阻塞，MemRL full retrieval 未运行；结论仅限 native global/value-selection components。详见新目录 SCOPE_CORRECTION.md、Stage4_1实验结果.md、最终结论.md 和 results/。

历史 verdict 均冻结：Run1 IDEA2_RUN1_NO_GO；Confirmatory IDEA2_CONFIRM_GO；Stage-2 CAUSAL_SUFFICIENCY_WEAK；Stage-3 REAL_FORMATION_WEAK；Stage-4 POLICY_MEMORY_GO。本阶段停止，不自动进入方法设计或下一阶段。

## Idea 2 Stage-5 — Method Viability Study — 2026-10-05

独立目录：idea_validation/idea2_method_viability/。新增 verdict：**METHOD_VIABILITY_GO**；选择 practical candidate **M1 StateStandardizedUtility**（暂用描述性名称）。57项测试在正式运行前通过，锁定预注册与实现；两系统复现 Stage-4.1 native selected IDs。36个exact bank、720条method/target结果，G0–G9通过。

M1 在本轮已观测离散state下实现null PIG/NPE=0，真实global gap=.10、TSR=1，P/Q×三档gamma全部query crossover正确；通过两个native metadata adapters，未读取true propensity/gamma。M4也满足常规Gate但有small shrinkage bias；M2不随target变化，crossover失败，.99 clipping偏差明显；M3是ORACLE / NOT CANDIDATE METHOD。M0是native selection-support proxy，不能当作成功概率；报告用absolute NPE、TGE、TSR及same-scale A1消融共同判断。

M1统计核心就是direct standardization/g-computation，不声明novelty。exact低support结果不证明sampling robustness，也不证明自然语言state解析或full-agent效果。历史六阶段verdict全部冻结：IDEA2_RUN1_NO_GO、IDEA2_CONFIRM_GO、CAUSAL_SUFFICIENCY_WEAK、REAL_FORMATION_WEAK、POLICY_MEMORY_GO、NATIVE_EVIDENCE_GO。详见新目录theory.md、Method候选比较.md、Stage5实验结果.md、最终结论.md与results/。本轮停止，不自动开始新颖性审计。

## Idea 2 Stage-6A — Cross-Policy Memory Certification — 2026-10-06
独立目录 idea_validation/idea2_cross_policy_certification/。W1 same-policy echo 保持 D_policy=0、DESCRIPTIVE；W2 识别交替方向与 C_conflict=1；W3 invariant profile 为 PRESCRIPTIVE；W4 false-diversity D=.0333 对比 true-diversity D=.60；M1 utility 在 echo/diverse 下同为 gap=.4，但 lifecycle 不同。最终 **CROSS_POLICY_CERT_NARROW**：G0–G4、G6–G9 通过；G5 因运行器未充分隔离生成器与 candidate 输入而失败，故不声称完成 oracle-free 执行认证。24 项测试通过，正式 deterministic run 一次，未调阈值。Stage-6A 已停止。

## Idea 2 Stage-6A.1 — Oracle-Free Boundary Hardening — 2026-10-06

独立目录：idea_validation/idea2_cross_policy_certification_hardening/。本轮结论 **ORACLE_FREE_HARDENING_GO**，H0–H9 全 PASS，G5 由真实的 schema、拒绝、AST、字符串、进程、文件、环境、metadata invariance 与数值复现检查组合计算。77 项预运行测试通过；正式运行一次，无 restart。

候选仅在临时目录读取匿名逐条观测与冻结公开阈值；11 个固定配置复现 Stage-6A，5 种私有元数据变换得到逐字节相同的输出。M1 ECHO/DIVERSE gap 均 .40，认证分别 DESCRIPTIVE/PRESCRIPTIVE。1,956 个历史文件及链接核验一致。Stage-6A 的 **CROSS_POLICY_CERT_NARROW** 永久保留，未回写历史结果。新增证据仅限受审计代码路径的执行边界，不等同于 OS 级恶意代码隔离，也不扩大 synthetic/exact-count 研究结论。本轮已停止，未进入后续阶段。


## Idea 2 Stage-6B — Native-System Mapping + Method Differentiation Audit — 2026-10-06

独立目录：idea_validation/idea2_native_mapping_and_differentiation/。静态审计结论 **NATIVE_MAPPING_GO / DIFFERENTIATION_BORDERLINE / STAGE6B_NARROW**。JitRL MAP-L1、MemRL MAP-L3、ExpeL MAP-L1、Reflexion MAP-L0、ReasoningBank MAP-L3；JitRL与Reflexion提供最小过门槛证据。MemRL异常fallback动作对齐和ReasoningBank细粒度观察/执行证据链缺口未隐去。映射只表示原生数据落点，不代表动态行为多样性或干预收益。

正式核验16篇agent memory/learning与8篇母领域论文的方法正文；C1和广义utility/使用资格分离已有直接重叠，未找到完整cross-policy支持+transfer certification lifecycle组合的直接覆盖，但尚未排除漂移/不变性化约、既有gate替换证据以及evidence-aware confidence/support决策三项风险。同M1不同status不足以证明不可替代性。12项校验测试通过；2035个历史文件/链接SHA核验一致，预注册不变。未运行LLM、API、benchmark或训练，未改upstream和九项历史verdict。本轮停止，不进入Stage7。详见Stage6B研究结果.md、两个track矩阵和results/final_verification.json。


## Idea 2 Stage-6C — Target-Relative Transfer Envelope — 2026-10-06

独立目录：idea_validation/idea2_target_relative_transfer_envelope/。最终 **TARGET_RELATIVE_ENVELOPE_GO**，G0–G9全PASS。45项测试预先通过并SHA锁定；一次deterministic formal run，无restart。原Stage-6A.1全局认证代码不变，8个case均PRESCRIPTIVE，所有M1精确为A=4/5、B=2/5、gap=2/5。

P1/P2/P3相同source evidence与source summary/provenance SHA对应不同target位置，probe分别TRANSFERABLE/OUT_OF_ENVELOPE。P4最近TV均精确1/10，但convex membership不同。独立Fraction几何验证与HiGHS结果一致。结果只排除指定source-only及nearest-scalar信息投影，不能排除target-aware uncertainty/provenance/已有support geometry方法；OUT在本world也有真实+.40 gap，未证明实际迁移失败或causal safety。Convex hull仅diagnostic probe，无method novelty claim。

十个历史目录2074个文件/链接SHA一致，Stage-6B **STAGE6B_NARROW**永久保留。本轮未查论文、调用LLM或运行agent benchmark；到此停止。下一步只建议对target-relative transportability、support geometry、multi-logger OPE与target-aware gating做精确collision audit，不自动开始，不进入Stage7。详见Stage6C实验结果.md及results/final_verification.json。


## Idea 2 Stage-7 — Policy-Relative Memory Validity — 2026-10-07

独立目录：idea_validation/idea2_policy_relative_validity/。最终 **POLICY_RELATIVE_VALIDITY_GO**，G0–G6全PASS。19项正式前测试通过并锁定预注册与正式代码；一次deterministic formal run，无restart。五状态固定MDP中，同一m0=(s0,a_L,+2,pi_A)的exact Q随continuation从pi_A切换pi_B，由+2变−2，环境与奖励fingerprint不变。

pi_B下NoMemory回报+1；SimilarityMemory、HistoricalUtility和simplified JitRL-style均因历史成功m0选择a_L，回报−2、20轮累计regret 60、harmful-use rate=1。Oracle与naive provenance-only拒绝并恢复+1。F3中m0首次复用令共享a_L偏好θ从0到2，continuation由a_R变a_L，m0在同轮发生+2→−2 validity flip；负trajectory写回后，naive最高历史utility检索仍重复m0，形成最小M_t→pi_t→trajectory_t→M_(t+1)闭环。

policy-dependent Q本身是经典RL事实；本轮额外验证的仅是self-generated memory同时作为旧policy产物和改变未来policy的干预变量。共享偏好更新是人为固定toy机制；B2/B3不是MemRL/JitRL复现；无真实LLM、自然语言memory、benchmark、novelty或真实系统普遍性主张。此前2144个历史文件/链接SHA一致，Stage-6C verdict永久保留。本轮停止，不自动映射真实系统或开始下一阶段。详见Stage7实验结果.md与results/final_verification.json。

## Idea 2 Stage-8 — JitRL Native Mapping & Policy-Relative Failure Reproduction — 2026-10-07

独立目录：`idea_validation/idea2_jitrl_native_failure/`。使用项目内固定 JitRL
commit `143d22185d95fbf633a0befe6861d5e8b732543b`，Stage-8A 得
**JITRL_MAPPING_GO**；23 项预运行测试与 SHA256 lock 通过，唯一一次 deterministic
formal run 无 restart。source-extracted WebArena 原生 storage/retrieval/advantage/
score correction 路径在 `pi_A→pi_B` 下检索 +2 历史信号，native signal=+1，而
current exact target advantage=-1.5；动作由 `a_R` 改为 `a_L`。20 episodes 中
NoMemory/JitRLNative/Oracle 平均回报为 +1/-2/+1，JitRLNative 累计 regret=60，
harmful-use/bias rate=1。G0–G7 PASS，G8 NOT_TESTABLE，最终
**JITRL_NATIVE_FAILURE_GO**。结论仅限 toy MDP、固定 seed/commit 和薄 adapter；
无完整 LLM benchmark、native closed-loop、普遍性、novelty 或方法主张。
