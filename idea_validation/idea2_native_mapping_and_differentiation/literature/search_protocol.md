# 检索协议与实际记录
审计日期2026-10-06（Asia/Shanghai；本轮起始UTC 2026-10-05）。开始前已冻结preregistration；后续只补来源，不改GO/kill边界。

优先arXiv、会议proceedings、ACL Anthology、作者/官方仓库。搜索引擎与二手目录仅用于定位标识，关键判断回到方法正文。纳入与经验来源、跨环境稳定性或复用权限存在实质关系且方法可读的论文；正式16篇agent、8篇母领域。不是全库系统综述或绝对首次证明。

下列为实际搜索query记录；OR合并查询用于召回，命中后按标题核验。另直接打开已知论文一手URL、按正文引用追踪BASM/RoboHarness，并核验作者/版本/venue。所有最终来源和已读章节逐行保存在paper_matrix，不将全文下载缓存提交。

## 簇 B

- `"COUNTERMEM" memory`
- `"Memory Contagion" agents`
- `"Memory Reward Inflation"`
- `"Experience-Following" agents memory`

## 簇 B

- `"SAMem" "state" memory agent`
- `"AMemGym"`
- `"MemLineage"`
- `"Belief Memory" agents self reinforcement`

## 簇 A/B

- `"Causal Memory Policy" agent`
- `"memory" "retrieval intervention" propensity agent`
- `"policy-conditioned experience memory" OR "behavior-policy-conditioned memory"`
- `"cross-policy memory" OR "multi-policy experience memory"`

## 簇 A

- `"memory transferability" agent OR "memory certification" agent`
- `"memory epistemic status" OR "prescriptive memory" agent`
- `"experience memory reliability" OR "memory promotion lifecycle"`
- `"memory trust" agent OR "experience reuse across policies"`

## 簇 A/B/C

- `"retrieved experience" "policy bias"`
- `"self-improving agent" "experience bias"`
- `"Memory Reward Inflation" site:arxiv.org`
- `"Invariant causal prediction" "multiple logging policies"`

## 簇 C

- `Causal inference using invariant prediction Peters Buhlmann Meinshausen 2016`
- `Invariant Risk Minimization Arjovsky 2019`
- `Optimal Off-Policy Evaluation from Multiple Logging Policies Kallus Saito Uehara`
- `Transportability causal effects Pearl Bareinboim 2014`

## 簇 C

- `In Search of Lost Domain Generalization Gulrajani Lopez Paz 2021`
- `Safe Policy Improvement with Baseline Bootstrapping Laroche 2019`
- `Robust Control Markov Decision Processes uncertain transition matrices Nilim El Ghaoui 2005`
- `Performative Prediction Perdomo Zrnic Mendler Duenner Hardt 2020`

## 簇 C

- `adaptive control persistent excitation system identification Willems Rapisarda Markovsky De Moor 2005 note persistency excitation`
- `evidence independence belief revision Alchourron Gardenfors Makinson partial meet contraction 1985`
- `meta-analysis heterogeneity Higgins Thompson Deeks Altman Measuring inconsistency 2003`

## 簇 B/followup

- `"Memory Reward Inflation" paper arxiv`
- `"When Not to Imitate" "Boundary-Aware"`
- `"memory" "policy diversity" "certification" agent`
- `"memory" "cross-policy" transfer eligibility`

## 来源边界
全部用户指定疑似agent近邻均找到公开一手全文，包括最初检索未命中的Memory Reward Inflation。未再将其标NOT VERIFIED。其HTML显示的dateline与arXiv标识月份不一致，记录该异常；不依据该日期做优先权判断。
JitRL审计论文是v4（2026-09-27），代码仍是用户冻结commit；论文和源码版本不能混为一体。ExpeL/ReasoningBank venue分别由arXiv接受说明核验为AAAI2024/ICLR2026；其它未核验会议录的2026新工作标preprint，不编造接受状态。
母领域另三项正文无法充分读取，列于mother_field_matrix的未计数部分。缺检索命中、PDF读取失败都不是不存在的证据。网页方法阅读由工具直接完成，研究缓存只用于辅助定位；没有调用新的LLM/provider/benchmark。

## 判读规则
C1–C8矩阵为人工逐篇审计，不由关键词脚本决定。DIRECT只针对单一子claim的相应含义；整组kill还需同问题、关键假设、对象、机制/claim的组合覆盖。C6广义已直接覆盖，而狭义cross-behavior-era eligibility尚未直接覆盖。PARTIAL不是隐含的完整等价证明。
无完整组合被核验为DIRECT，仍保留U1–U3不可替代性风险，给BORDERLINE。可以确认当前公开证据中的差异，不能声称绝对首次。
