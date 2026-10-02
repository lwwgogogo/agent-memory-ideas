# Mem0源码行为审计

审计对象：当前项目 venv 内 `mem0ai==2.2.1` 的 `mem0/memory/main.py`，只读检查，未修改 site-packages。

## 源码事实

- `Memory.add()` 位于 `mem0/memory/main.py` 约 760 行；同步 add 在约 942 行执行 extraction LLM 调用，使用 `ADDITIVE_EXTRACTION_PROMPT` 和 `generate_additive_extraction_prompt()`。
- extraction 响应为空、解析失败或得到空 memory 列表时，约 988 行进入空结果分支；源码注释表明 message/history 可以被保存，但不会形成 vector memory item，因此可能返回 `results: []`。
- 非空 extracted memories 在约 993 行 embedding，随后与已有 memories 比较；约 1017 行开始处理 ADD/UPDATE/DELETE 事件。
- ADD/UPDATE/DELETE 事件写入 vector store，并在约 1096 行写入 history/database；history/database 与 vector memory 是两套相关但不等价的状态。
- `get_all()` 位于约 1269 行，使用 filters 访问 memory store；本轮使用 `filters={"user_id": uid}`。
- `search()` 位于约 1393 行；2.2.1 拒绝顶层 `user_id`，要求将 user filter 放入 `filters`，然后执行相似度查询和过滤。
- 源码同时存在同步和异步 add/search/get_all；本轮使用同步 API。

## ADD/UPDATE/DELETE/NONE

- ADD/UPDATE/DELETE 是 memory operation events，不等价于 LLM 提取事实的数量。
- additive extraction 先产生候选 memory，再与已有 memory 比较，决定新增、更新或删除。
- “NONE”没有作为本轮 trace event 出现；空 `results` 主要对应 extraction 为空、解析失败或没有可插入 records。
- sequential add 时已有 memory 会参与后续 update 判断。

## 可能造成写入后不可见的配置或状态

- extraction 为空或 extraction JSON 解析失败；
- vector store insert 没成功形成 records；
- get_all/search 的 filter 位置或 user_id 错误；
- Qdrant path/collection 与读取实例不一致；
- history/database 有记录但 vector store 没有对应 item；
- entity/filter 逻辑过滤掉 search 结果。

## 推测（不是源码事实）

- 当前大量 trace 的 `add_return.results=[]` 且每轮 get_all 为空，优先怀疑 extraction 为空或解析失败；但 trace 未保存内部 extraction response，无法进一步区分。
- 目前没有“add 非空、随后 get_all 为空”的样本证据支持 persistence/read bug。
- spaCy/fastembed warning 可能影响 entity/BM25 辅助路径，但不足以单独解释 add 为空。
