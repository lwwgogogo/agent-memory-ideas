# Agent Memory Ideas 实验项目

根据 `Agent_Memory_三条Idea研究备忘录.docx` 和补充的 `Agent_Memory_Idea1_后续推进与JitRL验证方案.docx` 初始化。

当前已实现 **Idea 1 — Noise or Change? 的 Phase A、A.1、D1/D2 诊断及 A.2 非平稳对照**。包括在线Q/R离散后验、遗忘与精确滑动窗口HMM估计；这些都是经典方法或启发式baseline，不声称新算法。Idea 2是备选，Idea 3是独立旁支，尚未实施LLM或真实Agent benchmark。

**当前研究判定：NO-GO，停止Idea 1复杂updater路线。** A.2验证选出的最佳可部署baseline为Forgetting-BMA（rho=.995），五个变化场景的Oracle全程accuracy gap为0.53–1.08pp，所有95% CI上界<2pp，没有达到预先规定的至少两类场景门槛。建议将主要研究精力切换到独立Idea 3，先验证fresh/revision/reset的信息等价路径差异。

- [D1/D2诊断报告](docs/execution_phase_a1_diagnostics_20260929.md)：网格加密、先验敏感性、严格配对的长度诊断、stationary NO-GO。
- [A.2完整执行报告](docs/execution_phase_a2_20260929.md)：逐场景全部指标与CI、选参、限制、最终NO-GO。
- [A.2运行前补充定义](docs/phase_a2_implementation_frozen_20260929.md)：候选网格、全局validation选择、控制与恢复定义。

已在服务器完成 smoke 与完整网格，结果已取回本地。运行命令、环境修复与首轮结果见 [2026-09-24 执行记录](docs/execution_20260924.md)。Oracle 对每格验证选参 baseline 仅增加约 0.168 个百分点，尚不足以支持复杂方法的必要性。

2026-09-29 首轮 **Phase A.1 在线 Bayesian 模型平均**：49模型准确率83.185%，追回约76.5%的Oracle-global差距。随后完成672模型Dense与长度诊断：主Dense追回83.84%、残差0.855pp；再按冻结方案完成A.2。历史记录保持原样，最终判定以上方最新报告为准。

## 环境与快速运行

