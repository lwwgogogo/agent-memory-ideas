# Stage-4 实验结果

## 设计与执行

本阶段固定六个目标系统，五个官方仓库成功 clone，另一个 Memento 记录为 `OFFICIAL_CODE_NOT_FOUND`。第三方源代码只读，均在 gitignored `third_party/`。预注册 SHA-256 锁存于 `results/preregistration_lock.json`。合成日志在固定随机种子下生成，P/Q 条件每组 2000 条，BAL 每个 state-action cell 等额曝光。真实 outcome 对 action 无因果差异；变化来自 behavior-policy exposure。propensity 只提供给 oracle 基线，不传入原生选择器。

运行了 JitRL 的原生 episode top-k ranker 与 MemRL 的原生 QValueUpdater/ValueAwareSelector。该结果是两个真实开源实现中被隔离的原生组件在固定合成记忆条目上的动态最小测试，属于 L2 组件证据；没有调用完整 agent、LLM、embedding recall 或环境循环。

## 结果

| 系统组件 | PSI | RCD | PIUR | BAL gap reduction | State-matched query |
|---|---:|---:|---:|---:|---|
| JitRL episode ranker | 1.247 | 0.600 | 1 | 0.978 | 原生 helper 不接收 state，UNSUPPORTED |
| MemRL value selector | 0.249 | 0.600 | 1 | 0.978 | selector 不接收 state，UNSUPPORTED |

P 与 Q 下两组件的 action-score preference 均相反，方向与日志中 action exposure 的反转一致；BAL 后差异近乎消失。JitRL PSI 更大，来自 top-k final_score ranker；MemRL PSI 反映 Q 更新与排序的较小但可逆偏好变化。不得将该数值解释为完整系统任务表现。

State-matched effect 没有可估计值，因为两个被测原生 query/selector 接口不接收 state。JitRL 的另一条全系统检索路径确实结合 current state/history embedding，但没有运行，因此不能据此主张 state-aware retrieval 会保留偏差，也不能声称已证实它消除偏差。

## 静态机制与动态一致性

代码审计中五个可 clone 的仓库均未找到 behavior-policy identity、action propensity 或显式 exposure correction；JitRL 和 MemRL 动态组件表现出 policy-sensitive utility/ranking。ExpeL、Reflexion、ReasoningBank 的经验压缩/反思路径静态符合 blind-spot 条件，但本轮未执行完整动态测试。详细静态证据与动态边界见 `SYSTEM_AUDIT.md` 和机器可读 JSON。

## Gate

预注册门槛：G0 PASS，G1 PASS（5/5 code-audited systems），G2 PASS（5 个 L1+、2 个 L2），G3 PASS（两个原生组件政策方向一致），G4 PASS（两个组件 BAL reduction 约 97.8%），G5 收窄解释，G6 PASS（0/5 显式曝光校正）。`POLICY_MEMORY_GO` 仅支持“这些原生排序/价值选择组件在 aggregate experience utility 下存在 policy-conditioned sensitivity”；不推广到全 agent，也不覆盖 state-matched 结果。
