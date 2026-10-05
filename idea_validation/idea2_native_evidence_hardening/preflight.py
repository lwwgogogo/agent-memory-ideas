"""Run required tests, then lock protocol and implementation before formal native calls."""
import datetime,json,subprocess,sys,re,importlib.metadata
from common import ROOT,PROJECT,SOURCES,sha,save,canonical,check_sources,history_hashes
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
    assert sys.version_info[:3]==(3,10,21)
    assert not list((ROOT/'results').glob('*_native_raw.jsonl'))
    assert not (ROOT/'results/preregistration_lock.json').exists()
    source=check_sources()
    prior=subprocess.check_output(['git','-C',str(PROJECT),'rev-parse','HEAD'],text=True).strip()
    start=now()
    run=subprocess.run([sys.executable,'-m','pytest','-q','tests'],cwd=ROOT,text=True,capture_output=True)
    output=run.stdout+run.stderr
    (ROOT/'results/preflight_tests.txt').write_text(output)
    matches=re.search(r'(\d+) passed',output)
    test={'started_at_utc':start,'completed_at_utc':now(),'exit_code':run.returncode,
          'passed':int(matches.group(1)) if matches else 0,'failed':0 if run.returncode==0 else 1,
          'command':'python -m pytest -q tests','python':sys.version,
          'test_output_sha256':sha(output.encode())}
    save(ROOT/'results/preflight_tests.json',test)
    print(output)
    if run.returncode!=0:raise SystemExit(run.returncode)
    history=history_hashes();save(ROOT/'results/history_frozen_hashes.json',history)
    source_files=[
      SOURCES/'jitrl/Jericho/src/prompt_update_with_history.py',
      SOURCES/'jitrl/Jericho/src/cross_episode_memory.py',
      SOURCES/'jitrl/Jericho/src/openai_helpers.py',
      SOURCES/'memrl/memrl/service/value_driven.py',
      SOURCES/'memrl/memrl/service/retrievers.py',
      SOURCES/'memrl/memrl/service/memory_service.py']
    save(ROOT/'results/source_manifest.json',{
        'created_at_utc':now(),'project_head_before':prior,'initial_repo_status':'clean (verified before new directory creation)',
        'python':sys.version,'python_executable':sys.executable,'conda_environment':'agentmem_lab',
        'sources':source,'upstream_source_sha256':{str(p):sha(p.read_bytes()) for p in source_files},
        'history_tracked_file_count':len(history),'history_hash_manifest_sha256':sha(canonical(history).encode()),
        'native_import_boundaries':{'jitrl':'unused openai_helpers.claude_completion_with_retries raises if invoked',
                                    'memrl':'MOS annotation import + duck-typed storage; no provider retrieval'},
        'formal_expected_calls':{'jitrl.get_top_episodes':640,'memrl.QValueUpdater.update':320000,'memrl.ValueAwareSelector.select':640},
        'packages':{p:importlib.metadata.version(p) for p in ['pytest','numpy','scipy','matplotlib']}})
    code={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(ROOT.rglob('*.py'))}
    save(ROOT/'results/preregistration_lock.json',{'locked_at_utc':now(),
       'preregistration_sha256':sha((ROOT/'preregistration.md').read_bytes()),
       'implementation_sha256':code,'preflight_tests_sha256':sha((ROOT/'results/preflight_tests.json').read_bytes()),
       'formal_native_run_started':False})
    print('LOCKED',sha((ROOT/'preregistration.md').read_bytes()))
if __name__=='__main__':main()
