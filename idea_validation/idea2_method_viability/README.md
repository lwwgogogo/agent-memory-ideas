# Idea 2 Stage-5：方法可行性研究

工作区为远程 /home/liaoweiwen/projects/agent-memory-ideas，环境 agentmem_lab / Python 3.10.21。六个历史目录冻结；本目录独立比较 M0/M1/M2/M3/M4 与 no-state 消融 A1。

先运行 python preflight.py 完成测试与 SHA256 lock，再 python native_baselines.py 复现 Stage-4.1；G0 不过立即停。随后 python run_experiment.py、python evaluate.py、python report.py。Raw 输出以独占模式写入，拒绝覆盖正式运行。已有结果可直接阅读或仅重新评估，不能将 order seeds 当 outcome sampling。

build_worlds.py 产生 exact logs；methods.py 只实现固定公式；adapters/ 读原生字段并做 secondary selection；native_baselines.py 直接执行固定 upstream 原生函数；evaluate.py 只计算统计和 Gate。M3 oracle 永不候选；M0选择支持度与估计成功概率明确区分。详细范围、公式与阈值见 preregistration.md、theory.md。
