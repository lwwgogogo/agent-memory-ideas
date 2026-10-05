from __future__ import annotations
import hashlib, json, math, re, sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
STAGE2 = REPO / "idea_validation" / "idea2_causal_sufficiency"
PRIMARY_WRITER = "qwen2.5:14b"
SECONDARY_WRITER = "qwq:32b"
READER = "qwq:32b"
OPTIONS_WRITER = {"temperature": 0, "top_p": 1.0, "seed": 20261005, "num_ctx": 8192, "num_predict": 512}
OPTIONS_AUDIT = {"temperature": 0, "top_p": 1.0, "seed": 20261005, "num_ctx": 8192, "num_predict": 512}
OPTIONS_READER = {"temperature": 0, "top_p": 1.0, "seed": 20261005, "num_ctx": 8192, "num_predict": 256}
FORMATION_TYPES = ["GenericSummary", "ReflectionLesson", "StrategyMemory", "ConsolidatedExperience"]
WRITERS = {"primary": PRIMARY_WRITER, "secondary": SECONDARY_WRITER}
CELLS = [("S0", "A"), ("S0", "B"), ("S1", "A"), ("S1", "B")]

FORMATION_SYSTEM = "只输出严格 JSON 对象，且仅含 memory 一个字符串字段。memory 只能依据提供的经验，不得编造事实，不得超过指定字符预算。不要输出解释、置信度、分析或额外字段。"
FAITHFUL_SYSTEM = "你是事实核验器。只核对生成记忆中明确陈述的事实是否被原始经验支持。不要评价记忆质量、用途或策略。严格输出 schema 指定的四个布尔字段。"
RECOVERY_SYSTEM = "你只能依据记忆中明确表达的信息恢复计数。没有明确提供的数字必须输出 null，绝不猜测。严格输出 schema 指定的八个字段。"
DOWNSTREAM_SYSTEM = "只输出严格 JSON 对象，且仅含 p_success_left 和 p_success_right 两个 0 到 1 之间的数字。不要输出 choice、reason、confidence 或解释。"

FORMATION_SCHEMA = {"type":"object","properties":{"memory":{"type":"string"}},"required":["memory"],"additionalProperties":False}
FAITHFUL_SCHEMA = {"type":"object","properties":{k:{"type":"boolean"} for k in ["contradiction","unsupported_specific_claim","numeric_error","faithful"]},"required":["contradiction","unsupported_specific_claim","numeric_error","faithful"],"additionalProperties":False}
RECOVERY_FIELDS = ["s0_action_a_success","s0_action_a_exposure","s0_action_b_success","s0_action_b_exposure","s1_action_a_success","s1_action_a_exposure","s1_action_b_success","s1_action_b_exposure"]
RECOVERY_SCHEMA = {"type":"object","properties":{k:{"type":["integer","null"],"minimum":0} for k in RECOVERY_FIELDS},"required":RECOVERY_FIELDS,"additionalProperties":False}
DOWNSTREAM_SCHEMA = {"type":"object","properties":{"p_success_left":{"type":"number","minimum":0,"maximum":1},"p_success_right":{"type":"number","minimum":0,"maximum":1}},"required":["p_success_left","p_success_right"],"additionalProperties":False}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")

def load_source():
    return json.loads((ROOT/"cases"/"source_worlds.json").read_text(encoding="utf-8"))

def source_table(world):
    return world["cells"]

def oracle_summary(world):
    lines = []
    for state, action in CELLS:
        c = world["cells"][state][action]
        lines.append(f"状态={state}；动作={action}；执行={c['n']}；成功={c['success']}；失败={c['n']-c['success']}")
    return "观察到的历史计数：\n" + "\n".join(lines)

def aggregate_summary(world):
    lines = []
    for action in ["A","B"]:
        c=world["aggregate"][action]
        lines.append(f"动作={action}；执行={c['n']}；成功={c['success']}；失败={c['n']-c['success']}")
    return "观察到的汇总计数：\n" + "\n".join(lines)

