# Idea 2 Stage-4：Policy-Conditioned Experience Memory Audit

本目录审计经验记忆中的行为策略选择效应。研究问题是：经验记忆提供的是带有行为策略条件的证据，而非天然与策略无关的知识。

执行入口：`preregistration.md`、`discover_repos.py`、`static_audit.py`、`build_synthetic_logs.py`、`run_dynamic_audit.py`、`evaluate.py`。外部代码仅临时放在被忽略的 `third_party/` 下，不会提交。

状态标签严格区分论文机制证据、官方源码证据和真实动态调用等级。无法运行、依赖阻塞、缺少机制及动态失败不会相互替代。历史 Idea 2 结果目录只读。
