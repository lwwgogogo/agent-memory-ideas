# Stage-6A 实验结果
W1 echo K=1→20 support 增长20倍、D=0、NO_EFFECTIVE_POLICY_DIVERSITY、DESCRIPTIVE。W2 signs +,-,+,-，D=.60，Cconflict=1，PROVISIONAL/POLICY_CONDITIONED。W3 signs +,+,+，D=.60，Cpos=1、Cconflict=0、PRESCRIPTIVE，真值 A=4/5,B=2/5。W4 与W3同为3 era，Dfalse=1/30,Dtrue=.60,ratio=18，W4不晋升。M1 echo/diverse 均 A=.8,B=.4,gap=.4，但 lifecycle 不同。
限制：synthetic discrete states、exact counts、eras 已知；无自动policy-change detection、自然语言 parsing、full-agent integration、finite-sample variance、continuous state；阈值为 research probe；未证 novelty、lineage independence、long-run stability。

## 最终 Gate 审计补充
运行器将 G5 直接设为 true，且合并了造数与评估路径；因此无法由这次实现证明候选执行严格满足无 oracle 输入边界。G5 记 FAIL，最终 verdict 为 CROSS_POLICY_CERT_NARROW。其余数值结果保留为本次 deterministic run 的描述性输出；不把它升级为完整的 oracle-free candidate 验证。正式运行没有重启，阈值和数据未更改。
