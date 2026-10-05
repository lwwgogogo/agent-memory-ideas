# Idea 2 Stage-4.1 预注册：Native Evidence Hardening

本文件须在正式原生选择运行前完成 SHA256 锁定。所有历史目录只读，Stage-4 POLICY_MEMORY_GO 永久保留。本轮只审 JitRL commit 143d22185d95fbf633a0befe6861d5e8b732543b 与 MemRL commit c1b322ca43de36ddf64c6712f89d0095bfc35ce0；commit 不符立即停止。不得更新第三方仓库或改其源码。

## 固定数据和顺序

gamma 固定为 0.50、0.70、0.85、0.95；每个 state 恰有 1000 experiences。S0、S1 的成功率分别精确为 9/10、1/5，所有 state-action cell 均使用整数 exposure × rate 构造成功数。P 的 P(A|S0)=gamma，P(A|S1)=1−gamma；Q 相反。target P(S0)=P(S1)=1/2，V(A)=V(B)=11/20。没有 Bernoulli sampling。

canonical records 按 S0/S1、A/B、成功/失败、cell 内索引产生；id 仅由 state/action/outcome/index 组成，不编码 policy、gamma、seed。P/Q 只改变 cell 中的记录数量；同一条件所有 replicate 的记录逐项完全相同。gamma=.50 的 P/Q 原始数据完全相同，BAL 使用该条件 P 的返回结果。

20 个顺序种子固定为 20261005 到 20261024。使用 Python 3.10 random.Random(seed).shuffle；同一个 seed 在两个系统、P/Q、各 gamma 使用相同的固定 shuffle 协议；不得重采样 outcome。记录 multiset 与 order SHA256，前者先把每条 canonical JSON 按字典序排序再计算，后者保留输入顺序。只生成八份 canonical log，replicate 由固定 seeds 重建。

## 原生执行协议和边界

JitRL 只通过上游原文件 importlib loader 执行 get_top_episodes。每条输入 experience 转成单步 episode，原始 outcome 直接成为 final_score，所有排序和 top-k 选择完全由原生函数完成。保存整个原生返回列表，并验证返回项对象来自输入 episode。

MemRL 从上游原文件加载 QValueUpdater.update 与 ValueAwareSelector.select。保持 Stage-4 固定配置：alpha=.1、gamma=0、q_init_pos=q_init_neg=0、epsilon=0、recency_boost=0；epsilon=0 是已有受控 greedy 配置，上游默认 epsilon=.1，本轮不是默认完整系统性能测试。每条新 memory 更新一次，成功/失败反馈分别使用原生配置 +1/−1。storage boundary 只实现 get/update，不实现排序。所有 candidates 的 similarity 固定 .5，保留 state/action metadata；这只隔离 value selector，不模拟语义 recall、向量或 embedding。每个 k 调用 select；其完整 selected、actions、simmax 原样保存；原生全量 candidates 排序用 count 与 SHA256 保存，避免每个 k 重复提交整个 bank。保留 native timestamps，不启用 recency 排序。

两个系统 primary k=20；全部 sensitivity k=5、10、20、50。每个 system 共 4 gamma × 2 policy × 20 seeds × 4 k=640 条原生返回。JitRL 640 次 ranker 调用；MemRL 320000 次单步 update 和 640 次 select。相同日志与逐项 reward 映射使两组件可能产生一致选择，不能把它们当成相互独立的证据样本。

JitRL 原生模块的未使用 LLM helper import 用显式抛错边界隔离；helper 一旦被调用则终止。MemRL MOS 只在类型导入处隔离。上游原生函数不复制、不 AST 重写、不 monkey-patch。所有 full state-aware 依赖检查在单独进程中进行，禁止使用上述边界作为完整检索替身。

## 指标

