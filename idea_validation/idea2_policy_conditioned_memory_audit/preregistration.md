# Stage-4 预注册：Policy-Conditioned Experience Memory Audit

日期：2026-10-05。主目录与环境见 `results/final_verification.json`。本文件在任何正式 synthetic/dynamic 运行前冻结；不得按观察结果修改提示、种子、目标系统、指标或门槛。

## 研究命题

Experience Memory is Policy-Conditioned Evidence, not Policy-Independent Knowledge。观察成功率可能反映 `behavior policy → selected experience → memory → future decision`，不等同于 policy-invariant utility。Ground-truth 环境中两个动作在给定状态下具有相同 outcome mechanism，因此 target policy 的两动作价值相等。

## 固定系统样本

依次审计六个预先指定名称，不因结果替换：
JitRL (`https://github.com/liushiliushi/JitRL`),
MemRL (`https://github.com/MemTensor/MemRL`),
Memento（论文 *Selective Memory Retention for Long-Horizon LLM Agents*, arXiv:2606.29178；搜索确认官方代码前不采用同名第三方项目）,
ReasoningBank (`https://github.com/google-research/reasoning-bank`),
ExpeL (`https://github.com/LeapLabTHU/ExpeL`),
Reflexion (`https://github.com/noahshinn/reflexion`)。
官方链接无法确认时记 `OFFICIAL_CODE_NOT_FOUND`。其他官方 repo 可参与静态审计但不替换上述名单。动态尝试仅限已确认官方 source snapshot。

## 合成环境

使用 Python 3.10.21 的 `agentmem_lab`，不装第三方系统依赖。固定 seed=20261005。状态等概率；对每个动作：
`P(Y=1|S0,A)=P(Y=1|S0,B)=0.9`，
`P(Y=1|S1,A)=P(Y=1|S1,B)=0.2`。
目标 state 分布为 S0/S1 各 0.5，故 target value(A)=target value(B)=0.55。

生成 D_P、D_Q 各 2000 条。P: P(A|S0)=0.95、P(A|S1)=0.05；Q: P(A|S0)=0.05、P(A|S1)=0.95。D_BAL 为 2000 条、每个 state×action cell 恰好 500 条。Outcome Bernoulli 抽样按相同状态机制生成。固定数据只生成一次，所有 baseline/adapters 重用这些 JSONL。

## Baselines 和 metrics

B0 Aggregate Success Memory: action score 为该动作总体成功率。
B1 State-Conditioned: 每动作按 state 估计成功率，再以固定 target distribution 加权。
B2 Oracle Exposure-Aware: 使用日志 propensity 的 direct-stratification/IPW 诊断实现；不得作为外部系统机制，也不把 propensity 注入其 memory。

`PSI=|score_P(A)-score_Q(A)|+|score_P(B)-score_Q(B)|`。
只有返回 per-action score 的系统计算 PSI。
`RCD` 为 top-k retrieved action labels 的 action-frequency 分布之间 TV distance；`PIUR=1` 仅当 P/Q action-preference signs 相反（两者差值绝对值须 >0.01），且真值相等。缺少接口则 N/A。
Balanced reduction 对 score 接口定义为 `1 - |delta_BAL| / mean(|delta_P|,|delta_Q|)`，其中 delta=score(A)-score(B)；若分母为 0 则 N/A，结果不截断。
State-matched effect 分别报告 S0、S1 的 P/Q delta 差与 P/Q action preference，不作结果挑选。

动态调用每个支持的 adapter 固定对 P/Q/BAL 三库各 reset、ingest 一次；query：target、S0、S1；top-k=20。外部默认机制不得注入 propensity、平衡样本、覆盖 utility/retrieval 公式。外部模型/API 不可用时记录准确阻断层级，不模拟成成功。

## Static audit 分类

每个系统回答 Q1–Q8，逐条提供文件、函数、行号和来源。论文证据与源码证据区分。关键词命中仅用于候选；最终 JSON 需人工核对公式/调用链。结构盲点仅当 self-generated policy-selected experience、outcome 用于未来 utility/reuse、没有保存/使用 propensity 或 exposure correction 三项均有证据时为 true。

L0=仅静态；L1=能以原生构造/ingest 并观测存储或 score；L2=能运行原生 retrieval/ranking；L3=能运行最终 memory-conditioned action/policy。必须记录真实运行等级。

分类：A=存储/使用 policy 或曝光校正；B=曝光盲但状态条件化，观测中无明显 aggregate bias；C=满足 structural blindspot 且动态出现 PSI/RCD 或 PIUR；D=不适用。证据不足用 UNKNOWN/NOT_APPLICABLE，不把静态线索推断成实测动态效应。

## 预注册 Gate

G0：六个指定对象中至少 5 个有 paper/repo/mechanism evidence。
G1：至少 3/5（按有充分静态证据的首五个适用系统）满足 self-generated + outcome-weighted reuse + no exposure correction。
G2：至少 2 个系统 L1+，至少一个 L2+。
G3：至少两个 L1+ 系统显示 PSI≥0.10 或 RCD≥0.10，且方向与 P/Q logging policy 一致。
G4：至少一个真实系统的 balanced reduction≥0.50。
G5：如所有系统 state-matched query 消除 effect，则结论限制为 aggregate/global utility；不得称为普遍 blind spot。此项为解释规则，不做独立 PASS/FAIL。
G6：少于 3/5 有显式 propensity/OPE/behavior-policy correction 才 PASS；若 ≥3/5 已实现则 FAIL 并偏向 NO_GO。

GO 必须 G0–G4、G6 全过，且至少 3 个 structural blindspot、至少 2 个真实动态支持。BORDERLINE 用于有静态广泛信号但动态阻断/仅一个动态复现/仅 aggregate 作用等。NO_GO 用于多数系统已有校正/反事实或真实动态普遍不随 logging policy 变化。最终 verdict 仅允许 POLICY_MEMORY_GO / POLICY_MEMORY_BORDERLINE / POLICY_MEMORY_NO_GO。

## 操作纪律

第三方代码仅临时置于被忽略的 `third_party/`，不直接改 upstream。优先下载官方 source archive 并记录 commit；若 git clone 失败，明确 clone 失败、archive 成功与否。禁止将 LLM/API 缺失伪装成动态通过。第三方依赖按需使用独立 `pcm_<system>` 环境并导出 yml；主环境不装大型依赖。每个项目最多一次有边界的依赖尝试。所有负结果保留。完成 verdict 后停止。
