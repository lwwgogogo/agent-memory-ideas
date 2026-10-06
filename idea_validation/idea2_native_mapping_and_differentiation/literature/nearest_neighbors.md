# 近邻逐篇审计

日期2026-10-06。下列均阅读矩阵所列方法正文，不是摘要筛选。NO/NONE仅指所读版本未发现相应机制，不证明全部未来版本没有。完整作者与venue见paper_matrix。

## A01 Just-In-Time Reinforcement Learning: Continual Learning in LLM Agents Without Gradient Updates
[一手来源](https://arxiv.org/html/2601.18510v4)；arXiv preprint；阅读 §4; Appendix C（完整假设及误差分解）。

问题/对象：检索经验实现无梯度策略改进；state-action-return episode。已覆盖：旧策略产生的回报与当前策略Q有漂移误差；C1已覆盖。与候选对象差异：假设slow policy drift来保证估计，不按多样性/矛盾给记忆迁移资格。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A02 MemRL: Self-Evolving Agents via Runtime Reinforcement Learning on Episodic Memory
[一手来源](https://arxiv.org/html/2601.03192v2)；arXiv preprint；阅读 §3–4；§4.4。

问题/对象：记忆检索utility学习；intent-experience-utility。已覆盖：显式memory-conditioned policy；utility由闭环反馈更新。与候选对象差异：Q与相关性排序不等于按行为来源授予transfer资格。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A03 ExpeL: LLM Agents Are Experiential Learners
[一手来源](https://arxiv.org/html/2308.10144)；AAAI 2024；arXiv 2023/v3 2024；阅读 §4.1–4.4；abs确认venue。

问题/对象：经验抽取和跨任务复用；trajectory/rule。已覆盖：明确off-policy experience，成功失败对比与rule投票管理。与候选对象差异：rule票数不是独立行为支持；无跨era资格证书。风险：MEDIUM。未把名称相似或不同当作kill或保留依据。

## A04 Reflexion: Language Agents with Verbal Reinforcement Learning
[一手来源](https://arxiv.org/html/2303.11366)；NeurIPS 2023；阅读 §3；算法与memory机制。

问题/对象：用语言反馈改进行为；reflection buffer。已覆盖：反思参与actor policy；失败反馈改变后续行为。与候选对象差异：少量反思窗口，不评估跨策略多样性与资格。风险：MEDIUM。未把名称相似或不同当作kill或保留依据。

## A05 ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory
[一手来源](https://arxiv.org/html/2509.25140)；ICLR 2026；arXiv 2025/v2 2026；阅读 §3.1–3.3；MaTTS。

问题/对象：从成功失败提炼可泛化策略；title-description-content memory。已覆盖：MaTTS多轨迹对比一致模式；memory影响policy。与候选对象差异：rollout多样不等于behavior-policy多样；无来源条件认证。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A06 COUNTERMEM: World-Model Verified Counter-Factual Memory for Language Agents
[一手来源](https://arxiv.org/html/2609.31874v1)；arXiv preprint；阅读 §3.1–3.4。

问题/对象：验证替代动作形成可复用修复经验；q,a-,a+,e,c,u。已覆盖：源任务修复证据、复用utility、适用条件与选择/跳过分开。与候选对象差异：局部反事实验证与条件匹配，不是多behavior-era观察支持认证。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A07 Memory Contagion: Cross-Temporal Propagation of Evaluator Bias via Agent Memory
[一手来源](https://arxiv.org/html/2606.23195)；arXiv preprint；阅读 §3；§4.1。

问题/对象：评估器偏差经记忆跨时间传播；state/action/reward/next-state及摘要。已覆盖：区分内容与检索通道，偏差可进入后续行为。与候选对象差异：研究偏差传播不提出cross-policy promotion；效果有模型/偏差种类边界。风险：MEDIUM。未把名称相似或不同当作kill或保留依据。

## A08 How Memory Management Impacts LLM Agents: An Empirical Study of Experience-Following Behavior
[一手来源](https://aclanthology.org/2026.acl-long.27.pdf)；ACL 2026；arXiv 2505.16067；阅读 §3.3–3.4；§4开头；Appendix A相关段落。

问题/对象：经验跟随及错误传播；experience input/output pair。已覆盖：选择添加/删除和历史utility改变复用。与候选对象差异：无policy-era支持分层；真值替换只是诊断。风险：MEDIUM。未把名称相似或不同当作kill或保留依据。

## A09 SAMem: State-Aware Memory as a Fine-Grained Memory for LLM Agents in Decision-Making
[一手来源](https://aclanthology.org/2026.findings-acl.722.pdf)；Findings of ACL 2026；阅读 §3.1–3.2。

问题/对象：细粒度状态关联经验复用；state-thought-action-reward。已覆盖：state/thought聚类和Q/遗忘改善检索。与候选对象差异：state-aware不提供跨行为来源稳定性证书。风险：MEDIUM。未把名称相似或不同当作kill或保留依据。

## A10 AMemGym: Interactive Memory Benchmarking for Assistants in Long-Horizon Conversations
[一手来源](https://arxiv.org/html/2603.01966)；arXiv preprint；阅读 §3.1–3.3相关环境和生成定义。

问题/对象：交互记忆评估的on-policy问题；assistant conversational memory。已覆盖：assistant生成后续数据，静态记忆评测不同于交互闭环。与候选对象差异：benchmark对象；没有memory transfer certification。风险：MEDIUM。未把名称相似或不同当作kill或保留依据。

## A11 MemLineage: Lineage-Guided Enforcement for LLM Agent Memory
[一手来源](https://arxiv.org/html/2605.14421v1)；arXiv preprint；阅读 §3.1–3.7。

问题/对象：阻止不可信来源经记忆授权敏感动作；签名memory entry和parent graph。已覆盖：内容可保留供回忆，却不能授权；来源改变使用权限。与候选对象差异：来源安全/taint不是behavior-era效应稳定性；泛化版C6/C8已不新。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A12 Belief Memory: Agent Memory Under Partial Observability
[一手来源](https://arxiv.org/html/2605.05583v1)；arXiv preprint；阅读 §3.1–3.3；Appendix A.1/A.2。

问题/对象：部分可观察条件下防止过早点估计自我强化；attribute candidates及证据概率。已覆盖：维护替代解释；noisy-OR合并；冲突降权并保留版本。与候选对象差异：候选概率不是policy来源独立性；无跨era多样性profile。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A13 Causal Memory Policy: Making Memory Utility Identifiable by Intervening on Retrieval
[一手来源](https://arxiv.org/html/2610.02070v1)；arXiv preprint；阅读 §2；§3.1–3.4；相关实施限制。

问题/对象：检索干预使记忆utility可识别；retrieval arm / stored memory。已覆盖：已识别当次utility与未来保留/忘却决策分开；欠支持时abstain。与候选对象差异：随机检索positivity和SNIPS/SE，不是跨behavior-era资格；限制不能抹去重叠。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A14 Memory Reward Inflation in Self-Improving LLM Agents
[一手来源](https://arxiv.org/html/2608.00017)；arXiv preprint；HTML dateline与ID月份不一致；阅读 §3.1–3.3；§5；§6.3及相关正文。

问题/对象：自评分膨胀经复用闭环放大；query/action/utility episode。已覆盖：独立误差信号比judge数量关键；全局校准不能选择性纠错。与候选对象差异：EIA校正错误utility，不以policy-diversity决定观察经验迁移资格。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A15 When Not to Imitate: Boundary-Aware Skill Memory for Reliable Tool-Use LLM Agents
[一手来源](https://arxiv.org/html/2608.22339)；arXiv preprint；阅读 §4.1–4.2。

问题/对象：防止对成功skill的越界模仿；procedure/applicability/risk/avoidance/recovery。已覆盖：适用范围和runtime gate阻止危险复用。与候选对象差异：边界来自成功失败抽取和校验，不是跨behavior-era经验稳定性。风险：HIGH。未把名称相似或不同当作kill或保留依据。

## A16 RoboHarness: Memory-Driven Orchestration of Heterogeneous Robot Policies for Long-Horizon Planning
[一手来源](https://arxiv.org/html/2607.18060)；arXiv preprint；阅读 §3；§4.1–4.2。

问题/对象：异构机器人policy编排与handoff；policy-specific episodic banks/anchors。已覆盖：按VLA/RL/TAMP策略分库并做跨库检索和状态兼容。与候选对象差异：MemoryBridge解决handoff邻域/进度，不认证经验对未来policy普遍处方资格。风险：HIGH。未把名称相似或不同当作kill或保留依据。
