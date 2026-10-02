# Provenance Identifiability under Lossy Agent Memory Transformations

本目录是一个独立的 Problem Validation 实验，不是 Method Development。

本阶段只研究：当 evidence 经过 summary、merge、rewrite 等有损 memory transformation，且系统没有完整 lineage 时，claim 的真实 support set 是否仍然可以从当前 observation 中识别。

本实验不研究 generic provenance logging、memory parent id、dependency graph、semantic taint tracking、普通 claim-to-source attribution 或 rollback/repair。Idea 1 仍为 NO-GO，Candidate 01 仍为 NOVELTY_NO_GO，旧实验代码和输出不修改。

执行入口：`src/run.py`。正式运行前先执行 `tests/test_core.py`。
