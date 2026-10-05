# Idea 2 Stage-2: Causal Sufficiency of Experience Memory

CAUSAL_SUFFICIENCY_WEAK

## Phase A

The exhaustive integer search produced 20 matched pairs (40 worlds). Each pair has identical aggregate action exposure/success counts, different state-conditioned counts, and exact opposite optimal target-policy actions. All checks use integer counts and Fraction arithmetic.

## Formal run

Planned 800; valid 800; retried 0; invalid 0; complete worlds 40/40. Model qwq:32b, Python 3.10.21, fixed temperature 0 and seed 20261005. R0 is secondary; the hard gates use R1-R4.

| Representation | Accuracy | Regret | Signed preference error |
|---|---:|---:|---:|
| R1 StatePreservingSummary | 0.643750 | 0.074479 | 0.017169 |
| R2 FaithfulLossySummary | 0.500000 | 0.102083 | -0.001111 |
| R3 CausalSufficientCompact | 0.631250 | 0.077604 | 0.026743 |
| R4 LengthMatchedControl | 0.562500 | 0.096701 | 0.025138 |

## Matched-pair impossibility

All 80 FaithfulLossySummary prompts (20 pairs x 2 labels x 2 orders) are byte-identical within each pair while the exact optimal actions are opposite. This is a representation-level non-identifiability result; it does not depend on a particular model error.

## Controls

R2/R4 length equality: True; R1/R3 label and order slices and R4 are recorded in statistics.json. Raw episodic records are secondary and are excluded from the hard verdict.

## Gates

| Gate | Result |
|---|---|
| PhaseA_identifiability | PASS |
| G0_valid_and_complete | PASS |
| G1_R1_high_accuracy_low_regret | FAIL |
| G2_R2_low_accuracy_high_regret | PASS |
| G3_R3_recovery | FAIL |
| G4_R1_vs_R2_accuracy_bootstrap | FAIL |
| G5_R3_vs_R2_accuracy_bootstrap | FAIL |
| G6_regret_improvements | FAIL |
| G7_representation_impossibility | PASS |
| G8_label_order_length_controls | FAIL |

The R2 summaries are factual aggregate counts generated from the same world data; they do not contain evaluative or causal wording. R1, R3, and R4 are also factual mechanically generated counts.

Run 1 remains IDEA2_RUN1_NO_GO / IDEA2_NO_GO and its files and result are unchanged. This Stage-2 result is limited to the fixed model, protocol, and toy worlds; it is not a literature or real-world Agent generalization claim.

No literature search, Mem0, method design, or Idea 3 work was performed. Formal inference is stopped.
