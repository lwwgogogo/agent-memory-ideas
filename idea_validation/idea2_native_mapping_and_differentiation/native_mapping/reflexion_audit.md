# Reflexion 原生审计
固定提交 218cf0ef1df84b05ce379dd4a8e47f17766733a0。[源码](https://github.com/noahshinn/reflexion/tree/218cf0ef1df84b05ce379dd4a8e47f17766733a0)。ALFWorld 完整 trial log 范围 **MAP-L0**。

alfworld_runs/alfworld_trial.py:alfworld_run:46–72 用初始 observation、base prompt 和最后三个 reflection 创建 EnvironmentHistory，记录生成 action、env.step 返回观察及终止。返回成功采用 done 分支；虽然读取 info.won，不应把 done 代理直接宣传为真实成功的因果真值。
run_trial:83–142 以 env 配置遍历任务，保存完整 history 与 STATUS。:112–120 已成功任务会跳过，不能把重复 SUCCESS 日志当新经验。env_history.py:__str__:29–41 输出 _cur_query 加完整 actions/observations；_get_base_query:43–52 把实际使用 memory 也写进 _cur_query。
generate_reflections.py:29–45 只给未跳过的失败轨迹追加反思。main.py:85–114 每轮运行后更新 memory 并保存 env_results_trial_i.json；这是更新后的快照，下一轮使用；当轮使用内容应以 trial log 为准，不能错位 join。

最小字段 state/action/outcome=NATIVE；era_id=DERIVABLE。推导依据是同一 env、固定 model/base prompt 条件下 trial log 中实际使用的 last-three reflection 发生变化，以及对应更新事件。不是 trial_id 本身等于 era。相同实际 memory 的 trial 不应自动生成不同 regime；不同任务初始状态不能冒充策略更换。完整日志可比较机制输入，不需要 oracle policy label 或新日志字段。
这只能识别候选行为机制边界，不能证明分布真的不同。权重固定而反思更新可以改变 μ(a|x,M)；如果 use_memory=False 或内容始终不变，只有单 regime，不能认证跨策略支持。

动作 STRUCTURED，描述符 FEATURE_DISTRIBUTION；需要相同/可比较状态的有效样本，原生少量 trial 通常不足以稳定估计行为分布。最佳 hook：alfworld_run 创建 EnvironmentHistory 前决定哪些 reflection 可作指令；history log 是证据来源，不把日志读写本身说成 certification gate。
MAP-L0 仅说明字段与机制边界已有可观测落脚点，不说明 prototype 已实现或性能已证实。任务级 outcome 不能无条件归因到每步动作；动态成功语义、descriptor 覆盖、gate 效果标 DYNAMIC_VALIDATION_BLOCKED。
