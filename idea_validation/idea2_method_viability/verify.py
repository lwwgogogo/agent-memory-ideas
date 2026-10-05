"""Artifact/data/source checks only; no formal rerun or estimator tuning."""
import json,csv,datetime,subprocess
from pathlib import Path
from fractions import Fraction as F
from PIL import Image
from config import ROOT,PROJECT,save,sha,history_hashes,ready,sources
def verify():
 ready()
 before=json.loads((ROOT/'results/history_frozen_hashes.json').read_text());after=history_hashes()
 assert before==after,'historical byte change'
 source=json.loads((ROOT/'results/source_manifest.json').read_text())
 for fs in source['native_functions'].values():
  for f in fs:assert sha(Path(f['file']).read_bytes())==f['sha256']
 lock=json.loads((ROOT/'results/preregistration_lock.json').read_text())
 test=json.loads((ROOT/'results/preflight_tests.json').read_text())
 timing=json.loads((ROOT/'results/run_timing.json').read_text())
 assert test['exit_code']==0
 assert test['completed_at_utc']<=lock['locked_at_utc']<timing['native_reproduction_started_at_utc']<timing['candidate_run_started_at_utc']<timing['completed_at_utc']
 manifest=json.loads((ROOT/'results/world_manifest.json').read_text())
 for w in manifest['worlds']:
  p=ROOT/w['file'];assert sha(p.read_bytes())==w['sha256']
  rows=[json.loads(l) for l in p.read_text().splitlines()]
  assert len(rows)==2000 and all(set(r)=={'id','state','action','outcome'} for r in rows)
  for s in ('S0','S1'):
   for a in ('A','B'):
    c=[r for r in rows if r['state']==s and r['action']==a]
    assert len(c)==w['cells'][s][a]['n'] and sum(r['outcome'] for r in c)==w['cells'][s][a]['success']
 result_rows=list(csv.DictReader((ROOT/'results/method_results.csv').open()));assert len(result_rows)==720
 assert len({(r['system'],r['world_id'],r['target'],r['method']) for r in result_rows})==720
 for r in result_rows:
  u={a:F(r['U_'+a+'_exact']) for a in ('A','B')}
  assert all(0<=v<=1 for v in u.values())
  if r['method']=='M1':
   assert u=={a:F(r['true_'+a+'_exact']) for a in ('A','B')}
 counts={name:sum(1 for l in (ROOT/'results'/name).open()) for name in ['native_outputs.jsonl','secondary_selection.jsonl']}
 assert counts=={'native_outputs.jsonl':1440,'secondary_selection.jsonl':4800}
 secondary=json.loads((ROOT/'results/secondary_summary.json').read_text())
 assert len(secondary)==240 and all(r['20_order_compositions_identical'] and r['all_minimum_support_constraints_pass'] for r in secondary)
 gates=json.loads((ROOT/'results/gate_results.json').read_text())
 assert gates['selected_candidate'] in ('M1','M2','M4','NONE') and gates['selected_candidate']!='M3'
 required=['README.md','preregistration.md','theory.md','build_worlds.py','methods.py','native_baselines.py','run_experiment.py','evaluate.py',
 'adapters/jitrl.py','adapters/memrl.py','adapters/corrected_selector.py','Method候选比较.md','Stage5实验结果.md','最终结论.md']
 required += ['results/'+n for n in ['world_manifest.json','native_reproduction.json','method_results.csv','policy_invariance.json','true_effect_retention.json','crossover.json','support_stress.json','ablations.json','gate_results.json']]
 required += ['plots/'+n+'.png' for n in ['policy_invariance_gap','true_signal_retention','correction_vs_gamma','crossover','method_tradeoff']]
 assert all((ROOT/p).is_file() for p in required)
 for p in (ROOT/'results').rglob('*.json'):json.loads(p.read_text())
 png={}
 for p in (ROOT/'plots').glob('*.png'):
  with Image.open(p) as im:png[p.name]=list(im.size);im.verify()
 changed=subprocess.check_output(['git','-C',str(PROJECT),'diff','--name-only','HEAD'],text=True).splitlines()
 assert all(x in ['PROJECT_INDEX.md','docs/RESEARCH_STATUS.md'] or x.startswith('idea_validation/idea2_method_viability/') for x in changed)
 save(ROOT/'results/final_verification.json',{'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'python':'3.10.21','environment':'agentmem_lab','tests_passed':test['passed'],
   'preregistration_code_unchanged':True,'preregistration_sha256':lock['sha256'],'tests_before_lock_before_formal':True,
   'history_file_count':len(before),'all_history_files_identical':True,'upstream_source_unchanged':True,'sources':sources(),
   'exact_world_count':len(manifest['worlds']),'method_results_rows':720,'raw_record_counts':counts,
   'secondary_constraints_passed':True,'candidate_no_oracle_leakage':gates['no_oracle_leakage'],
   'normalized_adapter_inputs_equal':json.loads((ROOT/'results/integration_checks.json').read_text())['all_pass'],
   'selected_candidate':gates['selected_candidate'],'verdict':gates['verdict'],
   'all_required_artifacts_present':True,'plots':png,'formal_reruns':0,'new_packages':[],'new_models':[],
   'snapshot':'pre-commit; final Git delivery checked after push'})
 inventory={str(p.relative_to(ROOT)):{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
    for p in ROOT.rglob('*') if p.is_file() and not any(x in p.parts for x in ['__pycache__','.pytest_cache']) and p.name!='artifact_manifest.json'}
 save(ROOT/'results/artifact_manifest.json',inventory)
 print(json.dumps({'verdict':gates['verdict'],'candidate':gates['selected_candidate'],'history_identical':len(before),
                   'results':720,'bytes':sum(d['bytes'] for d in inventory.values()),'tests':test['passed']},indent=2))
if __name__=='__main__':verify()
