# Phase A.2 非平稳验证执行记录

## 1 做了什么

D1/D2完成并满足预定stationary停止门槛后，运行冻结的Q increase/decrease、R increase/decrease、100步temporary corruption，以及四个匹配端点的stationary controls。只比较既有方法，无新updater、NIS、LLM/API或GPU。

## 2 为什么做

检查Q/R本身变化时stationary统计是否导致迟滞，以及简单遗忘/窗口估计能否解决大部分问题。目标是判断研究空间，不是证明Idea1正确。

## 3 协议与补充定义

严格沿用phase_a1_a2_plan.md的场景数值、步数、变化范围和种子。原计划未给定的window/rho候选、control数值、retention proxy和control退化阈值已在phase_a2_implementation_frozen_20260929.md中于validation/test前冻结。Q两个方向只计一类，R同理。
新增生成器使用4个独立随机流分别控制初始状态、转移、噪声和变化时刻；同一seed跨方法完全相同，跨场景使用公共随机数。没有改变生成分布以获取正结果；旧generate/API及旧输出保留。
窗口估计通过两栈HMM矩阵乘积精确计算最近W条观测后验，经过逐窗口从头过滤对照测试。Forgetting只折扣模型posterior权重，明确是heuristic。Oracle每步知道Q/R，不读latent truth。

## 4 配置与种子

configs/phase_a2.json：T3000，burn-in100，start在[900,1500]均匀整数；验证200–219，测试300–339；9场景等权validation accuracy选择一次全局方法与各family超参数，不向方法透露test场景类型。5000次paired seed bootstrap。
实际选参：{"selected_global": "recency_0.8", "selected_forgetting": "forget_0.995", "selected_window": "window_bma_500", "selected_deployable": "forget_0.995"}。4个CPU workers，每worker BLAS线程为1。

## 5 源码hash与环境

配置SHA256：a693b9226bef9608f29b6690e659ec6043a41343b216721bb523d7790f5b11db。
runner SHA256：932357afa5cd150c843402cbe87a100b4105f98c98e89e6804fcb985ff3f59fe。
generator SHA256：0a2fdb6aa6127975c54b73e5a826d4caa1f7ee2a46bd4e916f7b6ca004dad7eb。
window SHA256：a52e54bcde852b15af1060ddf9757962c6be7be8fb78735a1f6f8e9b8ecf5497。
Python 3.10.21，NumPy 1.24.4；完整环境见environment-lock.txt。运行开始已存source_snapshot.zip、全部source_sha256、config.json及前置D1/D2 run.json哈希。

## 6 时间与检查

核心运行366.92秒（不含绘图），180条validation轨迹、360条test轨迹。18项unittest本地与服务器通过。audit.json验证源码归档、原始结果hash、方法/场景/seed覆盖、变化时间和污染长度。旧结果未覆盖。

## 7 逐场景核心数值

以下区间均为95% seed bootstrap；accuracy和error使用百分数，gap使用百分点。best指validation选出的Forgetting-BMA rho=.995，非test选优。

### q_increase

- selected_global accuracy：83.5164 [83.1103, 83.8733]%。
- online_bma accuracy：82.0397 [81.5741, 82.4741]%。
- dense_bma accuracy：83.4009 [82.9233, 83.8534]%。
- selected_forgetting accuracy：85.6147 [85.2612, 85.9595]%。
- selected_window accuracy：85.5759 [85.2224, 85.9224]%。
- oracle_qr accuracy：86.3698 [86.0112, 86.7095]%。
- Oracle-best accuracy gap：0.7552 [0.5991, 0.9095] pp。
- best brier：0.0995 [0.0971, 0.1019]（原指标单位）。
- best false_update_rate：0.3651 [0.3467, 0.3851]（原指标单位）。
- best noise_overreaction：0.2314 [0.2241, 0.2391]（原指标单位）。
- best adaptation_delay_capped：0.7700 [0.7262, 0.8114]（原指标单位）。
- best adaptation_censored_rate：0.0984 [0.0900, 0.1070]（原指标单位）。
- best stale_reuse_proxy：0.1540 [0.1490, 0.1593]（原指标单位）。
- error_50：best 27.6500 [25.3500, 29.9500]%；Oracle 19.5500 [17.8000, 21.3000]%。
- error_100：best 27.0500 [25.2000, 28.9500]%；Oracle 20.2000 [18.7994, 21.6000]%。
- error_300：best 24.1000 [23.0165, 25.3083]%；Oracle 19.8917 [19.1333, 20.6750]%。
- recovery完成10连对延迟：33.6000 [26.5244, 42.0256]步；censoring：0.0000 [0.0000, 0.0000]%。

