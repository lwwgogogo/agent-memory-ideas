"""Statistics and fixed candidate/Gate rules; never changes estimator or native algorithm."""
import csv,json,statistics,ast,inspect
from fractions import Fraction as F
from config import ROOT,save,ready
from methods import PRACTICAL,m1,m2,m4
from metrics import pig,gap,npe,tge,tsr,correction,rank,reversal,crossover,null_gate,signal_gate
def exact(r):return {'A':F(r['U_A_exact']),'B':F(r['U_B_exact'])}
def serial(x):
 if isinstance(x,F):return float(x)
 if isinstance(x,dict):return {k:serial(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [serial(v) for v in x]
 return x
def no_leakage():
 allowed=('items','rho')
 funcs=(m1,m2,m4)
 return all(tuple(inspect.signature(f).parameters)==allowed for f in funcs) and not any(
  isinstance(n,(ast.Import,ast.ImportFrom)) and 'build_worlds' in ast.unparse(n)
  for n in ast.walk(ast.parse((ROOT/'methods.py').read_text())))
def verdict(gates,per):
 if not gates['G0']:return 'METHOD_VIABILITY_NO_GO'
 if all(gates.values()) and any(all(d.values()) for d in per.values()):return 'METHOD_VIABILITY_GO'
 if any(d['G1'] or d['G3'] or d['G5'] for d in per.values()):return 'METHOD_VIABILITY_WEAK'
 return 'METHOD_VIABILITY_NO_GO'
def evaluate():
 ready()
 rows=list(csv.DictReader((ROOT/'results/method_results.csv').open()))
 ix={(r['system'],r['family'],r['mechanism'],r['gamma'],r['policy'],r['target'],r['method']):r for r in rows}
 systems=('jitrl','memrl');methods=('M0','A1','M1','M2','M3','M4');gammas=('0.50','0.70','0.85','0.95')
 def get(s,f,m,g,p,t,method):return exact(ix[s,f,m,g,p,t,method])
 policies=[];retention=[];cross=[];stress=[];pairs=[]
 for s in systems:
  for f,mech,gs,targets in [('A','A',gammas,['T']),('B','B',gammas,['T']),('C','C',gammas,['T','T0','T1'])]+[
       ('D',mech,('0.95','0.99'),['T','T0','T1'] if mech=='C' else ['T']) for mech in ('A','B','C')]:
   for g in gs:
    for t in targets:
     base=pig(get(s,f,mech,g,'P',t,'M0'),get(s,f,mech,g,'Q',t,'M0'))
     for method in methods:
      up,uq=[get(s,f,mech,g,p,t,method) for p in ('P','Q')]
      rec={'system':s,'family':f,'mechanism':mech,'gamma':g,'target':t,'method':method,
           'PIG':pig(up,uq),'NPE_P':npe(up),'NPE_Q':npe(uq),'CorrectionRate':correction(pig(up,uq),base),
           'false_reversal':reversal(up,uq),'gap_P':gap(up),'gap_Q':gap(uq)}
      pairs.append(rec)
      if f=='A':policies.append(rec)
      if f=='B':
       for p,u in [('P',up),('Q',uq)]:
        retention.append({'system':s,'gamma':g,'policy':p,'method':method,'estimated_gap':gap(u),
          'TSR':tsr(u),'TGE':tge(u,F(1,10)),'rank':rank(u),'ranking_correct':rank(u)=='A',
          'TRUE_EFFECT_REVERSAL':rank(u)=='B'})
      if f=='D':
       from build_worlds import truth
       gt=truth(mech,t);truegap=gap(gt)
       for p,u in [('P',up),('Q',uq)]:
        stress.append({'system':s,'mechanism':mech,'gamma':g,'policy':p,'target':t,'method':method,
          'U_A':u['A'],'U_B':u['B'],'estimated_gap':gap(u),'TGE':tge(u,truegap),'minimum_cell_n':50 if g=='0.95' else 10,
          'bounded':all(0<=v<=1 for v in u.values()),
          'mechanism_criteria_pass':(npe(u)<=F(3,100) if mech=='A' else (rank(u)=='A' and tge(u,truegap)<=F(3,100)) if mech=='B' else (rank(u)==rank(gt) if t!='T' else npe(u)<=F(3,100)))})
  for g in gammas:
   for p in ('P','Q'):
    for method in methods:
     t0,t1=[get(s,'C','C',g,p,t,method) for t in ('T0','T1')]
     cross.append({'system':s,'gamma':g,'policy':p,'method':method,'T0_gap':gap(t0),'T1_gap':gap(t1),
       'T0_rank':rank(t0),'T1_rank':rank(t1),'both_correct':crossover(t0,t1),
       'ranking_accuracy':F((rank(t0)=='A')+(rank(t1)=='B'),2)})
 integrated=json.loads((ROOT/'results/integration_checks.json').read_text())['all_pass']
 leaked=not no_leakage();per={}
 for method in PRACTICAL:
  a95=[r for r in policies if r['method']==method and r['gamma']=='0.95']
  a_all=[r for r in policies if r['method']==method and r['gamma']!='0.50']
  b=[r for r in retention if r['method']==method and r['gamma']!='0.50']
  c=[r for r in cross if r['method']==method and r['gamma']!='0.50']
  supp=[r for r in stress if r['method']==method and r['gamma']=='0.95']
  per[method]={'G1':all(null_gate(r['CorrectionRate'],r['NPE_P'],r['NPE_Q']) for r in a95),
    'G2':all(r['CorrectionRate'] is not None and r['CorrectionRate']>=F(3,5) and max(r['NPE_P'],r['NPE_Q'])<=F(3,100) for r in a_all),
    'G3':signal_gate([r['rank'] for r in b],[r['TSR'] for r in b]),
    'G4':all(r['TSR'] is not None and r['TSR']>=F(1,2) for r in b),
    'G5':all(r['both_correct'] for r in c),
    'G6':not leaked,'G7':all(r['bounded'] and r['mechanism_criteria_pass'] for r in supp),
    'G8':integrated,'G9':True}
 gates={'G0':json.loads((ROOT/'results/native_reproduction.json').read_text())['pass'],
        'G1':sum(d['G1'] for d in per.values())>=2}
 for i in range(2,10):gates[f'G{i}']=any(d[f'G{i}'] for d in per.values())
 eligible=[m for m,d in per.items() if all(d.values())]
 # Fixed lexicographic tie-break: all gates, median target PIG, median true-gap error,
 # crossover rate, .99 stress error, simplicity; never choose oracle.
 def order(m):
  pi=[r['PIG'] for r in pairs if r['method']==m and r['family']!='D' and r['gamma']!='0.50']
  te=[r['TGE'] for r in retention if r['method']==m and r['gamma']!='0.50']
  co=sum(r['both_correct'] for r in cross if r['method']==m)
  su=[r['TGE'] for r in stress if r['method']==m and r['gamma']=='0.99']
  return (statistics.median(pi),statistics.median(te),-co,max(su),{'M1':0,'M4':1,'M2':2}[m])
 selected=min(eligible,key=order) if eligible else 'NONE'
 v=verdict(gates,per)
 if not gates['G1'] and v=='METHOD_VIABILITY_GO':v='METHOD_VIABILITY_WEAK'
 outputs={'policy_invariance.json':policies,'true_effect_retention.json':retention,'crossover.json':cross,
          'support_stress.json':stress,'ablations.json':{'mapping':{'A0':'M0','A1':'A1','A2':'M1','A3':'M4','A4':'M2','A5':'M3'},'pair_metrics':pairs},
          'gate_results.json':{'gates':gates,'candidate_gates':per,'selected_candidate':selected,'verdict':v,
          'method_selection_order':eligible if len(eligible)<2 else sorted(eligible,key=order),
          'no_oracle_leakage':not leaked,'scope':'exact finite discrete observed-state viability, not novelty or finite-sample robustness'}}
 for name,value in outputs.items():save(ROOT/'results'/name,serial(value))
 print(json.dumps(serial(outputs['gate_results.json']),indent=2))
if __name__=='__main__':evaluate()
