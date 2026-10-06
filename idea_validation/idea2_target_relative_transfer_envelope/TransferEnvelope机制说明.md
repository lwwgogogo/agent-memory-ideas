# Transfer Envelope 机制说明
该probe回答“目标行为descriptor是否属于历史支持的凸组合”，不回答“目标下动作是否真实安全”。

1. Source逐条era/state/action/outcome恢复b_k=(P_hat(A|S0),P_hat(A|S1))；target仅state/action恢复b*，两者每state1000观测。
2. 使用冻结Stage6A.1认证函数，正式与原public CLI逐字段一致。该部分不读取target。
3. 仅选支持dominant memory conclusion的source descriptors；若global非PRESCRIPTIVE，返回GLOBAL_NOT_CERTIFIED。
4. 在λ≥0、Σλ=1、Σλb_k=b*约束下以HiGHS求可行性。残差1e-10；可行TRANSFERABLE，不可行OUT_OF_ENVELOPE。solver异常不当作outside。
5. nearest TV与λ集中度/entropy仅诊断，不影响决定。

source-only summary匹配论证排除相应信息投影的所有函数，而不是故意选择弱confidence阈值。B2/B4不设置阈值，输出完整信息签名/精确标量供比较；不伪造ALLOW/BLOCK。
独立evaluator用Fraction消元枚举≤3个source点验证成员关系。候选不读取生成参数、私有case标签或expected decision；文件名与进程输入匿名，字段白名单拒绝target outcome。

convex hull只是minimal diagnostic probe；interpolation不等于causal validity，extrapolation不等于失败。本world所有target的真实A/B utility始终.8/.4，因此不同transfer标签不是不同真实effect。这一实验说明source-only表示无法表达定义的target-relative支持决策，不证明最终方法创新或跨策略运输保证。
