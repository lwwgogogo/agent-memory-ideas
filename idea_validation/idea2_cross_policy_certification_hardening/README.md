# Idea 2 Stage-6A.1：观测输入边界加固

独立于历史 Stage-6A。private generator → 匿名逐条 JSONL → 临时目录中的独立候选进程 → evaluator。候选只有两个路径参数；配置复制自已冻结的公开阈值。研究结果和局限见 Stage6A_1实验结果.md。

运行使用 agentmem_lab / Python 3.10.21；先测试，再锁定全部源码，最后运行 evaluator/run_hardening.py。正式运行器禁止覆盖已有正式完成记录。
