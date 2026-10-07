from dataclasses import dataclass
from policies import POLICIES

@dataclass(frozen=True)
class Decision:
    action: str
    accepted: bool

class NoMemory:
    name="B0_NoMemory"
    def decide(self,state,memory,target_policy):
        return Decision(POLICIES[target_policy][state],False)

class SimilarityMemory:
    name="B1_SimilarityMemory"
    def decide(self,state,memory,target_policy):
        if memory is not None and memory.state==state:
            return Decision(memory.action,True)
        return Decision(POLICIES[target_policy][state],False)

class HistoricalUtility:
    name="B2_HistoricalUtility"
    def decide(self,state,memory,target_policy):
        if memory is not None and memory.state==state and memory.observed_return>0:
            return Decision(memory.action,True)
        return Decision(POLICIES[target_policy][state],False)

class JitRLStyle:
    name="B3_JitRLStyle"
    def decide(self,state,memory,target_policy):
        current=POLICIES[target_policy][state]
        scores={"a_L":int(current=="a_L"),"a_R":int(current=="a_R")}
        accepted=False
        if memory is not None and memory.state==state:
            scores[memory.action]+=memory.observed_return
            accepted=max(scores,key=lambda a:(scores[a],a=="a_R"))==memory.action
        action=max(scores,key=lambda a:(scores[a],a=="a_R"))
        return Decision(action,accepted)

class OraclePolicyValidity:
    name="B4_OraclePolicyValidity"
    def __init__(self,mdp): self.mdp=mdp
    def decide(self,state,memory,target_policy):
        if (memory is not None and memory.state==state and
            self.mdp.q_value(POLICIES[target_policy],state,memory.action)>=0):
            return Decision(memory.action,True)
        return Decision(POLICIES[target_policy][state],False)

class ProvenanceOnly:
    name="B5_ProvenanceOnly"
    def decide(self,state,memory,target_policy):
        if memory is not None and memory.state==state and memory.source_policy==target_policy:
            return Decision(memory.action,True)
        return Decision(POLICIES[target_policy][state],False)

def evaluate_baseline(mdp,memory,baseline,target_policy,episodes=20):
    policy=POLICIES[target_policy]
    optimal=max(mdp.q_value(policy,"s0",a) for a in ("a_L","a_R"))
    returns=[];accepted=harmful=0
    for _ in range(episodes):
        d=baseline.decide("s0",memory,target_policy)
        _,value=mdp.rollout(policy,initial_action=d.action)
        returns.append(value)
        accepted+=d.accepted
        harmful+=bool(d.accepted and mdp.q_value(policy,"s0",memory.action)<0)
    return {"baseline":baseline.name,"target_policy":target_policy,"episodes":episodes,
      "average_return":sum(returns)/episodes,
      "cumulative_regret":sum(optimal-r for r in returns),
      "harmful_memory_use_rate":harmful/episodes,
      "memory_acceptance_rate":accepted/episodes,
      "chosen_action":baseline.decide("s0",memory,target_policy).action,
      "deterministic_return":returns[0],"optimal_target_return":optimal}
