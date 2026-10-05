# Stage-6A 范围更正

Stage-6A 历史结论 CROSS_POLICY_CERT_NARROW 永久保留。只读审计确认：

1. 造数和评估耦合在 run_experiment.py。
2. 没有独立候选进程边界。
3. schema.validate 存在，但正式执行未证明必须经过它。
4. certification.py、build_worlds.py、policy_profile.py、baselines.py 都只是 from run_experiment import *。
5. 原运行器将 G5 硬编码为 True；最终人工审计据此降级。
6. 因此 Stage-6A 没有建立足够强的 execution isolation，无法证明 oracle-free。

上述缺口不是已经发现使用 oracle 的证据。本轮仅加固执行边界，保持世界、公式、阈值、生命周期和历史文件不变。
