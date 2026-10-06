import hashlib
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def history_snapshot():
    before=json.loads((BASE/"results/history_before.json").read_text())
    roots={Path(*Path(n).parts[:2]) for n in before}
    current={}
    for root in sorted(roots):
        for p in sorted((ROOT/root).rglob("*")):
            name=str(p.relative_to(ROOT))
            if p.is_symlink(): current[name]={"symlink":str(p.readlink())}
            elif p.is_file():
                raw=p.read_bytes()
                current[name]={"sha256":hashlib.sha256(raw).hexdigest(),"size":len(raw)}
    return current
def history_matches():
    return history_snapshot()==json.loads((BASE/"results/history_before.json").read_text())
def science_files():
    return sorted([*BASE.glob("*.py"),*BASE.glob("tests/*.py"),BASE/"preregistration.md",BASE/"public_config.json"])
def make_lock():
    legacy=BASE.parent/"idea2_cross_policy_certification_hardening"
    return {"files":{str(p.relative_to(BASE)):sha(p) for p in science_files()},
            "legacy":{str(p.relative_to(ROOT)):sha(p) for p in
                       [*sorted((legacy/"candidate").glob("*.py")),legacy/"public_config.json"]}}
def check_lock(lock):
    return all(sha(BASE/n)==h for n,h in lock["files"].items()) and all(
        sha(ROOT/n)==h for n,h in lock["legacy"].items())
