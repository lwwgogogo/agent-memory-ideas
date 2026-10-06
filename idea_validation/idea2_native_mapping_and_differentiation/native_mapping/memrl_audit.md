# MemRL 原生审计
固定提交 c1b322ca43de36ddf64c6712f89d0095bfc35ce0。[官方源码](https://github.com/MemTensor/MemRL/tree/c1b322ca43de36ddf64c6712f89d0095bfc35ce0)。范围 ALFWorld。最终 **MAP-L3**：为遵守预注册，不将正常路径可映射冒充完整原生数据流可映射。

## schema 与实际写入分开
memrl/service/procedural_memory.py:MempMetadata:27–72 声明 task_description、trajectory/script、source_episode_id、success_rate、retrieval_count、version 和时间字段；声明 optional 字段不证明 runner 填写了它。
memrl/run/alfworld_rl_runner.py:892–923 收集 task_description、完整 messages trajectory、success、retrieved_queries/retrieved_mems、steps、gamefile。:1054–1093 将轨迹和 success 交给 add_memories，并记录 success/q_value/q_visits/q_updated_at/last_used_at/reward_ma。
memrl/service/memory_service.py:add_memories:1508–1609 传递相关 memory IDs 和 metadata；:2028–2102 保存 dict_memory/query_embeddings/mem_cache/q_cache。runner:1114–1123 的 section snapshot 比 minibatch Q 更新粗。
memrl/service/builders.py:TrajectoryBuilder:77–102 原样返回 trajectory；updater.py:VanillaUpdater.prepare_update_op:272–290 将 memory_body 放 metadata.full_content，metadata 合并在 :46–68。这条原生模式可保留观测和 assistant 输出；其他摘要模式不能反推丢失细节。本轮没有变更配置选择有利模式或调用构建器。

## 动作对齐是实质缺口
memrl/agent/memp_agent.py:act:232–276 在 history 写观察与 assistant 文本，再解析 action。runner:854–875 对异常/缺失动作可执行 look 或 inventory，:877 才 env.step。持久 assistant 文本未必就是执行动作。
因此普通成功解析路径的 action 可 DERIVABLE，但所有 fallback 路径不是；仅加 policy_version 不能补齐 executed-action 对齐。若以 trajectory 为动作，也仍需区分提议轨迹和实际执行轨迹，不能绕过缺口。state 为可见 observation，success 是环境 reward>0 的观测，Q 是记忆使用价值而不是环境动作的真实因果值。
候选 quartet：state=NATIVE（TRAJECTORY 模式）；action=DERIVABLE（仅正常解析，整体 MISSING 部分行）；outcome=NATIVE；era=MISSING。这超出 MAP-L1 仅补 marker 的允许范围，所以不计入 GO 分母。若未来另行限定且验证完整正常路径，可能达到局部 MAP-L1；本轮没有据此升级。

## era、检索、闭环与 hook
memrl/service/value_driven.py:90–151 按相似度/Q/epsilon 选 memory IDs；此处 actions 是 memory IDs，不是环境 action。QValueUpdater:181–219 更新 Q、访问数、reward/time，覆盖最新值而非完整历史。
MemRL frozen LLM 不等于 frozen μ：检索值、库和内容更新均影响未来动作。schema.version 不是已验证 behavior era。未来仅 era 部分可用更新 counter 标记，但整个 quartet 还有上述动作缺口。故 era_status=REQUIRES_INSTRUMENTATION 与 mapping=MAP-L3 并不冲突。
自然 hook 是 value selector 取条目之后、memp_agent._construct_messages:164–214 注入之前；输入现场可见，完整历史未持久。Q update 可作为证据收集点，不能把每次 Q 变化自动解释为显著行为多样性。
动作 STRUCTURED；描述符 FEATURE_DISTRIBUTION 仅对已对齐样本有可行性。retrieval IDs 在 runner/related_memory_ids 部分保留；完整检索排名及库快照没有证明。

## 验证边界
静态确认调用链；未导入或调用 Mem0、provider、LLM、benchmark。实际配置、异常覆盖、快照恢复及 selector gate 的效果均 DYNAMIC_VALIDATION_BLOCKED。缺口不是用 oracle 可修补的理由，也不是本轮实现日志的新授权。
