# 母领域映射与不可替代性边界
正式纳入8篇；标题、作者、URL、正文阅读范围见 paper_matrix 的 M01–M08。以下是审计判断，不是本轮提出的方法。

| 母领域 | 可迁移数学对象 | 对当前对象的威胁 | memory额外结构及不足 |
|---|---|---|---|
| [ICP](https://arxiv.org/pdf/1501.01332) | 环境索引、条件机制不变性、可接受集合 | C3–C5不是新的数学原则 | 条目形成/复用/晋升不同于预测变量集合；尚未证明不是ICP后接门控 |
| [IRM](https://arxiv.org/pdf/1907.02893) | 表征下各环境共享最优classifier | 跨policy稳定目标可能是改名 | 不应误写为简单embedding分布匹配；memory许可对象差异需实证必要性 |
| [Transportability](https://papers.nips.cc/paper_files/paper/2014/file/29d8ab58bcd65e45a831feeaed051d23-Paper.pdf) | selection diagram、机制变化与源/目标信息 | “看多个来源即可迁移”太弱 | 日志四元组不提供完整图、无隐藏混杂或未来机制假设，不能宣称运输保证 |
| [DomainBed](https://arxiv.org/pdf/2007.01434) | 多域风险、held-out域、模型选择协议 | policy era 可退化成domain标签 | memory影响后续数据是附加闭环，但闭环自身已有母领域 |
| [Multi-logger OPE](https://proceedings.mlr.press/v139/kallus21a/kallus21a.pdf) | 分层logger样本、union overlap、高效估计 | policy来源/覆盖不同于版本数早已有之 | OPE估target value；本对象是memory许可；不能谎称OPE必须oracle propensity，论文含未知logger估计 |
| [SPIBB](https://proceedings.mlr.press/v97/laroche19a/laroche19a.pdf) | 低支持集合、baseline保守约束 | 同Q但不同support导致不同权限已有先例 | memory lifecycle未覆盖，但“同估计不同status”不够新 |
| [Robust MDP](https://people.eecs.berkeley.edu/~elghaoui/Pubs/RobMDP_OR2005.pdf) | 不确定转移集合、最坏情况Bellman | 点估计和安全决策分离早已标准化 | 现有profile是否仅刻画一个不确定集合仍未排除 |
| [Performative Prediction](https://proceedings.mlr.press/v119/perdomo20a/perdomo20a.pdf) | 部署参数诱导D(theta)、稳定点/最优点区别 | 数据会随行为变化不是memory独有 | memory写回、检索选择和条目许可是具体对象；不自动产生新数学 |

## 静态多环境之外究竟增加什么
memory参与动作生成，动作决定未来轨迹，新轨迹又影响memory内容/检索值/使用许可；证据单位可在抽取、合并、检索中变化。它要求追踪“当前条目接受了哪些来源的支持”，不是固定数据集上只训练一次预测器。但MemRL、JitRL、Performative Prediction已分别覆盖大量闭环结构。闭环是背景，不是充分novelty。

同一task分布、可观测状态和稳定评估器是比较跨era证据的重要前提。观察到的冲突也可能来自任务难度、未观测状态、评价器变化或表示损失；一致也可能是共同偏差。跨policy一致性最多是给定支持范围内的证据，不是任意未来策略的因果充分性。

## 已检索但未正式计数
persistent excitation/system identification：Willems等《A note on persistency of excitation》(2005)，[作者库](https://eprints.soton.ac.uk/262195/)定位，PDF工具读取失败，未作方法级判定。
belief revision：Alchourrón/Gärdenfors/Makinson (1985) AGM论文，Cambridge官方页面定位到摘要，未纳入正式全文审计。
meta-analysis heterogeneity：Higgins等《Measuring inconsistency in meta-analyses》(2003)，DOI 10.1136/bmj.327.7414.557，BMJ/PMC正文访问失败，未对其具体方法作新颖性判定。
这三项属于检索覆盖，不充当已读母领域篇数，也不把未读部分当作不存在；相关化约风险保留。
