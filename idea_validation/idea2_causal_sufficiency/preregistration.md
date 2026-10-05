# Idea 2 Stage-2 preregistration: Causal Sufficiency of Experience Memory

This is an independent Stage-2 evaluation in a new directory. It does not modify Idea 2 Run 1 or its confirmatory replication. No literature search, Mem0, method design, or Idea 3 work is part of this run.

## Phase A: representation identifiability

A deterministic exhaustive integer search enumerates two-state, two-action experience tables. The target policy samples S0 and S1 with weights 1/2 and intervenes on one fixed action independently of state. For each matched pair, g_lossy is the exact integer tuple of aggregate exposure and success totals for A and B. g_preserve is the four state-action exposure/success cells. A pair is retained only when its lossy tuples are identical, its state-preserving tables differ, and exact Fraction arithmetic gives strict opposite optimal actions with absolute value difference at least 1/20. At least 20 pairs are required before Phase B.

All summary numbers are generated from the integer cells. Target causal value is (success_S0/n_S0 + success_S1/n_S1)/2; the comparison is exact rational arithmetic, with floating values emitted only as a display field.

## Phase B: same data, different representations

The fixed dataset for each world is the same deterministic set of X,A,Y records. Only the memory representation changes.

- R0 RawEpisodic: every observed (state, action, outcome) record; secondary diagnostic only.
- R1 StatePreservingSummary: per-state, per-action exposure, success, and failure counts.
- R2 FaithfulLossySummary: per-action aggregate exposure, success, and failure counts only. It contains no state structure and no causal or evaluative wording.
- R3 CausalSufficientCompact: compact per-state, per-action success/exposure counts.
- R4 LengthMatchedControl: per-state, per-action factual counts in a different compact syntax, padded to exactly the same 256-character width as R2. It retains state structure and controls representation length.

R1, R2, R3, and R4 are mechanically rendered from the same integer data. Prompts use neutral wording, fixed state weights, and no world or pair identifier. Two deterministic memory orders (O1/O2) and A/B-to-Left/Right label maps (AB/BA) are crossed for every world and condition.

## Frozen model protocol

Model qwq:32b, Ollama endpoint /api/chat, temperature 0, top_p 1, seed 20261005, num_ctx 4096, num_predict 128. The system message requests only JSON fields p_success_left and p_success_right; the strict schema has exactly those two numeric fields with bounds [0,1]. A malformed or out-of-range response gets at most one retry with identical prompt, model, options, and schema. Transport errors are not reissued. The durable journal records started and completed events.

There are 20 matched pairs, 40 worlds, 5 representations, 2 label maps, and 2 memory orders: 800 planned formal calls. A format-only capability probe is recorded separately and excluded.

## Offline metrics

The parsed probabilities are mapped back to canonical A/B according to the label map. For each world and representation, Decision Accuracy is whether the sign of predicted A-minus-B matches the exact target-policy OptimalAction (ties choose A only if a tie occurs; retained worlds are strict). Action Value Regret is target-policy value of the optimal action minus the value of the predicted action. Signed Preference Error is (predicted A-minus-B) - (true target value A-minus-B). World-level summaries average the four label/order views.

## Frozen gates

The representation-level gate must first pass: Phase A has at least 20 pairs, every pair has identical integer g_lossy, different g_preserve, strict opposite optimal actions, and exact Fraction checks.

For formal calls, all 800 are expected valid; at least 99% validity and all 40 worlds complete are required. The primary behavior gates are:

1. R1 accuracy >= 0.85 and mean regret <= 0.05.
2. R2 accuracy <= 0.65 and mean regret >= 0.10.
3. R3 accuracy >= 0.85 and mean regret <= 0.05.
4. Paired bootstrap (10,000 resamples, default_rng seed 20261005) lower 95% CI for R1-minus-R2 accuracy > 0.05.
5. Paired bootstrap lower 95% CI for R3-minus-R2 accuracy > 0.05.
6. Both R1-minus-R2 and R3-minus-R2 mean regret differences are >= 0.05.
7. R2 matched-pair prompts are byte-identical for each label/order while the target optimal actions are opposite, establishing representation-level non-identifiability independent of model behavior.
8. Label/order controls: R1 and R3 accuracy are at least 0.75 in each label and order slice, with maximum within-condition slice spread <= 0.25. R4 accuracy is at least 0.75 and its accuracy is within 0.15 of R3. R2 and R4 memory strings have equal character length for every world/label/order cell.

Raw Episodic is reported but never enters a hard GO gate. The final verdict is CAUSAL_SUFFICIENCY_GO only when all gates pass; otherwise CAUSAL_SUFFICIENCY_WEAK is used when Phase A and the matched-pair impossibility pass but at least one behavioral/control gate fails while R1/R3 remain directionally better than R2; all other outcomes are CAUSAL_SUFFICIENCY_NO_GO.

No prompt, model, seed, sample size, or representation is changed after formal inference begins.