def source_text(world):
    return "\n".join(f"状态={s}；动作={a}；执行={world['cells'][s][a]['n']}；成功={world['cells'][s][a]['success']}；失败={world['cells'][s][a]['n']-world['cells'][s][a]['success']}" for s,a in CELLS)

def formation_prompt(world, formation_type, budget):
    prompts={
      "GenericSummary":"把过去这些交互压缩成一条简洁、对未来有帮助的长期记忆。只根据历史经验，不允许编造，保留你认为以后最重要的信息。",
      "ReflectionLesson":"回顾这些经验，总结以后遇到类似任务时值得记住的 lesson。基于经验，不编造，生成简洁 reflection memory。不要给行动建议。",
      "StrategyMemory":"从过去交互中提取未来决策可能有用的策略性经验。忠实，不增加未观察事实。",
      "ConsolidatedExperience":"把重复、零散的经验合并成一条长期 consolidated memory，减少冗余但保留重要信息。忠实，不增加事实。"}
    return f"以下是虚构系统中记录的历史交互计数。\n{source_text(world)}\n\n任务：{prompts[formation_type]}\n只输出 memory 字段。memory 字符数不得超过 {budget}。"

def action_label(action, version):
    return ("Left" if action=="A" else "Right") if version=="AB" else ("Right" if action=="A" else "Left")

def replace_action_labels(memory, version):
    # Token-boundary replacement prevents A in ordinary words from changing.
    temp=re.sub(r"(?<![A-Za-z0-9])A(?![A-Za-z0-9])","__ACTION_A__",memory)
    temp=re.sub(r"(?<![A-Za-z0-9])B(?![A-Za-z0-9])","__ACTION_B__",temp)
    return temp.replace("__ACTION_A__",action_label("A",version)).replace("__ACTION_B__",action_label("B",version))

def faithful_prompt(world, memory):
    return "原始经验表：\n"+source_text(world)+"\n\n待核验记忆：\n"+memory+"\n\n逐项判断记忆明确陈述的事实是否与原始经验一致且有支持。未提及的信息本身不算错误。faithful 仅在无矛盾、无不支持具体事实、无数字错误时为 true。"

def recovery_prompt(memory):
    return "只根据下面的记忆，恢复明确给出的四个状态-动作单元的成功数和执行数。未被明确提供或无法唯一映射的字段一律 null。字段映射：s0_action_a 表示 S0/A，s0_action_b 表示 S0/B，s1_action_a 表示 S1/A，s1_action_b 表示 S1/B。\n\n记忆：\n"+memory

def downstream_prompt(memory):
    return "下面是一条关于过去交互的长期记忆。下一任务状态分布为 P(S0)=0.5、P(S1)=0.5。下一任务将不论状态如何固定采用同一个动作。请分别预测固定采用 Left 与固定采用 Right 时的成功概率，只依据记忆中信息。\n\n记忆：\n"+memory

def parse_json(raw):
    try: return json.loads(raw)
    except Exception: return None

def valid_formation(x, budget):
    return isinstance(x,dict) and set(x)=={"memory"} and isinstance(x["memory"],str) and len(x["memory"])<=budget

def valid_faithfulness(x):
    return isinstance(x,dict) and set(x)=={"contradiction","unsupported_specific_claim","numeric_error","faithful"} and all(type(x[k]) is bool for k in x)

def valid_recovery(x):
    return isinstance(x,dict) and set(x)==set(RECOVERY_FIELDS) and all(x[k] is None or type(x[k]) is int and x[k]>=0 for k in RECOVERY_FIELDS)

def valid_downstream(x):
    return isinstance(x,dict) and set(x)=={"p_success_left","p_success_right"} and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in x.values())

