# 系统机制审计

审计静态证据以官方仓库固定 commit 为准。关键词扫描结果是候选，不直接作为机制结论。Memento 无可确认官方代码，仅纳入论文级审计。动态数据只执行 JitRL 与 MemRL 的原生 ranking/value-selection 组件；没有运行完整 agent、embedding candidate generation 或外部 LLM benchmark。

| System | Official Repo | Commit | Audit Level | Self-generated Experience | Observed Reward Utility | Stores State | Stores Propensity | Exposure Correction | Counterfactual Handling | Feedback Loop | PSI | RCD | PIUR | Balanced Reduction | Classification |
|---|---|---|---:|---|---|---|---|---|---|---|---:|---:|---:|---:|---|
| jitrl | yes | 143d22185d | L2 | SELF_GENERATED | yes | True | False | none | NONE | yes | 1.247 | 0.600 | 1 | 0.978 | C |
| memrl | yes | c1b322ca43 | L2 | SELF_GENERATED | yes | True | False | none | NONE | yes | 0.249 | 0.600 | 1 | 0.978 | C |
| expel | yes | e41ec9a248 | L1 | SELF_GENERATED | partial | True | False | none | HEURISTIC | yes | — | — | — | — | C |
| reflexion | yes | 218cf0ef1d | L1 | SELF_GENERATED | partial | True | False | none | NONE | yes | — | — | — | — | C |
| reasoningbank | yes | ed80611788 | L1 | SELF_GENERATED | partial | True | False | none | HEURISTIC | yes | — | — | — | — | C |
| memento | no (paper-only) | — | L0 | SELF_GENERATED | yes | None | False | none disclosed | NONE disclosed | yes | — | — | — | — | C |

各系统 Q1–Q8 的证据路径、函数及结论见 `results/system_audits/*.json`。Structural blind spot 只用于有代码可审的五个仓库计数；5/5 符合定义，不把 paper-only Memento 混入该分母。
