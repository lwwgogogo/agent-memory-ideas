# Stage-5 方法可行性结果

最终判定：**METHOD_VIABILITY_GO**。选择候选：**M1**。本轮是 discrete-state exact-count viability，不是方法新颖性或大规模 benchmark 结果。

## 1. 协议与原生 baseline

所有六个历史目录冻结；正式运行前57项测试通过，并锁定预注册及实现 SHA256。固定 upstream commit、原生函数和 Stage-4.1 配置不变。G0 两系统均复现 null/.95 的20/20原生 reversal、median Native-RCD=.625，全部 selected IDs 与 Stage-4.1一致。

A/B/C 各8个bank；D复用A/B/C机制各4个bank，合计36个bank。每bank2000条整数exact记录，无outcome sampling；不同target复用同bank，只改变rho。两系统共产生720条 method/target结果，1440条额外native selection记录，4800条secondary selection记录。结果无 formal retry/调参/改公式。

Practical 输入不含 gamma、family 或真实 propensity；统一为原生对象可读的 state/action/outcome。JitRL reward/final_score是binary；MemRL读取原生update已有last_reward，按固定+1/−1编码转成binary。两系统 normalized数学输入和估计结果逐项相同，不作为独立统计样本。此 adapter 假定已有已标注 discrete state/action，不代表自动解析自然语言 memory。

## 2. Primary endpoint与尺度边界

M1/M2/M3/M4/A1 返回outcome-based utility。M0原生只返回selected items，本轮U0明确是20个order replicate的f_A/f_B中位数，属于selection-support proxy，不是成功概率。因此相对M0的CorrectionRate只作描述性归一化，必须共同满足absolute NPE、真实gap、TSR及crossover。A1为同一success尺度的no-state消融。下表中M0的gap/TSR只能按支持度解释。

## 3. Family A：null（gamma=.95）

| 方法 | PIG | NPE P | NPE Q | CorrectionRate | strict false reversal |
|---|---|---|---|---|---|
| M0 | 1.200000 | 0.600000 | 0.600000 | 0.000000 | True |
| A1 | 1.260000 | 0.630000 | 0.630000 | -0.050000 | True |
| M1 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | False |
| M2 | 0.013125 | 0.006562 | 0.006562 | 0.989062 | True |
| M3 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | False |
| M4 | 0.012989 | 0.006495 | 0.006495 | 0.989175 | True |


false reversal按严格符号定义，没有事后容差。M2/M4即使CorrectionRate很高仍可能残留小幅反转，不能宣称完全消除。M1使用精确state均值与rho，所有gamma均PIG=NPE=0；M3 oracle同样为0但不候选。

## 4. Family B：真实global advantage

真实gap=.10，非BAL primary共P/Q×3档=6个条件。

| 方法 | .95 gap P | .95 gap Q | .95 TSR P | .95 TSR Q | A>B accuracy (.70/.85/.95) |
|---|---|---|---|---|---|
| M0 | 0.650000 | -0.500000 | 6.500000 | NA | 3/6 |
| A1 | 0.640000 | -0.440000 | 6.400000 | NA | 3/6 |
| M1 | 0.100000 | 0.100000 | 1.000000 | 1.000000 | 6/6 |
| M2 | 0.105625 | 0.094375 | 1.056250 | 0.943750 | 6/6 |
| M3 | 0.100000 | 0.100000 | 1.000000 | 1.000000 | 6/6 |
| M4 | 0.104534 | 0.093400 | 1.045339 | 0.934001 | 6/6 |


TSR只在estimated gap>0时输出，错误或平局不填0冒充有效retention。M1保留全部真实gap，而非把所有actions压平。平凡equalization会在G3/G4失败。

## 5. Family C：context crossover

同一bank的T0=(.8,.2)、T1=(.2,.8)，真实gap分别+.18、−.18。

| 方法 | .95 P: T0/T1 | .95 Q: T0/T1 | 所有非BAL bank均正确 |
|---|---|---|---|
| M0 | A/A | B/B | 0/6 |
| A1 | A/A | B/B | 0/6 |
| M1 | A/B | A/B | 6/6 |
| M2 | A/A | B/B | 0/6 |
| M3 | A/B | A/B | 6/6 |
| M4 | A/B | A/B | 6/6 |


