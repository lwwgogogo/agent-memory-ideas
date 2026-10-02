# Phase A.1 D1 D2 诊断执行记录

## 1 做了什么与为什么

完整读取execution_20260924.md、execution_20260929.md、phase_a1_a2_plan.md、protocol.md，核对配置、测试、原49模型代码和历史输出。文件与用户给定数字一致：Phase A global79.881%/per-cell85.114%/Oracle85.282%；A.1 global79.1392%/online83.1853%/Oracle84.4298%，追回76.48%，残差1.2445pp。

D1仅加密Q/R候选以排查discretization。D2仅延长高噪声序列，以排查有限样本。未引入新的updater、NIS、神经网络、LLM或下游环境。此前历史输出未覆盖。

## 2 配置与种子

D1：configs/phase_a1_dense.json；原25格、T2000、burn-in100、验证100–109、测试40–59、原17个fixed候选不变。Dense由25个log-Q mesh与21个linear-R mesh并入全部原候选轴和全部evaluation轴组成，共32×21=672模型。每条轨迹的真实参数不进入算法。

Dense-BMA主结果使用均匀参数先验；增加dense_prior_matched控制原粗区域先验总质量，用于说明discretization与prior effect不能完全混为一谈。两套配置均在test运行前写入，未按结果选先验。

D2：configs/phase_a1_length_diag.json；Q=.001/.01、R=.45；seed40–59；T2000/5000/10000；burn-in100。一次生成10000步后截取前缀，以最大化配对。500/1000/2000/5000/10000端点和分段窗口均有CSV。此诊断是exploratory。

## 3 与旧协议的差异

D1按照本次用户要求复用40–59，而非此前文字提议的新seed；不称为新独立confirmatory证据。候选网格含所有evaluation参数可能值，但方法不知道当前轨迹的参数。

原generate在整段转移抽样后才抽初始状态，独立调用不同T不保证前缀一致。D2不改原API，使用最长轨迹前缀，保持原生成分布；本次各长度可严格配对。D2 T2000的逐轨迹状态不保证等同D1，但不应将这种实现差异解释为方法收益。

全局固定、per-cell、Oracle、original BMA在D1与历史A.1共有的7600个accuracy/Brier/false-update/delay非缺失值差异全部为0。

## 4 复现、源码和环境

服务器/home/liaoweiwen/projects/agent-memory-ideas；Python3.10.21、NumPy1.24.4，CPU；每run保存完整environment-lock.txt。D1耗时212.07秒，D2耗时84.57秒，不含绘图。

每run在计算前保存source_snapshot.zip、完整source_sha256、config.json及run.json。关键SHA256：

- D1配置：9fd6c7cea5efbbce20dbcd1ab58fd3f87a7de9ae6f3405e55541d8efd477f9bb。
- D2配置：281c0bbf92437d2ea80349d2ddc1ea61bdcba8092b94149b0260a039da16d39d。
- online.py：e2b8947aba0bf13eeb0a47597117236c115feebf47dcaab8697fb7faf6cfe43d。
- run_diagnostics.py：5266db0f6adf37693590db21b431a841dd2a0c1a5e195ef719efd88bbf12a925。

运行阶段13项测试通过；随后用于A2的测试扩展至18项也通过。模型权重先验/衰减参数是可选项，原model_average三参数调用保持数值一致。

## 5 D1 结果与置信区间

- global fixed：79.1392%。
- original BMA：83.1853%。
- Dense-BMA：83.5747%。
- Dense prior-matched：83.2945%。
- per-cell validation baseline：84.2669%。
- Oracle：84.4298%。

Dense相对original提高0.3895pp，paired bootstrap95% CI [0.3122,0.4693]pp。Oracle-Dense残差0.8551pp，CI [0.6896,1.0306]pp。追回83.84%，CI [80.84%,86.59%]。以预设点估计门槛通过；残差CI上界略超过1pp，不能声称置信区间完全落在门槛内。

off-grid Q=.15/R=.1：original gap3.1842pp [2.7079,3.6264]；Dense gap0.1789pp [0.0711,0.3053]；prior-matched gap0.1316pp [0.0421,0.2368]。此格强烈支持粗候选限制的解释。

总体prior-matched只追回78.54% [74.78%,82.25%]，因此uniform Dense整体改善不能全归因于加密本身。完整Brier、False Update、Noise Overreaction、adaptation/censoring、stale proxy及CI均在overall.csv/summary.csv/contrasts.csv，不以单一accuracy替代原指标。

## 6 D2 结果与置信区间

Q=.001/R=.45：

- original Oracle gap：T2000 9.0921pp；T5000 4.9653pp；T10000 2.7020pp。
- Dense Oracle gap：7.9316pp [4.5526,11.7003] → 4.3990pp [2.1826,7.1972] → 2.4919pp [1.3000,4.0188]。
- Dense最后5000步gap0.6230pp，CI [-0.0350,1.4410]。
- Dense Q后验均值从T2000的.05462到T10000的.001683；R从.43638到.45001；有效模型数47.74到4.90。

Q=.01/R=.45：

- original Oracle gap：5.6632pp → 4.4602pp → 2.9444pp。
- Dense Oracle gap：3.2737pp [1.9368,4.6343] → 2.7235pp [1.6377,3.8602] → 1.9278pp [1.1859,2.7436]。
- Dense最后5000步gap1.1480pp，CI [0.6520,1.7530]。
- Dense Q后验均值从.10154到.02831；R从.42911到.44764；有效模型数78.42到18.44。

误差随长度下降且后验向真实值靠近，有限观测/参数学习速度解释了相当部分gap；第二格尚未完全收敛，不能声称所有问题已解决。不同模型数下effective count不能直接按绝对数比较集中程度。

## 7 限制与判定

所有区间为5000次seed配对bootstrap，跨格先按seed平均；未做多重比较修正。原误更新率方法相关分母和封顶首次命中delay不等价于因果噪声效应或稳定恢复，stale proxy仍只是状态错误代理。假设binary HMM模型族正确，不涉及真实语言memory。

**Stationary verdict：NO-GO for new stationary updater/formula。** 主Dense在全网格点估计满足追回>=80%、gap<=1pp；合理经典估计已足够强，不支持发明新memory updating mechanism。此结论不是声称每一高噪声格点已达到Oracle。先验敏感性、有限序列参数不确定性仍存在，不能把残差自动当作创新空间。

## 8 下一步与输出

按用户允许与冻结方案，D1/D2完成后进入A2，测试参数本身变化导致的适应迟滞；不新增我们的方法。若A2不满足预先门槛，停止复杂Idea1并建议独立Idea3。

输出：outputs/phase_a1_dense_20260929与outputs/phase_a1_length_diag_20260929。图表使用其summary/contrasts/window/posterior CSV，PNG位于各自figures目录；绘图是运行结束后的派生产物，与计算source snapshot单独记录。

```bash
.venv/bin/python scripts/run_diagnostics.py d1 --config configs/phase_a1_dense.json --output outputs/d1_new
.venv/bin/python scripts/run_diagnostics.py d2 --config configs/phase_a1_length_diag.json --output outputs/d2_new
.venv/bin/python scripts/plot_diagnostics.py d1 outputs/d1_new
.venv/bin/python scripts/plot_diagnostics.py d2 outputs/d2_new
```
