from __future__ import annotations
import datetime, hashlib, json, math, sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = "qwq:32b"
OPTIONS = {"temperature": 0, "top_p": 1.0, "seed": 20261005, "num_ctx": 4096, "num_predict": 128}
SYSTEM = "Output only one JSON object with exactly p_success_left and p_success_right. Each value must be a decimal probability from 0 to 1, such as 0.55. Do not output choice, reason, confidence, or any explanation."
SCHEMA = {"type": "object", "properties": {"p_success_left": {"type": "number", "minimum": 0, "maximum": 1}, "p_success_right": {"type": "number", "minimum": 0, "maximum": 1}}, "required": ["p_success_left", "p_success_right"], "additionalProperties": False}
CONDITIONS = ["RawEpisodic", "StatePreservingSummary", "FaithfulLossySummary", "CausalSufficientCompact", "LengthMatchedControl"]
PRIMARY = ["StatePreservingSummary", "FaithfulLossySummary", "CausalSufficientCompact", "LengthMatchedControl"]
ORDERS = ["O1", "O2"]
VERSIONS = ["AB", "BA"]
MEMORY_WIDTH = 256

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def load_worlds():
    return json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["worlds"]

def world_cells(world):
    return {(state, action): world["cells"][state][action] for state in ["S0", "S1"] for action in ["A", "B"]}

def display_action(action: str, version: str) -> str:
    return "Left" if (action == "A") == (version == "AB") else "Right"

def ordered_cells(order):
    base = [("S0", "A"), ("S0", "B"), ("S1", "A"), ("S1", "B")]
    return base if order == "O1" else list(reversed(base))

def target_values(world):
    cells = world_cells(world)
    return {action: sum((Fraction(cells[(state, action)]["success"], cells[(state, action)]["n"]) for state in ["S0", "S1"]), Fraction(0)) / 2 for action in ["A", "B"]}

def optimal_action(world):
    values = target_values(world)
    if values["A"] == values["B"]:
        raise AssertionError("search promised strict target-policy differences")
    return "A" if values["A"] > values["B"] else "B"

def _pad(text: str) -> str:
    note = " Neutral format note: every listed entry is an observed count."
    while len(text) < MEMORY_WIDTH:
        text += note
    return text[:MEMORY_WIDTH]

def representation(world, condition: str, version: str, order: str) -> str:
    cells = world_cells(world)
    if condition == "RawEpisodic":
        records = []
        for state, action in ordered_cells(order):
            cell = cells[(state, action)]
            records += [f"X={state};A={display_action(action, version)};Y=1" for _ in range(cell["success"])]
            records += [f"X={state};A={display_action(action, version)};Y=0" for _ in range(cell["n"] - cell["success"])]
        return "Observed experience records:\n" + "\n".join(records)
    if condition == "FaithfulLossySummary":
        actions = ["A", "B"] if order == "O1" else ["B", "A"]
        lines = ["Observed aggregate action counts:"]
        for action in actions:
            cell = world["aggregate"][action]
            lines.append(f"action={display_action(action, version)};exposure={cell['n']};success={cell['success']};failure={cell['n']-cell['success']}")
        return _pad("\n".join(lines))
    if condition == "StatePreservingSummary":
        lines = ["Observed state and action counts:"]
        for state, action in ordered_cells(order):
            cell = cells[(state, action)]
            lines.append(f"state={state};action={display_action(action, version)};exposure={cell['n']};success={cell['success']};failure={cell['n']-cell['success']}")
        return _pad("\n".join(lines))
    if condition == "CausalSufficientCompact":
        lines = ["Observed state-action success counts:"]
        for state, action in ordered_cells(order):
            cell = cells[(state, action)]
            lines.append(f"{state}|{display_action(action, version)}|{cell['success']}/{cell['n']}")
        return _pad("\n".join(lines))
    if condition == "LengthMatchedControl":
        lines = ["Observed state-action count facts:"]
        for state, action in ordered_cells(order):
            cell = cells[(state, action)]
            lines.append(f"state:{state},action:{display_action(action, version)},success:{cell['success']},exposure:{cell['n']},failure:{cell['n']-cell['success']}")
        return _pad("\n".join(lines))
    raise KeyError(condition)

def make_prompt(world, condition: str, version: str, order: str) -> str:
    memory = representation(world, condition, version, order)
    return ("This is a neutral fictional decision system. The next state is sampled with probability 1/2 for S0 and 1/2 for S1. "
            "For the next task, one fixed action is used regardless of state. Based only on the observed experience information below, "
            "predict separately the success probability if the fixed action is Left and if the fixed action is Right. "
            "The response format is specified separately.\n\n" + memory)

def validate_parsed(value):
    if not isinstance(value, dict) or set(value) != {"p_success_left", "p_success_right"}:
        return False, "schema_keys"
    for key in ["p_success_left", "p_success_right"]:
        x = value[key]
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 1:
            return False, "probability_range"
    return True, None

def parse(raw: str):
    try:
        value = json.loads(raw)
    except Exception:
        return None
    ok, _ = validate_parsed(value)
    return value if ok else None

def canonical(parsed, version):
    return (parsed["p_success_left"], parsed["p_success_right"]) if version == "AB" else (parsed["p_success_right"], parsed["p_success_left"])

def run_with_retry(prompt, invoke):
    first = invoke(prompt, 0)
    first_parsed = parse(first.get("raw", "")) if "raw" in first else None
    first["parsed"] = first_parsed
    first["valid"] = first_parsed is not None
    first["retryable"] = first_parsed is None and "transport_error" not in first
    if first["valid"]:
        return {"first_attempt": first, "retry_attempt": None, "final_status": "VALID", "parsed": first_parsed}
    if not first["retryable"]:
        return {"first_attempt": first, "retry_attempt": None, "final_status": "INVALID", "parsed": None}
    retry = invoke(prompt, 1)
    retry_parsed = parse(retry.get("raw", "")) if "raw" in retry else None
    retry["parsed"] = retry_parsed; retry["valid"] = retry_parsed is not None; retry["retryable"] = False
    return {"first_attempt": first, "retry_attempt": retry, "final_status": "VALID" if retry_parsed is not None else "INVALID", "parsed": retry_parsed}

def ensure_env():
    if sys.version_info[:3] != (3, 10, 21):
        raise RuntimeError(f"required Python 3.10.21, got {sys.version}")

