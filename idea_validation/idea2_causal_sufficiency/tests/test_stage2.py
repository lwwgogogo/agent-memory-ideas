import json
from fractions import Fraction
from pathlib import Path
import pytest
from core import ROOT, CONDITIONS, ORDERS, VERSIONS, make_prompt, representation, run_with_retry, validate_parsed, target_values, optimal_action

def load():
    return json.loads((ROOT / "cases.json").read_text())

def test_phase_a_identifiability():
    checks = json.loads((ROOT / "results" / "identifiability_checks.json").read_text())
    assert checks["verdict"] == "CAUSAL_SUFFICIENCY_MATH_GO"
    assert checks["search"]["pairs"] >= 20
    assert all(x["lossy_equal"] and not x["g_preserve_equal"] and x["exact_opposite"] for x in checks["pairs"])

def test_exact_world_values_and_opposites():
    data = load()
    assert len(data["pairs"]) == 20 and len(data["worlds"]) == 40
    for world in data["worlds"]:
        values = target_values(world)
        assert all(isinstance(v, Fraction) for v in values.values())
        assert optimal_action(world) == world["optimal_action"]
        assert values["A"] != values["B"]
        for action in ["A", "B"]:
            c = world["aggregate"][action]
            assert sum(world["cells"][state][action]["n"] for state in ["S0", "S1"]) == c["n"]
            assert sum(world["cells"][state][action]["success"] for state in ["S0", "S1"]) == c["success"]

def test_raw_and_factual_representations():
    data = load()
    for world in data["worlds"]:
        raw = representation(world, "RawEpisodic", "AB", "O1")
        assert raw.count("X=") == sum(world["aggregate"][a]["n"] for a in ["A", "B"])
        for order in ORDERS:
            r1 = representation(world, "StatePreservingSummary", "AB", order)
            r2 = representation(world, "FaithfulLossySummary", "AB", order)
            r3 = representation(world, "CausalSufficientCompact", "AB", order)
            r4 = representation(world, "LengthMatchedControl", "AB", order)
            for state in ["S0", "S1"]:
                for action in ["A", "B"]:
                    cell = world["cells"][state][action]
                    assert f"state={state}" in r1 and f"exposure={cell['n']}" in r1 and f"success={cell['success']}" in r1
                    assert f"{cell['success']}/{cell['n']}" in r3
                    assert f"state:{state}" in r4
            for action in ["A", "B"]:
                cell = world["aggregate"][action]
                assert f"exposure={cell['n']}" in r2 and f"success={cell['success']}" in r2
            assert len(r2) == len(r4) == 256

def test_lossy_prompt_identity_and_state_difference():
    data = load()
    by_pair = {}
    for world in data["worlds"]:
        by_pair.setdefault(world["pair_id"], []).append(world)
    for pair in by_pair.values():
        assert pair[0]["aggregate"] == pair[1]["aggregate"]
        assert pair[0]["cells"] != pair[1]["cells"]
        assert pair[0]["optimal_action"] != pair[1]["optimal_action"]
        for version in VERSIONS:
            for order in ORDERS:
                assert make_prompt(pair[0], "FaithfulLossySummary", version, order) == make_prompt(pair[1], "FaithfulLossySummary", version, order)
                assert make_prompt(pair[0], "StatePreservingSummary", version, order) != make_prompt(pair[1], "StatePreservingSummary", version, order)

def test_validator_and_one_retry_same_prompt():
    calls = []
    def invoke(prompt, attempt):
        calls.append((prompt, attempt))
        return {"raw": "bad"} if attempt == 0 else {"raw": '{"p_success_left":0.4,"p_success_right":0.6}'}
    result = run_with_retry("same", invoke)
    assert result["final_status"] == "VALID" and result["retry_attempt"] is not None
    assert calls == [("same", 0), ("same", 1)]
    assert validate_parsed({"p_success_left": 0.2, "p_success_right": 0.8})[0]
    assert not validate_parsed({"p_success_left": 2, "p_success_right": 0.8})[0]

def test_job_count_and_formal_cases():
    data = json.loads((ROOT / "cases" / "cases.json").read_text())
    assert len(data["worlds"]) == 40 and len(data["runs"]) == 800
    assert len({x["run_id"] for x in data["runs"]}) == 800

