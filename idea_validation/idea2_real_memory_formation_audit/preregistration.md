# Idea 2 Stage-3 预注册：真实记忆形成审计

## 研究问题与范围

检验常见 Agent 风格的记忆形成是否会自然产生“事实忠实但无法恢复完整 state-conditioned 结构”的记忆，以及结构丢失是否与下游决策 regret 相关。本研究使用 Stage-2 的固定 synthetic experience worlds，只评价本模型、本提示和本协议；不推论所有 Agent 或真实长期部署。

历史冻结：Idea 2 Run 1 为 IDEA2_RUN1_NO_GO（原始 IDEA2_NO_GO）；Confirmatory 为 IDEA2_CONFIRM_GO；Stage-2 为 CAUSAL_SUFFICIENCY_WEAK。上述目录、数据和 verdict 不修改。

## 固定输入与来源

输入完整复制自 idea_validation/idea2_causal_sufficiency/cases.json。SHA256：76fbd6c45e70a8737a6b81b220f480c8f95aa63b18d6d454b969cc8fda2ac148。来源有 20 matched pairs / 40 worlds。运行前检查确认 pair 内 aggregate action exposure/success 完全相同，四格 state-action 统计不同，target optimal action 相反，且有理数 Fraction 精确比较通过。每个 world 的 experience table 不变。

Oracle summary 逐格陈述 state、action、exposure、success、failure。40 个长度的最大值为 117 字符。正式预算冻结为 MEMORY_BUDGET=512，即 max(512, ceil(1.25 × 117))。完整 Oracle representation 可在预算内表示；任何自然生成 memory 超预算视为该 formation call INVALID，不截断或重写。

## 条件与提示

F1 GenericSummary：将历史交互压缩为简洁、对未来有帮助的长期记忆；仅依历史、不编造、保留自认为未来重要的信息。
F2 ReflectionLesson：回顾经验，总结以后类似任务值得记住的 lesson；忠于经验、不编造、不输出行动建议。
F3 StrategyMemory：提取未来决策可能有用的策略性经验；忠实、不增加未观察事实。
F4 ConsolidatedExperience：合并重复零散经验为长期 memory，减少冗余但保留重要信息；忠实、不增加事实。

不在 formation prompt 或 system 指令中出现 causal、confounder、selection bias 或要求保留 state。Writer 仅输出严格 JSON {"memory":"..."}。每个 writer × world × formation type 只运行一次。

## 模型与调用协议

Primary writer qwen2.5:14b；secondary robustness writer qwq:32b，仅在 Primary 全流程和正式统计结束后运行，不得替代 Primary。Downstream reader 与结构恢复 reader 均为 qwq:32b。双 source-aware faithfulness auditors：A qwq:32b、B qwen2.5:14b。

所有调用 temperature=0、top_p=1、seed=20261005；num_ctx=8192。formation num_predict=512，auditor num_predict=512，reader num_predict=256。各类输出使用严格 JSON schema。非法 JSON、缺字段、越界或错误类型最多对同一 prompt/model/options/schema 重试一次；transport error 记 INVALID 不重发。原始请求、模型、条件、world、attempt、时间、原始及解析响应逐条记入 JSONL。不得下载模型。

## Controls 与审计流程

C1 StatePreservingOracle 机械呈现每个 state × action 的 exposure/success/failure；C2 FaithfulLossyAggregate 机械呈现每个 action 的 aggregate exposure/success/failure。两者均由源表生成、不调用 writer。先用 qwq:32b 的 memory-only reader 恢复结构并校准：C1 mean CRA≥0.95 且 full retention≥0.90；C2 mean CRA≤0.50。任一失败则最终 verdict 为 STAGE3_RECOVERY_PIPELINE_INVALID，停止后续 inference。

