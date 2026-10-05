# Idea 2 Stage-2: Causal Sufficiency of Experience Memory

This directory is an independent Stage-2 run. It does not edit Idea 2 Run 1 or the 2026-10-05 confirmatory replication.

Phase A exhaustively searches integer two-state/two-action experience tables and saves 20 matched-world pairs. The pairs share exact aggregate action-success statistics while having opposite exact target-policy optimal actions. Phase B uses the same underlying X,A,Y data within each world and changes only the memory representation.

Formal conditions are RawEpisodic (secondary), StatePreservingSummary (R1), FaithfulLossySummary (R2), CausalSufficientCompact (R3), and LengthMatchedControl (R4). The frozen protocol uses qwq:32b, temperature 0, seed 20261005, strict two-field JSON, two deterministic memory orders, and AB/BA label swaps.

The final pre-registered verdict is CAUSAL_SUFFICIENCY_WEAK. Phase A and the representation-level matched-pair impossibility pass. R1/R3 are directionally better than R2 but the model behavior does not meet the pre-registered high-accuracy, bootstrap, regret, and control gates. Formal calls are complete and stopped.

Key files:
- preregistration.md
- results/matched_worlds.csv
- results/identifiability_checks.json
- cases/cases.json
- results/raw_outputs.jsonl
- results/statistics.json
- Confirmatory结果.md
- 最终结论.md

No literature search, Mem0 use, method design, or Idea 3 work was performed.

