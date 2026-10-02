"""Static, exportable scientific heatmaps from a completed run."""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot(run):
    root = Path(run)
    with (root/"summary.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    qs = sorted({float(row["q"]) for row in rows})
    rs = sorted({float(row["r"]) for row in rows})
    methods = ["last", "majority", "selected_global", "selected_per_cell", "oracle_qr"]
    if any(row["method"] == "online_bma" for row in rows):
        methods = ["last", "selected_global", "selected_per_cell", "online_bma", "oracle_qr"]
    metrics = ["accuracy", "false_update_rate", "adaptation_delay_capped", "stale_reuse_proxy"]
    figures = root/"figures"
    figures.mkdir(exist_ok=True)
    for metric in metrics:
        arrays = []
        for method in methods:
            lookup = {(float(v["q"]),float(v["r"])): float(v[metric]) if v[metric] else np.nan
                      for v in rows if v["method"] == method}
            arrays.append(np.array([[lookup[q,r] for r in rs] for q in qs]))
        upper = max((float(a[np.isfinite(a)].max()) for a in arrays if np.isfinite(a).any()), default=1)
        fig, axes = plt.subplots(1, len(methods), figsize=(19,4), constrained_layout=True)
        for ax, method, values in zip(axes, methods, arrays):
            im = ax.imshow(values, origin="lower", vmin=0, vmax=upper if "delay" in metric else 1, aspect="auto", cmap="viridis")
            ax.set(title=method, xlabel="R (observation flip probability)", ylabel="Q (state flip probability)")
            ax.set_xticks(range(len(rs)), [str(r) for r in rs])
            ax.set_yticks(range(len(qs)), [str(q) for q in qs])
        fig.suptitle(f"{metric}: test-seed mean; blank = no eligible events")
        fig.colorbar(im, ax=axes, label="steps" if "delay" in metric else "fraction")
        fig.savefig(figures/f"{metric}.png", dpi=160)
        plt.close(fig)
    lookup = {(float(v["q"]),float(v["r"]),v["method"]):float(v["accuracy"]) for v in rows}
    fig, axes = plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    for ax, method in zip(axes,["selected_global","selected_per_cell"]):
        a = np.array([[lookup[q,r,"oracle_qr"]-lookup[q,r,method] for r in rs] for q in qs])
        lim = max(float(np.abs(a).max()), 0.001)
        im = ax.imshow(a,origin="lower",cmap="RdBu",vmin=-lim,vmax=lim,aspect="auto")
        ax.set(title=f"Oracle minus {method}",xlabel="R (observation flip probability)",ylabel="Q (state flip probability)")
        ax.set_xticks(range(len(rs)),[str(r) for r in rs])
        ax.set_yticks(range(len(qs)),[str(q) for q in qs])
        fig.colorbar(im,ax=ax,label="accuracy difference")
    fig.suptitle("Held-out accuracy gap; hyperparameters selected on validation seeds")
    fig.savefig(figures/"oracle_gap.png",dpi=180)
    plt.close(fig)
    print(figures)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("run")
    plot(parser.parse_args().run)
