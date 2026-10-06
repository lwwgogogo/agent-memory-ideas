# Stage-6C 实验结果

## 背景与对象
Stage-6B保持STAGE6B_NARROW。U1为漂移/不变性化约，U2为已有使用门控替换证据，U3为证据感知confidence/support化约。本轮从C(m)改为C(m,b*)，只测试固定信息投影的可区分性，未消除所有target-aware近邻风险。

## 输入、认证与probe
source只含era_id/state/action/outcome，target只含state/action。每state1000计数恢复二维descriptor；不输入构造参数。复用冻结Stage6A.1代码，并与原CLI逐字段比较。PRESCRIPTIVE之后用HiGHS等式可行性判断凸支持，残差1e-10；独立Fraction仿射消元枚举最多3顶点核验geometry。

## 配对结果
| Pair | Side | Target | Global | Nearest TV | Hull | Transfer |
|---|---|---|---|---|---|---|
| P1 | IN | ['1/2', '2/5'] | PRESCRIPTIVE | 1/5 | True | TRANSFERABLE |
| P1 | OUT | ['1/2', '19/20'] | PRESCRIPTIVE | 3/40 | False | OUT_OF_ENVELOPE |
| P2 | IN | ['1/2', '2/5'] | PRESCRIPTIVE | 1/5 | True | TRANSFERABLE |
| P2 | OUT | ['1/2', '19/20'] | PRESCRIPTIVE | 3/40 | False | OUT_OF_ENVELOPE |
| P3 | IN | ['1/2', '2/5'] | PRESCRIPTIVE | 1/5 | True | TRANSFERABLE |
| P3 | OUT | ['1/2', '19/20'] | PRESCRIPTIVE | 3/40 | False | OUT_OF_ENVELOPE |
| P4 | IN | ['1/2', '1/2'] | PRESCRIPTIVE | 1/10 | True | TRANSFERABLE |
| P4 | OUT | ['1/2', '1/2'] | PRESCRIPTIVE | 1/10 | False | OUT_OF_ENVELOPE |

## P1：invariance reduction
相同source SHA、global和M1，target位置不同。B0/B1不读取target，所以相同；probe的IN/OUT不同。
## P2：provenance reduction
固定source provenance SHA相同，probe不同。只排除source-only provenance，不排除target-aware扩展。
## P3：confidence/support reduction
完整source summary及SHA相同：utility/counts/variance/agreement/diversity/global均相同。任何f(S_source)无法区分；不声称所有target-aware uncertainty都不行。
## P4：nearest-distance reduction
两个source set围绕同一target的布局不同。最近TV均为1/10且独立rational验证相等，而凸包成员关系不同。排除nearest-scalar-only规则，不排除完整几何方法。
## M1比较与逻辑边界
所有case逐state标准化得到U(A)=4/5、U(B)=2/5、gap=2/5。M1没有估错；当前不同标签来自支持几何定义。P1/P2/P3重用相同数值，不是三个独立统计重复；不计算p值或假装样本扩张。
## G0–G9
| Gate | Result |
|---|---|
| G0 | PASS |
| G1 | PASS |
| G2 | PASS |
| G3 | PASS |
| G4 | PASS |
| G5 | PASS |
| G6 | PASS |
| G7 | PASS |
| G8 | PASS |
| G9 | PASS |

## 解释纪律
本轮只构造 target-relative matched counterexamples，表明 global/source-only evidence summary 不足以表达当前 probe 的 transfer decision。
Convex hull 是 minimal diagnostic probe，不证明其最佳或方法新颖性。
Inside hull 不意味着 causal safety；outside hull 不意味着一定不能 transfer。
本轮 invariant world 中 OUT 的真实 utility gap 也为 +.40；没有验证实际迁移失败或安全收益。
不排除 target-aware uncertainty、provenance、boundary-aware reuse、ICP/OPE 或 support geometry 方法表达同类决策。

## 局限
synthetic discrete states；exact counts；known source eras；假设target已有最近trace；观测descriptor不等于真实future policy distribution；无finite-sample noise；无natural-language memory；无automatic era detection；无full-agent integration；无dynamic memory-policy feedback；无method novelty claim；尚未重新审计transportability/support geometry文献。

## Verdict
TARGET_RELATIVE_ENVELOPE_GO

## 下一步与停止
若GO，仅建议针对target-relative transportability、support geometry、multi-logger OPE、boundary-aware reuse和target-aware gating做精确collision audit。本轮不自动查论文，不进入Stage7。

## 执行与验证

45项测试在锁定前通过，包括11个历史固定输入的原CLI输出复核。正式运行1次、restart=false，共8个target candidate进程及8次原global CLI调用。全部paired约束、独立有理数geometry、锁定SHA和2074个历史文件/链接核验通过。四张图已人工检查。预注册SHA：fab608426f42d8a4b366af605b797ef53d8e96df8e77a42f64816265e07cb330。
