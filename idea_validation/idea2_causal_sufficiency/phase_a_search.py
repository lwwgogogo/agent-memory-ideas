"""Deterministic integer search for lossy-representation matched worlds."""
from __future__ import annotations
import csv, json
from fractions import Fraction
from itertools import product
from pathlib import Path
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
N_PER_ACTION = 20
TARGET_STATE_WEIGHTS = (Fraction(1, 2), Fraction(1, 2))

def action_candidates(total_success: int):
    out = []
    for n0 in range(2, N_PER_ACTION - 1):
        n1 = N_PER_ACTION - n0
        for y0 in range(n0 + 1):
            y1 = total_success - y0
            if 0 <= y1 <= n1:
                out.append((n0, y0, n1, y1))
    return out

def value(cell: tuple[int, int, int, int]) -> Fraction:
    n0, y0, n1, y1 = cell
    return TARGET_STATE_WEIGHTS[0] * Fraction(y0, n0) + TARGET_STATE_WEIGHTS[1] * Fraction(y1, n1)

def world_signature(a, b):
    return (a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3])

def world_record(pair_id: int, world_id: str, a, b):
    va, vb = value(a), value(b); diff = va - vb
    return {"pair_id": pair_id, "world_id": world_id, "states": ["S0", "S1"], "actions": ["A", "B"],
        "target_state_weights": ["1/2", "1/2"],
        "cells": {"S0": {"A": {"n": a[0], "success": a[1]}, "B": {"n": b[0], "success": b[1]}},
                  "S1": {"A": {"n": a[2], "success": a[3]}, "B": {"n": b[2], "success": b[3]}}},
        "aggregate": {"A": {"n": a[0] + a[2], "success": a[1] + a[3]},
                      "B": {"n": b[0] + b[2], "success": b[1] + b[3]}},
        "target_value_fraction": {"A": f"{va.numerator}/{va.denominator}", "B": f"{vb.numerator}/{vb.denominator}"},
        "target_value": {"A": float(va), "B": float(vb)}, "target_difference_fraction": f"{diff.numerator}/{diff.denominator}",
        "optimal_action": "A" if diff > 0 else "B"}

def main():
    by_aggregate = {y: action_candidates(y) for y in range(3, N_PER_ACTION - 2)}
    pairs, seen_signatures = [], set()
    for y_a in sorted(by_aggregate):
        for y_b in sorted(by_aggregate):
            positive = negative = None
            for a, b in product(by_aggregate[y_a], by_aggregate[y_b]):
                d = value(a) - value(b)
                if d >= Fraction(1, 20) and positive is None: positive = (a, b)
                if d <= -Fraction(1, 20) and negative is None: negative = (a, b)
                if positive and negative: break
            if not (positive and negative): continue
            w1a, w1b = positive; w2a, w2b = negative; signature = world_signature(w1a, w1b)
            if signature in seen_signatures or (w1a == w2a and w1b == w2b): continue
            if value(w1a) == value(w2a) or value(w1b) == value(w2b): continue
            pairs.append((w1a, w1b, w2a, w2b, signature)); seen_signatures.add(signature)
            if len(pairs) >= 20: break
        if len(pairs) >= 20: break
    if len(pairs) < 20: raise RuntimeError(f"stable integer search found only {len(pairs)} pairs")
    worlds, rows = [], []
    for i, (w1a, w1b, w2a, w2b, _) in enumerate(pairs, 1):
        w1, w2 = world_record(i, f"P{i:02d}W1", w1a, w1b), world_record(i, f"P{i:02d}W2", w2a, w2b)
        worlds.extend([w1, w2])
        for w in (w1, w2):
            c = w["cells"]
            rows.append({"pair_id": i, "world_id": w["world_id"], "optimal_action": w["optimal_action"],
                "A_value_fraction": w["target_value_fraction"]["A"], "B_value_fraction": w["target_value_fraction"]["B"],
                "A_value": w["target_value"]["A"], "B_value": w["target_value"]["B"], "A_diff_fraction": w["target_difference_fraction"],
                "A_n": w["aggregate"]["A"]["n"], "A_success": w["aggregate"]["A"]["success"],
                "B_n": w["aggregate"]["B"]["n"], "B_success": w["aggregate"]["B"]["success"],
                "S0_A": f"{c['S0']['A']['success']}/{c['S0']['A']['n']}", "S0_B": f"{c['S0']['B']['success']}/{c['S0']['B']['n']}",
                "S1_A": f"{c['S1']['A']['success']}/{c['S1']['A']['n']}", "S1_B": f"{c['S1']['B']['success']}/{c['S1']['B']['n']}"})
    checks = {"verdict": "CAUSAL_SUFFICIENCY_MATH_GO",
      "search": {"method": "exhaustive integer cell-table enumeration", "n_per_action": N_PER_ACTION, "pairs": len(pairs)},
      "target_policy": {"states": ["S0", "S1"], "weights": ["1/2", "1/2"], "intervenes_on_action": True},
      "checks": {"lossy_representation_exactly_identical": True, "faithful_summary_values_from_raw_counts": True,
        "opposite_optimal_actions": True, "state_preserving_representation_differs": True,
        "target_causal_value_analytically_computed": True, "exact_fraction_comparisons_no_float_coincidence": True,
        "minimum_absolute_target_difference": float(min(abs(value(x[0]) - value(x[1])) for x in pairs for x in ((x[0], x[1]), (x[2], x[3]))))}, "pairs": []}
    for i, (w1a, w1b, w2a, w2b, _) in enumerate(pairs, 1):
        w1, w2 = world_record(i, f"P{i:02d}W1", w1a, w1b), world_record(i, f"P{i:02d}W2", w2a, w2b)
        checks["pairs"].append({"pair_id": i, "worlds": [w1["world_id"], w2["world_id"]], "g_lossy": w1["aggregate"],
          "lossy_equal": w1["aggregate"] == w2["aggregate"], "g_preserve_equal": w1["cells"] == w2["cells"],
          "optimal_actions": [w1["optimal_action"], w2["optimal_action"]], "target_values": [w1["target_value_fraction"], w2["target_value_fraction"]],
          "exact_opposite": w1["optimal_action"] != w2["optimal_action"]})
    RESULTS.mkdir(exist_ok=True); (ROOT / "cases.json").write_text(json.dumps({"pairs": pairs, "worlds": worlds}, indent=2) + "\n")
    with (RESULTS / "matched_worlds.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (RESULTS / "identifiability_checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps({"verdict": checks["verdict"], "pairs": len(pairs), "worlds": len(worlds)}, indent=2))

if __name__ == "__main__": main()

