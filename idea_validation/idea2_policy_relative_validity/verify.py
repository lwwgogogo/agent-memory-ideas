import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
HISTORICAL=[
'idea_validation/idea2_policy_confounding',
'idea_validation/idea2_policy_confounding_confirmatory',
'idea_validation/idea2_causal_sufficiency',
'idea_validation/idea2_real_memory_formation_audit',
'idea_validation/idea2_policy_conditioned_memory_audit',
'idea_validation/idea2_native_evidence_hardening',
'idea_validation/idea2_method_viability',
'idea_validation/idea2_cross_policy_certification',
'idea_validation/idea2_cross_policy_certification_hardening',
'idea_validation/idea2_native_mapping_and_differentiation',
'idea_validation/idea2_target_relative_transfer_envelope']
FORMAL_CODE=["mdp.py","policies.py","memory.py","baselines.py","run_experiment.py","verify.py"]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def history_snapshot():
    snapshot={}
    for root in map(Path,HISTORICAL):
        for p in sorted((ROOT/root).rglob("*")):
            key=str(p.relative_to(ROOT))
            if p.is_symlink(): snapshot[key]={"symlink":str(p.readlink())}
            elif p.is_file():
                raw=p.read_bytes()
                snapshot[key]={"sha256":hashlib.sha256(raw).hexdigest(),"size":len(raw)}
    return snapshot

def history_match():
    return history_snapshot()==json.loads((BASE/"results/history_before.json").read_text())

def make_manifest():
    names=["preregistration.md",*FORMAL_CODE]
    return {"files":{n:sha(BASE/n) for n in names}}

def manifest_match(manifest=None):
    if manifest is None:
        manifest=json.loads((BASE/"results/preregistration_manifest.json").read_text())
    return all(sha(BASE/n)==value for n,value in manifest["files"].items())