M2按题述固定global SNIPS公式实现，没有rho权重；因此它不具备query自适应能力。这一negative result完整保留，没有为过Gate改公式。M1/M4的preference可随target改变；M3使用target-aware oracle SNIPS，只作classical reference。

## 6. Support sensitivity

.95最小cell n=50，.99最小n=10；Jeffreys prior与clip均固定，未调参。

| 方法 | gamma | 最大 null NPE | B gap min/max | C非均匀ranking正确 | 全部范围有限且[0,1] |
|---|---|---|---|---|---|
| M0 | 0.95 | 0.600000 | -0.500000/0.650000 | 2/4 | True |
| A1 | 0.95 | 0.630000 | -0.440000/0.640000 | 2/4 | True |
| M1 | 0.95 | 0.000000 | 0.100000/0.100000 | 4/4 | True |
| M2 | 0.95 | 0.006562 | 0.094375/0.105625 | 2/4 | True |
| M3 | 0.95 | 0.000000 | 0.100000/0.100000 | 4/4 | True |
| M4 | 0.95 | 0.006495 | 0.093400/0.104534 | 4/4 | True |
| M0 | 0.99 | 0.700000 | -0.500000/0.600000 | 2/4 | True |
| A1 | 0.99 | 0.686000 | -0.488000/0.688000 | 2/4 | True |
| M1 | 0.99 | 0.000000 | 0.100000/0.100000 | 4/4 | True |
| M2 | 0.99 | 0.466859 | -0.300165/0.500165 | 2/4 | True |
| M3 | 0.99 | 0.000000 | 0.100000/0.100000 | 4/4 | True |
| M4 | 0.99 | 0.031465 | 0.068434/0.122374 | 4/4 | True |


M1在这些exact cell means下可保持精确；这不代表n=10时有限样本方差很小。本轮未Bernoulli抽样，也没有声称confidence或sampling-robustness结论。零support时M1显式失败，positivity是必要限制。M2在.99因clip可能保留较大偏差；M4的不同cell shrinkage会产生与exposure有关的偏差。.99结果为sensitivity，不据其好坏回改Gate。

## 7. 必要消融和secondary selector

A0=M0，A1=aggregate action mean，A2=M1，A3=M4，A4=M2，A5=M3。A1在null/.95仍有PIG=1.260000和NPE=0.630000；M1为0，支持state conditioning是此已识别离散环境中的关键。A1也不随rho变化，无法完成crossover。

M1/M4 wrapper按rho给state quota，每state/action保留至少2条，余下按fixed temperature=1的corrected utility softmax分配；cell内按输入顺序选，不按success挑选。全部240个system/bank/target/method组合、每组20个seed满足quota/minimum-support且composition不随order改变：True。小k下softallocation舍入可能让A/B各10条，即使utility估计保留真实差异；secondary composition不进入任何primary Gate，也未评估后续LLM读取效果。

## 8. Gates与方法选择

| Gate | 全局判定 |
|---|---|
| G0 | PASS |
| G1 | PASS |
| G2 | PASS |
| G3 | PASS |
| G4 | PASS |
| G5 | PASS |
| G6 | PASS |
| G7 | PASS |
| G8 | PASS |
| G9 | PASS |


逐方法必须同时过所有必要Gate，不能把多个方法不同优点拼接：

| 方法 | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 |
|---|---|---|---|---|---|---|---|---|---|
| M1 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| M2 | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | PASS | PASS |
| M4 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |


固定选择顺序得到M1。M3是ORACLE / NOT CANDIDATE METHOD。M1统计核心就是direct standardization/g-computation形式，本轮不声明新颖性。后续必须单独做方法新颖性/差异化审计，不能将经典公式重新包装为新方法。

## 9. 可复核性与停止

results下保存逐method精确分数、PIG/retention/crossover/support/ablation/Gate和完整原生selected记录；source/preregistration/历史hash见manifest与final_verification。所有历史verdict保持独立、不回写。未使用新LLM、新reward model、训练或大benchmark。完成指定Git提交后停止。
