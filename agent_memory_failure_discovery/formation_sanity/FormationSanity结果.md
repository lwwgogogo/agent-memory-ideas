# FormationSanity结果

本轮只测试 formation，不测试 downstream answer；原 96-case experiment 未重跑。

## 结果矩阵

| Condition | Writer | Input | infer | Created | No memory | Error |
|---|---|---|---:|---:|---:|---:|
| A_current_qwen | qwen2.5:14b | raw string | True | 0/12 | 11/12 | 1/12 |
| B_official_qwen | qwen2.5:14b | official | True | 0/12 | 11/12 | 1/12 |
| C_raw_storage | qwen2.5:14b | official | False | 12/12 | 0/12 | 0/12 |
| D_official_qwq | qwq:32b | official | True | 0/12 | 12/12 | 0/12 |

## Decision

- C infer=False = 12/12：storage/Qdrant/user_id/get_all 路径通过。
- A current qwen：0/12 created，11 NO_MEMORY，1 ERROR。
- B official qwen：0/12 created，11 NO_MEMORY，1 ERROR。
- D official qwq：0/12 created，12 NO_MEMORY。
- A 与 B 同样失败：没有证据支持 raw-string 与 official message protocol 的差异是主要原因。
- qwen 与 qwq 都无法让简单 positive controls 形成 memory：当前结果不是单纯 qwen writer confound。
- 当前最保守 verdict：`MEM0_LOCAL_INFERENCE_COMPATIBILITY_OR_PROMPT_FAILURE`。
- `FORMATION_SELECTIVITY_SIGNAL`：当前不成立。

## P04 特殊错误

qwen A/B 的 P04 报告了 `AttributeError: str has no attribute get`。Mem0 2.2.1 additive path 在 extraction 后按 memory item dict 调用 `m.get("text")`，但该次 writer 返回了字符串元素。

## Raw extraction capture

首次 matrix wrapper 绑定了旧的 `generate` 名称，而 2.2.1 实际调用的是 `generate_response`；因此没有保存完整 raw response。源码调用链和 P04 traceback 已保存，未修改 site-packages。

## 下一步

不要重跑原 96，也不要进入 candidate。唯一值得做的是在新的独立诊断中正确包裹 `mem.llm.generate_response`，保存 qwen/qwq 的原始 JSON，并确认是 `memory=[]`、`memory=[string]` 还是 `memory=[{"text":...}]`。
