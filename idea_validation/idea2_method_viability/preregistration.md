# Stage-5：方法可行性预注册

本轮仅做固定、离散、已观测 state 的 correction viability，不声称方法新颖性；六个历史目录的 code/result/verdict/report 全部只读。使用 agentmem_lab / Python 3.10.21。所有正式运行前先测试全通过，再锁定本文件及实现 SHA256。

## 数据、基线和 endpoint

A：S0 A/B=.9/.9，S1=.2/.2；B：S0=.9/.8，S1=.3/.2；C：S0=.9/.6，S1=.2/.5。每 state=1000 条，所有 exposure 和 success 都为整数，Fraction 校验。A/B/C 使用 gamma=.50/.70/.85/.95、P/Q。D sensitivity 同时复用 A/B/C outcome 机制，gamma=.95/.99，每 state 仍为1000；.99 不进 hard Gate。A/B target=.5/.5；C 同时报告均匀 T、T0=.8/.2、T1=.2/.8。分别真实 gap 为 A=0、B=.10、C(T)=0/C(T0)=+.18/C(T1)=−.18。

原生固定 commit：JitRL 143d22185d95fbf633a0befe6861d5e8b732543b；MemRL c1b322ca43de36ddf64c6712f89d0095bfc35ce0。保持 Stage-4.1 对象转换、epsilon=0 的受控 greedy 配置及原生 ranker/update/select，不修改 upstream。gamma=.95/null 的20 seeds=20261005–20261024 必须复现旧 selected IDs（并 reversal rate≥.80、median Native-RCD≥.30），否则 G0 FAIL，停止候选实验。

M0 不具有 action-level success-probability 输出，本轮不伪造它。明确定义 U0(a) 为原生 k=20 selection fraction f_a 在20顺序 seeds 上的中位数；它是“选择支持度”，不是 causal success value。之后 PIG0=各 action 的中位支持度 P/Q 差之和。因此它与 Stage-4.1 median paired RCD 不应混同。CorrectionRate=1−PIG(M)/PIG0 是跨统计量的描述性归一化，不能单独证明估计器成功，必须结合 NPE/TGE/TSR/crossover。A1 aggregate action mean 是同一 success-value 尺度的消融参照，完整报告其 PIG。

两个系统使用同一 exact records。Practical 方法只获得已存在的 state/action/outcome/native utility 和 rho，不接收 family/gamma/true propensity。JitRL 单步 reward/final_score 是 binary outcome；MemRL 使用已有 last_reward，按固定 +1/−1反馈编码还原 binary outcome，q_value 原样留作 provenance，不把跨尺度 Q 直接当成功率。两系统得到相同的 (id,state,action,outcome)，并不要求 native score 数值相等。这是已标注离散元数据的 synthetic adapter，不声称从自由文本自动发现 state/action。

## 固定公式和候选

- M1：sum_x rho(x) × cell outcome mean；目标质量非零的 cell 若空则显式 positivity failure。
- M2：mu_hat=(Nxa+1)/(Nx+2)，w=1/max(mu_hat,.05)，按 action self-normalized weighted outcome。严格按给定全局公式实现，rho 不参与加权；不为改善 C 事后改造它。
- M3：ORACLE / NOT CANDIDATE METHOD。target-aware classical SNIPS：w=rho(x)/(P_logged(x)×mu(a|x))，P_logged(x)=.5。均匀 target 时退化为普通逆真实 propensity；从不参与候选选择。
- M4：sum_x rho(x)×(success+.5)/(N+1)，固定 Jeffreys prior；不调 prior。
- A1：只做 aggregate action outcome mean，去掉 state conditioning，忽略 rho。

Practical 主结果每 bank/target/method 是一次确定性 utility，无伪造 stochastic dataset replicates。M0 的20顺序只衡量原生 order robustness，系统输出不作为独立 dataset 样本；其余方法没有 order-based显著性检验。

## Secondary selection

M1/M4 wrapper 接口 fit、estimate_action_utility、select。k=20；先按 rho largest-remainder 分 state quota，各 state/action 至少2 slots。剩余 slots 按 exp(corrected action utility / 1) largest-remainder 分给 A/B，余数相等按字母顺序。每个 cell 从现有 candidates 的 insertion order 取前若干；不按成功过滤、不创建重复项。不足则报 support failure。用20固定顺序 seeds，报告 quota/min support 和 composition 稳定性；selected composition 不进入 primary Gates，小 k 舍入可能保留相同 composition 而 utility 已有真实差异。

## 指标和固定 Gates

PIG、NPE、TGE、CorrectionRate 均按用户公式计算，内部 Fraction；false reversal 使用严格非零相反符号，不引入事后容差。TSR 只在 estimated gap>0 时输出，否则 NA。Family B 任一 P/Q 的 B>A 单独记 TRUE_EFFECT_REVERSAL。Family C T0/T1 对同一 bank 仅改变 rho。报告 deterministic differences，不作“显著性”宣称。

候选的判定必须同时在两个 adapter 上成立。G1 为全局至少两个 practical methods 达阈值；最终候选自身也须通过。G1–G9 逐候选记录，禁止不同方法各过一个 Gate 拼出最终方法。

| Gate | 冻结规则 |
|---|---|
| G0 | native null/.95 复现旧 selected IDs，20 seeds reversal≥.80 且 median RCD≥.30，两个系统均通过；否则停止 |
| G1 | .95/null 的 CorrectionRate≥.80 且 P/Q 各 NPE≤.03，至少两个 practical 通过 |
| G2 | 一个同一 practical 在 .70/.85/.95 全部 CorrectionRate≥.60，P/Q 各 NPE≤.03，避免反向大偏差 |
| G3 | 同一 practical 在 B 的 P/Q×.70/.85/.95 全部 A>B，median TSR∈[.70,1.30] |
| G4 | 最终方法 B 的每个上述条件 TSR≥.50，NA 或更低皆失败，排除平凡等化 |
| G5 | C 的所有 P/Q×.70/.85/.95：T0=A 且 T1=B |
| G6 | 实际 API/字段测试，无真实 propensity/gamma 输入或读取；M3 单独 oracle API，不入候选 |
| G7 | D .95 utility 有限且在[0,1]：Null NPE≤.03，B A>B 且 TGE≤.03，C T0/T1 正确且 T NPE≤.03；.99同样记录但不影响 GO |
| G8 | 两系统所有 bank 的 normalized observed inputs 完全相同；源码未改 |
| G9 | 固定 count arithmetic，无训练、新 LLM、reward model 或存真实 propensity |

只有至少一个 practical 自身 G1–G9 全通过且全局 G0/G1 成立才 GO。若部分 null correction、signal retention 或 crossover 有支持但不满足全部，则 WEAK；三者皆无支持则 NO_GO。G0 failure 直接 NO_GO/STOP。

方法选择固定字典序：先全部 G1–G8（且 G9），再 A/B/C非BAL的全部target median PIG，B非BAL median TGE，C通过数，D .99最大 TGE，最后复杂度 M1<M4<M2。M3永不候选。不依据单一最好场景，不调参数/样本/公式。

## 理论、范围与停止

本轮的已观测 state 必须足以消除 confounding，且每个目标 cell 有正 support；不是一般文本 memory 的自动因果识别。Exact outcomes 排除了 sampling noise，也意味着本轮不能证明稀疏 support 下的 sampling robustness。M1 的统计核心就是 direct standardization/g-computation 形式，不声明 novelty。即使 GO，也只支持此数学/接口可行性；完成报告和指定 commit/push 后停止，不自动查新论文、命名、设计更复杂方法或运行下一阶段。
