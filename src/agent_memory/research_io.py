"""Immutable experiment outputs, source archives, and seed-cluster inference."""
import csv
import hashlib
import json
import platform
import subprocess
import time
import zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def write_csv(path, rows):
    if not rows:
        return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def start_run(config_path, output):
    c=json.loads(Path(config_path).read_text(encoding='utf-8'))
    out=Path(output)
    out.mkdir(parents=True, exist_ok=False)
    files=[p for folder in ('src','scripts','configs','tests','docs') for p in (ROOT/folder).rglob('*')
           if p.is_file() and '__pycache__' not in p.parts]
    files += [ROOT/'requirements.txt',ROOT/'README.md']
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with zipfile.ZipFile(out/'source_snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in files: z.write(p,p.relative_to(ROOT).as_posix())
    write_json(out/'config.json',c)
    meta=dict(config=c, config_sha256=hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
              source_sha256=hashes, python=platform.python_version(),numpy=np.__version__,
              platform=platform.platform(),start_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              status='running',bootstrap_unit='seed; cells jointly resampled',bootstrap_samples=c['bootstrap_samples'])
    write_json(out/'run.json',meta)
    try:
        import sys
        freeze=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True)
        (out/'environment-lock.txt').write_text(freeze,encoding='utf-8')
    except subprocess.CalledProcessError:
        (out/'environment-lock.txt').write_text('pip freeze unavailable\n')
    return c,out,meta,time.monotonic()


def finish_run(out,meta,started,**extra):
    meta.update(status='complete',elapsed_seconds=time.monotonic()-started,**extra)
    meta['output_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in out.glob('*') if p.is_file() and p.name!='run.json'}
    write_json(out/'run.json',meta)


def ci(values, samples=5000, seed=917):
    a=np.asarray(values,dtype=float)
    a=a[np.isfinite(a)]
    if not len(a): return dict(mean=None,ci_low=None,ci_high=None,n=0)
    draws=np.random.default_rng(seed).integers(len(a),size=(samples,len(a)))
    boot=a[draws].mean(axis=1)
    return dict(mean=float(a.mean()),ci_low=float(np.quantile(boot,.025)),
                ci_high=float(np.quantile(boot,.975)),n=len(a))


def summarize(rows,groups,metrics,samples=5000):
    buckets=defaultdict(list)
    for row in rows: buckets[tuple(row[k] for k in groups)+ (row['method'],)].append(row)
    result=[]
    for key, records in buckets.items():
        for metric in metrics:
            # Preserve across-cell pairing by averaging each seed first.
            seeds=defaultdict(list)
            for r in records:
                if r.get(metric) is not None: seeds[r['seed']].append(r[metric])
            result.append(dict(zip(groups,key[:-1]),method=key[-1],metric=metric,
                               **ci([np.mean(v) for v in seeds.values()],samples)))
    return result


def contrasts(rows,groups,metrics,samples=5000,reference='oracle_qr'):
    buckets=defaultdict(list)
    for r in rows: buckets[tuple(r[k] for k in groups)].append(r)
    result=[]
    for key, records in buckets.items():
        methods=list(dict.fromkeys(r['method'] for r in records))
        for metric in metrics:
            values=defaultdict(lambda:defaultdict(list))
            for r in records:
                if r.get(metric) is not None: values[r['method']][r['seed']].append(r[metric])
            for method in methods:
                if method==reference: continue
                common=sorted(set(values[reference]) & set(values[method]))
                delta=[np.mean(values[reference][s])-np.mean(values[method][s]) for s in common]
                result.append(dict(zip(groups,key),reference=reference,method=method,metric=metric,
                                   **ci(delta,samples)))
    return result


def recovery_fraction(rows,method,samples=5000):
    a=defaultdict(lambda:defaultdict(list))
    for r in rows: a[r['method']][r['seed']].append(r['accuracy'])
    seeds=sorted(set(a[method]) & set(a['oracle_qr']) & set(a['selected_global']))
    num=np.array([np.mean(a[method][s])-np.mean(a['selected_global'][s]) for s in seeds])
    den=np.array([np.mean(a['oracle_qr'][s])-np.mean(a['selected_global'][s]) for s in seeds])
    idx=np.random.default_rng(918).integers(len(seeds),size=(samples,len(seeds)))
    db=den[idx].mean(1)
    if den.mean()<=1e-6 or (db<=1e-6).any(): return dict(mean=None,ci_low=None,ci_high=None)
    ratios=num[idx].mean(1)/db
    return dict(mean=float(num.mean()/den.mean()),ci_low=float(np.quantile(ratios,.025)),
                ci_high=float(np.quantile(ratios,.975)))
