"""Single locked deterministic formal run for Idea 2 Stage-8."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from jitrl_adapter import STAGE_DIR, adapter_mapping, native_method_ast_hashes
from native_probe import (
    B3_EPISODES,
    CLOSED_LOOP_REASON,
    CLOSED_LOOP_STATUS,
    FORMAL_SEED,
    baseline_records,
    probe_case,
    summarize_baselines,
)
from verify import finalize, verify_manifest

RESULTS = STAGE_DIR / "results"
PLOTS = STAGE_DIR / "plots"


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rate(rows: Iterable[Dict[str, Any]], field: str) -> float:
    values = [bool(row[field]) for row in rows]
    return sum(values) / len(values)


def make_plots(cases: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    labels = ["Same policy", "Policy shift"]
    x = np.arange(len(labels))
    width = 0.34
    native = [row["native_raw_advantage"] for row in cases]
    target = [row["target_advantage"] for row in cases]
    with plt.rc_context({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(6.2, 3.8), layout="constrained")
        ax.bar(x - width / 2, native, width, label="JitRL historical raw advantage", color="#0072B2", hatch="//")
        ax.bar(x + width / 2, target, width, label="Exact target-policy advantage", color="#D55E00", hatch="..")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks(x, labels)
        ax.set_ylabel("Advantage signal")
        ax.set_title("Historical signal versus current-policy oracle")
        ax.legend(frameon=False)
        fig.savefig(PLOTS / "historical_vs_target_advantage.png", dpi=180)
        plt.close(fig)

        names = ["NoMemory", "JitRLNative", "OracleValidity"]
        returns = [summary[name]["average_return"] for name in names]
        colors = ["#009E73", "#D55E00", "#0072B2"]
        fig, ax = plt.subplots(figsize=(6.2, 3.8), layout="constrained")
        bars = ax.bar(names, returns, color=colors, edgecolor="black", linewidth=0.5)
        for bar, hatch in zip(bars, ["", "//", ".."]):
            bar.set_hatch(hatch)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_ylabel("Average return")
        ax.set_title("Policy-shift behavioral effect (20 deterministic episodes)")
        fig.savefig(PLOTS / "policy_bias_effect.png", dpi=180)
        plt.close(fig)


def main() -> Dict[str, Any]:
    if (RESULTS / "formal_started.json").exists():
        raise RuntimeError("Formal run already started; restart requires explicit bug protocol")
    lock = verify_manifest()
    if not lock["ok"]:
        raise RuntimeError(f"Pre-registration lock failed: {lock}")
    pretests = json.loads((RESULTS / "preformal_tests.json").read_text(encoding="utf-8"))
    if pretests["status"] != "PASS":
        raise RuntimeError("Preformal tests did not pass")
    for name in (
        "source_target_trace.csv", "advantage_mismatch.csv", "baseline_results.csv",
        "experiment_summary.json", "gate_results.json", "final_verification.json",
    ):
        if (RESULTS / name).exists():
            raise RuntimeError(f"Refusing to overwrite formal output: {name}")

    (RESULTS / "formal_started.json").write_text(
        json.dumps({
            "formal_run_id": "stage8_formal_001",
            "formal_run_count": 1,
            "restart": False,
            "seed": FORMAL_SEED,
            "b3_episodes": B3_EPISODES,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    b1 = probe_case("pi_A")
    b2 = probe_case("pi_B")
    cases = [b1, b2]
    trace_fields = [
        "condition", "source_policy", "target_policy", "historical_action",
        "historical_return", "historical_q_source", "historical_advantage_source",
        "retrieved", "retrieved_count", "retrieval_score", "native_memory_signal",
        "native_raw_advantage", "target_q", "target_advantage", "target_q_right",
        "signal_sign_match", "sign_mismatch", "positive_historical_negative_target",
        "base_action", "chosen_action", "optimal_action", "policy_bias_applied",
        "chosen_return", "regret", "harmful_memory_use", "harmful_policy_bias",
        "memory_read", "oracle_read",
    ]
    trace = [{field: row[field] for field in trace_fields} for row in cases]
    write_csv(RESULTS / "source_target_trace.csv", trace)
    write_csv(RESULTS / "advantage_mismatch.csv", trace)

    baseline = baseline_records()
    write_csv(RESULTS / "baseline_results.csv", baseline)
    b3_summary = summarize_baselines(baseline)
    metrics = {
        "NativeRetrievalRate": rate(cases, "retrieved"),
        "NativeSignal": {"B1": b1["native_memory_signal"], "B2": b2["native_memory_signal"]},
        "TargetOracleSignal": {"B1": b1["target_advantage"], "B2": b2["target_advantage"]},
        "SignalMismatchRate": rate(cases, "sign_mismatch"),
        "PolicyShiftSignalMismatchRate": float(b2["sign_mismatch"]),
        "PositiveHistoricalNegativeTargetRate": float(b2["positive_historical_negative_target"]),
        "HarmfulMemoryUseRate": b3_summary["JitRLNative"]["harmful_memory_use_rate"],
        "HarmfulPolicyBiasRate": b3_summary["JitRLNative"]["harmful_policy_bias_rate"],
        "AverageReturn": {key: value["average_return"] for key, value in b3_summary.items()},
        "CumulativeRegret": {key: value["cumulative_regret"] for key, value in b3_summary.items()},
        "ValidityFlipCount": None,
    }
    payload = {
        "stage": "Idea 2 Stage-8B",
        "formal_seed": FORMAL_SEED,
        "B1": b1,
        "B2": b2,
        "B3": b3_summary,
        "B4": {"status": CLOSED_LOOP_STATUS, "validity_flip_count": None, "reason": CLOSED_LOOP_REASON},
        "metrics": metrics,
        "native_execution": {
            "source_extracted_methods": True,
            "adapter_boundary_only": True,
            "method_ast_hashes": native_method_ast_hashes(),
            "mapping": adapter_mapping(),
        },
    }
    (RESULTS / "experiment_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    make_plots(cases, b3_summary)
    final = finalize()
    print(json.dumps(final, indent=2, sort_keys=True))
    return final


if __name__ == "__main__":
    main()
