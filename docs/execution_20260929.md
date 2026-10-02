# Phase A.1 在线 Bayesian 模型平均执行记录

参考《Agent Memory 三条研究 Idea 备忘录》2.5/2.6：在线估计作为下一阶段，先检查强对照，不把经典过滤方法包装为创新。运行前方案见 phase_a1_a2_plan.md。本次不实施 A.2、NIS、LLM 或 JitRL。

## 实现与验证

新增 online.py：49组固定Q/R假设的均匀先验，每步先计算观测predictive likelihood，再更新模型权重和状态后验。只接收观测和预先配置的候选网格，不读取真实Q/R、truth或验证标签。

新增3项测试，与原7项一起在本地、服务器全部通过。测试用联合参数/隐状态枚举核对预测概率、状态后验和参数后验均值，检查单模型退化、因果性和6000步数值稳定性。

服务器：/home/liaoweiwen/projects/agent-memory-ideas，独立Python3.10环境。25格、验证种子100–109、全新测试种子40–59，2000步、burn-in100。完整计算约101.25秒。结果保存到outputs/phase_a1_20260929并已取回本地；取回时run.json全部源码哈希与本地一致。compare_online.py为运行完成后新增的汇总脚本，未包含在原运行哈希清单中。

## 新种子结果

- 全局固定baseline：79.1392%。
- 每格验证选参baseline：84.2669%。
- 在线BMA：83.1853%。
- Oracle-Q/R：84.4298%。

在线BMA比全局固定高4.0461个百分点，paired seed bootstrap 95%区间[3.8058,4.2829]个百分点。追回Oracle-global差距的76.4768%，bootstrap区间[73.2893%,79.3970%]。Oracle-online残差1.2445个百分点，95%区间[1.0611,1.4242]个百分点。

不同于上次种子，不能把两次绝对accuracy的下降解释为代码退化。新种子内部，Oracle对per-cell仍只多0.1628个百分点，重复了简单调参方法很强的观察。

本轮未达到运行前的80%追回、1个百分点残差参考线；也不能因此宣称需要新记忆机制。结果表明普通在线方法有较大收益，但有限观测和候选网格仍造成误差。

## 误差诊断与限制

最大Oracle-online accuracy差距为Q=0.001/R=0.45处9.0921个百分点，其次Q=0.01/R=0.45处5.6632个百分点。以第一格为例，1999时刻的跨seed平均Q后验均值仍约0.0718，真实Q为0.001；模型有效数约5.81。该现象与高噪声下有限样本参数不确定性相符，但尚未通过延长序列验证其原因，不能断言不可辨识。

Q=0.15/R=0.1处残差3.1842个百分点。配置网格中不包含0.15或0.1，末步平均后验Q约0.1115、R约0.1413，有效模型数约1.02。这提示模型集中到不精确候选的离散化限制；需要加密网格消融才能确认因果归因。

高准确率也不意味着Q/R已被正确分离；参数后验均值不能单独作为noise/change判别成功的证据。当前先验知道二元HMM模型族，并不是无先验Agent。

## 下一步判断

暂不宣告GO，不进入JitRL。优先做一个小的诊断消融：固定更密候选网格，用新种子检查离散化；对预先列出的高噪声条件延长序列，分时间窗报告表现，检查样本量影响。该消融尚未执行，不覆盖或替换本轮结果。

若普通在线BMA经合理消融已逼近Oracle，应停止stationary场景的新公式研究。只有存在应用依据时再按已写明的A.2方案测试轨迹内Q/R变化；不以改环境追求正结果。Idea2/3仍保持独立，遵循备忘录的优先级和kill条件。

## 复现

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_phase_a.py --config configs/phase_a1.json --output outputs/phase_a1_new
.venv/bin/python scripts/plot_results.py outputs/phase_a1_new
.venv/bin/python scripts/compare_online.py outputs/phase_a1_new
```

关键输出：per_seed.csv、summary.csv、run.json、comparison.json、online_diagnostics.csv（100/500/1000/2000步的参数诊断）、environment-lock.txt及figures/accuracy.png等5张图。
