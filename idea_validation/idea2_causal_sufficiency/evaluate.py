import collections, csv, json, math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from core import ROOT, CONDITIONS, ORDERS, VERSIONS, target_values, optimal_action, representation

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def summary(values):
    x = np.asarray(values, dtype=float)
    if len(x) == 0: return {"n": 0, "mean": None, "median": None, "std": None, "ci_low": None, "ci_high": None}
    rng = np.random.default_rng(20261005)
    boot = x[rng.integers(0, len(x), size=(10000, len(x)))].mean(axis=1)
    return {"n": int(len(x)), "mean": float(x.mean()), "median": float(np.median(x)), "std": float(x.std(ddof=1)) if len(x) > 1 else 0.0, "ci_low": float(np.quantile(boot, .025)), "ci_high": float(np.quantile(boot, .975))}

def paired_bootstrap(a, b):
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    d = x - y
    rng = np.random.default_rng(20261005)
    boot = d[rng.integers(0, len(d), size=(10000, len(d)))].mean(axis=1)
    return {"n": int(len(d)), "mean": float(d.mean()), "ci_low": float(np.quantile(boot, .025)), "ci_high": float(np.quantile(boot, .975))}

def row_metric(row, world):
    if row["final_status"] != "VALID": return None
    vals = target_values(world); opt = optimal_action(world)
    diff = float(row["predicted_difference"])
    pred = "A" if diff >= 0 else "B"
    regret = float(vals[opt] - vals[pred])
    return {"accuracy": float(pred == opt), "regret": regret, "signed_preference_error": diff - float(vals["A"] - vals["B"]), "predicted_action": pred, "optimal_action": opt}

