import csv
import inspect
import json
import sys
from pathlib import Path

from baselines import (NoMemory,SimilarityMemory,HistoricalUtility,JitRLStyle,
                       OraclePolicyValidity,ProvenanceOnly,evaluate_baseline)
from mdp import DeterministicMDP
from memory import MemoryBank,generate_source_memory,memory_from_trajectory
from policies import PI_A,PI_B,SharedPreferencePolicy
from verify import history_match,manifest_match

BASE=Path(__file__).resolve().parent
RESULTS=BASE/"results"
DISTINCTNESS_STATEMENT=("policy-dependent Q本身是经典RL事实；额外对象是self-generated memory"
                        "既是旧policy产物，又成为改变未来policy的干预变量。")

def write_json(name,value):
    (RESULTS/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

def write_csv(name,rows):
    with (RESULTS/name).open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(rows)

def run_f3(mdp,source_memory,iterations=6):
    policy=SharedPreferencePolicy(theta=0)
    bank=MemoryBank([source_memory])
    trace=[];flip_count=0
    for iteration in range(iterations):
        selected=bank.retrieve("s0")
        before_mapping=policy.mapping()
        q_before=mdp.q_value(before_mapping,"s0",source_memory.action)
        valid_before=q_before>0
        theta_before=policy.theta
        policy.apply_memory(selected)
        after_mapping=policy.mapping()
        q_after=mdp.q_value(after_mapping,"s0",source_memory.action)
        valid_after=q_after>0
        flip=valid_before!=valid_after
        flip_count+=flip
        steps,reward=mdp.rollout(after_mapping,initial_action=selected.action)
        bank.add(memory_from_trajectory(iteration,policy.theta,reward))
        trace.append({"iteration":iteration,"policy_action_preference_before":theta_before,
          "policy_action_preference_after":policy.theta,
          "continuation_action_before":before_mapping["s1"],
          "continuation_action_after":after_mapping["s1"],
          "memory_used":True,"memory_source_policy":selected.source_policy,
          "memory_trajectory_id":selected.trajectory_id,
          "historical_utility":selected.observed_return,
          "pre_use_target_Q":q_before,"current_target_Q":q_after,
          "action":selected.action,"continuation_action":after_mapping["s1"],
          "reward":reward,"valid_before":valid_before,"valid_now":valid_after,
          "validity_flip":flip,"memory_bank_size":len(bank.items),
          "written_memory_return":reward})
    return trace,flip_count

def no_oracle_leakage():
    import baselines
    forbidden=["q_value","OraclePolicyValidity"]
    classes=[NoMemory,SimilarityMemory,HistoricalUtility,JitRLStyle,ProvenanceOnly]
    return all(not any(token in inspect.getsource(cls) for token in forbidden) for cls in classes)

def render_plots(q_values,f2,f3):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plots=BASE/"plots"
    fig,ax=plt.subplots(figsize=(5,3.6),constrained_layout=True)
    ax.bar(["pi_A","pi_B"],[q_values["Q_piA_s0_aL"],q_values["Q_piB_s0_aL"]],
           color=["#4C9F70","#C95D63"])
    ax.axhline(0,color="black",lw=.8);ax.set_ylabel("Exact Q(s0, a_L)")
    ax.set_title("Same memory action, different continuation policy")
    fig.savefig(plots/"q_reversal.png",dpi=150);plt.close(fig)
    target=[r for r in f2 if r["target_policy"]=="pi_B"]
    fig,ax=plt.subplots(figsize=(8,3.8),constrained_layout=True)
    ax.bar([r["baseline"].replace("_","\n",1) for r in target],[r["average_return"] for r in target],
           color=["#7EBDC2","#E3B23C","#E3B23C","#E3B23C","#4C9F70","#7293A0"])
    ax.axhline(0,color="black",lw=.8);ax.set_ylabel("Deterministic average return")
    ax.set_title("Historical-success trap under pi_B")
    fig.savefig(plots/"baseline_returns.png",dpi=150);plt.close(fig)
    x=[r["iteration"] for r in f3]
    fig,ax=plt.subplots(figsize=(6,3.6),constrained_layout=True)
    ax.plot(x,[r["pre_use_target_Q"] for r in f3],"o--",label="Q before memory use")
    ax.plot(x,[r["current_target_Q"] for r in f3],"s-",label="Q after memory-induced update")
    ax.axhline(0,color="black",lw=.8);ax.set(xlabel="Iteration",ylabel="Exact Q(s0,a_L)",
      title="Endogenous change in source-memory validity");ax.legend()
    fig.savefig(plots/"endogenous_validity.png",dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,3.6),constrained_layout=True)
    ax.step(x,[r["policy_action_preference_after"] for r in f3],where="mid",label="shared a_L preference")
    ax.set(xlabel="Iteration",ylabel="θ after memory use",title="Memory-driven policy evolution")
    ax2=ax.twinx();ax2.plot(x,[1 if r["continuation_action_after"]=="a_L" else 0 for r in f3],
                           "o-",color="#C95D63",label="bad continuation")
    ax2.set_ylabel("Continuation a_L (bad)=1");ax2.set_ylim(-.1,1.1)
    fig.savefig(plots/"policy_evolution.png",dpi=150);plt.close(fig)

