# ExpeL 原生审计
固定提交 e41ec9a24823e7b560c561ab191441b56d9bcefc。[源码](https://github.com/LeapLabTHU/ExpeL/tree/e41ec9a24823e7b560c561ab191441b56d9bcefc)。判 **MAP-L1**，范围为已保留完整训练轨迹的 trajectory-level 经验，不泛化为逐步因果奖励。

memory/episode.py:Trajectory:4–28 保存 task、raw trajectory、reflection 副本，并拆分观察/action/thought/step。agent/expel.py:next_task:83–120 用 log_history 构造 Trajectory，按 is_success 分入 task-keyed 成功/失败字典。因此 context、trajectory action、终局 outcome 可从原生对象得到；每步动作继承终局成功不是合法的逐步因果标签。
utils.py:save_trajectories_log:197–218 保存 txt/pkl/true.txt。内存对象与可选磁盘保存需区分；本判定限启用原生保存的运行。agent/expel.py:create_rules:287–402 批量比较成功失败轨迹，更新 rule_items_with_count；:353–361 可选 saving_dict 保存 agent 状态、critique index/fold/log。计数是 rule support，不是行为策略数。

insert_before_task_prompt:404–412 在 eval 插入 rules；动态 fewshot 选择 :498–653 基于 task/step/action/thought/reflection 文档，改变实际输入。因此行为机制可能随 rules/reflection/bank 更新，但同一固定库里的 query-specific retrieval 只是 μ 对状态的条件依赖，不自动增加 era。
没有已验证全路径 executed rules/bank revision。最小 quartet 为 state/action/outcome=NATIVE，era=MISSING；未来只记录实际启用的 revision/update marker，可判 REQUIRES_INSTRUMENTATION。不能把 insight extraction 中间候选规则当已执行策略。模型配置也需纳入标记的含义，而不是用 trial/fold 编号代替。

最自然 reuse hook 是插入 rules 及 fewshots 之前；rule importance count 更新是 formation/consolidation 点。gate 需要未来实现，MAP-L1 只评价现有数据与轻量标记是否足够，不声称已有 certification。动作对象 TRAJECTORY_LEVEL，描述符 FEATURE_DISTRIBUTION：只能在可比较任务/状态支持上解释，不实现 embedding。
动态日志完整性、任务成功判定语义、descriptor 样本覆盖与所有注入入口的 gate 均 DYNAMIC_VALIDATION_BLOCKED。本轮没有修改规则、阈值或 upstream。