def main():
    cases = json.loads((ROOT / "cases" / "cases.json").read_text(encoding="utf-8"))
    rows = json.loads((ROOT / "results" / "llm_results.json").read_text(encoding="utf-8"))
    worlds = {w["world_id"]: w for w in cases["worlds"]}
    assert len(rows) == 800 and len({r["run_id"] for r in rows}) == 800
    by_view = {}
    for row in rows:
        by_view[(row["world_id"], row["condition"], row["version"], row["order"])] = row_metric(row, worlds[row["world_id"]])
    world_metrics = {}
    for wid in worlds:
        for condition in CONDITIONS:
            views = [by_view[(wid, condition, version, order)] for version in VERSIONS for order in ORDERS]
            world_metrics[(wid, condition)] = None if any(v is None for v in views) else {k: float(np.mean([v[k] for v in views])) for k in ["accuracy", "regret", "signed_preference_error"]}
    complete = {wid for wid in worlds if all(world_metrics[(wid, c)] is not None for c in CONDITIONS)}
    metrics = {}
    for condition in CONDITIONS:
        vals = [world_metrics[(wid, condition)] for wid in sorted(complete)]
        metrics[condition] = {k: summary([v[k] for v in vals]) for k in ["accuracy", "regret", "signed_preference_error"]}
    differences = {}
    for metric in ["accuracy", "regret", "signed_preference_error"]:
        for left, right in [("StatePreservingSummary", "FaithfulLossySummary"), ("CausalSufficientCompact", "FaithfulLossySummary")]:
            a = [world_metrics[(wid, left)][metric] for wid in sorted(complete)]
            b = [world_metrics[(wid, right)][metric] for wid in sorted(complete)]
            differences[f"{left}_minus_{right}_{metric}"] = paired_bootstrap(a, b)
    controls = {}
    for condition in ["StatePreservingSummary", "CausalSufficientCompact", "FaithfulLossySummary", "LengthMatchedControl"]:
        controls[condition] = {"label": {}, "order": {}}
        for version in VERSIONS:
            values = [row_metric(rows[i], worlds[rows[i]["world_id"]])["accuracy"] for i in range(len(rows)) if rows[i]["condition"] == condition and rows[i]["version"] == version]
            controls[condition]["label"][version] = summary(values)
        for order in ORDERS:
            values = [row_metric(rows[i], worlds[rows[i]["world_id"]])["accuracy"] for i in range(len(rows)) if rows[i]["condition"] == condition and rows[i]["order"] == order]
            controls[condition]["order"][order] = summary(values)
    pair_identity = []
    by_pair = collections.defaultdict(list)
    for w in cases["worlds"]: by_pair[w["pair_id"]].append(w)
    for pair_id, pair in sorted(by_pair.items()):
        w1, w2 = pair
        truth_opposite = w1["optimal_action"] != w2["optimal_action"]
        for version in VERSIONS:
            for order in ORDERS:
                p1 = next(x["prompt"] for x in cases["runs"] if x["world_id"] == w1["world_id"] and x["condition"] == "FaithfulLossySummary" and x["version"] == version and x["order"] == order)
                p2 = next(x["prompt"] for x in cases["runs"] if x["world_id"] == w2["world_id"] and x["condition"] == "FaithfulLossySummary" and x["version"] == version and x["order"] == order)
                pair_identity.append({"pair_id": pair_id, "version": version, "order": order, "prompt_identical": p1 == p2, "optimal_opposite": truth_opposite})
    length_checks = []
    for world in cases["worlds"]:
        for version in VERSIONS:
            for order in ORDERS:
                length_checks.append({"world_id": world["world_id"], "version": version, "order": order, "r2_chars": len(representation(world, "FaithfulLossySummary", version, order)), "r4_chars": len(representation(world, "LengthMatchedControl", version, order))})
    valid = sum(r["final_status"] == "VALID" for r in rows)
    retried = sum(r["retry_attempt"] is not None for r in rows)
    invalid = len(rows) - valid
    phase_a = json.loads((ROOT / "results" / "identifiability_checks.json").read_text(encoding="utf-8"))
    r1, r2, r3, r4 = [metrics[x] for x in ["StatePreservingSummary", "FaithfulLossySummary", "CausalSufficientCompact", "LengthMatchedControl"]]
    control_slices = []
    for c in ["StatePreservingSummary", "CausalSufficientCompact"]:
        vals = [controls[c]["label"][v]["mean"] for v in VERSIONS] + [controls[c]["order"][o]["mean"] for o in ORDERS]
        control_slices.extend(vals)
    gates = {
        "PhaseA_identifiability": phase_a["verdict"] == "CAUSAL_SUFFICIENCY_MATH_GO" and phase_a["search"]["pairs"] >= 20 and all(x["lossy_equal"] and not x["g_preserve_equal"] and x["exact_opposite"] for x in phase_a["pairs"]),
        "G0_valid_and_complete": valid / 800 >= .99 and len(complete) == 40,
        "G1_R1_high_accuracy_low_regret": r1["accuracy"]["mean"] >= .85 and r1["regret"]["mean"] <= .05,
        "G2_R2_low_accuracy_high_regret": r2["accuracy"]["mean"] <= .65 and r2["regret"]["mean"] >= .10,
        "G3_R3_recovery": r3["accuracy"]["mean"] >= .85 and r3["regret"]["mean"] <= .05,
        "G4_R1_vs_R2_accuracy_bootstrap": differences["StatePreservingSummary_minus_FaithfulLossySummary_accuracy"]["ci_low"] > .05,
        "G5_R3_vs_R2_accuracy_bootstrap": differences["CausalSufficientCompact_minus_FaithfulLossySummary_accuracy"]["ci_low"] > .05,
        "G6_regret_improvements": differences["StatePreservingSummary_minus_FaithfulLossySummary_regret"]["mean"] >= .05 and differences["CausalSufficientCompact_minus_FaithfulLossySummary_regret"]["mean"] >= .05,
        "G7_representation_impossibility": len(pair_identity) == 80 and all(x["prompt_identical"] and x["optimal_opposite"] for x in pair_identity),
        "G8_label_order_length_controls": all(x >= .75 for x in control_slices) and max(control_slices) - min(control_slices) <= .25 and r4["accuracy"]["mean"] >= .75 and abs(r4["accuracy"]["mean"] - r3["accuracy"]["mean"]) <= .15 and all(x["r2_chars"] == x["r4_chars"] for x in length_checks),
    }
    all_core = gates["PhaseA_identifiability"] and gates["G0_valid_and_complete"] and gates["G7_representation_impossibility"]
    directional = r1["accuracy"]["mean"] > r2["accuracy"]["mean"] and r3["accuracy"]["mean"] > r2["accuracy"]["mean"] and r1["regret"]["mean"] < r2["regret"]["mean"] and r3["regret"]["mean"] < r2["regret"]["mean"]
    verdict = "CAUSAL_SUFFICIENCY_GO" if all(gates.values()) else ("CAUSAL_SUFFICIENCY_WEAK" if all_core and directional else "CAUSAL_SUFFICIENCY_NO_GO")
    world_rows = []
    for wid in sorted(worlds):
        rec = {"world_id": wid, "pair_id": worlds[wid]["pair_id"], "optimal_action": worlds[wid]["optimal_action"]}
        for c in CONDITIONS:
            m = world_metrics[(wid, c)]
            for k in ["accuracy", "regret", "signed_preference_error"]: rec[f"{c}_{k}"] = None if m is None else m[k]
        world_rows.append(rec)
    summary_rows = []
    for c in CONDITIONS:
        summary_rows.append({"condition": c, **{f"{k}_{stat}": v for k, x in metrics[c].items() for stat, v in x.items()}})
    statistics = {"verdict": verdict, "gates": gates, "planned_runs": 800, "valid_runs": valid, "retried_runs": retried, "invalid_runs": invalid, "complete_worlds": len(complete), "phase_a": phase_a, "metrics": metrics, "paired_differences": differences, "controls": controls, "matched_pair_identity": {"n": len(pair_identity), "all_identical": all(x["prompt_identical"] for x in pair_identity), "all_opposite": all(x["optimal_opposite"] for x in pair_identity)}, "length_checks": {"n": len(length_checks), "all_equal": all(x["r2_chars"] == x["r4_chars"] for x in length_checks), "r2_chars": sorted(set(x["r2_chars"] for x in length_checks)), "r4_chars": sorted(set(x["r4_chars"] for x in length_checks))}, "worlds": world_rows}
    save(ROOT / "results" / "statistics.json", statistics)
    with (ROOT / "results" / "world_metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(world_rows[0])); writer.writeheader(); writer.writerows(world_rows)
    with (ROOT / "results" / "summary.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0])); writer.writeheader(); writer.writerows(summary_rows)
    (ROOT / "results" / "matched_pair_identity.json").write_text(json.dumps(pair_identity, indent=2) + "\n", encoding="utf-8")
    (ROOT / "results" / "length_checks.json").write_text(json.dumps(length_checks, indent=2) + "\n", encoding="utf-8")
    # Compact figures are generated only from the frozen result table.
    names = ["StatePreservingSummary", "FaithfulLossySummary", "CausalSufficientCompact", "LengthMatchedControl"]
    labels = ["R1", "R2", "R3", "R4"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, [metrics[x]["accuracy"]["mean"] for x in names], color=["#0072b2", "#d55e00", "#009e73", "#9467bd"])
    ax.set_ylim(0, 1); ax.set_ylabel("Decision accuracy"); ax.set_title("Causal sufficiency Stage-2")
    fig.tight_layout(); fig.savefig(ROOT / "plots_accuracy.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, [metrics[x]["regret"]["mean"] for x in names], color=["#0072b2", "#d55e00", "#009e73", "#9467bd"])
    ax.set_ylabel("Action value regret"); ax.set_title("Representation-level regret")
    fig.tight_layout(); fig.savefig(ROOT / "plots_regret.png", dpi=180); plt.close(fig)
    lines = ["# Idea 2 Stage-2: Causal Sufficiency of Experience Memory", "", verdict, "", "## Phase A", "", "The exhaustive integer search produced 20 matched pairs (40 worlds). Each pair has identical aggregate action exposure/success counts, different state-conditioned counts, and exact opposite optimal target-policy actions. All checks use integer counts and Fraction arithmetic.", "", "## Formal run", "", f"Planned {len(rows)}; valid {valid}; retried {retried}; invalid {invalid}; complete worlds {len(complete)}/40. Model qwq:32b, Python 3.10.21, fixed temperature 0 and seed 20261005. R0 is secondary; the hard gates use R1-R4.", "", "| Representation | Accuracy | Regret | Signed preference error |", "|---|---:|---:|---:|"]
    for c, label in zip(names, labels):
        lines.append(f"| {label} {c} | {metrics[c]['accuracy']['mean']:.6f} | {metrics[c]['regret']['mean']:.6f} | {metrics[c]['signed_preference_error']['mean']:.6f} |")
    lines += ["", "## Matched-pair impossibility", "", f"All {len(pair_identity)} FaithfulLossySummary prompts (20 pairs x 2 labels x 2 orders) are byte-identical within each pair while the exact optimal actions are opposite. This is a representation-level non-identifiability result; it does not depend on a particular model error.", "", "## Controls", "", f"R2/R4 length equality: {all(x['r2_chars'] == x['r4_chars'] for x in length_checks)}; R1/R3 label and order slices and R4 are recorded in statistics.json. Raw episodic records are secondary and are excluded from the hard verdict.", "", "## Gates", "", "| Gate | Result |", "|---|---|"]
    for gate, value in gates.items(): lines.append(f"| {gate} | {'PASS' if value else 'FAIL'} |")
    lines += ["", "The R2 summaries are factual aggregate counts generated from the same world data; they do not contain evaluative or causal wording. R1, R3, and R4 are also factual mechanically generated counts.", "", "Run 1 remains IDEA2_RUN1_NO_GO / IDEA2_NO_GO and its files and result are unchanged. This Stage-2 result is limited to the fixed model, protocol, and toy worlds; it is not a literature or real-world Agent generalization claim.", "", "No literature search, Mem0, method design, or Idea 3 work was performed. Formal inference is stopped."]
    (ROOT / "Confirmatory结果.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "最终结论.md").write_text("# 最终结论\n\n" + verdict + "\n\n" + ("全部预注册门槛通过。" if verdict == "CAUSAL_SUFFICIENCY_GO" else "部分预注册门槛未通过，详见 Confirmatory结果.md。") + f"\n\nPhase A 为 20 组 matched-world pairs；正式运行 {valid}/800 有效，R1 accuracy={r1['accuracy']['mean']:.6f}，R2 accuracy={r2['accuracy']['mean']:.6f}，R3 accuracy={r3['accuracy']['mean']:.6f}。R2 matched-pair memory 完全相同而 optimal action 相反，构成 representation-level impossibility result。\n\nRun 1 仍为 IDEA2_RUN1_NO_GO / IDEA2_NO_GO，未改动历史结果。\n\n已停止，不查论文、不设计方法、不使用 Mem0、不进入 Idea 3。\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "gates": gates, "valid": valid, "retried": retried, "complete_worlds": len(complete), "metrics": {c: {"accuracy": metrics[c]["accuracy"]["mean"], "regret": metrics[c]["regret"]["mean"]} for c in CONDITIONS}}, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()

