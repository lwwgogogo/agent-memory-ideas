# Method候选比较

本轮选择 **M1**；判定 **METHOD_VIABILITY_GO**。比较基于全部固定world/Gate，不按单个最好结果。

| 方法 | 输入与统计核心 | 实际可行性边界 | 是否候选 |
|---|---|---|---|
| M1 | observed state/action/outcome + rho；direct standardization | exact离散已识别state下去exposure bias、保留真实gap、完成crossover；需positivity | 是，本轮优先 |
| M2 | bank counts估计propensity，alpha=1，clip=.05，全局SNIPS | 能纠正常规均匀target的多数bias；忽略rho使crossover失败，.99 clipping留bias | 是，但当前固定版本未过全部Gate |
| M3 | 真propensity + target rho/P_logged(x) | oracle classical diagnostic，不能作为创新方法 | **ORACLE / NOT CANDIDATE METHOD** |
| M4 | Jeffreys(.5,.5) shrinkage + rho | 常规support下保留signal/crossover，但收缩偏差依赖cell exposure | 是，次于M1的exact结果 |

| 方法 | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 |
|---|---|---|---|---|---|---|---|---|---|
| M1 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| M2 | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | PASS | PASS |
| M4 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |


M1与经典standardization/g-computation一致，不声明novelty；后续仍需方法新颖性/差异化审计。两adapter输入一致仅在本轮已标注synthetic native objects成立，不推及自动state抽取、复杂轨迹、多步Q或完整semantic retrieval。Exact counts不能比较采样方差或证明shrinkage在现实任务的优劣。