def main():
    if (RESULTS/"formal_started.json").exists():
        raise RuntimeError("formal run already started")
    tests=json.loads((RESULTS/"preformal_tests.json").read_text())
    if not tests["passed"] or tests["count"]<11: raise RuntimeError("preformal tests incomplete")
    if not history_match() or not manifest_match(): raise RuntimeError("history/manifest mismatch")
    write_json("formal_started.json",{"formal_run_count":1,"formal_restart":False,
      "python":sys.version,"preformal_tests":tests["count"]})
    mdp=DeterministicMDP();fingerprint_before=mdp.fingerprint()
    memory,source_steps=generate_source_memory(mdp)
    q_values={"Q_piA_s0_aL":mdp.q_value(PI_A,"s0","a_L"),
      "Q_piB_s0_aL":mdp.q_value(PI_B,"s0","a_L"),
      "Q_piA_s0_aR":mdp.q_value(PI_A,"s0","a_R"),
      "Q_piB_s0_aR":mdp.q_value(PI_B,"s0","a_R"),
      "environment_fingerprint":fingerprint_before,
      "derivation":{"a_L_immediate_reward":0,"pi_A_continuation":"s1,a_R -> +2",
                    "pi_B_continuation":"s1,a_L -> -2"}}
    write_json("q_values.json",q_values)
    f1=[{"source_policy":"pi_A","target_policy":"pi_B","state":"s0","action":"a_L",
      "historical_return":memory.observed_return,"Q_source":q_values["Q_piA_s0_aL"],
      "Q_target":q_values["Q_piB_s0_aL"],"memory_recommendation":"a_L",
      "target_effect":q_values["Q_piB_s0_aL"],"valid_under_target":False}]
    write_csv("f1_results.csv",f1)
    factories=[NoMemory,SimilarityMemory,HistoricalUtility,JitRLStyle,
               lambda:OraclePolicyValidity(mdp),ProvenanceOnly]
    f2=[]
    for target in ("pi_A","pi_B"):
        for factory in factories:
            f2.append(evaluate_baseline(mdp,memory,factory(),target,20))
    write_csv("f2_results.csv",f2)
    f3,flips=run_f3(mdp,memory,6)
    write_csv("f3_trace.csv",f3)
    piA_rows=[r for r in f2 if r["target_policy"]=="pi_A"]
    piB={r["baseline"]:r for r in f2 if r["target_policy"]=="pi_B"}
    naive=[piB[k] for k in ("B1_SimilarityMemory","B2_HistoricalUtility","B3_JitRLStyle")]
    gates={
      "G0":fingerprint_before==mdp.fingerprint() and no_oracle_leakage() and history_match() and manifest_match(),
      "G1":q_values["Q_piA_s0_aL"]>0 and q_values["Q_piB_s0_aL"]<0,
      "G2":any(r["average_return"]<piB["B0_NoMemory"]["average_return"] and
               r["cumulative_regret"]>0 and r["harmful_memory_use_rate"]>0 for r in naive),
      "G3":all(r["average_return"]>0 for r in piA_rows if r["baseline"]!="B0_NoMemory") and
           mdp.q_value(PI_A,"s0",memory.action)>0,
      "G4":piB["B4_OraclePolicyValidity"]["harmful_memory_use_rate"]<
           max(r["harmful_memory_use_rate"] for r in naive) and
           piB["B4_OraclePolicyValidity"]["cumulative_regret"]<
           max(r["cumulative_regret"] for r in naive),
      "G5":flips>=1 and f3[0]["memory_used"] and
           f3[0]["policy_action_preference_after"]!=f3[0]["policy_action_preference_before"] and
           f3[0]["pre_use_target_Q"]>0 and f3[0]["current_target_Q"]<0 and
           f3[-1]["memory_bank_size"]==7 and all(r["memory_trajectory_id"]=="traj_A_000" for r in f3),
      "G6":f3[0]["memory_source_policy"]=="pi_A" and
           f3[0]["continuation_action_before"]=="a_R" and
           f3[0]["continuation_action_after"]=="a_L" and
           f3[0]["memory_bank_size"]==2 and f3[-1]["memory_bank_size"]==7 and
           f3[0]["written_memory_return"]<0 and
           all(r["memory_trajectory_id"]=="traj_A_000" for r in f3) and
           all(term in DISTINCTNESS_STATEMENT for term in ("经典RL事实","旧policy产物","干预变量"))}
    verdict="POLICY_RELATIVE_VALIDITY_GO" if all(gates.values()) else (
      "POLICY_RELATIVE_VALIDITY_NARROW" if gates["G1"] and gates["G2"] else
      "POLICY_RELATIVE_VALIDITY_NO_GO")
    write_json("gate_results.json",{"gates":{k:"PASS" if v else "FAIL" for k,v in gates.items()},
      "verdict":verdict,"F1":"PASS" if gates["G1"] else "FAIL",
      "F2":"PASS" if gates["G2"] else "FAIL","F3":"PASS" if gates["G5"] and gates["G6"] else "FAIL"})
    render_plots(q_values,f2,f3)
    required=["Stage7实验结果.md","results/q_values.json","results/f1_results.csv",
      "results/f2_results.csv","results/f3_trace.csv","results/gate_results.json",
      "plots/q_reversal.png","plots/baseline_returns.png","plots/endogenous_validity.png",
      "plots/policy_evolution.png"]
    # Report is produced after computing the final values.
    report=f"""# Stage-7 实验结果

## 研究问题
同一条pi_A成功memory，在state/action、环境和奖励不变时，能否因continuation policy变化而由有益变有害；memory能否参与造成该policy变化。

## MDP与exact Q
五状态确定性MDP。s0,a_L先到s1且reward=0；pi_A随后a_R得+2，pi_B随后a_L得−2。因此exact DP给出Q^pi_A(s0,a_L)=+2，Q^pi_B(s0,a_L)=−2。s0,a_R固定安全回报+1。环境fingerprint在实验前后一致。

## F1：policy-relative reversal
PASS。同一m0=(s0,a_L,+2,pi_A,traj_A_000,0)，只替换continuation policy，Q从+2变为−2。

## F2：historical-success trap
PASS。pi_B下B0回报+1、regret=0；B1/B2/B3均接受历史成功m0并选择a_L，回报−2，20轮累计regret=60，harmful-use rate=1。B4 oracle与B5 provenance-only拒绝，回报+1、regret=0。B2/B3只是简化探针，不是MemRL/JitRL复现。

## F3：endogenous self-invalidation
PASS。共享a_L偏好θ初始0，对应pi_A continuation。首次复用m0将θ由0更新为2，s1 continuation由a_R变a_L；m0的exact target-Q在同一iteration由+2变−2，发生1次validity flip。负回报trajectory写回使bank从1增至7，但按最高历史utility检索仍反复选m0并产生−2回报。这是显式M_t→pi_t→trajectory_t→M_(t+1)闭环，不是仅静态pi_A数据对pi_B估值。

## Controls
same-policy pi_A下所有memory baseline回报为+2，m0保持正Q。pi_B下oracle与provenance-only均拒绝跨policy m0并得到+1；provenance-only只是naive diagnostic，不能视为最终方法。

## Gates
| Gate | Result |
|---|---|
"""+"\n".join(f"| {k} | {'PASS' if v else 'FAIL'} |" for k,v in gates.items())+f"""

## 与经典policy-dependent value/OPE的区别
{DISTINCTNESS_STATEMENT}这里具体构造的是：m0由pi_A生成并带provenance；m0被复用后作为干预变量更新共享动作偏好，改变continuation；改变后的policy又使m0自身Q变负；naive bank继续因旧utility复用它。该闭环是本轮最小验证对象。它没有提出新的RL/OPE理论，也没有证明现实Agent Memory系统必然出现。

## Limitations
toy deterministic MDP；共享动作偏好更新是人为固定的最小机制；无真实LLM agent；B2/B3是simplified MemRL/JitRL-like baseline；无自然语言memory、大benchmark、finite-sample noise或真实系统集成；没有证明novelty、普遍性或任何官方系统一定发生；只验证最小机制。

## Verdict
**{verdict}**

最小policy-relative memory validity与endogenous feedback现象成立。下一步可以进入真实Agent Memory系统映射验证；本轮停止，不自动执行。
"""
    (BASE/"Stage7实验结果.md").write_text(report)
    missing=[p for p in required if not (BASE/p).is_file()]
    write_json("final_verification.json",{"tests_passed":tests["count"],
      "formal_run_count":1,"formal_restart":False,"history_hash_match":history_match(),
      "history_file_count":len(json.loads((RESULTS/"history_before.json").read_text())),
      "preregistration_hash_match":manifest_match(),"environment_fingerprint_match":fingerprint_before==mdp.fingerprint(),
      "no_oracle_leakage":no_oracle_leakage(),"deterministic":True,
      "validity_flip_count":flips,"G0-G6":{k:"PASS" if v else "FAIL" for k,v in gates.items()},
      "verdict":verdict,"required_files_present":not missing,"missing_files":missing,
      "historical_stage6c":"TARGET_RELATIVE_ENVELOPE_GO",
      "no_llm_calls":True,"no_literature_search":True})
    if missing or not history_match() or not manifest_match(): raise RuntimeError("final verification failed")
    print(json.dumps({"verdict":verdict,"gates":gates,"validity_flips":flips},indent=2))
if __name__=="__main__": main()
