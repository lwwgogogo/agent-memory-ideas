# 原生映射总结
审计五个固定 historical commit；**NATIVE_MAPPING_GO**。这是静态字段落点结论，不是部署/效果结论。

| 系统 | 级别 | 状态/动作/结果 | era | 最自然使用入口 |
|---|---|---|---|---|
| JitRL | MAP-L1 | 原生逐步文本、命令、反馈；奖励有加工 | 缺完整 revision，仅需未来 marker | update_scores 聚合前，并覆盖 guiding prompt |
| MemRL | MAP-L3 | trajectory 模式保留观察；异常动作与文本对齐不全；success/Q 原生 | marker 可补，但不能同时修复动作缺口 | selector 到消息注入之间 |
| ExpeL | MAP-L1 | 完整 trajectory+成功失败分组，终局 outcome | 需实际启用规则/库 revision | rules 与 fewshots 注入前 |
| Reflexion | MAP-L0 | trial log 含实际使用反思、action/obs、STATUS | 同 env 完整日志中的实际反思更新可推导 | EnvironmentHistory 构造前 |
| ReasoningBank | MAP-L3 | action/status 有，细粒度 state 与执行快照链未确认 | marker 本身不够 | select_memory 到 system prompt 注入前 |

JitRL + Reflexion 已满足至少两个 L0/L1 且包含 JitRL/MemRL 之一。即使不计条件较强的 ExpeL，门槛仍成立；不依赖 MemRL 局部正常路径升级。没有系统被评为 MAP-L2；这不表示行为发现问题已解决，只是已观察到的瓶颈不应以一个未实现 detector 遮蔽。

天然 state：JitRL 的文本、Reflexion 的 observation、ExpeL 轨迹；MemRL 取决于 TRAJECTORY 保存；ReasoningBank 的 query/think 仅部分。action：前三者已有执行轨迹；MemRL fallback 对齐缺口；ReasoningBank action_list 有。outcome：各系统均有环境/终局/评估器反馈或 utility，但反馈、真实成功与因果价值不能混为一谈。没有已核验完整通用 explicit behavior-policy version；Reflexion 的实际反思日志可在明确范围内推导机制变化。

base LLM weights 与 μ(a|x,M) 不同。memory/rule/Q 的持久更新可改变条件行为机制；状态不同而检索结果不同，本身不是全局 regime 改变；一轮一个 episode 也不是一轮一个独立策略。新 marker 必须关联实际生效更新，不是重命名时间戳。版本数量不证明行为多样性，behavior descriptor 的可比性、覆盖与精度本轮均未验证。

对复杂 action 仅给 STRUCTURED 或 TRAJECTORY_LEVEL 的 feature-distribution 可行性，不套二元 A/B，不实现 embedding/变点检测。候选不读取 true propensity、oracle gamma 或人工真值 policy label。JitRL 的折扣 gamma 另有原生语义。

所有 potential gate 是代码落点，不是已有 certification。接入 gate 必然是以后获准的新工作；本轮不修改 decision logic。需 provider/rollout 才能确定的有效多样性、执行覆盖、outcome 语义及干预收益记录为 DYNAMIC_VALIDATION_BLOCKED。
