# Idea 2 Stage-8C1: JitRL native retrieval path audit

只回答：真实 JitRL 已写入 memory，为什么 retrieval 返回 0。

不重跑 Stage-8C，不改 threshold，不改 `third_party/jitrl`。Stage-8C verdict `REAL_JITRL_FAILURE_NO_GO` 保留。

```bash
conda run -n jitrl_runtime python idea_validation/idea2_jitrl_retrieval_audit/verify.py
conda run -n jitrl_runtime python -m pytest idea_validation/idea2_jitrl_retrieval_audit/tests -q
```

Verdict：`RETRIEVAL_INFRA_BLOCKED`。详见 `retrieval_mapping.md`。
