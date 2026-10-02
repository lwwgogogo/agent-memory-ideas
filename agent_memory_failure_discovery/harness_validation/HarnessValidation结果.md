# Harness Validation 结果

## 结论摘要

- 实验完整性：`PASS`，96/96，C1–C8 各 12。
- Unit tests：13/13 通过。
- O1 Raw History：96/96（100%），通过 capability gate。
- O0 Full Pipeline：24/96（25.0%）。
- O2 True Retrieval Oracle：24/96（25.0%）。
- O3a Gold Atomic Facts：96/96（100%）。
- O3b Gold Structured Memory：84/96（87.5%）。
- Mem0 persistence：P1 NO_FORMATION = 96/96。
- Formation coverage：NO = 96/96；但该 coverage 依赖 case annotation，需结合 Mem0 extraction 内部响应进一步解释。

## Failure localization

96 个 case 中：

- 24 个 O0 correct；
- 72 个 O0 wrong + O1 correct；
- 0 个 O0 wrong + O1 wrong；
- 72 个 O1 correct 且 information=NO；
- 0 个 information=YES 且 O2 rescue；
- 0 个 O2 retrieval rescue；
- 72 个 O2 wrong + O3a correct；
- 0 个 O3a wrong + O3b correct；
- 12 个 O3b wrong。

因此，当前结果主要支持：

```text
Raw history 可解
但当前 Mem0 没有形成可见 memory
```

不支持：

```text
真实 Retrieval failure
C3/C7 representation failure
```

因为所有 case 的 final Mem0 memory 都为空，O2 没有可供 oracle 选择的实际 item。

## Persistence

96/96 case 的每一轮 `add_return.results` 都为空，每一轮 `get_all` 都为空，最终 memory 也为空。因此全部归为：

```text
P1 NO_FORMATION
```

没有观察到 P2、P3、P4 或 P5。

## Per-family signature

- C1：formation dominated；O1 全部正确，Mem0 未形成 memory。
- C2：formation dominated；O3b 仍有失败，但没有实际 Mem0 memory，不能解释为 representation。
- C3：O0 全部正确；没有形成有效 memory attribution signal。
- C4：formation dominated；sequential write 没有形成可见 memory，不能据此判断 update failure。
- C5：O0 全部正确；没有形成有效 memory attribution signal。
- C6：formation dominated；没有 True Retrieval rescue。
- C7：formation dominated；没有证据支持 conditional representation failure。
- C8：formation dominated；当前 trace 没有足够 memory evolution 证据支持 stale/correction failure。

## C3/C7 结构假设

本轮不保留 C3/C7 的结构性 failure 结论。O3a 已经 96/96 正确，且所有 case 的 Mem0 memory 都为空，因此不存在“信息已存在但必须通过显式 role/time/scope structure 才能解决”的干净证据。

## C1/C4/C5/C6 Retrieval 假设

本轮不保留旧的 retrieval-rescue 结论。True O2 没有任何实际 item 可选，O2=O0=24/96，无法证明 normal search 相比 oracle retrieval 造成了 failure。

## C8

C8 的 sequential trace 已保存，但所有 turn 的 memory state 都为空。因此当前不能区分：correction 未写入、旧 memory 未删除、冲突共存或 reasoner 不会处理 correction。F6 暂不计数。

## Harness verdict

形式完整性、canonical grader、O2 item ID integrity、sequential trace schema 和 unit tests 均通过。但由于 96/96 都是 P1，且 required memory annotation 偏强、trace 未保存 extraction 内部响应，本轮对 formation 阶段仍存在 measurement ambiguity。

最终判定：

```text
HARNESS_PARTIAL
```

不是 `HARNESS_INVALID`：没有发现 case 串线、O2 使用不存在 item、trace 序列化丢失或 grader 系统性误判。

## Candidate Gate

正式 Candidate = 0。

虽然 formation-like pattern 在 8 个 family 都重复出现，但当前还不能排除 extraction JSON 解析、writer prompt/模型输出格式或 vector insertion 链路问题；因此不进入 Formal Expansion，不做 literature audit，不启动第二 Memory system。

## 唯一下一步

在新的独立阶段中，只做一次最小化的 Mem0 writer observability validation：保存 extraction LLM 原始响应、解析后的 `extracted_memories`、embedding/insert 返回和 history/database 状态；确认 P1 的确是“writer 没有形成 memory”，再决定是否扩大 formation candidate。
