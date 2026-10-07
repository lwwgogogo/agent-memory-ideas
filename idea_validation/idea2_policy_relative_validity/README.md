# Idea 2 Stage-7：Policy-Relative Memory Validity
本目录只验证最小机制：同一条由旧policy产生的成功memory，在环境和奖励固定时，因continuation policy变化而由正Q变为负Q；并测试memory是否能参与造成这种policy变化。

运行环境为agentmem_lab / Python 3.10.21。先运行pytest，再锁定preregistration与正式代码SHA，最后只允许一次run_experiment.py。无论文检索、LLM、GPU、agent pipeline或benchmark。

B2、B3分别只是HistoricalUtility和简化JitRL-style探针，不代表MemRL/JitRL复现。B4是真实target-Q oracle upper bound。结论与边界见Stage7实验结果.md。
