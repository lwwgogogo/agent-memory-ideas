"""Paired-seed A.1 comparison; run after run_phase_a.py."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np


def compare(directory):
    root=Path(directory)
    meta=json.loads((root/'run.json').read_text())
    with (root/'per_seed.csv').open() as f:
        rows=list(csv.DictReader(f))
    seeds=meta['config']['test_seeds']
    methods=['selected_global','selected_per_cell','online_bma','oracle_qr']
    a={m:np.array([np.mean([float(v['accuracy']) for v in rows
                          if v['method']==m and int(v['seed'])==s]) for s in seeds]) for m in methods}
    if not all(np.isfinite(v).all() for v in a.values()):
        raise ValueError('Missing A.1 methods or seeds')
    idx=np.random.default_rng(918).integers(len(seeds),size=(meta['config']['bootstrap_samples'],len(seeds)))
    gain=a['online_bma']-a['selected_global']
    gap=a['oracle_qr']-a['selected_global']
    bootstrap_denominator=gap[idx].mean(1)
    valid=gap.mean()>1e-6 and np.all(bootstrap_denominator>1e-6)
    result=dict(accuracy={m:float(v.mean()) for m,v in a.items()},
                gain_vs_global=float(gain.mean()),
                gain_ci95=np.quantile(gain[idx].mean(1),[.025,.975]).tolist(),
                recovered_oracle_gap_fraction=float(gain.mean()/gap.mean()) if valid else None,
                recovery_ci95=np.quantile(gain[idx].mean(1)/bootstrap_denominator,[.025,.975]).tolist() if valid else None,
                runtime_seconds=meta['elapsed_seconds'], bootstrap_seed=918,
                note='Equal weight over grid cells; bootstrap clusters all cells by seed.')
    (root/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('run')
    compare(parser.parse_args().run)
