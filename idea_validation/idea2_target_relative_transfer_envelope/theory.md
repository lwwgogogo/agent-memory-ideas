# Target-relative Transfer Envelope 的对象与边界
历史Cert_global(m)只由source evidence决定。本轮probe为C(m,b*)：首先要求原有全局认证为PRESCRIPTIVE，再判断从target观察计数恢复的二维行为descriptor是否在支持dominant conclusion的source descriptors凸包内。λ≥0、Σλ=1、Σλb=b*是线性可行性条件，使用HiGHS，重建残差≤1e-10；没有额外utility/confidence/distance阈值。

同一个source输入可搭配不同target trace。对于相同S_source，任何确定性f(S_source)必然输出相同；随机规则的条件输出分布也相同。因此若定义的target-relative支持决策不同，它不能仅由source summary表达。这是信息可区分性论证，不是独立于probe定义的性能优势。P1/P2/P3使用同一组数值，各自检验不同信息投影，不能计作三次独立实验重复。

B4只保留到最近source的TV标量。存在最近距离相同但凸包成员关系不同的source集合，所以单个最近距离阈值不能重建所有这类支持判定；不排除使用完整target-aware几何或不确定性的已有方法。

本轮world在两个state中A成功率均4/5，B均2/5。因而OUT也真实具有+.40 utility gap，没有构造OUT的实际迁移失败。TRANSFERABLE仅是“通过该凸支持probe”的标签，不是安全保证；OUT_OF_ENVELOPE仅代表该probe不支持外推，不是真实不能迁移。convex hull是成熟几何对象，不主张其创新、最优性、causal transportability、优于ICP/OPE或最终方法新颖性。