def recovery_accuracy(recovered, world):
    if not valid_recovery(recovered): return None
    correct=0
    for state,action in CELLS:
        prefix=f"{state.lower()}_action_{action.lower()}"
        cell=world["cells"][state][action]
        if recovered[prefix+"_success"]==cell["success"] and recovered[prefix+"_exposure"]==cell["n"]: correct+=1
    return correct/4

def full_structure_retained(recovered, world):
    score=recovery_accuracy(recovered,world)
    return score==1.0 if score is not None else False

def state_label_retained(recovered, world):
    if not valid_recovery(recovered): return False
    return all(any(recovered[f"{state.lower()}_action_{a.lower()}_success"] is not None and recovered[f"{state.lower()}_action_{a.lower()}_exposure"] is not None for a in ["A","B"]) for state in ["S0","S1"])

def action_conditional_structure_retained(recovered, world):
    if not valid_recovery(recovered): return False
    return any(all(recovered[f"{s.lower()}_action_{a.lower()}_success"] is not None and recovered[f"{s.lower()}_action_{a.lower()}_exposure"] is not None for s in ["S0","S1"]) for a in ["A","B"])

def canonical_probabilities(parsed, version):
    if version=="AB": return parsed["p_success_left"],parsed["p_success_right"]
    return parsed["p_success_right"],parsed["p_success_left"]

def regret(predicted_difference, world):
    values={k:float(v) for k,v in world["target_value"].items()}
    optimal=world["optimal_action"]
    chosen="A" if predicted_difference>=0 else "B"
    return values[optimal]-values[chosen]

def pair_resolution(action_w1, action_w2, optimal_w1, optimal_w2):
    return action_w1==optimal_w1 and action_w2==optimal_w2

def bootstrap_mean_ci(values, seed=20261005, draws=10000):
    import numpy as np
    x=np.asarray(values,dtype=float)
    if len(x)==0:return None
    boot=x[np.random.default_rng(seed).integers(0,len(x),(draws,len(x)))].mean(axis=1)
    return float(np.quantile(boot,.025)),float(np.quantile(boot,.975))

def final_verdict(gates, pipeline_invalid=False):
    if pipeline_invalid:return "STAGE3_RECOVERY_PIPELINE_INVALID"
    return "REAL_FORMATION_GO" if all(gates.values()) else "REAL_FORMATION_WEAK"

def verify_frozen():
    tests_path=ROOT/"results"/"tests.json"
    if not tests_path.is_file(): raise RuntimeError("tests.json missing")
    manifest=json.loads(tests_path.read_text())
    if manifest.get("returncode")!=0: raise RuntimeError("frozen preflight tests failed")
    for name,digest in manifest["source_sha256"].items():
        if sha(ROOT/name)!=digest: raise RuntimeError("frozen source changed: "+name)

def source_sha():
    return sha(STAGE2/"cases.json")

def make_source_copy():
    source=STAGE2/"cases.json"
    data=json.loads(source.read_text(encoding="utf-8"))
    checks=json.loads((STAGE2/"results"/"identifiability_checks.json").read_text(encoding="utf-8"))
    assert len(data["pairs"])==20 and len(data["worlds"])==40
    assert checks["verdict"]=="CAUSAL_SUFFICIENCY_MATH_GO" and len(checks["pairs"])==20
    assert all(p["lossy_equal"] and not p["g_preserve_equal"] and p["exact_opposite"] for p in checks["pairs"])
    for pair_id in range(1,21):
        ws=[w for w in data["worlds"] if w["pair_id"]==pair_id]
        assert len(ws)==2 and ws[0]["optimal_action"]!=ws[1]["optimal_action"]
        assert ws[0]["aggregate"]==ws[1]["aggregate"] and ws[0]["cells"]!=ws[1]["cells"]
        for w in ws:
            for action in ["A","B"]:
                n=sum(w["cells"][s][action]["n"] for s in ["S0","S1"])
                success=sum(w["cells"][s][action]["success"] for s in ["S0","S1"])
                assert n==w["aggregate"][action]["n"] and success==w["aggregate"][action]["success"]
    return data