### q_decrease

- selected_global accuracy：88.7690 [88.2577, 89.2759]%。
- online_bma accuracy：89.3983 [88.8913, 89.9173]%。
- dense_bma accuracy：88.8543 [88.3276, 89.3742]%。
- selected_forgetting accuracy：90.3155 [89.8836, 90.7544]%。
- selected_window accuracy：90.1129 [89.6379, 90.5931]%。
- oracle_qr accuracy：90.8647 [90.4431, 91.2802]%。
- Oracle-best accuracy gap：0.5491 [0.4448, 0.6569] pp。
- best brier：0.0688 [0.0659, 0.0718]（原指标单位）。
- best false_update_rate：0.2525 [0.2333, 0.2716]（原指标单位）。
- best noise_overreaction：0.1876 [0.1796, 0.1953]（原指标单位）。
- best adaptation_delay_capped：0.7126 [0.6577, 0.7676]（原指标单位）。
- best adaptation_censored_rate：0.0772 [0.0666, 0.0877]（原指标单位）。
- best stale_reuse_proxy：0.0968 [0.0925, 0.1012]（原指标单位）。
- error_50：best 10.4500 [8.4487, 12.5500]%；Oracle 2.8500 [1.5000, 4.4500]%。
- error_100：best 8.5500 [7.1500, 10.0500]%；Oracle 2.4500 [1.6000, 3.3500]%。
- error_300：best 5.4750 [4.6583, 6.3833]%；Oracle 2.6500 [2.0333, 3.3917]%。
- recovery完成10连对延迟：22.4500 [18.1750, 27.6256]步；censoring：0.0000 [0.0000, 0.0000]%。

### r_increase

- selected_global accuracy：86.4603 [86.0758, 86.8526]%。
- online_bma accuracy：86.3388 [85.8387, 86.8828]%。
- dense_bma accuracy：86.4328 [85.9621, 86.9483]%。
- selected_forgetting accuracy：90.0750 [89.5517, 90.6241]%。
- selected_window accuracy：89.7078 [89.1414, 90.2888]%。
- oracle_qr accuracy：91.1526 [90.5956, 91.7474]%。
- Oracle-best accuracy gap：1.0776 [0.8241, 1.3267] pp。
- best brier：0.0744 [0.0709, 0.0777]（原指标单位）。
- best false_update_rate：0.1280 [0.1189, 0.1369]（原指标单位）。
- best noise_overreaction：0.1311 [0.1259, 0.1364]（原指标单位）。
- best adaptation_delay_capped：4.0316 [3.7075, 4.3561]（原指标单位）。
- best adaptation_censored_rate：0.0405 [0.0309, 0.0501]（原指标单位）。
- best stale_reuse_proxy：0.1030 [0.0968, 0.1093]（原指标单位）。
- error_50：best 19.7500 [17.1000, 22.5500]%；Oracle 7.9500 [4.3500, 12.1000]%。
- error_100：best 22.3000 [19.9000, 24.8250]%；Oracle 11.1000 [8.1744, 14.0750]%。
- error_300：best 18.5333 [16.6998, 20.4083]%；Oracle 11.7750 [9.6417, 14.0250]%。
- recovery完成10连对延迟：20.2000 [16.6750, 23.9000]步；censoring：0.0000 [0.0000, 0.0000]%。

### r_decrease

