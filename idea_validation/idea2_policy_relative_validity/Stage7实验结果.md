# Stage-7 实验结果

## 研究问题
同一条pi_A成功memory，在state/action、环境和奖励不变时，能否因continuation policy变化而由有益变有害；memory能否参与造成该policy变化。

## MDP与exact Q
五状态确定性MDP。s0,a_L先到s1且reward=0；pi_A随后a_R得+2，pi_B随后a_L得−2。因此exact DP给出Q^pi_A(s0,a_L)=+2，Q^pi_B(s0,a_L)=−2。s0,a_R固定安全回报+1。环境fingerprint在实验前后一致。

## F1：policy-relative reversal
PASS。同一m0=(s0,a_L,+2,pi_A,traj_A_000,0)，只替换continuation policy，Q从+2变为−2。

## F2：historical-success trap
PASS。pi_B下B0回报+1、regret=0；B1/B2/B3均接受历史成功m0并选择a_L，回报−2，20轮累计regret=60，harmful-use rate=1。B4 oracle与B5 provenance-only拒绝，回报+1、regret=0。B2/B3只是简化探针，不是MemRL/JitRL复现。

## F3：endogenous self-invalidation
PASS。共享a_L偏好θ初始0，对应pi_A continuation。首次复用m0将θ由0更新为2，s1 continuation由a_R变a_L；m0的exact target-Q在同一iteration由+2变−2，发生1次validity flip。负回报trajectory写回使bank从1增至7，但按最高历史utility检索仍反复选m0并产生−2回报。这是显式M_t→pi_t→trajectory_t→M_(t+1)闭环，不是仅静态pi_A数据对pi_B估值。

## Controls
same-policy pi_A下所有memory baseline回报为+2，m0保持正Q。pi_B下oracle与provenance-only均拒绝跨policy m0并得到+1；provenance-only只是naive diagnostic，不能视为最终方法。

## Gates
| Gate | Result |
|---|---|
| G0 | PASS |
| G1 | PASS |
| G2 | PASS |
| G3 | PASS |
| G4 | PASS |
| G5 | PASS |
| G6 | PASS |

## 与经典policy-dependent value/OPE的区别
policy-dependent Q本身是经典RL事实；额外对象是self-generated memory既是旧policy产物，又成为改变未来policy的干预变量。这里具体构造的是：m0由pi_A生成并带provenance；m0被复用后作为干预变量更新共享动作偏好，改变continuation；改变后的policy又使m0自身Q变负；naive bank继续因旧utility复用它。该闭环是本轮最小验证对象。它没有提出新的RL/OPE理论，也没有证明现实Agent Memory系统必然出现。

## Limitations
toy deterministic MDP；共享动作偏好更新是人为固定的最小机制；无真实LLM agent；B2/B3是simplified MemRL/JitRL-like baseline；无自然语言memory、大benchmark、finite-sample noise或真实系统集成；没有证明novelty、普遍性或任何官方系统一定发生；只验证最小机制。

## Verdict
**POLICY_RELATIVE_VALIDITY_GO**

最小policy-relative memory validity与endogenous feedback现象成立。下一步可以进入真实Agent Memory系统映射验证；本轮停止，不自动执行。
