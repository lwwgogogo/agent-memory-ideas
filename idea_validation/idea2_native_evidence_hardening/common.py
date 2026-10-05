"""Shared frozen experiment configuration and provenance guards."""
from pathlib import Path
import hashlib, json, subprocess, sys
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
HISTORY = [
 'idea2_policy_confounding', 'idea2_policy_confounding_confirmatory',
 'idea2_causal_sufficiency', 'idea2_real_memory_formation_audit',
 'idea2_policy_conditioned_memory_audit']
SOURCES = PROJECT/'idea_validation/idea2_policy_conditioned_memory_audit/third_party'
COMMITS = {'jitrl':'143d22185d95fbf633a0befe6861d5e8b732543b',
           'memrl':'c1b322ca43de36ddf64c6712f89d0095bfc35ce0'}
GAMMAS = ('0.50','0.70','0.85','0.95')
SEEDS = tuple(range(20261005, 20261025))
KS = (5,10,20,50)
def sha(data):
    return hashlib.sha256(data).hexdigest()
def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def save(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def check_sources():
    result={}
    for name,expected in COMMITS.items():
        path=SOURCES/name
        got=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        if got!=expected: raise RuntimeError(f'{name} COMMIT_MISMATCH')
        # Only read source; ignored caches predate this study.
        changes=subprocess.check_output(['git','-C',str(path),'diff','--name-only','HEAD'],text=True)
        if changes: raise RuntimeError(f'{name} upstream tracked source is modified')
        result[name]={'commit':got,'path':str(path),'tracked_source_clean':True}
    return result
def history_hashes():
    paths=['idea_validation/'+name for name in HISTORY]
    names=subprocess.check_output(['git','-C',str(PROJECT),'ls-files','-z','--',*paths]).decode().split('\0')
    return {name:sha((PROJECT/name).read_bytes()) for name in names if name}
def assert_ready():
    assert sys.version_info[:3]==(3,10,21), sys.version
    check_sources()
    lock=json.loads((ROOT/'results/preregistration_lock.json').read_text())
    assert sha((ROOT/'preregistration.md').read_bytes())==lock['preregistration_sha256']
    for f,h in lock['implementation_sha256'].items():
        assert sha((ROOT/f).read_bytes())==h, 'Frozen implementation changed: '+f
    tests=json.loads((ROOT/'results/preflight_tests.json').read_text())
    assert tests['exit_code']==0 and tests['failed']==0
