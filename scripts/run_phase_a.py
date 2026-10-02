"""Run validation-selected baselines on paired held-out synthetic sequences."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from agent_memory.environment import generate
from agent_memory.baselines import candidates, predict
from agent_memory.metrics import evaluate
from agent_memory.online import model_average


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def validate(c):
    if c["steps"] < 2 or not 1 <= c["burn_in"] < c["steps"]:
        raise ValueError("Invalid steps/burn_in")
    for key in ("validation_seeds", "test_seeds", "q_values", "r_values"):
        if not c[key] or len(set(c[key])) != len(c[key]):
            raise ValueError(f"Empty or duplicate {key}")
    if set(c["validation_seeds"]) & set(c["test_seeds"]):
        raise ValueError("Validation and test seeds must be disjoint")
    if len(c["test_seeds"]) < 2 or c["bootstrap_samples"] < 100:
        raise ValueError("Require >=2 test seeds and >=100 bootstrap samples")
    if any(not 0 <= v <= 0.5 for k in ("q_values", "r_values") for v in c[k]):
        raise ValueError("Q and R must be in [0,0.5]")


def run(config, output):
    c = json.loads(Path(config).read_text(encoding="utf-8"))
    validate(c)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    start = time.time()
    specs = candidates()
    cells = [(q, r) for q in c["q_values"] for r in c["r_values"]]
    validation, selected = [], {}
    for q, r in cells:
        scores = {s["name"]: [] for s in specs}
        for seed in c["validation_seeds"]:
            x, y = generate(q, r, c["steps"], seed)
            for spec in specs:
                acc = np.mean((predict(y, spec)[c["burn_in"]:] >= 0.5) == x[c["burn_in"]:])
                scores[spec["name"]].append(float(acc))
        for name, values in scores.items():
            validation.append(dict(q=q, r=r, method=name, accuracy=float(np.mean(values))))
        selected[(q, r)] = max(scores, key=lambda name: np.mean(scores[name]))
        print(f"validation q={q} r={r}: {selected[(q,r)]}", flush=True)
    global_best = max((s["name"] for s in specs), key=lambda name:
                      np.mean([v["accuracy"] for v in validation if v["method"] == name]))
    write_csv(out / "validation.csv", validation)
    rows, trace, online_diagnostics = [], [], []
    online = c.get("online_model_average")
    for q, r in cells:
        oracle = dict(name="oracle_qr", kind="bayes", q=q, r=r)
        for seed in c["test_seeds"]:
            x, y = generate(q, r, c["steps"], seed)
            cache = {}
            for spec in specs + [oracle]:
                belief = predict(y, spec)
                metrics = evaluate(x, y, belief, c["burn_in"])
                cache[spec["name"]] = metrics
                rows.append(dict(q=q, r=r, seed=seed, method=spec["name"], **metrics))
                if (q, r) == cells[len(cells)//2] and seed == c["test_seeds"][0]:
                    trace.extend(dict(t=t, method=spec["name"], truth=int(x[t]),
                                      observation=int(y[t]), belief=float(belief[t])) for t in range(len(x)))
            for alias, name in [("selected_global", global_best), ("selected_per_cell", selected[(q,r)])]:
                rows.append(dict(q=q, r=r, seed=seed, method=alias, **cache[name]))
            if online:
                belief, diagnostics = model_average(y, online["q_grid"], online["r_grid"])
                rows.append(dict(q=q,r=r,seed=seed,method="online_bma",
                                 **evaluate(x,y,belief,c["burn_in"])))
                for t in [99, 499, 999, len(y)-1]:
                    if t < len(y):
                        online_diagnostics.append(dict(q=q,r=r,seed=seed,**diagnostics[t]))
                if (q,r) == cells[len(cells)//2] and seed == c["test_seeds"][0]:
                    trace.extend(dict(t=t,method="online_bma",truth=int(x[t]),observation=int(y[t]),
                                      belief=float(belief[t])) for t in range(len(x)))
        print(f"test complete q={q} r={r}", flush=True)
    write_csv(out / "per_seed.csv", rows)
    write_csv(out / "trace.csv", trace)
    if online_diagnostics:
        write_csv(out / "online_diagnostics.csv", online_diagnostics)
    aggregate = []
    for q, r in cells:
        for name in [s["name"] for s in specs] + ["oracle_qr", "selected_global", "selected_per_cell"] + (["online_bma"] if online else []):
            subset = [row for row in rows if (row["q"],row["r"],row["method"]) == (q,r,name)]
            record = dict(q=q, r=r, method=name)
            for metric in cache["oracle_qr"]:
                values = [row[metric] for row in subset if row[metric] is not None]
                record[metric] = float(np.mean(values)) if values else None
            aggregate.append(record)
    write_csv(out / "summary.csv", aggregate)
    rng = np.random.default_rng(917)
    gaps = []
    for comparator in ["selected_global", "selected_per_cell"] + (["online_bma"] if online else []):
        deltas = []
        for seed in c["test_seeds"]:
            oracle_acc = np.mean([v["accuracy"] for v in rows if v["seed"] == seed and v["method"] == "oracle_qr"])
            baseline_acc = np.mean([v["accuracy"] for v in rows if v["seed"] == seed and v["method"] == comparator])
            deltas.append(oracle_acc - baseline_acc)
        boot = rng.choice(deltas, size=(c["bootstrap_samples"], len(deltas)), replace=True).mean(axis=1)
        gaps.append(dict(comparator=comparator, accuracy_gap=float(np.mean(deltas)),
                         ci95_low=float(np.quantile(boot, .025)), ci95_high=float(np.quantile(boot, .975))))
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ("src", "scripts", "configs") for p in (ROOT/folder).rglob("*")
              if p.is_file() and "__pycache__" not in p.parts}
    result = dict(config=c, global_selected=global_best,
                  per_cell_selected=[dict(q=q,r=r,method=selected[(q,r)]) for q,r in cells],
                  paired_seed_bootstrap=gaps, elapsed_seconds=time.time()-start,
                  python=platform.python_version(), numpy=np.__version__, git_revision=revision,
                  source_sha256=hashes, note="Synthetic Phase A; no automatic GO decision. Per-cell selection has privileged regime identity.")
    (out/"run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"output":str(out), "global_selected":global_best, "gaps":gaps}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT/"configs/smoke.json"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.config, args.output)
