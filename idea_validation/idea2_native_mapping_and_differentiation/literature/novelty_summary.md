# 方法差异化结论
截至 2026-10-06，审计16篇agent/experience memory工作和8篇母领域论文。**DIFFERENTIATION_BORDERLINE**。未找到单篇实质覆盖“behavior-policy来源+有效多样性+跨来源稳定性/冲突+未来复用资格+memory生命周期”的完整组合；这不构成绝对首次，也不证明当前对象不可化约。

C1 已有直接覆盖。C2/C3 的一般原理有强母领域和独立证据近邻。C4/C5 在所读agent方法中主要是局部覆盖；跨policy观察一致不自动保证未来policy有效。C6 的广义utility/使用资格分离已有直接覆盖；狭义“基于跨behavior-era证据授予transfer权限”仍有差异。C7 目前剩余的是profile中证据的含义与作用，不是字段名称；C8 三档命名不是独立创新。

## 最危险的五篇
### 1. JitRL v4
[方法与Appendix C](https://arxiv.org/html/2601.18510v4) 已显式区分经验生成策略与当前策略，限制局部策略漂移以解释回报估计。没有跨多样性支持的memory资格生命周期。审稿质疑：本项目是否只是把估计偏差/漂移条件写成标签？当前回答只能指出“单条/组memory未来使用权限”不同于当前Q一致估计；尚未证明这个权限对象超出已有漂移不确定性判据。**🔴 UNRESOLVED COLLISION U1**。

### 2. RoboHarness
[§3–4](https://arxiv.org/html/2607.18060) 已有异构policy来源分库、跨库检索及handoff状态约束。没有按跨regime经验稳定性晋升一般处方记忆。审稿质疑：Policy Support Profile 是否仅仅是policy bank metadata加兼容检查？当前差异是证据多样性/一致性决定未来复用权限，而非执行器切换；这一差异的必要性仍未证实。纳入 **U2**。

### 3. COUNTERMEM
[§3](https://arxiv.org/html/2609.31874v1) 已把验证修复证据、使用条件、源任务信息、复用utility与选择/跳过分开。没有用多个behavior-era的观察支持认证。审稿质疑：是否只是用跨policy证据替换它的验证器？现有回答明确证据来源不同，但不足以证明是独立方法对象而非验证器替换。**🔴 UNRESOLVED COLLISION U2**。

### 4. MemLineage
[§3](https://arxiv.org/html/2605.14421v1) 已让来源/信任改变行动授权：内容能被回忆不表示它能授权敏感参数。它不是基于行为策略的效应稳定性。审稿质疑：同内容/预测但不同来源产生不同permission并不新。对此必须承认；只有来源的统计可迁移含义可能剩余，三档status与provenance本身不可再作为贡献。纳入 **U2**。

### 5. Causal Memory Policy
[§2–3](https://arxiv.org/html/2610.02070v1) 已区分检索干预下可识别的当次utility和保留/忘却决策，并处理支持不足。不是跨behavior-policy diversity的资格证书。审稿质疑：profile是否只是为操作决策增加 uncertainty/support？当前不能仅用ECHO/DIVERSE同M1 gap反驳；必须区分“只看点估计”与“能看证据结构的决策”。**🔴 UNRESOLVED COLLISION U3**。

## 其他不可忽略的威胁
BASM 已有适用边界和runtime使用拦截；Memory Reward Inflation 已指出独立错误信号不能由更多同源judge替代，且全局校准不解决条目级偏差；Belief Memory 已有冲突降权与版本保留。ICP/IRM、multi-logger OPE、SPIBB 又分别覆盖跨环境稳定性、来源支持和保守权限。详见 paper_matrix 与 mother_field_matrix。没有因它们不使用相同术语而降低风险。

## 三档status是否独立于置信度
M1 ECHO gap=.40 与DIVERSE gap=.40、status不同，只排除“status完全由M1点估计决定”；不排除基于来源相关性、覆盖、不确定性或风险的标量决策。任意有限status都能编码为分数，故“能否写成阈值”不是有意义的区分。
有意义但尚未过关的问题是：在相同可用证据下，现有evidence-aware gate/uncertainty decision是否已经实现同一种使用约束。我们没有证明不可替代性，也没有本轮设计新算法来补洞。因此不给 DIFFERENTIATION_GO。

## 不作自动kill的理由
逐claim DIRECT表示该子命题及相应对象已有直接重叠，不等于同一论文覆盖全部组合。上述U1–U3是尚未排除的实质化约风险，不是已证明四要素相同的DIRECT COLLISION。按冻结kill规则，当前没有足以给NO_GO的单篇完整覆盖证据；也不能用这一“未找到”反向给GO。
