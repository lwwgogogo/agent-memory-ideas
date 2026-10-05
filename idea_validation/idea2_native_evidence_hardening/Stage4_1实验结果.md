# Idea 2 Stage-4.1 实验结果

最终判定：**NATIVE_EVIDENCE_GO**。G0–G7 均通过；G8 为 BLOCKED，不作为强化结论的依据。

## 1. Native evidence（原生返回证据）

固定 JitRL commit 143d22185d95fbf633a0befe6861d5e8b732543b 和 MemRL commit c1b322ca43de36ddf64c6712f89d0095bfc35ce0。正式输出每系统 640 条，无额外顺序、seed、k 或样本。JitRL 原文件 get_top_episodes 调用 640 次；MemRL 原文件 QValueUpdater.update 调用 320000 次、ValueAwareSelector.select 调用 640 次。函数路径、行号和源码 SHA256 随 raw 保存。

原生证据本身是：JitRL 返回的完整 episode 列表及顺序、MemRL 返回的完整 selected memories 及 actions/simmax。MemRL 全 2000 项 candidates 排序仅保留 count/hash，避免重复保存。每项 action/state/native stored score/rank/similarity 均可复核。下面所有 SSP、RCD、PIUR 和 reduction 数值均由 evaluator 读取这些原生返回项计算，并非上游自行输出的统计量。

primary gamma=.95、k=20：

| 系统 | Reversal rate | median SSP P | median SSP Q | median RCD | median BAL reduction |
|---|---|---|---|---|---|
| jitrl | 100.00% | 0.600 | -0.600 | 0.625 | 79.47% |
| memrl | 100.00% | 0.600 | -0.600 | 0.625 | 79.47% |


两组件的 selected IDs 在本次全部条件中完全一致：True。这来自相同 binary outcome 到分数的单调映射、同一候选集合、相同输入顺序与原生 stable tie handling。两套实际源码都确实执行，但它们不是两份独立抽样证据，不能合并成 N=40 的独立重复。

## 2. Evaluator-derived diagnostics（基于原生输出的统计和诊断）

### 精确环境与顺序控制

gamma=.50/.70/.85/.95，每 state 恰为 1000 experiences。S0/S1 每个 action 的成功率精确为 .9/.2，V(A)=V(B)=11/20=.55；所有 cell 整数检查通过。P/Q 仅改变 exposure，.50 的 P/Q 完全相同。20 seeds 固定为 20261005–20261024；所有顺序复本 sorted multiset hash 相同，order hash 各异。没有 outcome sampling，也未把 propensity 塞进原生系统。

### 全部 primary 顺序复本

两系统逐项选择一致，以下表格同时对应两系统；各自独立原生调用记录仍分别完整保存，不能只看最好 seed。

| Seed | SSP P | SSP Q | Native RCD | Native PIUR | BAL reduction |
|---|---|---|---|---|---|
| 20261005 | 0.70 | -0.60 | 0.650 | 1 | 0.692 |
| 20261006 | 0.50 | -0.70 | 0.600 | 1 | 0.667 |
| 20261007 | 0.70 | -0.70 | 0.700 | 1 | 0.857 |
| 20261008 | 0.70 | -0.50 | 0.600 | 1 | 0.500 |
| 20261009 | 0.60 | -0.60 | 0.600 | 1 | 0.500 |
| 20261010 | 0.30 | -0.40 | 0.350 | 1 | 0.714 |
| 20261011 | 0.90 | -1.00 | 0.950 | 1 | 0.789 |
| 20261012 | 0.70 | -0.60 | 0.650 | 1 | 0.846 |
| 20261013 | 0.70 | -0.70 | 0.700 | 1 | 0.857 |
| 20261014 | 0.60 | -0.80 | 0.700 | 1 | 0.857 |
| 20261015 | 0.50 | -0.50 | 0.500 | 1 | 0.800 |
| 20261016 | 0.50 | -0.60 | 0.550 | 1 | 0.818 |
| 20261017 | 0.80 | -0.80 | 0.800 | 1 | 0.875 |
| 20261018 | 0.50 | -0.90 | 0.700 | 1 | 0.857 |
| 20261019 | 0.80 | -0.50 | 0.650 | 1 | 1.000 |
| 20261020 | 0.40 | -0.40 | 0.400 | 1 | 0.500 |
| 20261021 | 0.50 | -0.40 | 0.450 | 1 | 0.111 |
| 20261022 | 0.70 | -0.70 | 0.700 | 1 | 0.714 |
| 20261023 | 0.60 | -0.30 | 0.450 | 1 | 1.000 |
| 20261024 | 0.30 | -0.60 | 0.450 | 1 | 0.556 |


### Dose response（k=20）

| 系统 | D_.50 | D_.70 | D_.85 | D_.95 | rho |
|---|---|---|---|---|---|
| jitrl | 0.000 | 0.275 | 0.525 | 0.625 | 1.000 |
| memrl | 0.000 | 0.275 | 0.525 | 0.625 | 1.000 |


rho 仅描述四个预设剂量点，不声称统计显著性。记录同时含 median |SSP(P)−SSP(Q)|，等于对应 median RCD 的两倍。

