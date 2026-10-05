# Stage-3 实验结果

REAL_FORMATION_WEAK

## 环境与完整性

Python 3.10.21；Primary writer qwen2.5:14b；Secondary writer qwq:32b；reader qwq:32b。模型及 GPU 信息见 results/environment.json。
输入 20 pairs / 40 worlds，source SHA256 76fbd6c45e70a8737a6b81b220f480c8f95aa63b18d6d454b969cc8fda2ac148。MEMORY_BUDGET=512 字符，max oracle 长度=117，自然输出 ceiling hit rate=0.000。
Primary 完整性 formation 160/160；faithfulness 320/320；recovery 160/160；downstream 320/320。
Secondary 完整性 formation 160/160；faithfulness 320/320；recovery 160/160；downstream 320/320。

## 记忆形成结果

| Writer | Formation | N generated | Strict faithful | Faithfulness rate | mean CRA | Full retention | FBIR | Accuracy | Regret | Pair resolution |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Primary | GenericSummary | 40 | 0 | 0.0000 | NA | NA | NA | 0.3750 | 0.1375 | 0.0000 |
| Primary | ReflectionLesson | 40 | 0 | 0.0000 | NA | NA | NA | 0.6000 | 0.0910 | 0.3000 |
| Primary | StrategyMemory | 40 | 0 | 0.0000 | NA | NA | NA | 0.3750 | 0.1389 | 0.0500 |
| Primary | ConsolidatedExperience | 40 | 19 | 0.4750 | 0.9474 | 0.7895 | 0.2105 | 0.5750 | 0.0917 | 0.2500 |
| Secondary | GenericSummary | 40 | 6 | 0.1500 | 1.0000 | 1.0000 | 0.0000 | 0.9250 | 0.0160 | 0.8500 |
| Secondary | ReflectionLesson | 40 | 2 | 0.0500 | 0.7500 | 0.5000 | 0.5000 | 0.8000 | 0.0444 | 0.6500 |
| Secondary | StrategyMemory | 40 | 5 | 0.1250 | 1.0000 | 1.0000 | 0.0000 | 0.8500 | 0.0312 | 0.7000 |
| Secondary | ConsolidatedExperience | 40 | 40 | 1.0000 | 0.9625 | 0.8500 | 0.1500 | 0.6250 | 0.0778 | 0.3500 |

## Controls

| Control | CRA | Full retention | Downstream accuracy | Downstream regret |
|---|---:|---:|---:|---:|
| C1_StatePreservingOracle | 1.0000 | 1.0000 | 0.4750 | 0.1090 |
| C2_FaithfulLossyAggregate | 0.0000 | 0.0000 | 0.5000 | 0.1021 |

## Faithfulness 与结构恢复

Primary STRICT_FAITHFUL memory 总数：19；Faithful-but-insufficient 数量：4。FBIR 以各 formation 内 strict faithful 为分母。

## 结构保留与 regret

Lost-minus-retained regret difference=-0.0130；world-cluster bootstrap 95% CI [-0.0417, 0.0000]；CRA/regret world-level Spearman rho=0.1217。

## Matched pairs

pair-level both sufficient / one sufficient / both insufficient 分类及 resolution 见 statistics.json。C1 oracle 的 downstream pair resolution=0.1000。

## Gates

| Gate | Result |
|---|---|
| G0 | PASS |
| G1 | PASS |
| G2 | FAIL |
| G3 | FAIL |
| G4 | FAIL |
| G5 | FAIL |
| G6 | FAIL |
| G7 | PASS |
| G8 | PASS |

Run1、Confirmatory、Stage-2 的历史目录及 verdict 未修改。结果只适用于固定 toy worlds、提示和所列模型，不外推至所有 Agent 或真实长期部署。没有查论文、使用 Mem0、设计新方法或执行 Idea 3。
