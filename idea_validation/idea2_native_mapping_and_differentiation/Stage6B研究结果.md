# Idea 2 Stage-6B 研究结果
审计日期2026-10-06。结论：**NATIVE_MAPPING_GO / DIFFERENTIATION_BORDERLINE / STAGE6B_NARROW**。真实系统有观测落点；现有证据不足以把当前对象宣称为不可替代的方法创新。

## 原生系统
| 系统 | 级别 | 关键依据与缺口 |
|---|---|---|
| JitRL | MAP-L1 | 逐步state/action/反馈已有；实际memory/prompt机制revision需轻量记录 |
| MemRL | MAP-L3 | TRAJECTORY模式正常路径可用，但fallback执行动作与assistant文本可能不一致，超出只补marker |
| ExpeL | MAP-L1 | 完整保存轨迹和成功失败分组可用；缺实际启用规则/库revision |
| Reflexion | MAP-L0 | 同env固定配置的完整trial日志记录实际使用reflection；变化可推导机制边界 |
| ReasoningBank | MAP-L3 | query/think不足以验证细粒度state；外部obs artifact与memory revision关联未核验 |

JitRL+Reflexion已满足预注册。ExpeL是附加支持，MemRL不用于勉强过关。所有级别都是静态可映射结论，原生源码证据逐条见native_mapping目录。

μ(a|x,M)与base LLM weights不同：memory/Q/反思更新可能改变行为，frozen权重不意味着单一行为机制。固定库根据不同x检索不同memory本身也不意味着新era。没有把episode/task/time当policy label；没有用true propensity或oracle gamma。outcome是系统可见反馈，不自动是无偏因果价值。已知era也不证明多样性，复杂动作仅做结构化/轨迹级映射。

## 最终对照
| 问题 | 已有工作 | 我们 | 是否独立 |
|---|---|---|---|
| policy-conditioned experience | JitRL、MemRL、ExpeL、RoboHarness | 将其作为证据前提 | 否，C1不能独立主张 |
| exposure correction | g-computation、multi-logger OPE、Causal Memory Policy | M1仍为经典baseline | 否 |
| state-aware retrieval | SAMem、JitRL及多种task检索 | 需要状态可比性 | 否 |
| cross-policy diversity | 多logger overlap、ICP环境异质性、RoboHarness异构库；MRI独立误差信号 | 将有效行为差异用于支持profile | 特定对象有剩余差异，独立性未证明 |
| contradiction detection | ExpeL、Belief Memory、ICP、BASM | 跨behavior-era冲突阻止promotion | 证据分层特定性尚有差异，原则不新 |
| transfer eligibility | COUNTERMEM条件过滤、BASM边界、MemLineage授权 | 基于跨policy观察支持授予复用资格 | 广义已覆盖；狭义化约风险未排除 |
| memory lifecycle | 更新/删除/信任等级/验证准入已有 | DESCRIPTIVE/PROVISIONAL/PRESCRIPTIVE | 命名不是独立贡献 |
| native runtime mapping | 原生日志与更新机制 | 五套固定提交静态审计 | 工程可行性证据，不是方法novelty |

一手文献与方法定位见literature/paper_matrix.csv（16+8篇）、nearest_neighbors.md和mother_field_matrix.md。最危险五篇是JitRL v4、RoboHarness、COUNTERMEM、MemLineage、Causal Memory Policy；其它HIGH条目同样保留。

## 不可替代性逐项审计
| 比较对象 | 对方解决什么 | 当前对象与重合 | 差异及是否足够 |
|---|---|---|---|
| M1 | 给定状态分布标准化utility | 当前还决定memory可否跨policy指导行为 | 相同M1可给不同status，但只排除点估计规则；不足以排除证据感知门控 |
| IPS/OPE | 由logging data估target policy value，可用已知或估计propensity | 都关心生成来源/支持 | 不同输出对象是value与许可；许可可能基于OPE不确定性，尚不能称不可替代 |
| state-aware retrieval | 匹配当前状态检索相关经验 | 都需condition on state | 匹配不直接检测跨来源稳定性；差异成立，但本身不是完整方法新颖性证明 |
| COUNTERMEM | 验证反事实修复并按条件选择/跳过 | 都分开证据、utility和允许使用 | 多era观察证据不同于局部反事实；可能仅替换验证器，未排除 |
| ICP/IRM | 由多环境不变性识别/学习泛化规则 | 都按来源比较稳定性 | memory生命周期是对象差别；“ICP加memory gate”化约未排除 |
| domain generalization | 从训练域学习新域泛化并严格选模 | era可视为环境，未来policy可视为目标 | memory闭环不是充分区别；Performative Prediction已有反馈对象 |
| simple majority vote | 聚合多个来源方向 | 都可能利用跨来源一致 | 多数忽略相关性/覆盖，但加权证据或相关性校正也可能实现同规则；只击败朴素投票不足 |
| metadata/provenance | 保存来源、签名、版本；MemLineage进一步授权 | profile含来源并改变使用权限 | 本项目试图赋予behavior支持以统计迁移含义；日志或不同status本身已不是新对象 |
| confidence calibration | 调整预测可信度；更强方法利用支持/不确定性决策 | lifecycle可被编码为分数阈值 | 与仅utility校准有差异；与证据感知风险决策不等价尚未证明 |

## claim和kill
C1有DIRECT覆盖；C2/C3有强PARTIAL母领域重叠；C4/C5有条件的部分重叠；C6广义已有DIRECT；C7/C8具体组合未发现DIRECT，但metadata和status名称不可充当novelty。逐篇C1–C8在claim_collision_matrix.csv。
未找到同问题+同关键假设+同解决对象+同核心组合claim的一篇论文，所以不满足NO_GO的kill条件。U1（漂移/不变性化约）、U2（existing gate替换证据）、U3（confidence/支持决策化约）尚未解决，所以也不满足GO。详见novelty_summary红色UNRESOLVED COLLISION标记。

跨policy观察一致不等于任意未来策略下因果充分；state遗漏、任务/评估器漂移与同源偏差都能混淆稳定性。证据只能支持已观察范围，不赋予无限运输保证。本轮没有改历史Stage6A阈值来救这些缺口。

## 验证与停止
九个历史目录的文件/链接SHA逐项复核；预注册SHA不变；所有CSV必需列、论文重复、来源、枚举和verdict边界由小脚本测试。实际结果在results/final_verification.json。
需要动态rollout/API才能确认的日志覆盖、真实行为差异、原生gate效果一律DYNAMIC_VALIDATION_BLOCKED；不是伪造provider通过。没有LLM推理、benchmark、训练、算法、wrapper或lineage实现。
按冻结第28节组合规则，GO+BORDERLINE=NARROW。只缺方法差异化关：必须排除上述不可替代性风险；本轮不自动解决为新方法，也不进入Stage7。
