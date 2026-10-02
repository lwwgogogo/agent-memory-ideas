"""Read-only checks of inference artifacts, with a new audit sidecar."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import zipfile


def audit(directory):
    root=Path(directory)
    meta=json.loads((root/'run.json').read_text(encoding='utf-8'))
    if meta['status']!='complete':raise ValueError('Incomplete run')
    with zipfile.ZipFile(root/'source_snapshot.zip') as z:
        for name,digest in meta['source_sha256'].items():
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise ValueError('Source archive mismatch '+name)
    for name,digest in meta['output_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Output changed '+name)
    with (root/'per_seed.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    c=meta['config']
    if {int(r['seed']) for r in rows}!=set(c['test_seeds']):raise ValueError('Unexpected seed set')
    for r in rows:
        for metric in ['accuracy','brier','false_update_rate','noise_overreaction','stale_reuse_proxy']:
            if r.get(metric) and not 0<=float(r[metric])<=1:raise ValueError('Out of range metric')
        if r.get('change') and not 900<=int(r['change'])<=1500:raise ValueError('Unexpected change time')
        if r.get('corruption_end') and int(r['corruption_end'])-int(r['change'])!=100:raise ValueError('Wrong corruption length')
    keycols=[k for k in ['q','r','length','scenario','seed','method'] if k in rows[0]]
    if len({tuple(r[k] for k in keycols) for r in rows})!=len(rows):raise ValueError('Duplicate result')
    expected_cells=len(c['q_values'])*len(c['r_values']) if 'q_values' in c else (len(c['cells'])*len(c['lengths']) if 'cells' in c else len(c['scenarios']))
    method_counts={m:sum(r['method']==m for r in rows) for m in {r['method'] for r in rows}}
    if any(v!=expected_cells*len(c['test_seeds']) for v in method_counts.values()):raise ValueError('Missing method/cell/seed rows')
    result=dict(status='passed',rows=len(rows),source_files_verified=len(meta['source_sha256']),
                inference_outputs_verified=len(meta['output_sha256']),seeds=len(c['test_seeds']),
                method_counts=method_counts)
    # Do not overwrite audit or scientific outputs.
    with (root/'audit.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(root,result)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directories',nargs='+');a=p.parse_args()
    for directory in a.directories:audit(directory)
