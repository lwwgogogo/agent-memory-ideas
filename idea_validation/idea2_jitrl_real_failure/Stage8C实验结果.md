# Idea 2 Stage-8C 实验结果

## 1. 研究问题

检验真实 JitRL + LLM trajectory 中，历史正向 memory 在后续匹配决策点被检索并使用后，是否产生负向即时 reward 差异：`Delta_current = Outcome_with_memory - Outcome_without_this_memory < 0`。

## 2. Runtime

Conda `jitrl_runtime`，Python 3.10.21，spaCy 3.8.16，en_core_web_sm 3.8.0；JitRL commit `143d22185d95fbf633a0befe6861d5e8b732543b`，第三方目录未修改。

## 3. Task / Model

Jericho `library`，ROM `Jericho/jericho-games/library.z5`；模型 `qwen2.5:14b`，通过 Ollama OpenAI-compatible endpoint `http://localhost:11434/v1` 推理；temperature 0，seed 20261008。

## 4. Preregistration

预注册和所有正式调用的根目录 Python 脚本在 formal 前做 SHA-256 lock。正式预算固定为 20 episodes、每 episode 1 step、最多 160 次推理、最多 20 个 paired events、每个 candidate 最多 3 个 repeats。30/30 项预正式测试通过。首次 pytest 命令因未设置 `PYTHONPATH=.` 而在 collection 阶段退出，0 项测试执行；formal 未开始，锁定文件未变化。保留原日志后，同一锁定测试集通过。

## 5. Real Memory Lifecycle

正式运行完成 20/20 episodes，JitRL 原生 `add_episode` 成功写入 20 个 episode 和 20 个 step memory。每个后续决策都调用原生 `retrieve_similar`，共 20 次 attempt。冻结环境缺少 `faiss`，而 Jericho 实现只执行 dual-vector retrieval 且无非向量 fallback；`history_index` 与 `state_index` 均不可用，20 次 attempt 全部返回空列表。

## 6. Retrieval Statistics

TotalRetrievalEvents=0，PositiveHistoricalMemoriesRetrieved=0。检索 attempt rate 为 20/20，但 returned retrieval event rate 为 0/20。没有 memory 可被标记为 `RETRIEVED_AND_USED` 或 `RETRIEVED_BUT_NO_BEHAVIOR_EFFECT`。

## 7. Paired Intervention

WITH_MEMORY / WITHOUT_THIS_MEMORY 只能针对真实返回的目标 memory。由于返回项为 0，无法只屏蔽一个目标 memory，也无法建立有效 state-matched pair。PairedEvents=0；没有用不同 episode 代替 counterfactual pair。

## 8. Candidate Failures

CandidateFailureCount=0。分母 PositiveHistoricalMemoriesRetrieved=0，因此 candidate rate 与 HistoricalSuccessCurrentHarmRate 记为 `null`，不写作 0。

## 9. Confirmed Failures

ConfirmedFailureCount=0，BehaviorChangingConfirmedFailures=0；没有执行 candidate repeats。

## 10. Representative Case

NONE。

## 11. Aggregate Metrics

- FormalEpisodes: 20
- MemoryWrites: 20
- TotalRetrievalEvents: 0
- PairedEvents: 0
- CandidateFailureCount: 0
- ConfirmedFailureCount: 0
- TotalInferenceCalls: 40
- Prompt/completion/total tokens: 36,520 / 10,018 / 46,538
- Mean / median / worst Delta_current: null / null / null

## 12. Gates

- G0 Integrity: PASS
- G1 Real JitRL Execution: PASS
- G2 Real Memory Lifecycle: FAIL（无 later retrieval event）
- G3 Valid Paired Intervention: FAIL
- G4 Historical Positive Retrieval: FAIL
- G5 Candidate Current Harm: FAIL
- G6 Confirmed Current Harm: FAIL
- G7 Native Behavioral Path: FAIL
- G8 Non-Triviality: PASS（未提出 failure case；结构化日志未见 parsing、invalid action、reset 或 runner error）
- G9 Budget Discipline: PASS

## 13. What This Establishes

在冻结的真实 JitRL/Jericho/Ollama runtime 中，原生 memory write 正常发生，但当前依赖状态不能形成原生 retrieval event，因此本协议无法检验 historical-success/current-harm paired existence claim。

## 14. What This Does NOT Establish

该结果不证明有害 memory 不存在，也不证明 JitRL 普遍可靠或失败。它不提供 failure 频率、多模型、多任务、跨系统、full endogenous self-invalidation、完整 source-policy provenance、方法必要性、方法 novelty 或论文 novelty 证据。

## 15. Limitations

单 task、单本地模型、20 个单步 episode；source-policy provenance 不完整；qwen2.5:14b 不是 JitRL 原论文固定 API 设置；Ollama 仅为兼容推理 transport；没有可配对的 retrieval event，因而 LLM 随机性、state restore 和 failure frequency 均无法由本轮估计；没有跨系统实验、方法设计或论文检索。

## 16. Verdict

**REAL_JITRL_FAILURE_NO_GO**

原因是冻结 runtime 没有 meaningful native retrieval，G2–G7 无法通过。按 stop rule 不换 task、模型、依赖或 retrieval 参数，也不增加 episode。
