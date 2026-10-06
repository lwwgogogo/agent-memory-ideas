# JitRL 原生审计
固定提交：143d22185d95fbf633a0befe6861d5e8b732543b。范围 Jericho。源码根为历史 third_party/jitrl；所有行号针对该提交。[官方源码](https://github.com/liushiliushi/JitRL/tree/143d22185d95fbf633a0befe6861d5e8b732543b)。结论 **MAP-L1**，仅需未来运行的行为机制更新标记；不声称现有日志能完整追溯 era。

## 原生对象与实际写入
Jericho/src/cross_episode_memory.py:18–38 初始化 episodes.jsonl、episode_abstract.jsonl、prompt_history.jsonl 和向量缓存。add_episode:557–638 从 game_history 取状态、命令、分数、reward；:613–623 写逐步 state/action/reward/score/delta_score/llm_step_score/llm_reasoning；:629–636 同时保存 episode 和向量索引。_store_step_in_vector_db:238–284 保存 episode_number、step_data、终局反馈、上下文和 future_rewards。
原生 gamma 是回报折扣，不是实验 oracle gamma/propensity。LLM 评估分非零时可替代环境 reward 用于索引回报；失败最后一步 reward 在 :626–627 被改为 -10。因此可观测 outcome 是系统实际反馈，不能称为未经处理的真实因果奖励。环境 score/delta_score 与评估器输出应区分。

jitrl_agent.py:821–843 记录实际动作、状态并在收到环境反馈后更新最后一步。state 是可见文本，不保证充分调整所有混杂；action 是游戏命令，不能直接二元化。

## era 与闭环
jitrl_agent.py:24–38 路径含模型名；这不是 immutable checkpoint。:80–90 start_episode 保存 guiding prompt；:92–135 end_episode 写经验并可能更新 prompt。cross_episode_memory.py:749–767 的推荐记录含 previous/recommended prompt；:791–828 保存 current_guiding_prompt，可能重写记录。
episode counter 在 add_episode 才递增，start_episode 使用旧计数。简单按同名 episode_number join 会有边界偏移风险。timestamp 是 base_dir basename（:591–597），不是可信每步时钟。仅有推荐 prompt 不等于已执行行为策略快照；memory bank、Q 聚合与探索配置也影响 μ(a|x,M)。
当前没有完整 executed-policy revision。未来在实际 memory/prompt/config 更新边界记录一个机制 revision 并关联已有步/episode，只是非 oracle marker，判 REQUIRES_INSTRUMENTATION，不能判 DERIVABLE。这一 MAP-L1 是前瞻静态可行性，不能补造历史 era。

## 描述符与 hook
已有 state/action 支持在可比状态下统计命令或命令特征分布；映射为 STRUCTURED / FEATURE_DISTRIBUTION。需要覆盖和重复状态，不能把文本相似直接当相同状态，未估计 μ。
jitrl_agent.py:update_scores:233–262 将检索回报聚合到 action score；这里是最自然的 prescriptive gate 位置，必须在聚合之前。get_prompts:424–450 还有指导文本路径，不能只拦一个文本入口就声称完整阻断。
cross_episode_memory.py:335、681 的 retrieval 返回值可现场观察，但不是完整持久检索审计史。update_history 只有部分 prompt/episode 记录。
最小字段：state/action/outcome=NATIVE；era_id=MISSING（未来 REQUIRES_INSTRUMENTATION）。没有使用真实 propensity 或真值 policy label。

## 范围限制
固定权重仍可因 memory 更新改变行为分布；反过来同一固定库因不同状态检索不同条目不自动构成新全局 era。可分段不等于分段间行为多样。动态覆盖、有效 descriptor、多步 outcome 归因以及完整 gate 均 DYNAMIC_VALIDATION_BLOCKED；本轮没有运行 provider、修改 agent 或实现 wrapper。
