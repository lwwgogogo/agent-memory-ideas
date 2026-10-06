# Stage-6C 预注册
日期2026-10-06；唯一远程工作区；基线c9bbb744a3200461728c5959469f86f3e13a32d7。十个历史目录和所有verdict冻结。无网络论文检索、LLM、Ollama、provider、训练、benchmark或原生agent运行。

## 固定数据
两个state，每个source era每state1000 action观测，每target每state1000。所有source cell成功计数严格为A exposure×4/5、B exposure×2/5，不采样；target只有state/action，无outcome。匿名era格式e000。
P1/P2/P3 source相同：(.20,.20),(.80,.20),(.50,.80)；target分别(.50,.40)/(.50,.95)。
P4 target固定(.50,.50)；IN source(.30,.40),(.70,.40),(.50,.70)；OUT source(.30,.50),(.10,.90),(.10,.10)。
共四paired records、八case，不扩样本、不扫种子。P2/P3复用P1，不当作统计独立重复。expected geometry由独立exact rational evaluator校验，不输入candidate。

## 固定方法与隔离
直接复用Stage6A.1冻结candidate函数及public_config；正式另调用其原始CLI核对全部scientific fields，不重实现认证。
descriptor由observations分组计数恢复。source schema仅era_id/state/action/outcome；target仅state/action；多余、缺失、重复JSON字段、非法值一律拒绝。每state计数必须1000。
candidate只在临时匿名目录执行，代码/观测/冻结公开config以外的实验文件不可读；无case名、private label、generator参数或target outcome。记录复制hash、参数、环境、读路径和顺序；隔离审计只针对本candidate路径，不宣称恶意代码OS sandbox。
支持dominant source conclusion的descriptor形成凸包；membership使用scipy.optimize.linprog(method="highs")，λ≥0，sum=1，二维重建等式。HiGHS primal/dual feasibility容差和重建最大残差固定1e-10。不可行给outside，其他solver failure停止；不可把数值失败当outside。
全局非PRESCRIPTIVE→GLOBAL_NOT_CERTIFIED；否则inside→TRANSFERABLE，outside→OUT_OF_ENVELOPE。无额外阈值。nearest TV=0.5×L1，P4相等阈值1e-12，同时用Fraction验证精确相等。凸权重/maxλ/entropy仅diagnostic，不进decision。D2距离可省略，不引入额外solver或decision。

## 基线
B0原冻结global status；B1仅source sign pattern/C_pos/C_conflict，有一致非零方向且conflict=0允许。B2不任意设阈值：保存完整source summary的canonical JSON/SHA，包括M1双utility/gap、total/per-era counts、gap mean/variance/min/max、C_pos/C_neg/C_conflict、D_policy、era数、有效不同pair数、global status。B2输出信息签名，证明任何只依赖该信息的函数均不能区分相同输入。
B3固定VERIFIED_RUNTIME_TRACE、相同trust/validation/lineage placeholder及era count，保存SHA；这些是受控baseline标记，不是candidate的真值输入。B4保存nearest scalar，无人为阈值；B5用逐state cell率、1/2标准化，Fraction严格验证4/5、2/5、2/5。

## G0–G9
G0：整数outcome率、每state1000、两descriptor来自counts、schema符合。
G1：全部source原冻结CLI与复用函数逐字段相同，均PRESCRIPTIVE，历史config不变。
G2：P1 source SHA、global、invariance、M1相同而target decision按独立geometry产生IN/OUT。
G3：P2 source/provenance SHA及source-only status相同，transfer不同。
G4：P3完整summary SHA和要求分量相同，transfer不同。
G5：P4 nearest相等≤1e-12且Fraction相等，membership/transfer不同，两global均PRESCRIPTIVE。
G6：全部M1 exact=.8/.4/.4，P1/P3 decision变化。
G7：target严格schema拒绝额外字段，candidate执行文件/环境/读取隔离和code审计通过；无target outcome。
G8：P1/P3 source完全相同和完整summary相同，decision不同，只推断source-only不能重建。
G9：报告明确convex hull仅probe，inside非causal safety，outside非必然失败，不声称方法创新；独立scope checklist记录。

## 测试、锁定与verdict
正式前至少28项测试，含用户指定schema、exact count、geometry、旧输入等价、配对关系、隔离、确定性、gate边界和历史哈希检测。测试包括P4手工坐标先验验证。之后锁定本文件、全部scientific Python、tests、public config及历史candidate引用hash。正式运行一次，started标记禁止覆盖。若正式后科学bug，停止并如实记录restart，修复后重新tests/lock；不调阈值救结果。
GO仅当G0–G9全部通过。NO_GO：无有效matched反例、被source-only/nearest投影完全重建、或必须target outcome；其余部分成立/完整性不足为NARROW。oracle boundary失败不计为GO，不自动设计补救新方法。
本轮结论仅为target-relative matched反例，下一步只能建议精确collision audit，本轮不执行。
