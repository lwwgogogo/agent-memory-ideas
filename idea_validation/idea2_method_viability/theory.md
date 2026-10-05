# 数学对象与识别边界

历史记录服从 P_mu(X,A,Y)=P(X)mu(A|X)P(Y|X,A)。对任意 action，历史 aggregate E_mu[Y|A=a] 使用 P_mu(X|A=a) 混合 state；即使各 state 内 action 效果相等，该混合也能造成 action 差异。Native top-score pool 同样继承这种 exposure composition。

目标对象是 U(a|rho)=sum_x rho(x)E[Y|X=x,A=a]。若要解释成干预结果，还需 consistency、已观测 state 的 conditional exchangeability、positivity 与稳定 outcome mechanism。本轮 synthetic worlds 按构造满足这些条件，真实文本 memory 不自动满足。

M1 是 direct standardization/g-computation 的直接形式：cell exposure 影响样本均值精度，但不替代目标 rho 的权重。Exact counts 下它能精确恢复 target utility，包括真实 global gap 与 query crossover。它不通过强制 A=B 消除偏差。这个统计核心不构成新颖性声明；若作为后续候选，仍须单独做 novelty/method differentiation。

M2 的经验 propensity 加平滑再 clip，通常只能近似恢复 logged state marginal。它按本轮给定公式没有 target rho 因子，所以不保证应对 query shift。clip 在弱 support 时会防止大权重，却可能保留显著 exposure bias。M3 使用真实 propensity 与 rho/P(X) 做 oracle target SNIPS，仅作 classical baseline，不得候选。

M4 的 Jeffreys shrinkage 有有限支持时的保守含义，但 cell 数量不同时 shrinkage 偏差不同，因此它一般不严格 policy-invariant。Exact-data 实验不能证明其方差优势；需如实保留微小 false reversal 和 .99 support limitation。

M0 返回 selection 而非 action success probability。把 native f_A/f_B 的中位数作为 U0 是明确标注的 selection-support proxy。与它的相对 CorrectionRate 只作描述性参照，实际估计目标由 absolute NPE、TGE、TSR、crossover 和 A1 same-scale ablation共同验证。不可把 native selection composition 当错误因果价值。

Adapters 读取 synthetic native objects 中已存 state/action/outcome；MemRL 的 last_reward 是实际原生 update 写入的 +1/−1 observed feedback，映射成 binary outcome，未读取 gamma 或真实 propensity。自然语言 state 离散化、长期 Q 与 outcome 的差异、完整 semantic retrieval 及有限样本 uncertainty 均不在本轮证据内。
