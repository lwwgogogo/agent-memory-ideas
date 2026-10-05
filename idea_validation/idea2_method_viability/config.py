from pathlib import Path
import json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
UPSTREAM=PROJECT/'idea_validation/idea2_policy_conditioned_memory_audit/third_party'
OLD41=PROJECT/'idea_validation/idea2_native_evidence_hardening'
COMMITS={'jitrl':'143d22185d95fbf633a0befe6861d5e8b732543b','memrl':'c1b322ca43de36ddf64c6712f89d0095bfc35ce0'}
HISTORIES=['idea2_policy_confounding','idea2_policy_confounding_confirmatory','idea2_causal_sufficiency','idea2_real_memory_formation_audit','idea2_policy_conditioned_memory_audit','idea2_native_evidence_hardening']
SEEDS=tuple(range(20261005,20261025));GAMMAS=('0.50','0.70','0.85','0.95')
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def history_hashes():
 files=subprocess.check_output(['git','-C',str(PROJECT),'ls-files','-z','--',*['idea_validation/'+n for n in HISTORIES]]).decode().split('\0')
 return {n:sha((PROJECT/n).read_bytes()) for n in files if n}
def sources():
 out={}
 for name,expected in COMMITS.items():
  path=UPSTREAM/name
  head=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
  assert head==expected
  assert not subprocess.check_output(['git','-C',str(path),'diff','--name-only','HEAD'],text=True)
  out[name]={'path':str(path),'commit':head}
 return out
def ready():
 assert sys.version_info[:3]==(3,10,21)
 sources()
 lock=json.loads((ROOT/'results/preregistration_lock.json').read_text())
 assert sha((ROOT/'preregistration.md').read_bytes())==lock['sha256']
 for f,h in lock['code_sha256'].items():assert sha((ROOT/f).read_bytes())==h,f
 assert json.loads((ROOT/'results/preflight_tests.json').read_text())['exit_code']==0
