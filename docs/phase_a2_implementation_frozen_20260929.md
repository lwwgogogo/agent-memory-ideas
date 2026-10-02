# A.2 实现细节冻结

不改变phase_a1_a2_plan.md的5个变化场景、T3000、burn-in100、start在[900,1500]离散均匀、污染100步、validation200–219、test300–339。Q/R过程不因方法结果调整。仅在D1/D2完成且D1满足stationary门槛后运行。

未指定细节在A2任何validation/test运行前固定如下：

- 四个stationary control匹配已规定场景端点：(Q,R)=(.005,.2),(.15,.2),(.01,.05),(.01,.35)。
- 原固定17个候选不变；原49模型BMA、Dense stationary BMA均保留。Forgetting-BMA和Sliding-window BMA采用相同Dense网格，避免自适应对照被粗网格人为削弱。
- Forgetting候选rho=.95/.99/.995/.999；每步model权重乘方衰减并混回原先验（log空间线性组合），不重置每个模型的state posterior。这是heuristic，不是精确非平稳Bayes。
- Window候选50/200/500。精确计算最近W条观测的HMM参数/状态后验，在窗口开始处重设uniform state/parameter prior；通过可结合的两栈矩阵乘积实现，不把使用全历史state的近似叫作window。测试与逐窗口从头过滤数值一致。
- 验证集对全部9场景等权平均accuracy，每个family选一个全局配置，全部候选再选一个best deployable。测试时使用同一配置，不根据真实场景/变化类型切换方法。ties按候选顺序。
- Q increase/decrease算同一个类型，R同理，corruption单独一类；防止同一变化的两个方向凑足两类。
- GO要求两类中至少一个方向达到Oracle全程accuracy gap>=2pp，且变化后50/100/300三个固定窗口error点估计均改善。全部CI同时展示，不把这些门槛声称为多重比较显著性标准。
- 原计划“control不明显退化”未给数字；这里操作化为best deployable相对fixed或Dense stationary任一对照，在任一control下降>1pp且paired CI下界>0视为明显退化。此定义在A2运行前固定并独立报告，若结论依赖此定义应标注敏感性。
- Recovery计数为首次完成连续10步正确时的可观察延迟，最小10步；未满足封顶并标删失。Corruption期间的恢复搜索止于污染结束，另单报污染结束后的恢复；Q/R其他变化止于轨迹结束。
- Error@50/100/300均为从变化时刻开始的前N步错误率；corruption的300步窗口跨污染与恢复段，另单报100步污染和恢复后100步/剩余全段error。
- Useful-memory retention仅为state proxy：污染前预测正确、旧truth连续保持不变的恢复后前100步中，预测仍正确的比例。保存eligible分母，缺失为missing；没有真实memory对象，不声称测量真实记忆保留。
- 事件对齐曲线为25步区间seed平均error/Brier（前400到后800），无平滑和选择性裁剪；controls名义对齐1200仅供画图，不作为模型输入。

4个CPU worker，BLAS线程1，无GPU/API。每run独立保存开始时source snapshot与hash、配置、环境、验证选择记录和原始指标；停止条件不会触发额外方法设计。
