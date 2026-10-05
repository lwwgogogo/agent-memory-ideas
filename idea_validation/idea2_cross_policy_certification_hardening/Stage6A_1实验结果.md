# Idea 2 Stage-6A.1 实验结果

## 历史范围与本轮目标
Stage-6A 永久保留 CROSS_POLICY_CERT_NARROW。其 generator/evaluator 耦合、候选进程与强制schema边界缺失、多个模块只是 import *，且 G5 被硬编码。由此不能证明 oracle-free，并非已经发现 oracle 被使用。详见 SCOPE_CORRECTION.md。
本轮只加固 execution boundary，不重新设计科学机制。world、case列表、outcome table、TV距离、pair权重、阈值及生命周期全部复用历史定义；按旧结果做数值复现。

## 隔离架构和输入
private generator 单独生成精确数据及私有清单；匿名 JSONL 只包含 era_id/state/action/outcome，每条是 individual observation。era 满足 e 后至少三位数字；候选自行重建 exposure/success counts、profile、aggregate gap 和全部认证指标。
11个正式配置各在独立临时目录和 subprocess 执行。该目录只复制候选源码、逐条输入及 public_config.json；CLI 只有固定 input.jsonl、output.json。Python -I -S -B、标准输入关闭、其他描述符不继承，环境仅 LANG/LC_ALL。评估器在所有候选进程退出后才读取私有清单。
AST逐项检查导入，候选源码禁用词扫描通过状态为 True。open audit限制读取在临时目录或解释器库、写入仅output.json；外部进程和网络禁止。临时目录外合成sentinel的实际读取拒绝测试为 True。这不是OS级恶意程序隔离证明；结论针对经过源码审计的正式执行路径。

## 强制schema与拒绝测试
六种额外字段分别为 gamma、policy_name、world、true_utility、ground_truth、expected_status。四种缺失字段与两种语义era ID亦分别测试。使用完整有效数据，只修改首条记录；要求明确schema错误、非零退出且不生成候选输出。额外字段拒绝：True；缺失字段拒绝：True；匿名era检查：True。G5 由实际11个子检查AND得到：True，未硬编码。

## 私有元数据变换
基准加 5 种私有元数据变换，涉及 world/effect/gamma/internal identifier。所有候选输入SHA相同：True；原始输出bitwise相同：True；canonical JSON相同：True。未把metadata放入CLI或候选临时目录。输出没有时间戳、进程ID或临时目录绝对路径。

## 数值复现与M1
全部11个配置与Stage-6A历史正式JSON逐项匹配：True。浮点绝对容差固定1e-12；整数cell严格相同。W4的D_true/D_false=18。M1只在评估器从observations按均匀target重算，候选认证不读取M1。
M1 ECHO与DIVERSE gap均为.40，而认证分别DESCRIPTIVE与PRESCRIPTIVE；复现通过状态：True。这体现utility estimation和lifecycle information的不同作用，不表示M1估计失败。

|配置|认证状态|D_policy|C_pos|C_conflict|M1 gap|
|---|---|---:|---:|---:|---:|
|M1_DIVERSE|PRESCRIPTIVE|0.6|1|0|0.4|
|M1_ECHO|DESCRIPTIVE|0|0|0|0.4|
|W1_K1|DESCRIPTIVE|0|0|0|0|
|W1_K10|DESCRIPTIVE|0|0|0|0|
|W1_K2|DESCRIPTIVE|0|0|0|0|
|W1_K20|DESCRIPTIVE|0|0|0|0|
|W1_K5|DESCRIPTIVE|0|0|0|0|
|W2_PQ|PROVISIONAL|0.9|0|1|0|
|W2_PQPQ|PROVISIONAL|0.6|0|1|0|
|W3|PRESCRIPTIVE|0.6|1|0|0.4|
|W4|PROVISIONAL|0.0333333333333|1|0|0.4|

## 测试、锁、历史与Gate
预运行测试 77 passed；正式运行 1 次，restart=False。源码/配置/预注册SHA核验：True。全部历史文件/链接数量 1956，逐字节/链接一致：True。

|Gate|结果|
|---|---|
|H0|PASS|
|H1|PASS|
|H2|PASS|
|H3|PASS|
|H4|PASS|
|H5|PASS|
|H6|PASS|
|H7|PASS|
|H8|PASS|
|H9|PASS|

## Verdict
ORACLE_FREE_HARDENING_GO。本轮仅新增oracle-free execution boundary evidence；Stage-6A历史NARROW保持不变。

## 局限
仍仅synthetic discrete states、exact counts、known era segmentation；无natural-language parsing、automatic policy-change detection、finite-sample variance、continuous context、full-agent integration；thresholds are research probes；无novelty claim、lineage或long-run closed-loop stability证明。临时目录和Python审计不等同于操作系统权限分离，不声称抵御任意恶意代码或原生扩展。未扩大科学claim，未进入后续阶段。
