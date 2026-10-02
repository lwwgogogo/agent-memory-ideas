# Phase A 评估协议

所有预测是 assimilation 后的 filtering estimate，仅使用截至当前的观测。truth 只供环境与指标，普通 baseline 接口没有 truth、实际 Q/R、change/noise 标签。所有方法以 p=0.5 开始，p>=0.5 时预测 1。

1. Accuracy：burn-in 后逐步二元正确率。Brier：同期 `(p-x)^2` 均值。
2. False Update Rate：分母是 burn-in 后真实状态未变、当前观测错误、前一步预测正确的步数；分子为这些步中当前预测变错的次数。无分母时为 missing，不是 0。
3. Noise Overreaction：状态未变但观测被翻转的步骤上 `abs(p_t-p_(t-1))` 的均值。这是 belief 扰动幅度，不是因果干预效应。
4. Adaptation Delay Capped：对 burn-in 后每个真实切换，记录首次预测新状态的延迟，立即正确为 0。若下一切换或序列结束前仍未命中新状态，以该段长度封顶，并计入 censoring。并报 adaptation_censored_rate。它是首次命中，不代表连续稳定恢复；短 regime 中可被封顶压低，跨 Q 比较须谨慎。
5. Stale Reuse Proxy：对 burn-in 后发生切换的各段，预测仍为上一段状态的步数 / 这些段总步数。二元任务中等于这些段的 tracking error，不是真实 retrieval 的旧 memory 检索率，不构成独立的机制证据。

summary 中率和延迟是“有定义的 seed 指标的均值”，不是事件池化加权均值；per_seed.csv 保留事件分子/分母。缺少 change/noise 的轨迹不能提供对应指标证据。

Q/R 在每条轨迹内恒定；不包含 noise burst、非平稳 Q/R、动作反馈或语言歧义。结果不能证明在线区分两类冲突已解决。后续可增加分段 regime、temporary corruption，以及相同冲突不同原因的干预对照。
