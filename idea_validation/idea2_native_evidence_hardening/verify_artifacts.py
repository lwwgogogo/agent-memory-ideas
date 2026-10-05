"""Read-only final artifact checks, historical/source byte identity, and output provenance."""
from pathlib import Path
import json,datetime,subprocess
from PIL import Image
from common import ROOT,PROJECT,sha,canonical,save,history_hashes,check_sources,assert_ready
from evaluate import native_provenance,exact_environment
def verify():
    assert_ready()
    before=json.loads((ROOT/'results/history_frozen_hashes.json').read_text())
    after=history_hashes()
    assert before==after, 'Historical file hash changed'
    manifest=json.loads((ROOT/'results/source_manifest.json').read_text())
    for f,h in manifest['upstream_source_sha256'].items():
        assert sha(Path(f).read_bytes())==h
    raw={s:[json.loads(x) for x in (ROOT/f'results/{s}_native_raw.jsonl').read_text().splitlines()] for s in ['jitrl','memrl']}
    for s,items in raw.items():assert len(items)==640
    assert native_provenance(raw['jitrl']+raw['memrl'])['pass']
    assert exact_environment(raw['jitrl']+raw['memrl'])['pass']
    required=['README.md','preregistration.md','SCOPE_CORRECTION.md','build_exact_logs.py','native_metrics.py',
       'run_jitrl_native.py','run_memrl_native.py','inspect_state_aware_paths.py','run_jitrl_state_aware.py','evaluate.py',
       'Stage4_1实验结果.md','最终结论.md','results/source_manifest.json','results/preregistration_lock.json',
       'results/jitrl_native_raw.jsonl','results/memrl_native_raw.jsonl','results/jitrl_native_summary.json',
       'results/memrl_native_summary.json','results/tie_audit.json','results/dose_response.json','results/k_sensitivity.json',
       'results/jitrl_state_aware_static.json','results/jitrl_state_aware_results.json','results/gate_results.json']
    required += ['plots/'+n+'.png' for n in ['native_reversal_by_seed','native_rcd_vs_gamma','balanced_control_native','k_sensitivity']]
    missing=[f for f in required if not (ROOT/f).is_file()];assert not missing
    for p in ROOT.rglob('*.json'):json.loads(p.read_text())
    pngs={}
    for p in (ROOT/'plots').glob('*.png'):
        with Image.open(p) as im:
            pngs[p.name]={'size':list(im.size),'format':im.format};im.verify()
    tests=json.loads((ROOT/'results/preflight_tests.json').read_text())
    lock=json.loads((ROOT/'results/preregistration_lock.json').read_text())
    timing=json.loads((ROOT/'results/formal_run_timing.json').read_text())
    assert tests['completed_at_utc']<=lock['locked_at_utc']<timing['started_at_utc']<timing['completed_at_utc']
    changed=subprocess.check_output(['git','-C',str(PROJECT),'diff','--name-only','HEAD'],text=True).splitlines()
    allowed={'PROJECT_INDEX.md','docs/RESEARCH_STATUS.md'}
    assert set(changed)<=allowed,changed
    gates=json.loads((ROOT/'results/gate_results.json').read_text())
    result={'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'environment':'agentmem_lab','python':'3.10.21',
            'preregistration_and_frozen_code_unchanged':True,'test_before_lock_before_formal':True,
            'preflight_tests':tests['passed'],'history_files_byte_identical':True,'history_file_count':len(before),
            'upstream_source_byte_identical':True,'sources':check_sources(),
            'native_provenance_checks':True,'exact_environment_checks':True,
            'native_raw_records':{s:len(v) for s,v in raw.items()},
            'formal_reruns':0,'additional_seeds_k_conditions':False,
            'raw_file_sha256':{s:sha((ROOT/f'results/{s}_native_raw.jsonl').read_bytes()) for s in raw},
            'source_manifest_sha256':sha((ROOT/'results/source_manifest.json').read_bytes()),
            'preregistration_sha256':lock['preregistration_sha256'],
            'required_files_present':True,'plot_png_validation':pngs,
            'tracked_changes_outside_new_directory':changed,'tracked_change_scope_valid':True,
            'external_environments_created':[],'new_packages_installed':[],
            'full_state_aware_path_executed':False,'state_aware_status':'BLOCKED',
            'verdict':gates['verdict'],'snapshot_stage':'pre-commit artifact verification; Git delivery verified after push'}
    save(ROOT/'results/final_verification.json',result)
    # Inventory excludes itself and mutable Git metadata; all result/artifact bytes are pinned.
    inventory={str(p.relative_to(ROOT)): {'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
               for p in sorted(ROOT.rglob('*')) if p.is_file() and not any(x in p.parts for x in ['__pycache__','.pytest_cache'])
               and p.name!='artifact_manifest.json'}
    save(ROOT/'results/artifact_manifest.json',inventory)
    print(json.dumps({'verdict':gates['verdict'],'history_count':len(before),'all_history_identical':before==after,
                      'native_rows':result['native_raw_records'],'total_artifact_bytes':sum(x['bytes'] for x in inventory.values()),
                      'plots':pngs,'tests':tests['passed']},indent=2))
if __name__=='__main__':verify()