每个自然 formation memory 使用两个 source-aware faithfulness auditors，且只有两者均 faithful=true 才进入 STRICT_FAITHFUL；分歧记 AUDIT_DISAGREEMENT，二者均 false 记 UNFAITHFUL。auditor 不评价质量。结构恢复 reader 只见 memory，八个 state/action success/exposure 字段在信息不足时必须为 null，不给 raw source。CRA 为四格中 success 与 exposure 同时正确的格数/4；CRA=1 定义 FULL_STRUCTURE_RETAINED。另报告 STATE_LABEL_RETAINED（S0 与 S1 各至少恢复一格完整 success/exposure）和 ACTION_CONDITIONAL_STRUCTURE_RETAINED（至少一个 action 在 S0、S1 两格均恢复完整 success/exposure，因而可计算该 action 的跨 state 成功率差）。

下游对每条生成 memory（以及 C1/C2 controls）各做 AB、BA 两次 label swap；memory 中 A/B label 同步替换。无 memory order 操作。下游 reader 只见 memory 和 P(S0)=P(S1)=0.5，输出 p_success_left/right。离线计算 Decision Accuracy、Action Value Regret、Signed Preference Error、Pair Resolution Rate。Pair resolution 指 matched pair 两边都选对真实 optimal action。

## 主要统计

Primary 和 Secondary 分开报告。每个 writer × formation type 报告生成数、双审计 STRICT_FAITHFUL 数和比例、CRA、FULL_STRUCTURE_RETAINED rate、FBIR、下游 accuracy/regret、pair resolution。FBIR = STRICT_FAITHFUL 且非 FULL_STRUCTURE_RETAINED 的数量 / STRICT_FAITHFUL 数量。

在 strict-faithful memory 中，比较 FULL_STRUCTURE_RETAINED true vs false 的下游 regret；用按 world 分层 bootstrap 10,000 次、default_rng seed 20261005，报告 lost-retained difference 和 95% CI。按 world 对 CRA 与 regret 计算 Spearman rho，并谨慎解释。matched pair 报告 both sufficient / one sufficient / both insufficient 及 downstream pair resolution。

## 预注册 GO 门槛

G0 完整性：Primary formation、双 faithfulness audits、recovery audits、downstream 各自有效率≥99%。
G1 Recovery calibration：C1 mean CRA≥0.95、full retention≥0.90；C2 mean CRA≤0.50。失败触发 STAGE3_RECOVERY_PIPELINE_INVALID。
G2 Faithfulness：至少 3/4 primary formation types 的 STRICT_FAITHFUL rate≥0.80。
G3 现象：至少 2/4 primary formation types 的 FBIR≥0.30。
G4 非单 prompt：至少两个 archetype FBIR≥0.30，且各自 strict faithful N≥30。
G5 后果：strict faithful cohort 中结构丢失组 mean regret 高于完整保留组，bootstrap difference 的 95% CI lower bound >0。若 world pairing 不成立，按 world 分层 bootstrap 并记录。
G6 matched pairs：至少两个 formation type 的 PAIR_BOTH_INSUFFICIENT rate≥0.25，并且这些 pair 的 downstream pair-resolution 低于 C1 oracle。
G7 writer robustness：secondary writer 至少一个 archetype FBIR≥0.25，主要位于 strict faithful cohort；若没有现象，最多 WEAK。
G8 容量控制：所有 C1 oracle summaries 均在 512 字符内；自然 formation 输出不得系统性撞预算 ceiling。若自然输出长度≥90%预算的比例超过 10%，标记 CAPACITY_CONFOUNDED，最高 WEAK。

REAL_FORMATION_GO 仅在 G0-G8 全通过时给出。REAL_FORMATION_WEAK 用于 G0 不足、G2-G4/G5/G6/G7 中出现部分现象但未满足 GO、secondary 未重复、审计分歧或 capacity confound 等情况。REAL_FORMATION_NO_GO 用于在 G0 与 G1 通过时，G3 与 G4 均未显示至少两个 archetype 的 faithful-but-insufficient，且 G5/G6/G7 均未显示后果或复现信号。REAL_FORMATION_GO 仍要求 G0-G8 全部通过。STAGE3_RECOVERY_PIPELINE_INVALID 仅用于 C1/C2 recovery calibration 失败。判定后停止。