### k sensitivity（gamma=.95）

| 系统 | k | median SSP P | median SSP Q | median RCD | reversal rate | 方向一致 |
|---|---|---|---|---|---|---|
| jitrl | 5 | 0.600 | -0.600 | 0.600 | 95.00% | True |
| jitrl | 10 | 0.600 | -0.600 | 0.600 | 95.00% | True |
| jitrl | 20 | 0.600 | -0.600 | 0.625 | 100.00% | True |
| jitrl | 50 | 0.620 | -0.600 | 0.580 | 100.00% | True |
| memrl | 5 | 0.600 | -0.600 | 0.600 | 95.00% | True |
| memrl | 10 | 0.600 | -0.600 | 0.600 | 95.00% | True |
| memrl | 20 | 0.600 | -0.600 | 0.625 | 100.00% | True |
| memrl | 50 | 0.620 | -0.600 | 0.580 | 100.00% | True |


primary 稳定性 Gate 只用 k=20。较小 k 的逐 seed reversal rate 如表完整保留；不能把“中位方向一致”写成每个 k 的每个 seed 都翻转。

### Tie audit 与 success-pool 机制

| 系统 | selected unique scores | item-in-tie fraction | 1−unique/k | top-score pool size |
|---|---|---|---|---|
| jitrl | [1] | 100% | 95% | [1100] |
| memrl | [1] | 100% | 95% | [1100] |


item-in-tie fraction 表示该项在 selected set 中存在同分伙伴；另列 duplicate fraction=1−unique/k。两个组件只有成功/失败两档原生分数，top-score pool 恰为 1100 项。JitRL 的成功 final_score=1；MemRL 一次原生 update 后成功 q_value=.1，失败为−.1。没有调整 native score 或 tie breaking。

gamma=.95 时 P 的成功池 A=865、B=235，A 比例 173/220≈.786364；Q 为 A=235、B=865，A 比例 47/220≈.213636。BAL 成功池 A=B=550，比例各 .5。候选全体 A=B=1000，但排序后的高分池继承 policy-selected exposure composition。原生 selected composition 的 mean/median/min/max 与精确成功池比较存于 results/success_pool_diagnostic.json。

20 个固定 shuffle 下 primary 全部同方向翻转，排除了单个特定 insertion order 才出现效应的解释；大量 ties 本身仍是被测机制的一部分，不能声称已证明去掉 ties 仍成立。结论是原生高分候选选择对 experience composition 的稳定响应，不是证明系统显式估算了错误 causal value。旧 adapter action-bank average score、PSI、旧 PIUR 均没有计算或进入 Gate。

## 3. State-aware boundary（完整检索边界）

**BLOCKED**。exact upstream CrossEpisodeMemory.retrieve_similar_with_vector 未运行，StateAware-RCD 和 mitigation ratio 均为 NA。静态核对发现：history/state 向量经双 FAISS recall；最终重排 similarity 实际是 .3×history Jaccard + .7×state Jaccard，随后 discounted reward 作为排序第二项。它不是仅依据全局 reward 的 selector。另有 similarity>.98 的路径保留全部高相似项，返回数可能多于 k。

## 4. Unsupported / blocked paths（未支持或被阻塞的路径）

JitRL 当前 agentmem_lab 缺 openai、tiktoken、dotenv、faiss；必要环境变量 OPENAI_API_KEY、OPENAI_API_KEY2 均 NOT_SET。仅检查是否设置，没有打印/加载 secret，没有运行 fake embedding、hash embedding、替代模型或手工向量。记录 FULL_STATE_AWARE_BLOCKED_BY_DEPENDENCY。

MemRL 上游 QueryRetriever/MOS 和 AveFactRetriever 的语义、关键词/embedding candidate generation 已静态定位，但 memos 与完整 provider/store 集成缺失，记录 MEMRL_FULL_RETRIEVAL_NOT_RUN。当前 native selector 固定 similarity=.5、epsilon=0（Stage-4 同配置，上游默认 epsilon=.1），属于受控 greedy component audit，不是完整默认系统行为。

因此，本轮加固了指定 native global/value-based selection 的证据，仍不能排除 full state-aware candidate recall 会缓解甚至消除这种 shift。

## 5. Gates、测试与可复核性

| Gate | 判定 |
|---|---|
| G0 | PASS |
| G1 | PASS |
| G2 | PASS |
| G3 | PASS |
| G4 | PASS |
| G5 | PASS |
| G6 | PASS |
| G7 | PASS |


G8=BLOCKED，非 hard gate。正式运行前 37 tests 全 PASS，修正过一个 unknown-system parser 的异常类型检查，修正发生在锁定/正式运行之前。预注册与执行代码 SHA256 未改变。原生算法未修改；五个历史目录的逐文件 hash 在最终核验中检查，最终结果见 results/final_verification.json。各历史 verdict 永久保持。

## 6. 停止

本阶段完成固定证据加固，不增加系统、benchmark 或实验，不开始 Stage-4.2 或方法设计。现象证据加固完成，可以进入方法设计阶段。
