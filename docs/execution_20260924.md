# 初始化与服务器执行记录

日期：2026-09-24。已阅读目录中的两份 DOCX，并保存文字提取。按备忘录优先执行 Idea 1 Phase A；Idea 2/3 仅建目录和研究入口。

## 实际部署

- 本地：`E:/agent/test_idea`。
- 远端：`liaoweiwen@222.20.98.121:/home/liaoweiwen/projects/agent-memory-ideas`。
- 同步方式：显式源码清单的 tar/scp，非 Git remote；私钥留在本机。
- 项目环境：`.venv`，Python 3.10.21、NumPy 1.24.4、Matplotlib 3.7.5。
- 系统 Python 3.8 缺少 ensurepip，第一次创建的未完成环境保存在 `.venv-incomplete-py38`。使用已有 conda testidea 解释器新建独立 venv；没有修改 conda testidea 或 base。
- pip 默认连接等待，进程内强制 IPv4 后安装完成。复用命令：`./scripts/sync_server.ps1 -RunSmoke -Ipv4Only`。
- 服务器存在 4 张 RTX 4090，本轮完全使用 CPU。

## 验证

本地及服务器 7 项 unittest 全部通过：生成器确定性、clean/stable 边界、在线因果性、枚举隐状态核对精确 Bayesian 后验、指标事件分母与 censored delay、无事件缺失值、无信息观测后验，以及验证/测试 seed 重叠拦截（部分在同一 test 中）。

服务器 smoke 与本地 smoke 的选参和配对 gap 数值一致。完整运行退出码为 0，科学绘图脚本成功生成 5 张 PNG。完整结果已复制回本地 `outputs/phase_a_20260924/`，源码 SHA256 全部匹配运行记录。源码同步不依赖本机 Python 环境；本机附带解释器未装 Matplotlib，因此图由服务器生成后取回。

## 完整运行

配置：25 个 Q/R 网格点，每格 10 个验证 seed、20 个测试 seed，T=2000，burn-in=100。17 个预设 baseline 候选加 Oracle；另记录验证选出的 global/per-cell 两种比较方式。测试轨迹共 500 条；参数选择不使用测试数据。核心计算约 51.83 秒（不含安装与绘图）。

网格等权的 held-out accuracy：

- Last observation：78.249%。
- Majority history：56.967%。
- 全局验证最优固定 baseline（Bayes，假设 Q=0.01/R=0.1）：79.881%。
- 每格验证选参 baseline：85.114%。
- Oracle-Q/R：85.282%。

以 seed 为单位配对 bootstrap，5000 次重采样：

- Oracle 相对全局固定 baseline：+5.401 个百分点，95% 区间 [5.140, 5.656] 个百分点。
- Oracle 相对每格验证选参 baseline：+0.168 个百分点，95% 区间 [0.099, 0.242] 个百分点。

这不是完整创新验证。强 baseline 已接近 Oracle；虽然配对区间为正，效应量很小，不足以证明复杂 noise/change updater 的必要性。全局 baseline 与 Oracle 的大差距含有参数信息差。Per-cell baseline 也获得 regime 身份和该条件的验证标签，因此不能当作未知环境下已可部署的自适应系统。

遵循备忘录的 failure-first 原则，当前不自动进入 JitRL。后续若继续，应先明确实际效应阈值，并检查信息匹配对照、轨迹内 Q/R 改变或短暂 corruption 是否产生更有价值的适应问题；这些属于下一轮实验，不是本轮已证实的结论。

## 输出入口

- `outputs/phase_a_20260924/run.json`：配置、选参、环境、源码哈希、bootstrap。
- `outputs/phase_a_20260924/per_seed.csv`：10000 行方法/seed/格点记录，含选参别名。
- `outputs/phase_a_20260924/summary.csv`：各方法网格聚合。
- `outputs/phase_a_20260924/environment-lock.txt`：服务器完整 pip freeze。
- `outputs/phase_a_20260924/figures/`：accuracy、误更新、适应延迟、stale proxy、Oracle gap。
- `outputs/phase_a_20260924.log`：完整计算日志。

原文的 related-work 和创新性论断未独立联网核验；本轮只实现备忘录要求的可控 baseline 与评估协议。
