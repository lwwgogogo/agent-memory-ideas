from dataclasses import asdict,dataclass

@dataclass(frozen=True)
class ExperienceMemory:
    state: str
    action: str
    observed_return: int
    source_policy: str
    trajectory_id: str
    generation_step: int

    def to_dict(self):
        return asdict(self)

class MemoryBank:
    def __init__(self,items=()):
        self.items=list(items)

    def add(self,item):
        self.items.append(item)

    def retrieve(self,state):
        candidates=[(i,m) for i,m in enumerate(self.items) if m.state==state]
        if not candidates: return None
        # Highest historical return; stable earliest tie break.
        return max(candidates,key=lambda pair:(pair[1].observed_return,-pair[0]))[1]

def generate_source_memory(mdp):
    from policies import PI_A
    steps,total=mdp.rollout(PI_A)
    assert steps[0]["state"]=="s0" and steps[0]["action"]=="a_L" and total==2
    return ExperienceMemory("s0","a_L",total,"pi_A","traj_A_000",0),steps

def memory_from_trajectory(iteration,theta,total):
    return ExperienceMemory("s0","a_L",total,f"theta_{theta}",
                            f"feedback_{iteration:03d}",iteration+1)
