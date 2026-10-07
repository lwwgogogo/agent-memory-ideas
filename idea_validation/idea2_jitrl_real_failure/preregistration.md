# Preregistration: Idea 2 Stage-8C

## Fixed question

Can a memory item that received a positive native JitRL historical signal cause a worse current outcome when retrieved in a later, exactly matched Jericho state?

## Frozen runtime

- Repository: `/home/liaoweiwen/projects/agent-memory-ideas`
- JitRL source: `idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl`
- JitRL commit: `143d22185d95fbf633a0befe6861d5e8b732543b`
- Conda environment: `jitrl_runtime`; Python 3.10.21
- Task: Jericho `library`; ROM `Jericho/jericho-games/library.z5`
- Model/backend: `qwen2.5:14b`; Ollama OpenAI-compatible API `http://localhost:11434/v1`
- spaCy/model: 3.8.16 / en_core_web_sm 3.8.0
- Seed: 20261008; temperature: 0
- JitRL settings: gamma 0.5, retrieval top-k 10, retrieval threshold 0.95, top actions 3, cross-episode memory enabled, guiding-prompt updates disabled, valid actions enabled, verbalized confidence
- One environment step per episode; two pilot episodes; exactly 20 formal episodes; no adaptive extension

No dependency, task, model, backend, prompt, retrieval rule, source code, or stopping rule may be changed after locking. Pilot data are excluded from primary statistics.

## Units and identity

A source memory is one persisted `episode × step` record in native `episodes.jsonl`. Its immutable `memory_id` is SHA-256 over the canonical JSON tuple `(episode_number, step_num, state, action, reward, score, delta_score, llm_step_score)`.

A retrieval event is one returned tuple from native `CrossEpisodeMemory.retrieve_similar`. Attempts returning an empty list are logged but are not retrieval events. All formal retrieval events are analyzed.

The native source-policy identity is recorded as `UNAVAILABLE` because the frozen record does not persist a full model/prompt/sampling identity. This field cannot be inferred.

## Historical positivity

The primary historical signal is the native stored `llm_step_score`. A source is positive iff this exact finite numeric field is greater than zero. The environmental `reward` and `delta_score` are logged as diagnostics and do not replace the primary definition.

## Paired intervention

For each eligible event, snapshot the exact pre-action environment state, agent state, RNG states, model request, retrieval list, and source store. Run:

- `WITH_MEMORY`: unmodified retrieved list.
- `WITHOUT_THIS_MEMORY`: the same list with only the target `memory_id` removed.

All other inputs must be byte-identical. Restore the snapshot before each branch. No other memory may be removed. Candidate pairs are limited to 20; candidates are selected in chronological order without outcome peeking.

Current outcome is the immediate environment reward after the selected action. The pair is valid only when pre-action state hashes match exactly. Define

`Delta_current = reward_with - reward_without`.

A failure candidate requires a positive native historical signal and `Delta_current < 0`. A candidate also requires a changed selected action, preventing claims based only on an inert prompt difference.

## Confirmation

Each candidate gets at most three total deterministic repeats, using the frozen seed and temperature. It is confirmed when either all observed deltas are negative, or the mean delta is negative and at least two of three repeats are negative. A confirmed behavioral failure additionally requires a changed action in at least two of three repeats.

## Budgets and stopping

- Pilot: 2 episodes, at most 20 model calls.
- Formal: exactly 20 episodes, at most 160 model calls.
- Candidate pairs: at most 20.
- Total repeats per candidate: at most 3.
- No formal restart and no sample extension.
- Stop on budget violation and classify NO_GO.

The technical pilot may show zero retrieval and formal execution will still proceed, because retrieval availability itself is part of the fixed runtime test.

## Metrics

Report memory writes, retrieval attempts, retrieval events, retrieval rate, positive-source retrievals, valid paired events, candidates, confirmed failures, behavior-changing confirmed failures, candidate rate, confirmation rate, mean/median delta, and model calls. Missing denominators are reported as null, never zero.

## Gates

- G0: preregistration/scripts locked before formal and preformal tests pass.
- G1: real frozen JitRL formal run completes exactly 20 episodes.
- G2: at least one real native write and at least one native retrieval event.
- G3: at least one exactly state-matched valid pair.
- G4: at least one retrieved positive native source.
- G5: at least one failure candidate.
- G6: at least one confirmed negative effect.
- G7: at least one confirmed behavior-changing failure.
- G8: every analyzed pair passes state/input integrity checks.
- G9: all episode, inference, pair, repeat, and restart budgets hold.

## Verdict

- `REAL_JITRL_MEMORY_FAILURE_GO`: G0–G9 all pass and at least two confirmed behavior-changing failures occur from at least two distinct sources.
- `REAL_JITRL_MEMORY_FAILURE_NARROW`: G0–G5 and G8–G9 pass, with at least one confirmed behavior-changing failure, but the GO replication threshold is not met.
- `REAL_JITRL_MEMORY_FAILURE_NO_GO`: otherwise.

A lack of retrieval is reported as a runtime-specific feasibility failure. It is not evidence that harmful retrieved memories cannot exist.
