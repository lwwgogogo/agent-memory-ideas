# JitRL Native Mechanism Mapping

## Source integrity

- Existing project-local upstream checkout: `idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl`
- Remote: `https://github.com/liushiliushi/JitRL.git`
- Commit: `143d22185d95fbf633a0befe6861d5e8b732543b`
- Primary audited path: WebArena implementation.
- Audited tracked files have no Git diff.
- Pre-existing untracked `Jericho/src/__pycache__/*.pyc` files were observed before Stage-8; they are not source and are not used or changed by this stage.

## Native chain

### M1 — Memory unit

The durable episode object is created by
`WebArena/memory_agents/utils/cross_episode_memory.py:add_episode` (lines 722–848).
It contains `timestamp`, `num_steps`, `final_score`, `success`, `llm_analysis`,
`task_goal`, and a list of step records. Each step contains the actual code fields
`step_num`, `state`, `action`, `normalized_action`, `semantic_action`,
`action_metadata`, `step_summary`, `reward`, `score`, `delta_score`,
`llm_step_score`, `llm_reasoning`, and `url`.

The retrieval unit is a per-step entry created by
`CrossEpisodeMemory._store_step_in_vector_db` (lines 266–329). Its metadata contains
`episode_timestamp`, `episode_number`, `task_goal`, `step_data`,
`episode_final_score`, `episode_success`, `trajectory_context`,
`current_env_info`, `future_rewards`, `step_summary`, `url`, and
`normalized_url`. The current WebArena path stores BM25 corpus tokens; its active
retriever below uses deterministic token/Jaccard calculations over the stored text.

### M2 — Source-policy provenance

**PARTIAL.** The storage path is partitioned by game, agent type, and model slug, and
entries carry episode number/timestamp. These fields give coarse model/run chronology,
but no step stores the behavior policy, prompt/policy snapshot, checkpoint, policy
version, propensity, or a policy-era identifier. Prompt/action behavior can change
inside the same directory without a per-memory source-policy binding.

### M3 — Retrieval

`CrossEpisodeMemory.retrieve_similar_with_vector` (lines 403–702) executes:

1. exact `normalized_url` filtering;
2. unigram Jaccard task similarity above `task_similarity_threshold` (default 0.27);
3. history similarity as unigram Jaccard over trajectory-context tokens;
4. `similarity = 0.7 * history_similarity + 0.3 * task_similarity`;
5. a dynamic threshold from `r` down to `r-0.1` as current step count approaches 20;
6. descending sort by `(similarity, discounted_return)`.

The present source returns every item above threshold because the later `[:k]` line is
commented out. The production call supplies `k=10, r=0.8`, but `k` does not truncate
this active return path.

### M4 — Historical return / advantage

Storage places the future `llm_step_score` sequence into `future_rewards`.
At retrieval, `discounted_return = sum(gamma**u * future_score[u])`.
The code returns this as `discounted_reward`. In
`BrowserGymJitRLAgent.update_scores` (lines 204–412), retrieved items are grouped by
`normalized_action`; each action receives the arithmetic mean of its retrieved
`discounted_reward` values. The baseline is the overall mean of retrieved rewards,
then it becomes the mean over action means after candidate actions absent from memory
are assigned the native exploration/zero value. Raw advantage is
`mean_action_return - overall_mean`.

If any advantage is positive, every advantage is divided by the largest positive
advantage; otherwise values are divided by the largest negative magnitude.

### M5 — Policy influence

The native update is
`corrected_logprob = normalized_prob + normalized_advantage`.
`generate_action` (lines 1018–1152) calls `update_scores` and executes the option
with maximum `corrected_logprob`. Thus the historical signal can directly change the
current action.

### M6 — Revaluation under current policy

**NO.** Retrieval recomputes a discounted sum from stored future step scores using the
configured gamma, but it does not roll those rewards forward under the current policy,
estimate current-policy continuation, or recompute a target-policy Q/advantage.

### M7 — Explicit correction audit

| Mechanism | Present? |
|---|---|
| Importance weighting | NO |
| Behavior-policy correction | NO |
| Target-policy correction | NO |
| Source/target policy comparison | NO |
| Provenance-aware rejection | NO |
| Off-policy validity test | NO |

### M8 — Confidence versus current-policy validity

Task/history similarity thresholds decide whether a past context resembles the current
query. LLM option confidence supplies a base option score in verbalized mode.
`calculate_exploration_probability` measures historical mean reward, stability, and
sample count, but the active `update_scores` path uses a fixed 0.05 exploration
probability. None of these checks asks whether the historical action-guiding signal
remains valid under the current continuation policy.

## Stage-7 → JitRL native object

| Stage-7 object | JitRL native object |
|---|---|
| source policy | only coarse model/run chronology; no bound per-step policy snapshot |
| historical experience | episode step plus per-step retrieval metadata |
| historical return | retrieved `discounted_reward` from stored `future_rewards` |
| retrieval | URL/task/history filters and Jaccard threshold |
| historical advantage/value | action mean discounted reward minus overall mean; normalized |
| target/current policy | current LLM option scores and action generation path |
| memory influence | normalized advantage added to current option score |
| validity check | absent; similarity and reward stability are not target-policy validity |

## Stage-8A gates

| Gate | Result | Evidence |
|---|---|---|
| A0 Source integrity | PASS | fixed existing checkout and commit; audited tracked files clean |
| A1 Native memory path found | PASS | `add_episode → _store_step_in_vector_db → retrieve_similar_with_vector` |
| A2 Native value path found | PASS | `future_rewards → discounted_reward → action mean → advantage` |
| A3 Native policy influence found | PASS | `normalized_prob + normalized_advantage → argmax` |
| A4 Provenance audit | PASS | coarse chronology only; no per-memory source policy |
| A5 Revaluation audit | PASS | no current-policy revaluation found |
| A6 Correction audit | PASS | no explicit correction sufficient for source/target validity mismatch |

## Stage-8A verdict

**JITRL_MAPPING_GO**

The audited WebArena path contains a complete historical-memory-to-current-action
influence chain, and no explicit current-policy validity correction was found. This is
a code mapping result; it does not by itself establish a behavioral failure.