所有 Gate 的 selection metrics 只从原生返回项的 action 和顺序计算：
- f_A=#A/k，f_B=#B/k，SSP=f_A−f_B；严格阈值使用整数计数/Fraction，避免浮点 .10 边界。
- Native-PIUR=1：SSP(P)>.10 且 SSP(Q)<−.10，或反方向；否则为 0。
- Native-RCD=|f_A(P)−f_A(Q)|。
- RWP 为 secondary：按原生 rank 的 1/log2(i+1) 加权 action 符号，再除权重总和。
- BAL reduction=1−|SSP(BAL)| / ((|SSP(P)|+|SSP(Q)|)/2)，每个 seed/k 与 gamma=.50/P 配对；分母零记 NA，报告有效数量。允许负 reduction，不裁剪。G4 使用 gamma=.95、k=20 的 20 seed reduction 中有限值的中位数。
- D_gamma=20 seeds 的 Native-RCD 中位数，primary k=20。报告四点 Spearman rho，常数序列记 0，不做显著性检验。
- tie fraction 定义为 selected 项中其 score 在该 selected set 至少重复两次的项数比例；额外报告 1−unique/k 以避免歧义。报告 candidate 唯一分数数、同分比例和 top-score candidate pool size。
- 额外机制诊断只计算 exact log 中 success-pool action composition，与 native selected composition 比较；不计算整个 bank 的 action-average score。

## 固定 Gate 与判定

| Gate | PASS 条件 |
|---|---|
| G0 | 两系统全部 640 条 primary/sensitivity selection 可追溯到指定 upstream 原生函数；所有指标可从保存的 native return 重算；旧 score_action 不调用、不进入 Gate |
| G1 | 所有 exact cell counts、P/Q exposure reversal、V(A)=V(B)=.55 和 20 replicate multiset 校验通过 |
| G2 | JitRL gamma=.95/k=20：Native-PIUR rate≥.80 且 median Native-RCD≥.30 |
| G3 | MemRL 同 G2 |
| G4 | 两系统分别 median BAL reduction≥.50（gamma=.95/k=20） |
| G5 | 两系统各自 D_.95>D_.70 且 D_.95>D_.50+.20，至少一个四点 Spearman rho≥.80 |
| G6 | 每个系统至少 3/4 k 在 gamma=.95 时中位 SSP P/Q 方向与 primary k=20 相同；primary 必须正负相反，零不视为方向一致 |
| G7 | 仅从 native returned selection 重算、完全无旧 action-average aggregation 时 G2/G3/G4/G5 仍通过 |
| G8 | 非 hard Gate：PERSISTENT / MITIGATED / BLOCKED，据实际边界收窄 claim |

G0–G7 全 PASS 才可 NATIVE_EVIDENCE_GO。若 G0/G1 失败，或两个系统 G2/G3 均失败，或两系统 BAL reduction 均不到 .50，则 NATIVE_EVIDENCE_NO_GO。其余部分支持为 NATIVE_EVIDENCE_NARROW。不随结果修改阈值、seed、k、样本或实现。G8 的 BLOCKED 不能加强 GO；所有 GO 都只限 native episode ranking 与 value-selection component。

## State-aware 路径

先静态核对 JitRL retrieve_similar_with_vector 的签名、双 FAISS candidate recall、最终 state/history Jaccard similarity、reward tie ordering 和 provider。当前预检查：openai、tiktoken、dotenv、faiss 缺失，OPENAI_API_KEY/OPENAI_API_KEY2 均 NOT_SET；只记录环境变量 SET/NOT_SET，不打印或加载秘密，不安装依赖或替换 embedding。按 FULL_STATE_AWARE_BLOCKED_BY_DEPENDENCY 记录 exact path 未运行，RCD/mitigation 为 NA，不推测。

若当前合法现有依赖自然可用才允许 exact upstream 路径；本次已确认缺失，不编造执行。MemRL 静态确认 selector 之前存在 MOS query/keyword/embedding candidate generation；memos 缺失，MEMRL_FULL_RETRIEVAL_NOT_RUN。动态结论均不包括这些 full retrieval 路径。

## 测试与停止

正式运行前必须所有测试通过，存机器可读时间与结果并锁定 preregistration 和实现 SHA256。运行前后核查两个 upstream commit、source SHA、五个历史目录 tracked 文件 SHA256。输出全 20 seeds，不挑最好顺序。完成固定报告、Git commit/push 后停止，不开始方法设计或下一阶段。
