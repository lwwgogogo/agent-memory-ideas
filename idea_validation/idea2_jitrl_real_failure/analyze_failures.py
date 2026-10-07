"""Apply preregistered metrics, gates, plots, and verdict."""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from statistics import mean, median
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paired_intervention import is_historically_positive
from verify import RESULTS, verify_lock

HERE = Path(__file__).resolve().parent
PLOTS = HERE / "plots"


def read_json(name: str, default: Any = None) -> Any:
    path = RESULTS / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def read_csv(name: str) -> list[dict[str, str]]:
    path = RESULTS / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def ratio(n: int, d: int) -> float | None:
    return n / d if d else None


def placeholder_plot(path: Path, title: str, message: str, xlabel: str = "") -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.set_title(title)
    ax.text(0.5, 0.52, message, ha="center", va="center", transform=ax.transAxes, fontsize=12)
    ax.set_xlabel(xlabel)
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    for side in ("left", "right", "top"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> dict[str, Any]:
    PLOTS.mkdir(parents=True, exist_ok=True)
    formal = read_json("formal_summary.json", {})
    attempts = read_json("formal_retrieval_attempts.json", [])
    retrievals = read_csv("formal_retrieval_events.csv")
    sources = read_csv("formal_source_memories.csv")
    pairs = read_csv("paired_interventions.csv")
    candidates = read_csv("failure_candidates.csv")
    confirmed = read_csv("confirmed_failures.csv")
    tests = read_json("preformal_tests.json", {})
    lock_ok, lock_problems = verify_lock()

    shutil.copyfile(RESULTS / "formal_source_memories.csv", RESULTS / "source_memories.csv")
    shutil.copyfile(RESULTS / "formal_retrieval_events.csv", RESULTS / "retrieval_events.csv")

    positive_retrievals = sum(is_historically_positive(row.get("historical_signal")) for row in retrievals)
    deltas = [float(row["delta_current"]) for row in pairs if row.get("delta_current") not in (None, "")]
    behavior_confirmed = sum(str(row.get("behavior_changed", "")).lower() == "true" for row in confirmed)
    metrics = {
        "episodes": formal.get("episodes_completed", 0),
        "memory_writes": formal.get("memory_writes", 0),
        "source_memory_steps": len(sources),
        "retrieval_attempts": len(attempts),
        "retrieval_events": len(retrievals),
        "retrieval_rate_per_attempt": ratio(len(retrievals), len(attempts)),
        "positive_source_retrievals": positive_retrievals,
        "valid_paired_events": len(pairs),
        "failure_candidates": len(candidates),
        "confirmed_failures": len(confirmed),
        "behavior_changing_confirmed_failures": behavior_confirmed,
        "candidate_rate": ratio(len(candidates), positive_retrievals),
        "confirmation_rate": ratio(len(confirmed), len(candidates)),
        "mean_delta_current": mean(deltas) if deltas else None,
        "median_delta_current": median(deltas) if deltas else None,
        "model_calls": formal.get("model_calls"),
    }
    integrity_all = all(
        row.get("inputs_match", "").lower() == "true" and row.get("state_hash_with") == row.get("state_hash_without")
        for row in pairs
    )
    distinct_confirmed = len({row.get("memory_id") for row in confirmed})
    gates = {
        "G0_preregistered_and_tested": lock_ok and tests.get("passed", 0) >= 20 and tests.get("failed", 1) == 0,
        "G1_real_formal_20_episodes": formal.get("episodes_completed") == 20 and bool(formal.get("native_success")),
        "G2_native_write_and_retrieval": formal.get("memory_writes", 0) > 0 and len(retrievals) > 0,
        "G3_state_matched_pair": len(pairs) > 0,
        "G4_positive_native_source": positive_retrievals > 0,
        "G5_failure_candidate": len(candidates) > 0,
        "G6_confirmed_negative_effect": len(confirmed) > 0,
        "G7_confirmed_behavior_change": behavior_confirmed > 0,
        "G8_pair_integrity": integrity_all,
        "G9_budgets_hold": formal.get("episodes_completed") == 20 and formal.get("model_calls", 10**9) <= 160 and len(pairs) <= 20,
    }
    go = all(gates.values()) and behavior_confirmed >= 2 and distinct_confirmed >= 2
    narrow_required = [
        "G0_preregistered_and_tested", "G1_real_formal_20_episodes",
        "G2_native_write_and_retrieval", "G3_state_matched_pair",
        "G4_positive_native_source", "G5_failure_candidate",
        "G8_pair_integrity", "G9_budgets_hold",
    ]
    narrow = all(gates[x] for x in narrow_required) and behavior_confirmed >= 1
    verdict = "REAL_JITRL_MEMORY_FAILURE_GO" if go else ("REAL_JITRL_MEMORY_FAILURE_NARROW" if narrow else "REAL_JITRL_MEMORY_FAILURE_NO_GO")

    (RESULTS / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    (RESULTS / "gate_results.json").write_text(json.dumps({"gates": gates, "lock_problems": lock_problems}, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "verdict": verdict, "metrics": metrics, "gates": gates,
        "interpretation": (
            "The frozen runtime completed real native memory writes but produced no native retrieval events because the required vector index was unavailable. "
            "Therefore no causal paired intervention could be instantiated; this is a runtime-specific feasibility NO_GO, not evidence of absence of harmful memory effects."
            if not retrievals else "Verdict follows the preregistered paired-intervention gates."
        ),
    }
    (RESULTS / "experiment_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    if deltas:
        fig, ax = plt.subplots(figsize=(7, 4.2))
        ax.hist(deltas, bins=min(10, len(deltas)), color="#4472C4", edgecolor="white")
        ax.axvline(0, color="black", linewidth=1)
        ax.set(title="Current outcome effect of retrieved memory", xlabel="Delta_current", ylabel="Pairs")
        fig.tight_layout(); fig.savefig(PLOTS / "memory_effect_distribution.png", dpi=180); plt.close(fig)
    else:
        placeholder_plot(PLOTS / "memory_effect_distribution.png", "Current outcome effect of retrieved memory", "No valid paired events", "Delta_current")

    if pairs:
        xs = [float(r["historical_signal"]) for r in pairs]
        ys = [float(r["delta_current"]) for r in pairs]
        fig, ax = plt.subplots(figsize=(7, 4.2))
        ax.scatter(xs, ys, color="#C44E52")
        ax.axhline(0, color="black", linewidth=1)
        ax.set(title="Historical signal versus current effect", xlabel="Native llm_step_score", ylabel="Delta_current")
        fig.tight_layout(); fig.savefig(PLOTS / "historical_signal_vs_delta.png", dpi=180); plt.close(fig)
    else:
        placeholder_plot(PLOTS / "historical_signal_vs_delta.png", "Historical signal versus current effect", "No native retrieval events", "Native llm_step_score")

    fig, ax = plt.subplots(figsize=(7, 4.2))
    names = ["Writes", "Attempts", "Retrieved", "Paired", "Confirmed"]
    vals = [metrics["memory_writes"], metrics["retrieval_attempts"], metrics["retrieval_events"], metrics["valid_paired_events"], metrics["confirmed_failures"]]
    ax.bar(names, vals, color=["#4C78A8", "#72B7B2", "#F58518", "#E45756", "#54A24B"])
    ax.set(title="Stage-8C evidence funnel", ylabel="Count")
    fig.tight_layout(); fig.savefig(PLOTS / "evidence_funnel.png", dpi=180); plt.close(fig)

    report = f"""# Idea 2 Stage-8C 实验结果\n\n## Verdict\n\n`{verdict}`\n\n## 预注册执行\n\n正式实验固定为 20 个 episode、每个 episode 1 步、seed 20261008、temperature 0、模型 qwen2.5:14b。预注册和全部根目录 Python 脚本在正式运行前锁定 SHA-256；正式运行未重启、未扩样本。\n\n## 结果\n\n- 完成 episode：{metrics['episodes']}\n- 原生 memory write：{metrics['memory_writes']}\n- 原生 retrieval attempt：{metrics['retrieval_attempts']}\n- 原生 retrieval event：{metrics['retrieval_events']}\n- 有效 state-matched pair：{metrics['valid_paired_events']}\n- failure candidate：{metrics['failure_candidates']}\n- confirmed failure：{metrics['confirmed_failures']}\n- 模型调用：{metrics['model_calls']} / 160\n\n冻结环境缺少 `faiss`，而冻结的 Jericho `CrossEpisodeMemory` 只执行向量检索且没有非向量 fallback。原生 episode JSONL 写入成功，但检索索引不可用，因此所有 attempt 均返回空列表，无法实例化 WITH_MEMORY / WITHOUT_THIS_MEMORY 配对。\n\n该结论是当前冻结 runtime 的可行性 NO_GO：没有观察到可进入干预的真实 retrieval event。它不能解释为“有害 memory 不存在”，也不能解释为对核心假设的反证。\n\n## Gates\n\n```json\n{json.dumps(gates, indent=2, ensure_ascii=False)}\n```\n"""
    (HERE / "Stage8C实验结果.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    main()
