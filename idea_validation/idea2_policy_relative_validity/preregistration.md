# Stage-7 预注册
日期：2026-10-07。基线commit：6e2c8d1a7433e133170fcf0ebbe99ca2cb410f63。历史Stage-1至Stage-6C全部只读。本轮不查论文、不调用LLM/Ollama/API、不运行真实agent pipeline。

## 固定MDP
折扣γ=1，五状态：s0、s1、terminal_safe、terminal_good、terminal_bad。确定性转移/奖励：
s0,a_L→s1,0；s0,a_R→terminal_safe,+1；s1,a_R→terminal_good,+2；s1,a_L→terminal_bad,−2。terminal无动作。
pi_A：s0选a_L，s1选a_R。pi_B：s0选a_R，s1选a_L。环境对象和fingerprint不随policy变化。
由exact DP计算：Q^piA(s0,a_L)=+2，Q^piB(s0,a_L)=−2；Q^piB(s0,a_R)=+1。MC不进入主结论。

## 固定memory
pi_A先生成成功trajectory。memory字段固定为state、action、observed_return、source_policy、trajectory_id、generation_step；m0=(s0,a_L,+2,pi_A,traj_A_000,0)。
B0 NoMemory；B1同state直接复用；B2 observed_return>0即接受（MemRL-like simplified，不是复现）；B3把observed_return作为对当前动作分数的加性bias（JitRL-style simplified，不是复现）；B4用真实target-policy Q拒绝负Q推荐，仅oracle；B5 source_policy与target_policy不等即拒绝，仅provenance heuristic。

## F1/F2
F1固定同一m0、state和action，仅从pi_A切到pi_B continuation，PASS当且仅当Q_source>0且Q_target<0。
F2每个baseline在pi_B下运行20个完全相同的deterministic episodes，不伪造独立样本或显著性。target optimal return固定+1；regret=1−episode return。harmful use由独立evaluator按Q^piB(m.action)<0判定，不提供给B0–B3。PASS要求B1/B2/B3至少一个接受m0、return低于B0且产生正regret/harmful-use；B4减少harmful use和regret。另运行pi_A same-policy控制。

## F3闭环
使用共享动作偏好θ和state-specific base score：score_L(s0)=1+θ、score_R(s0)=0；score_L(s1)=−1+θ、score_R(s1)=0；平局取a_R。θ=0即pi_A。接受正历史return的a_L memory时，固定更新θ←θ+observed_return，因此首次复用m0后θ=2，即pi_B continuation。
每轮在s0检索同state且observed_return最大的memory（平局按最早），复用前后分别exact计算m0的target-conditioned Q；随后执行memory动作与更新后的continuation，写入新s0 trajectory memory。负新memory不会覆盖m0的最高历史utility。固定6 iterations，不加world、不造振荡。
F3 PASS要求：m0在θ=0有效；实际memory use令θ改变；Q从正变负且至少一次validity flip；trajectory写回使M_t增长；后续仍检索m0并产生harmful reuse。该构造是最小共享动作偏好机制，不声称真实LLM必然如此。

## 指标与Gate
保存Q_source/Q_target、average_return、cumulative_regret、harmful_memory_use_rate、memory_acceptance_rate、validity_flip_count及θ/action preference trace。
G0：exact环境、无B0–B3 oracle leakage、历史hash一致、lock一致。
G1：F1严格正负反转。
G2：F2 naive历史memory产生可重复退化。
G3：pi_A same-policy下m0 Q>0、接受后return>0。
G4：oracle相对naive降低harmful reuse与regret；B5作为可选控制报告。
G5：F3存在memory use→θ/policy change→m0 target-Q变化，并至少一次validity flip、memory写回。
G6：报告明确policy-dependent Q是经典RL事实；额外验证对象仅为self-generated memory既是旧policy产物又是未来policy干预变量的闭环。若F3只有静态pi_A→pi_B mismatch则FAIL。

GO要求G0–G6全PASS及F1/F2/F3成立。F1/F2成立但F3弱或仅静态mismatch为NARROW。无法干净反转、无meaningful degradation、或本质只有普通value mismatch为NO_GO。formal run后不改Gate或world；bug需停止、修复、重测、重锁、重跑并记录restart。