- selected_global accuracy：90.8250 [90.3207, 91.3422]%。
- online_bma accuracy：93.2483 [92.6146, 93.8536]%。
- dense_bma accuracy：93.2560 [92.6068, 93.8673]%。
- selected_forgetting accuracy：93.6560 [92.9845, 94.2949]%。
- selected_window accuracy：93.6664 [93.0026, 94.3010]%。
- oracle_qr accuracy：94.1819 [93.5292, 94.7931]%。
- Oracle-best accuracy gap：0.5259 [0.3397, 0.7276] pp。
- best brier：0.0487 [0.0446, 0.0530]（原指标单位）。
- best false_update_rate：0.1101 [0.0954, 0.1262]（原指标单位）。
- best noise_overreaction：0.1233 [0.1174, 0.1297]（原指标单位）。
- best adaptation_delay_capped：3.1678 [2.8482, 3.5220]（原指标单位）。
- best adaptation_censored_rate：0.0232 [0.0149, 0.0326]（原指标单位）。
- best stale_reuse_proxy：0.0637 [0.0574, 0.0704]（原指标单位）。
- error_50：best 2.7000 [1.6000, 4.0000]%；Oracle 1.1000 [0.7500, 1.5000]%。
- error_100：best 2.4750 [1.7500, 3.3250]%；Oracle 1.1000 [0.8250, 1.4000]%。
- error_300：best 1.9167 [1.5583, 2.3333]%；Oracle 1.2750 [1.0917, 1.4917]%。
- recovery完成10连对延迟：10.7750 [10.2250, 11.4750]步；censoring：0.0000 [0.0000, 0.0000]%。

### temporary_corruption

- selected_global accuracy：96.0828 [95.8457, 96.3181]%。
- online_bma accuracy：97.1353 [96.9733, 97.2948]%。
- dense_bma accuracy：97.1603 [97.0043, 97.3138]%。
- selected_forgetting accuracy：97.1828 [97.0250, 97.3397]%。
- selected_window accuracy：97.1371 [96.9836, 97.2888]%。
- oracle_qr accuracy：97.8310 [97.5931, 98.0603]%。
- Oracle-best accuracy gap：0.6483 [0.4198, 0.8638] pp。
- best brier：0.0226 [0.0214, 0.0238]（原指标单位）。
- best false_update_rate：0.1277 [0.1203, 0.1351]（原指标单位）。
- best noise_overreaction：0.2239 [0.2168, 0.2309]（原指标单位）。
- best adaptation_delay_capped：1.1501 [1.1120, 1.1913]（原指标单位）。
- best adaptation_censored_rate：0.0061 [0.0024, 0.0103]（原指标单位）。
- best stale_reuse_proxy：0.0291 [0.0275, 0.0307]（原指标单位）。
- error_50：best 36.0500 [31.9000, 40.2512]%；Oracle 15.9000 [8.2487, 24.4500]%。
- error_100：best 39.5500 [36.1750, 42.9000]%；Oracle 21.8500 [15.7250, 28.4750]%。
- error_300：best 14.2667 [13.0998, 15.4500]%；Oracle 8.2083 [6.1417, 10.4000]%。
- recovery完成10连对延迟：35.6250 [28.4988, 43.5506]步；censoring：7.5000 [0.0000, 17.5000]%。
- best corruption_error：39.5500 [36.1750, 42.9000]%。
- best post_corruption_error_100：1.5000 [1.0500, 1.9750]%。
- best post_corruption_error_remaining：1.4861 [1.3780, 1.5944]%。
- best useful_memory_retention_proxy：99.4224 [98.7306, 99.9412]%。
- 污染结束后10连对恢复延迟：10.5250 [10.1250, 11.2250]步；censoring：0.0000 [0.0000, 0.0000]%。

### control_low_q

