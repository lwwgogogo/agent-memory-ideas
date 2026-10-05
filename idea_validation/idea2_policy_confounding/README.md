# Idea 2：Policy-Confounded Experience 最小验证

状态：ACTIVE。只检验 Successful Experience ≠ Causal Evidence；不查文献、不用 Mem0、不设计方法，不换模型找正结果。

## 环境与固定执行

只允许 Python 3.10 的 agentmem_lab。使用：

```bash
cd /home/liaoweiwen/projects/agent-memory-ideas/idea_validation/idea2_policy_confounding
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python generate_cases.py
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python simulate.py
# 只有 PHASE_A_GO 后：
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python run_llm_test.py
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python evaluate.py
```

数学脚本执行 pytest，输出 results/math_gate.json；任何测试失败则 IDEA2_MATH_NO_GO，禁止 LLM。

## 行为协议（首次调用前固定）

20 个基础场景：五类中性虚构系统 × 四档 γ=0.50/0.70/0.85/0.95，每档五个。各场景结构同构，仅系统编号和不透明状态标签不同。两动作的真实干预成功率均为 0.55。未来任务状态各占 50%，提示明确预测不论状态固定执行动作的成功率，不询问历史条件成功率。

每个历史数据集有 2000 次执行、每状态 1000 次；用期望频率的精确整数计数，不引入抽样噪声。C1 保留四个状态×动作计数；C2 改为各状态各动作 500 次，整体数据量不变；C3 展示 C1 同一计数的分层百分比；C4 只做确定性聚合，丢弃状态，不是让 LLM 自行总结。C0 无历史记录。

五条件：NoMemory / ConfoundedMemory / BalancedMemory / StratifiedOracle / AggregateSummary。条件名称与 γ 不展示给模型，不展示真实成功率或“因果效果相同”。

每场景交叉两个动作标签映射和两个顺序种子 17、43，共 4 个视图；总调用固定 20×5×4=400，不扩大基础场景。交换时将历史策略偏好的规范 A 显示为 B，分析再按映射还原；因此不能把字面 A 偏好误记成策略偏差。报告未还原的 NoMemory 字母偏好，避免平均抵消掩盖问题。顺序只改变列举排列。

模型固定 qwq:32b，Ollama /api/chat，严格 JSON Schema；温度 0、模型 seed=20261004、上下文 4096、最大输出 768，任务顺序 seed=20261005。不重启服务、不下载模型、不选择性重试失败响应。原始响应与完整提示逐次存储，resume 仅跳过已完成键并校验配置与源码摘要。

## 解析与统计

完整 JSON 校验：字段、概率范围、有限数值、重复键；非法输出 UNRESOLVED，不做 substring grading。choice 允许 A/B/TIE，不因平局或选择与概率不一致丢弃合法概率，只另记一致性诊断。confidence 不是成功概率，不进入 MIAB。

MIAB 是还原后的 p_success_A−p_success_B。先按场景×条件平均 4 个视图，主分析仅使用五条件均完整的场景；报告失败分布，缺失不填零。基础样本最多 20，不把 400 调用当独立样本。均值、中位数、样本标准差与 10000 次场景 bootstrap 区间，种子 20261004；配对差使用同一场景。按 γ 的区间每档最多 5 个场景；趋势先算每个 family 的四点回归斜率，再对五个 family 自助重采样。区间是模板表面变化的描述，不能声称现实任务总体显著性，也没有多重比较校正。

## 预先固定的判定细则

先要求至少 16 个完整场景，且每档不少于 4 个；不足时不得宣称 GO，报告证据不足。核心额外偏差稳定定义为 Confounded−NoMemory 配对区间下界>0，且 Confounded 均值区间下界>0，并在两种标签映射及两种顺序的分层均值中方向都为正。

- G1：满足上述稳定偏差。
- G2：四档 Confounded 均值总体递增，相邻允许最多 0.02 数值波动；完整 family 的回归斜率 bootstrap 下界>0，且 γ=.95 比 .50 高。
- G3：Confounded−Balanced 区间下界>0，Balanced 场景平均绝对 MIAB≤0.05。
- G4：Confounded−Stratified 区间下界>0，Stratified 场景平均绝对 MIAB≤0.05。
- G5：NoMemory 原始未还原字母概率差的平均绝对值≤0.05，且核心额外偏差稳定。
- G6：至少三个 family 的 Confounded 平均 MIAB>0.03，且两种 correction 都为正。

全部通过才 IDEA2_GO；存在稳定额外偏差但其他条件失败为 IDEA2_WEAK；没有稳定额外偏差为 IDEA2_NO_GO。不修改门槛、不调整提示救结果。C4 的放大效应只作为次要比较，不作为替代 G1 的证据。

## 限制

五个 family 是表面语境复制，机制共享，不能算五类因果结构。C3 的表格组织和直接提供百分比同时变化，因此 correction 不能唯一归因于来源感知；C4 信息不足，不同于可识别的 C1。仅两个顺序不能穷尽位置效应；单模型单机制不支持通用结论。达到最终 verdict 后仅完成报告与 Git，停止，不进入 Idea 3。
