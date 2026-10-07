PI_A={"s0":"a_L","s1":"a_R"}
PI_B={"s0":"a_R","s1":"a_L"}
POLICIES={"pi_A":PI_A,"pi_B":PI_B}

class SharedPreferencePolicy:
    """Minimal policy feedback: a successful action memory updates shared a_L preference."""
    def __init__(self,theta=0):
        self.theta=theta

    def score(self,state,action):
        if action=="a_R": return 0
        return (1 if state=="s0" else -1)+self.theta

    def action(self,state):
        # Fixed tie break to a_R.
        return "a_L" if self.score(state,"a_L")>self.score(state,"a_R") else "a_R"

    def mapping(self):
        return {s:self.action(s) for s in ("s0","s1")}

    def apply_memory(self,memory):
        if memory.action=="a_L" and memory.observed_return>0:
            self.theta+=memory.observed_return