- selected_global accuracy：96.0276 [95.7723, 96.2862]%。
- online_bma accuracy：96.8517 [96.5508, 97.1354]%。
- dense_bma accuracy：97.0888 [96.8147, 97.3509]%。
- selected_forgetting accuracy：97.0034 [96.7241, 97.2733]%。
- selected_window accuracy：97.0009 [96.7189, 97.2664]%。
- oracle_qr accuracy：97.0940 [96.8034, 97.3595]%。
- Oracle-best accuracy gap：0.0905 [0.0319, 0.1440] pp。
- best brier：0.0242 [0.0221, 0.0264]（原指标单位）。
- best false_update_rate：0.0348 [0.0310, 0.0387]（原指标单位）。
- best noise_overreaction：0.0799 [0.0759, 0.0842]（原指标单位）。
- best adaptation_delay_capped：3.8083 [3.6253, 4.0109]（原指标单位）。
- best adaptation_censored_rate：0.0119 [0.0046, 0.0205]（原指标单位）。
- best stale_reuse_proxy：0.0317 [0.0289, 0.0345]（原指标单位）。

### control_high_q

- selected_global accuracy：76.2750 [75.9370, 76.6173]%。
- online_bma accuracy：79.6767 [79.3690, 79.9811]%。
- dense_bma accuracy：80.0069 [79.7353, 80.2767]%。
- selected_forgetting accuracy：79.7121 [79.4509, 79.9750]%。
- selected_window accuracy：79.8388 [79.5810, 80.1095]%。
- oracle_qr accuracy：80.1474 [79.8836, 80.4336]%。
- Oracle-best accuracy gap：0.4353 [0.2871, 0.5948] pp。
- best brier：0.1384 [0.1366, 0.1402]（原指标单位）。
- best false_update_rate：0.7269 [0.6996, 0.7559]（原指标单位）。
- best noise_overreaction：0.3597 [0.3510, 0.3690]（原指标单位）。
- best adaptation_delay_capped：0.5533 [0.5187, 0.5853]（原指标单位）。
- best adaptation_censored_rate：0.0799 [0.0733, 0.0865]（原指标单位）。
- best stale_reuse_proxy：0.2031 [0.2004, 0.2057]（原指标单位）。

### control_clean

- selected_global accuracy：97.3181 [97.1310, 97.5035]%。
- online_bma accuracy：98.5379 [98.4466, 98.6311]%。
- dense_bma accuracy：98.5414 [98.4483, 98.6353]%。
- selected_forgetting accuracy：98.5302 [98.4388, 98.6233]%。
- selected_window accuracy：98.5250 [98.4328, 98.6181]%。
- oracle_qr accuracy：98.5509 [98.4586, 98.6457]%。
- Oracle-best accuracy gap：0.0207 [0.0121, 0.0310] pp。
- best brier：0.0124 [0.0117, 0.0131]（原指标单位）。
- best false_update_rate：0.0591 [0.0525, 0.0660]（原指标单位）。
- best noise_overreaction：0.2080 [0.1993, 0.2163]（原指标单位）。
- best adaptation_delay_capped：1.1091 [1.0792, 1.1420]（原指标单位）。
- best adaptation_censored_rate：0.0061 [0.0024, 0.0103]（原指标单位）。
- best stale_reuse_proxy：0.0152 [0.0142, 0.0161]（原指标单位）。

### control_noisy

- selected_global accuracy：79.9267 [79.4353, 80.4328]%。
- online_bma accuracy：86.2129 [85.3551, 87.0768]%。
- dense_bma accuracy：86.2621 [85.4111, 87.1302]%。
- selected_forgetting accuracy：85.8086 [84.9569, 86.6621]%。
- selected_window accuracy：85.8483 [84.9878, 86.7095]%。
- oracle_qr accuracy：86.7405 [85.9206, 87.5862]%。
- Oracle-best accuracy gap：0.9319 [0.6543, 1.2190] pp。
- best brier：0.1070 [0.1014, 0.1124]（原指标单位）。
- best false_update_rate：0.1147 [0.1033, 0.1265]（原指标单位）。
- best noise_overreaction：0.1027 [0.0982, 0.1074]（原指标单位）。
- best adaptation_delay_capped：6.5468 [6.0380, 7.0747]（原指标单位）。
- best adaptation_censored_rate：0.0609 [0.0485, 0.0736]（原指标单位）。
- best stale_reuse_proxy：0.1452 [0.1362, 0.1544]（原指标单位）。