Python **3.8–3.11**，CPU 即可。依赖固定在 `requirements.txt`，不安装 PyTorch 或 CUDA。服务器系统 Python 3.8 缺少 ensurepip；同步脚本优先借用已有 `~/miniconda3/envs/testidea/bin/python`（3.10）创建项目独立 `.venv`，不改动原环境。当前 conda base 为 Python 3.14，不适合这组依赖。其他服务器可通过 `PYTHON_BIN` 指定解释器。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/run_phase_a.py --config configs/smoke.json --output outputs/smoke
python scripts/plot_results.py outputs/smoke
python scripts/run_phase_a.py --config configs/phase_a.json --output outputs/phase_a
python scripts/plot_results.py outputs/phase_a
```

Windows 用 `py -3.11 -m venv .venv` 创建环境，以 `.venv\Scripts\python.exe` 替代上述 `python`，无需激活。输出目录必须是新目录，重复运行请换名称，避免覆盖结果。

## 目录

```text
configs/                       smoke 与完整 Q×R 网格
src/agent_memory/              environment / baselines / metrics
scripts/run_phase_a.py         验证集选参数、测试评估、配对 bootstrap
scripts/plot_results.py        科研热力图 PNG
scripts/sync_server.ps1        Windows → Linux 源码同步
scripts/server_smoke.sh        独立虚拟环境安装与远程试跑
tests/                        因果性、精确后验、指标边界检查
docs/                         原备忘录文本提取、实验协议、执行记录
experiments/idea2_*/           备选方向入口，尚未实现
experiments/idea3_*/           独立方向入口，尚未实现
data/                         生成式数据说明
outputs/                      运行结果，不纳入 Git
```

## 第一版 baseline

二元隐状态：`P(x_t != x_(t-1)) = Q`，观测翻转：`P(y_t != x_t) = R`，初始状态均匀。模型在线接收 `y_t` 后预测 `x_t`。

- Last Observation；累计 Majority；Sliding Window（5/15/51）。
- Fixed EMA（0.05/0.15/0.35/0.65）；归一化 Recency Decay（0.5/0.8/0.95/0.99）。二者长期行为接近，不能当作独立机制证据。
- Raw Conflict：观测与当前二元估计冲突时使用较大 EMA 更新率（0.65），否则 0.05。
- Fixed Bayesian：预先固定三组假设 Q/R；不读取生成器的实际参数。
- Oracle-Q/R：同一个 Bayesian 更新公式，额外获知真实 Q/R，但不读取真实状态或噪声事件标签。

Bayesian 递推：`p_prior = Q + (1-2Q)*p_previous`，再按二元观测 likelihood 做 Bayes 更新。Oracle 是该生成模型下逐时 0–1 loss 的 Bayes 决策参照，不保证有限样本中每个指标都最好，不是事件标签 oracle。

## 公平比较与输出

所有方法在同一 seed、同一 Q/R 使用完全相同的轨迹。验证 seeds 100–109 与测试 seeds 0–19 分离，测试前冻结参数。完整配置为 25 个网格点，每条序列 2000 步，前 100 步用于 warm-up。

`selected_global` 从全部候选中按验证集全网格平均 accuracy 选择一个固定方法。`selected_per_cell` 在每个网格点用验证集单独选最强候选，是更强但获知 regime 身份的对照。两者均不使用测试成绩选择参数。

Oracle 获知真实 Q/R，因此与全局固定方法的差距包含额外参数信息收益，不能直接证明未知 Q/R 时存在可实现优势。每格调参仍不是信息完全等价的控制：后续应加入已知 Q/R 的匹配策略或参数条件化对照。Phase B 是否启动需要综合 grid 覆盖和匹配信息量的后续检查。

- `validation.csv`：候选验证成绩。
- `per_seed.csv`：每格、每 seed、每方法全部指标与事件计数。
- `summary.csv`：每格方法的 seed 均值；缺失事件不当作 0。
- `run.json`：完整配置、所选方法、Python/NumPy 版本、Git revision（若有）、源文件 SHA256、耗时、Oracle gap 的配对 seed bootstrap 95% 区间。
- `trace.csv`：一个网格点的轨迹，便于调试。
- `figures/*.png`：accuracy、false update、adaptation delay、stale proxy 和 Oracle gap 热力图。

bootstrap 以 seed 为重采样单位，同一 seed 的所有网格点一起聚合，保留公共随机数造成的跨格相关性。区间仅描述这套合成网格的随机性，不是跨任务泛化置信区间。未做逐格多重比较显著性检验。

指标的精确定义与限制见 [docs/protocol.md](docs/protocol.md)。不存在足够事件时记录空值。GO/NO-GO 暂由研究者结合效应量、覆盖面和信息匹配判断；备忘录没有预注册数值阈值，因此程序不会自动宣布 GO。

## 服务器同步

使用用户指定 SSH 账户，私钥仅留在本机，不进代码、不上传。Windows PowerShell：

```powershell
.\scripts\sync_server.ps1 -RunSmoke -Ipv4Only
ssh -i "$env:USERPROFILE/.ssh/liaoweiwen_imds_ed25519" -p 22 liaoweiwen@222.20.98.121
```

远端默认目录 `/home/liaoweiwen/projects/agent-memory-ideas`，使用项目内 `.venv`。`-Ipv4Only` 让本次 pip 进程仅用 IPv4，解决此服务器连接 PyPI 时的等待，不修改系统网络；该兼容脚本使用 pip 内部接口，升级 pip 后需复验。脚本通过 tar/scp 同步列出的源码目录，更新同名源文件，不删除远端旧文件，也不上传本机环境、私钥、输出或其他项目。此同步不是 Git 远程仓库；若需要版本化协作可后续配置 Git remote。

进入远端目录后运行完整配置：

```bash
.venv/bin/python scripts/run_phase_a.py --config configs/phase_a.json --output outputs/phase_a_new
.venv/bin/python scripts/plot_results.py outputs/phase_a_new
```

## 下一阶段

按备忘录顺序：A 现象与 Oracle → B 在线 Q/R 或 change probability 估计 → C 自然语言 synthetic → D Jericho/JitRL。只有前一阶段获得可信证据才扩大工程投入。原文相关工作和论文创新性判断未在此次初始化中独立核验。
