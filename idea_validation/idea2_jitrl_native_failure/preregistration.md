# Idea 2 Stage-8B Pre-registration

Status: **LOCKED BEFORE FORMAL RUN**

## Question and scope

Can the frozen Stage-7 policy-relative value reversal pass through an actual JitRL
memory → retrieval → historical advantage → current score path and create an observable
signal mismatch and behavioral loss? This is a deterministic toy reproduction, not a
full WebArena/Jericho/LLM benchmark and not a method proposal.

## Fixed source

- Existing JitRL checkout:
  `idea_validation/idea2_policy_conditioned_memory_audit/third_party/jitrl`
- Commit: `143d22185d95fbf633a0befe6861d5e8b732543b`
- Native functions:
  - `WebArena/memory_agents/utils/cross_episode_memory.py:CrossEpisodeMemory._store_step_in_vector_db`
  - `WebArena/memory_agents/utils/cross_episode_memory.py:CrossEpisodeMemory.retrieve_similar_with_vector`
  - `WebArena/memory_agents/jitrl_agent.py:BrowserGymJitRLAgent.update_scores`
  - action argmax documented from `BrowserGymJitRLAgent.generate_action`
- No upstream file may be modified.

## Adapter mapping

The adapter parses the fixed upstream Python source, extracts the named method AST
bodies, compiles them unchanged into dependency-light harness classes, and invokes
those bodies. It does not rewrite retrieval, discounted return, action aggregation,
advantage normalization, score correction, or argmax.

Allowed boundary substitutions are frozen:

1. the unavailable LLM trajectory summarizer is replaced by fixed materialized strings;
2. abstract toy actions `a_L/a_R` are already canonical, so normalization is identity;
3. the WebArena LLM step-score fields are populated with the frozen trajectory's
   deterministic step rewards `[0,+2]`;
4. JitRL `gamma` is set to the Stage-7 environment's frozen `gamma=1`.

## Frozen Stage-7 reference

- `idea2_policy_relative_validity/mdp.py` SHA256:
  `8c2e51bdaa29c57da5d2208885bbbe11815de2b639969036e488b909b8242181`
- `idea2_policy_relative_validity/policies.py` SHA256:
  `52aaaf4e1b3325de4dfea7d7e818ae18367b96b1ad20bba36539926d887c1166`
- `pi_A={s0:a_L,s1:a_R}`; `pi_B={s0:a_R,s1:a_L}`.
- Exact values: `Q^pi_A(s0,a_L)=+2`, `Q^pi_B(s0,a_L)=-2`,
  and `Q(s0,a_R)=+1`.
- Source experience is the successful `pi_A` trajectory. Source policy is retained in
  the experiment ledger only; it is not injected into native JitRL memory fields.

## Locked native inputs

- seed: 0
- retrieval: production call values `k=10`, `r=0.8`
- task threshold: native default 0.27
- contexts: `s0 start branch` and `s1 continuation outcome different`
- URL: `toy://stage7`
- current option scores: exact one-hot encoding of frozen deterministic `pi_A/pi_B`
- B3 episodes: 20
- Native exploration probability and score coefficient remain the upstream values
  (0.05 and 1). Seed 0 fixes the native random branch before formal execution.

## Signal definitions

- Historical return: upstream retrieved `discounted_reward`.
- Native raw advantage and normalized signal: exact outputs of upstream `update_scores`.
- Target Q: exact Stage-7 `Q^pi_t(s0,a)`.
- Target advantage: target Q minus the mean exact Q over `a_L/a_R`, matching the
  action-mean baseline form used by the native path.
- Sign mismatch: sign(native normalized historical signal for `a_L`) differs from
  sign(target exact advantage for `a_L`).
- Behavioral choice: upstream corrected-score argmax.
- Oracle values are joined after native action selection. Only `OracleValidity` may
  read target Q before selecting.

## Experiments

- **B1 same-policy:** source `pi_A`, target `pi_A`; require retrieval and sign agreement.
- **B2 policy shift:** source `pi_A`, target `pi_B`; test positive native signal,
  negative target signal, retrieval, and current score bias.
- **B3 performance:** 20 deterministic episodes each for `NoMemory`,
  `JitRLNative`, and diagnostic `OracleValidity`. NoMemory uses frozen current
  policy. Oracle rejects native influence only when current exact target advantage is
  negative.
- **B4 closed loop:** predeclared `NOT_TESTABLE`. The permitted no-LLM harness can
  execute native storage/retrieval/value/score correction, but the upstream episode
  scorer/text generator requires the excluded LLM runtime and no standalone native
  policy-update rule exists. No update rule will be invented; no time-series plot will
  be produced.

## Primary metrics

NativeRetrievalRate, NativeSignal, TargetOracleSignal, SignalMismatchRate,
PositiveHistoricalNegativeTargetRate, HarmfulMemoryUseRate, HarmfulPolicyBiasRate,
AverageReturn, CumulativeRegret. ValidityFlipCount is null because B4 is not testable.

## Gates and verdict

G0–G8 follow the user-specified definitions. G0 requires hashes, preformal tests, clean
tracked history, and access-boundary checks. G6 requires execution of extracted upstream
method bodies. G7 requires retrieval, reinjection, and behavioral harm beyond the exact-Q
fact. G8 is `NOT_TESTABLE`.

`JITRL_NATIVE_FAILURE_GO` requires G0–G7 PASS and G8 PASS or NOT_TESTABLE.
If mapping/mismatch survives but behavioral harm or fidelity fails, verdict is NARROW.
If native correction prevents mismatch, native reuse does not occur, or only a rewritten
JitRL-like implementation fails, verdict is NO_GO.

## Formal-run discipline

All locked hashes are stored in `results/preregistration_manifest.json`. Tests must
pass before the one formal run. If a bug occurs: stop, document it, fix it, rerun tests,
regenerate the lock, and restart the formal run. No prompt/model/sample/gate changes are
allowed after seeing formal results.
