"""Fixed run: native bank -> adapter -> utility; metadata/truth remain in evaluator records."""
import csv,json,random,statistics
from fractions import Fraction as F
from dataclasses import asdict
from config import ROOT,SEEDS,canonical,sha,save,ready
from build_worlds import TARGETS,build,true_mu,truth
from native_baselines import create_bank,select,support,identity
from adapters import jitrl,memrl
from adapters.corrected_selector import CorrectedMemorySelector
from methods import estimate,oracle
def norm(items):return [(x.id,x.state,x.action,x.outcome) for x in items]
def run():
 ready()
 assert json.loads((ROOT/'results/native_reproduction.json').read_text())['pass'], 'G0 must pass first'
 manifest=build();results=[];integration=[];secondary_stats=[]
 with (ROOT/'results/native_outputs.jsonl').open('x') as native_file,(ROOT/'results/secondary_selection.jsonl').open('x') as sec_file:
  for w in manifest:
   rows=[json.loads(x) for x in (ROOT/w['file']).read_text().splitlines()]
   banks={s:create_bank(s,rows) for s in ('jitrl','memrl')}
   obs={s:reader.observations(banks[s]) for s,reader in [('jitrl',jitrl),('memrl',memrl)]}
   identical=norm(obs['jitrl'])==norm(obs['memrl'])
   assert identical
   integration.append({'world_id':w['id'],'normalized_inputs_identical':identical,
                       'sha256':sha(canonical(norm(obs['jitrl'])).encode())})
   for system,bank in banks.items():
    selecteds=[select(system,bank,seed) for seed in SEEDS]
    support_values=[support(system,v) for v in selecteds]
    u0={a:statistics.median(v[a] for v in support_values) for a in ('A','B')}
    for seed,ret in zip(SEEDS,selecteds):
     native_file.write(canonical({'system':system,'world_id':w['id'],'seed':seed,'k':20,'native_selected':ret})+'\n')
    wrappers={m:CorrectedMemorySelector(system,m).fit(bank) for m in ('M1','M2','M4')}
    for target in w['targets']:
     rho=TARGETS[target]
     estimates={'M0':u0,'A1':estimate('A1',obs[system],rho),
                'M3':oracle(obs[system],rho,true_mu(w['gamma'],w['policy']),TARGETS['T'])}
     estimates.update({m:wrapper.estimate_action_utility(rho) for m,wrapper in wrappers.items()})
     gt=truth(w['mechanism'],target)
     for method,u in estimates.items():
      results.append({'system':system,'world_id':w['id'],'family':w['family'],'mechanism':w['mechanism'],
          'gamma':w['gamma'],'policy':w['policy'],'target':target,'method':method,
          'U_A':float(u['A']),'U_B':float(u['B']),'U_A_exact':str(u['A']),'U_B_exact':str(u['B']),
          'true_A_exact':str(gt['A']),'true_B_exact':str(gt['B']),
          'estimand':'native_selection_support' if method=='M0' else 'target_success_probability' if method!='M2' and method!='A1' else 'global_observed_weighted_or_unweighted_mean',
          'oracle':method=='M3'})
     for method in ('M1','M4'):
      wrapper=wrappers[method];composition_set=set();cell_sets=[]
      for seed in SEEDS:
       ordered=list(bank);random.Random(seed).shuffle(ordered)
       ret=wrapper.select(ordered,20,rho);parsed=wrapper.reader.observations(ret)
       counts={s:{a:sum(x.state==s and x.action==a for x in parsed) for a in ('A','B')} for s in ('S0','S1')}
       composition_set.add(canonical(counts))
       assert len(ret)==20 and all(counts[s][a]>=2 for s in counts for a in counts[s])
       sec_file.write(canonical({'system':system,'world_id':w['id'],'target':target,'method':method,'seed':seed,
           'selected_ids':[identity(system,x) for x in ret],'cell_counts':counts})+'\n')
      secondary_stats.append({'system':system,'world_id':w['id'],'target':target,'method':method,
        '20_order_compositions_identical':len(composition_set)==1,'composition':json.loads(next(iter(composition_set))),
        'all_minimum_support_constraints_pass':True})
   print('finished',w['id'],flush=True)
 with (ROOT/'results/method_results.csv').open('x',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(results[0]),lineterminator='\n');writer.writeheader();writer.writerows(results)
 save(ROOT/'results/integration_checks.json',{'all_pass':all(x['normalized_inputs_identical'] for x in integration),'worlds':integration})
 save(ROOT/'results/secondary_summary.json',secondary_stats)
 print('method rows',len(results))
if __name__=='__main__':run()