## 8 Failure patterns 与强baseline对比

Stationary BMA确实迟滞：R increase下Dense stationary全程86.433%，forgetting90.075%；变化后前100步error分别24.50%和22.30%，Oracle11.10%。固定参数posterior累计大量旧证据后适应较慢，但普通forgetting显著缓解全程损失。
Window存在速度/噪声trade-off，证据来自validation：R increase前50步error W50为15.2%、W500为17.6%；control_noisy accuracy W50为83.459%、W500为85.722%。不能把test的不同场景重新选不同W。全局validation选W500，其初期适应不总快于forgetting。
Forgetting存在trade-off：validation control_noisy rho=.95/.995/.999 accuracy为83.231%/85.883%/86.040%，而R increase为89.059%/90.452%/88.300%。rho=.995是全局折中，不是新机制。
Temporary corruption仍有明显局部误差：best污染100步error39.55%，Oracle21.85%，差17.70pp [11.05,23.9006]。但恢复后前100步error仅1.50% vs1.15%；恢复延迟约10.525 vs10.325步（定义下最小10步），没有发现持续被带偏的强证据。全程gap仅0.6483pp，不能事后改以局部指标替代冻结的2pp门槛。

## 9 CI与GO门槛审计

五个变化场景的Oracle-best全程gap为0.7552、0.5491、1.0776、0.5259、0.6483pp；95%上界均<2pp。符合>=2pp的场景为0，更不满足至少两类。Oracle在post-change fixed windows仍更好，但这不满足联合门槛。
best相对Dense stationary在四controls下降0.0853/0.2948/0.0112/0.4534pp，最大paired95%上界0.6906pp，均未达到运行前>1pp的明显退化规则。该规则怎么收紧都无法改变全程gap门槛已失败的事实。

## 10 Limitations

限定于本次binary HMM、单次参数变化/100步污染、有限网格和有限候选。不是所有Agent Memory问题无价值的证明。Oracle拥有真实参数/时刻信息，剩余gap包含信息差，不可直接称可实现创新空间。
Useful-memory retention是有条件state正确率proxy，方法相关分母与缺失seed见原始CSV，非真实memory对象保留。Recovery是10连对首次完成，不能证明参数后验已恢复；短期偶然连续正确也可满足。
区间为seed配对，未校正多重比较；没有改test seed、改环境难度或追加有利场景。冻结门槛看full-trajectory accuracy，因此报告中如实保留污染阶段的大局部差距，而不拿它反转门槛。

## 11 Idea 1 Verdict

**NO-GO — 简单方法已经足够。**
现有简单 online/window/forgetting 方法已经足够解释或解决大部分现象，目前没有足够证据支持新的 Noise-or-Change memory updater。
此结论按本次预先设定的工程研究门槛作出。停止Idea1复杂算法路线，不设计NIS/Kalman/neural updater、uncertainty gate、新loss，不进入JitRL。

## 12 下一步与复现

建议把主要研究精力切换到独立的Idea3 Revision Inertia；下一步应先做信息等价的fresh/revision/reset现象验证，不在本轮实施。Idea1保留代码、负结果、图表和审计记录。
输出位于outputs/phase_a2_20260929。原始指标per_seed.csv、验证全候选validation_per_seed.csv、曲线curves.csv、汇总与CI summary.csv/contrasts.csv/curve_summary.csv，选参selection.json，判定decision.json。6张PNG与underlying CSV共同保存；绘图源码单独归档。
```bash
.venv/bin/python scripts/run_phase_a2.py --config configs/phase_a2.json --output outputs/a2_new --diagnostics-d1 outputs/phase_a1_dense_20260929 --diagnostics-d2 outputs/phase_a1_length_diag_20260929
.venv/bin/python scripts/plot_phase_a2.py outputs/a2_new
.venv/bin/python scripts/audit_research_outputs.py outputs/a2_new
```
