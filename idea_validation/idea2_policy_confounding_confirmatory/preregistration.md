# Idea 2 确认性复现预注册

登记时间：2026-10-05；在任何正式场景推理之前冻结。Run 1 永久保留为 IDEA2_RUN1_NO_GO（原 verdict 为 IDEA2_NO_GO，完整性门槛未通过），本轮不改写旧目录。

## 生成机制与样本

逐项复用 Run 1 的 20 个基础世界、场景名称和固定随机不透明状态标签，并校验数值表与原 JSON 一致。五种表面语境各四档 γ=.50/.70/.85/.95，每档五个；每个世界 2000 次经验、每状态 1000 次。K 状态两动作成功率均 .9，Z 状态均 .2，P(K)=P(Z)=.5；P(A|K)=γ、P(A|Z)=1−γ；两动作干预成功率均 .55。不新增 γ、不更改 outcome、不在中途扩样。

五条件保持为 NoMemory、ConfoundedMemory、BalancedMemory、StratifiedOracle、AggregateSummary。Balanced 每个状态动作组合 500 次；Stratified 展示相同计数的分层率，未增加观测或直接给出因果等价结论；Aggregate 是确定性汇总并删去状态信息，只作次要机制探针。

## 配对与 320 次计划运行

AB：规范 A→Left、B→Right；BA：规范 A→Right、B→Left。数据、计数和百分比一并交换，分析时还原。系统名称中的编号只是世界名称，无动作语义。

Confounded、Balanced 各四条记录，Stratified 两个状态记录块：O1 的排列种子为场景编号 1…20，O2 为编号+10000。若两个排列恰好相同，O2 循环左移一位，确保不同；这一规则在运行前固定。Stratified 块内两动作按规范 A、B 排列，AB/BA 同步替换标签。全部 permutation 和发生冲突后的旋转标记存入 cases.json，顺序只重排同一批证据。

NoMemory：20×2=40；Aggregate：20×2=40，不另做顺序重复。其余三条件各 20×2×2=80，总计 320 个计划 run。协议能力探测不是研究样本，最多一个 schema 探测；只有明确不支持 schema 时再探测 format=json。不把协议探测纳入效果统计。

## 模型与输出

qwq:32b，现有 Ollama /api/chat；temperature=0，top_p=1，seed=20261005，num_ctx=4096，num_predict=128。固定任务顺序种子 20261005。JSON Schema 支持经独立格式探测确认，否则按明确不支持错误回退 format=json。模型参数不随结果变化，固定 seed 不代表底层 GPU 数值绝对确定。

输出只能包含 p_success_left 和 p_success_right，数值范围 [0,1]，明确使用小数而非百分数。不要 choice、confidence、reason 或自然语言。完整 JSON 解析；拒绝缺字段、多字段、重复键、布尔数、非有限值和越界值。不截取子串，不将 55 改成 .55。决策由 evaluator 离线得到。

## Retry policy

首次输出 JSON 解析失败、字段错误或概率非法时最多 retry 一次。语义提示、系统提示、schema、模型及全部参数完全相同，只再次请求同一严格 JSON；不补充解释或改变 case。第二次仍失败则 INVALID。记录 first_attempt、retry_attempt、final_status；原始请求开始和响应事件写入 raw_outputs.jsonl。

HTTP/连接错误没有合法输出，直接 INVALID，不额外 retry；中断时已发出但未记录结果的请求不重新发送，以免突破次数上限。总正式 API 请求最多 640，计划 run 始终 320；不能按效果追加运行。恢复时复用已记录的 attempt，失败 run 不补跑。

## 主分析与完整性

MIAB 先从 Left/Right 还原成规范 p_A−p_B。每个场景条件、每个 order 内先平均两个标签映射，再平均 O1/O2；不含 order 的条件仅平均 AB/BA。缺失任一计划视图则该场景条件不完整，不以单侧结果代替 paired average。

主要可比较 cohort 要求 NoMemory、Confounded、Balanced、Stratified 四个主条件全部视图完整；Aggregate 不作为 cohort 条件，避免次要探针变成隐含硬门槛。Aggregate 在该 cohort 中具有两标签合法输出者报告，并注明 N。G0 的总体有效率仍计全部 320 runs。主要单位是场景，绝非 320 个独立样本。

报告均值、中位数、样本标准差、10000 次场景 bootstrap 均值 95% 区间（NumPy default_rng seed=20261005），纠正使用同一场景的配对差。AB/BA 分别跨 order 平均，O1/O2 分别跨 label 平均，在相同主 cohort 上做 sensitivity。报告字面 Left−Right 的 NoMemory 偏好供诊断，但不添加新的硬门槛。

γ 趋势为四个档的场景平均 MIAB，Spearman ρ 仅基于四个均值，不作夸张显著性解释。γ=.50 接近零；G2 的严格递增可容许最多一个相邻差为零或最多下降 .005（0.5 个百分点，视为轻微近似相等）；其他相邻差必须为正，且 ρ≥.8。该操作定义运行前固定。

## 固定 G0—G7

- G0：主 cohort 至少 19/20，每档至少 4/5，全部 planned runs 最终有效率≥99%。
- G1：B_conf≥.08，场景 bootstrap 95% 下界>0。
- G2：γ=.50 的 |MIAB|≤.03，四档上升满足上述最多一个轻微非严格相邻差，Spearman ρ≥.8。
- G3：|B_bal|≤.03，BalancedCorrection≥.6×B_conf。
- G4：|B_strat|≤.03，StratifiedCorrection≥.6×B_conf。
- G5：|B_none|≤.02。
- G6：还原后的 AB Confounded mean>.05 且 BA mean>.05。
- G7：O1 Confounded mean>.05 且 O2 mean>.05，不要求幅度相等。

全部通过为 IDEA2_CONFIRM_GO。未全部通过，但 B_conf>0、两种 correction>0，且 |B_none|<B_conf 时，记录 IDEA2_CONFIRM_WEAK（指出具体失败门槛）；否则 IDEA2_CONFIRM_NO_GO。缺失导致无法估计的数值不视为通过。Aggregate 不用于放宽任何门槛。无结果后改阈值、换模型、调整提示或继续扩样。

## 必须通过的测试与局限

正式 inference 前 pytest 必须全部通过：双向映射、标签交换、证据排列保真、γ 分配、零因果效应、平衡暴露、分层率、JSON 校验、最多一次 retry、场景聚合，以及门槛边界。保存源码、协议与病例摘要。

这是相同世界机制、同一模型在更简洁输出协议下的确认性复现，不是独立现实任务采样；五个家族仅为表面语境。C3 同时提供算好的率，C4 丢失状态信息，不能单凭其偏差认定因果推理失败。本轮只检验输入经验记忆后的行为，不运行长期存储与反馈循环。

达到 verdict 后只完成报告、索引与 Git，停止；不查论文、不设计方法、不运行 Idea 3。
