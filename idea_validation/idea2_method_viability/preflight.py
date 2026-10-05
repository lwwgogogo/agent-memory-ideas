import datetime,sys,subprocess,re,json
from config import ROOT,PROJECT,save,sha,history_hashes,sources
from native_baselines import provenance
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 assert sys.version_info[:3]==(3,10,21)
 assert not (ROOT/'results/preregistration_lock.json').exists()
 assert not (ROOT/'results/method_results.csv').exists()
 src=sources();start=now()
 run=subprocess.run([sys.executable,'-m','pytest','-q','tests'],cwd=ROOT,capture_output=True,text=True)
 out=run.stdout+run.stderr;print(out)
 (ROOT/'results/preflight_tests.txt').write_text(out)
 m=re.search(r'(\d+) passed',out)
 save(ROOT/'results/preflight_tests.json',{'started_at_utc':start,'completed_at_utc':now(),'exit_code':run.returncode,
    'passed':int(m.group(1)) if m else 0,'python':sys.version,'command':'python -m pytest -q tests',
    'development_fixes_before_lock':['native baseline dictionary-comprehension syntax','frozen-slots exception-type expectation; field injection still rejected']})
 if run.returncode:raise SystemExit(run.returncode)
 save(ROOT/'results/history_frozen_hashes.json',history_hashes())
 save(ROOT/'results/source_manifest.json',{'sources':src,'native_functions':provenance(),
     'python_executable':sys.executable,'python':sys.version,'initial_worktree_clean':True,
     'base_commit':subprocess.check_output(['git','-C',str(PROJECT),'rev-parse','HEAD'],text=True).strip(),
     'new_packages_installed':[],'new_models_used':[],'created_at_utc':now()})
 save(ROOT/'results/preregistration_lock.json',{'locked_at_utc':now(),'sha256':sha((ROOT/'preregistration.md').read_bytes()),
   'code_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in ROOT.rglob('*.py')},'formal_run_started':False})
 print('LOCKED',sha((ROOT/'preregistration.md').read_bytes()))
if __name__=='__main__':main()
