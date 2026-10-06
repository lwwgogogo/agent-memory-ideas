# ReasoningBank 原生审计
固定提交 ed80611788292ea739f1effd31f16c53823b8a0d。[源码](https://github.com/google-research/reasoning-bank/tree/ed80611788292ea739f1effd31f16c53823b8a0d)。范围 WebArena 本仓库已核验数据；下文未写 WebArena/ 的源码路径均相对该子目录。**MAP-L3**。

induce_memory.py:extract_think_and_action:47–68 从 step_*.pkl.gz 取 agent_info.think/action，未将原始 observation 拷入 memory。get_info:96–134 读任务 intent/template、动作/思考序列与 status，支持 GT/cum_reward 或 autoeval；候选只能用正常可获得反馈，不调用 GT 分支作 oracle。:176–186 的 memory JSONL 有 task_id/query/think_list/action_list/status/memory_items/template_id。
因此 action 与观察到的 evaluator outcome 存在；query 和 think 是部分 context，不能证明足够 state-conditioned adjustment。legacy agent.py:get_action:103–137 有 obs_history 和 MainPrompt 的 live observation，但本轮未验证外部 BrowserGym 持久 schema 能完整恢复 observation—action—memory revision 关联。

pipeline_memory.py:47–86 依次运行 agent/eval/induce。run.py:157–193 从 memory_path 的 txt stem 找 jsonl，检索后写回 txt；故不是 txt/jsonl 文件名不匹配的 bug。txt 可被后续检索覆盖，不是完整检索决策审计史。memory_management.py:select_memory:138–196 维护 query embedding/cache，并非持久所有实际采用 memory 的日志。
model/temperature 配置在 run.py:208–225；配置名称不是稳定 checkpoint/version。库更新可能改变 μ，固定库针对不同 query 的检索不自动构成新 era。era 部分未来可加 update counter，但仍缺已核验细粒度 state/执行 memory 关联，所以总体不能 MAP-L1。

quartet：state=MISSING（细粒度；query-only context=NATIVE 不足以替代）；action/outcome=NATIVE；era=MISSING。action STRUCTURED，descriptor NOT_CLEAR。最自然 hook 是 run.py 选择 memory 后到 legacy agent 注入 system prompt 前；需要证据历史而不只是当前 memory 文本。
本轮不凭外部依赖可能保存字段就判 DERIVABLE。BrowserGym artifact 对齐、真实运行入口全覆盖和成功判定均 DYNAMIC_VALIDATION_BLOCKED。没有运行或修补该系统。
