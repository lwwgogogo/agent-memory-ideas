# Idea 2 Stage-4.1：原生证据加固

唯一工作区为服务器 /home/liaoweiwen/projects/agent-memory-ideas，研究环境为 conda agentmem_lab / Python 3.10.21。只读复用 Stage-4 clone 的指定 JitRL/MemRL commit。

本阶段使用整数 exact logs、20 个固定顺序复本和原生 returned ranking/selection 检验 policy-conditioned selection。机制、阈值和范围见 preregistration.md、SCOPE_CORRECTION.md。历史五阶段结果全部冻结。

## 文件职责

build_exact_logs.py 只构造记录；adapters/ 只转换对象和隔离 import/storage 边界；两个 native runner 执行上游函数；native_metrics.py 只读原生返回；evaluate.py 重算统计并判 Gate。inspect_state_aware_paths.py 和 run_jitrl_state_aware.py 检查真实完整检索依赖；BLOCKED 时不模拟。

## 复核命令

在此目录和指定环境中运行 python -m pytest -q tests。数据用 python build_exact_logs.py 构建；正式 runner 要求预注册、实现 hash 与测试通过记录已经锁定，且使用独占新建输出文件以防覆盖正式结果。依次运行 python run_jitrl_native.py、python run_memrl_native.py、python evaluate.py。已有正式 raw 文件时 runner 会拒绝覆盖；评估可从保存的 native return 重算。

完整结果见 Stage4_1实验结果.md、最终结论.md，逐条 raw/summary/Gate 在 results/。第三方源码、credentials、依赖环境和 cache 均不提交。
