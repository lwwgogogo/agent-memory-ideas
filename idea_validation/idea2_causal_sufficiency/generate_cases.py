from __future__ import annotations
import json
from pathlib import Path
from core import ROOT, CONDITIONS, ORDERS, VERSIONS, make_prompt, sha

def main():
    source = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    worlds = source["worlds"]
    if len(worlds) != 40:
        raise AssertionError(len(worlds))
    formal_worlds = []
    jobs = []
    for world in worlds:
        wid = world["world_id"]
        formal = {k: v for k, v in world.items() if k != "target_value"}
        formal["target_value"] = world["target_value"]
        formal["optimal_action"] = world["optimal_action"]
        for condition in CONDITIONS:
            for version in VERSIONS:
                for order in ORDERS:
                    run_id = f"{wid}:{condition}:{version}:{order}"
                    jobs.append({"run_id": run_id, "world_id": wid, "pair_id": world["pair_id"], "condition": condition, "version": version, "order": order, "prompt": make_prompt(world, condition, version, order)})
        formal_worlds.append(formal)
    r2_same = []
    by_pair = {}
    for world in formal_worlds:
        by_pair.setdefault(world["pair_id"], []).append(world)
    for pair_id, pair_worlds in by_pair.items():
        w1, w2 = pair_worlds
        for version in VERSIONS:
            for order in ORDERS:
                p1 = next(x["prompt"] for x in jobs if x["world_id"] == w1["world_id"] and x["condition"] == "FaithfulLossySummary" and x["version"] == version and x["order"] == order)
                p2 = next(x["prompt"] for x in jobs if x["world_id"] == w2["world_id"] and x["condition"] == "FaithfulLossySummary" and x["version"] == version and x["order"] == order)
                r2_same.append(p1 == p2)
    if not all(r2_same):
        raise AssertionError("R2 prompts are not identical within matched pairs")
    out = ROOT / "cases"; out.mkdir(exist_ok=True)
    (out / "cases.json").write_text(json.dumps({"pairs": source["pairs"], "worlds": formal_worlds, "runs": jobs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "source.json").write_text(json.dumps({"phase_a_cases_sha256": sha(ROOT / "cases.json"), "pairs": 20, "worlds": 40, "planned_runs": len(jobs), "r2_identical_prompt_checks": len(r2_same)}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"worlds": len(formal_worlds), "runs": len(jobs), "r2_identical": all(r2_same)}, indent=2))

if __name__ == "__main__":
    main()

