# JitRL Jericho retrieval path

固定代码：`idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl` @ `143d22185d95fbf633a0befe6861d5e8b732543b`。只读。Stage-8C verdict `REAL_JITRL_FAILURE_NO_GO` 未改。

## 1. Memory Write Path

`JitRLAgent.end_episode` 在 `enable_cross_mem` 时调用 `CrossEpisodeMemory.add_episode`（`Jericho/src/jitrl_agent.py`）。

`add_episode`（`Jericho/src/cross_episode_memory.py`）写入 `episodes.jsonl`。step 字段为 `step_num, state, action, step_summary, reward, score, delta_score, llm_step_score, llm_reasoning`。

这一步只证明 memory object 被创建并序列化。它不证明向量已插入。

## 2. Representation / Embedding

`_encode_trajectory_context` 调用 `generate_trajectory_context_for_vector`（`Jericho/src/utils.py`）。传入 `info` 时只拼接 `info['look']` 与当前 state，不调用 LLM。未传入 `info` 时才调用 `find_detailed_environment_info`。

向量由 `get_embedding_with_retries`（`Jericho/src/openai_helpers.py`）生成。backend 是 OpenAI Embeddings API，默认模型 `text-embedding-ada-002`，维度 `vector_dim=1536`。函数读取 `OPENAI_API_KEY2`；缺失时直接返回 `None`，不访问 Ollama。

`encoder_available` 在 `_init_vector_database` 中被写死为 `True`，不代表 embedding 调用成功。

## 3. Index

索引类型是两个 `faiss.IndexFlatIP`：`history_index`、`state_index`。初始化在 `CrossEpisodeMemory._init_vector_database`。`faiss` 导入失败时两个 index 都设为 `None`，并打印 vector database disabled。

插入点是 `_store_step_in_vector_db` 的 `history_index.add` / `state_index.add`。index 为 `None` 时该函数在 `.add` 之前返回。

Jericho 这条路径没有 numpy index、没有远程 index、也没有非向量检索 fallback。`retrieve_similar` 忽略 `use_vector`，始终调用 `retrieve_similar_with_vector`。

## 4. Query

`JitRLAgent.generate_action` 调用 `update_scores`，再调用 `retrieve_similar`。Stage-8C 参数是 `k=retrieval_top_k=10`，`r=retrieval_threshold=0.95`。

query 文本进入 `_encode_trajectory_context`。history 向量来自 `current_summary`，state 向量来自 `step {n}: State: {current_env_info}`。

## 5. Search

`retrieve_similar_with_vector` 在 search 之前按这个顺序返回空列表：

1. `history_index is None` 或 `state_index is None`：`"Dual vector database not available"`
2. `ntotal == 0`：`"Dual vector database is empty"`
3. query 向量为 `None`：`"Failed to encode query trajectory"`

通过这三道 guard 后才调用 `history_index.search` 和 `state_index.search`。

## 6. Post-filter

search 之后还有原生过滤，本轮没有执行到：

- recall 后再算 Jaccard：`similarity = 0.3 * sim1 + 0.7 * sim2`
- `dynamic_threshold` 从 `r` 线性降到 `r-0.1`（step 0 时等于 `r`）
- `similarity < dynamic_threshold` 的候选被丢弃
- 返回的是过滤后的 `filtered_trajectories`，低于阈值的候选不返回

Jericho 路径没有 URL matching。

## 7. Stage-8C Zero Point

Stage-8C 只读记录：20 次 attempt，`history_index_available=false`，`returned_count=0`。

本轮离线 probe 复现了同一 guard。`faiss` 在 import 时失败，`_init_vector_database` 把两个 index 设为 `None`。随后 `retrieve_similar_with_vector` 在 search 之前返回 `[]`。

query embedding 也失败：`OPENAI_API_KEY2` 未设置，`get_embedding_with_retries` 返回 `None`。该失败的 return guard 位于 index guard 之后，所以这次实际命中的返回点是 index 不可用，不是 threshold。

## 8. Unit Probe

未调用 LLM。`evaluate_step_scores_with_llm` 仅在 probe 进程内替换为常数 0，避免 `add_episode` 发请求；threshold、top-k、Jaccard、JitRL 源码都未改。

- memory created: YES
- memory persisted: YES（`episodes.jsonl`）
- embedding generated: NO（直接调用与 query 路径均为 `None`）
- index insertion called: NO（未出现 `Stored step`，无 `.index` 文件）
- index insertion success: NO
- index size: 未初始化（`history_ntotal = null`）
- exact query search: NOT EXECUTED
- raw candidates: NOT REACHED
- post-filter: NOT REACHED
- final returned: 0
- self-retrieval: FAIL
- near-identical: NOT_RUN

## 9. Verdict

`RETRIEVAL_INFRA_BLOCKED`

Jericho / library 的原生 retrieval 依赖 `faiss.IndexFlatIP` 与 OpenAI embedding。当前 `jitrl_runtime` 两者都不可用，search 没有执行。这不是原生 threshold 把候选滤成 0。

因此 Stage-8C 没有测到一次有效的 memory retrieval。`REAL_JITRL_FAILURE_NO_GO` 保留。本轮不安装依赖，不改检索，不重跑 Stage-8C。
