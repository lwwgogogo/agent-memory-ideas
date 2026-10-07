from dataclasses import dataclass
import hashlib
import json

@dataclass(frozen=True)
class Transition:
    next_state: str
    reward: int

class DeterministicMDP:
    def __init__(self):
        self.transitions={
          ("s0","a_L"):Transition("s1",0),
          ("s0","a_R"):Transition("terminal_safe",1),
          ("s1","a_R"):Transition("terminal_good",2),
          ("s1","a_L"):Transition("terminal_bad",-2)}
        self.terminals={"terminal_safe","terminal_good","terminal_bad"}
        self.gamma=1

    def step(self,state,action):
        return self.transitions[(state,action)]

    def value(self,policy,state):
        if state in self.terminals: return 0
        action=policy[state]
        t=self.step(state,action)
        return t.reward+self.gamma*self.value(policy,t.next_state)

    def q_value(self,policy,state,action):
        t=self.step(state,action)
        return t.reward+self.gamma*self.value(policy,t.next_state)

    def rollout(self,policy,initial_action=None):
        state="s0";total=0;steps=[]
        while state not in self.terminals:
            action=initial_action if state=="s0" and initial_action is not None else policy[state]
            t=self.step(state,action)
            steps.append({"state":state,"action":action,"reward":t.reward,"next_state":t.next_state})
            total+=t.reward;state=t.next_state
        return steps,total

    def fingerprint(self):
        payload={"gamma":self.gamma,"transitions":{
          f"{s}|{a}":{"next_state":t.next_state,"reward":t.reward}
          for (s,a),t in sorted(self.transitions.items())}}
        raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()
