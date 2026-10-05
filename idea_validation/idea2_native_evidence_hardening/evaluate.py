"""Recompute every endpoint from native-returned items; no action-bank utility means."""
import json,statistics,ast
from fractions import Fraction
from pathlib import Path
from scipy.stats import spearmanr
from common import ROOT,GAMMAS,KS,SEEDS,SOURCES,COMMITS,sha,save,assert_ready
from native_metrics import parse,selection,rcd,native_piur,balanced_reduction
from build_exact_logs import multiset_hash,order_hash,counts,target_value,RATES,ordered
def median(xs):
    vals=[v for v in xs if v is not None]
    return statistics.median(vals) if vals else None
def dose(gamma_to_d):
    ds=[gamma_to_d[g] for g in GAMMAS]
    rho=0.0 if len(set(ds))==1 else float(spearmanr([float(g) for g in GAMMAS],ds).statistic)
    return {'D_gamma':dict(zip(GAMMAS,ds)),'spearman_rho':rho,
            'thresholds_pass':ds[3]>ds[1] and ds[3]>ds[0]+0.20}
def direction(p,q):return (1 if p>0 else -1 if p<0 else 0, 1 if q>0 else -1 if q<0 else 0)
def k_consistency(summary):
    ref=direction(summary[20]['median_SSP_P'],summary[20]['median_SSP_Q'])
    valid=ref[0]*ref[1]==-1
    entries={str(k):{'median_SSP_P':summary[k]['median_SSP_P'],
                     'median_SSP_Q':summary[k]['median_SSP_Q'],
                     'reversal_rate':summary[k]['reversal_rate'],
                     'median_RCD':summary[k]['median_RCD'],
                     'direction_consistent':valid and direction(summary[k]['median_SSP_P'],summary[k]['median_SSP_Q'])==ref}
             for k in KS}
    n=sum(v['direction_consistent'] for v in entries.values())
    return {'primary_direction':ref,'by_k':entries,'consistent_k_count':n,'pass':n>=3}
def reversal_gate(summary):
    return summary['reversal_rate']>=.80 and summary['median_RCD']>=.30
def decide(gates,primary):
    if all(gates[f'G{i}']['pass'] for i in range(8)):return 'NATIVE_EVIDENCE_GO'
    if not gates['G0']['pass'] or not gates['G1']['pass']:return 'NATIVE_EVIDENCE_NO_GO'
    if not (gates['G2']['pass'] or gates['G3']['pass']):return 'NATIVE_EVIDENCE_NO_GO'
    if all(primary[s]['median_BAL_reduction'] is None or primary[s]['median_BAL_reduction']<.5 for s in primary):
        return 'NATIVE_EVIDENCE_NO_GO'
    return 'NATIVE_EVIDENCE_NARROW'
def exact_environment(records):
    all_checks=[]
    for g in GAMMAS:
        conditions={}
        for p in ('P','Q'):
            rows=[json.loads(x) for x in (ROOT/f'results/exact_logs/gamma_{g}_{p}.jsonl').read_text().splitlines()]
            c=counts(rows);conditions[p]=c
            good=len(rows)==2000 and len({r['id'] for r in rows})==2000
            for state in RATES:
                good=good and sum(c[f'{state}/{a}']['exposure'] for a in ('A','B'))==1000
                for action in ('A','B'):
                    cell=c[f'{state}/{action}']
                    pa=Fraction(g) if state=='S0' else 1-Fraction(g)
                    if p=='Q':pa=1-pa
                    expected=1000*(pa if action=='A' else 1-pa)
                    good=good and cell['exposure']==expected and Fraction(cell['success'],cell['exposure'])==RATES[state]
            h=multiset_hash(rows);reps=[]
            for seed in SEEDS:
                ordered_rows=ordered(rows,seed)
                checks=[r for r in records if r['gamma']==g and r['policy']==p and r['seed']==seed]
                valid=len(checks)==8 and all(r['input_multiset_sha256']==h and
                    r['input_order_sha256']==order_hash(ordered_rows) for r in checks)
                reps.append(valid and multiset_hash(ordered_rows)==h)
            all_checks.append({'gamma':g,'policy':p,'exact_cells':good,'all_20_order_multisets_identical':all(reps),
                               'multiset_sha256':h,'cells':c})
        for state in RATES:
            assert conditions['P'][f'{state}/A']==conditions['Q'][f'{state}/B']
            assert conditions['P'][f'{state}/B']==conditions['Q'][f'{state}/A']
    return {'pass':all(c['exact_cells'] and c['all_20_order_multisets_identical'] for c in all_checks)
                  and target_value('A')==target_value('B')==Fraction(11,20),'checks':all_checks,'target_value_exact':'11/20'}
def native_provenance(records):
    expected=2*len(GAMMAS)*2*len(SEEDS)*len(KS)
    good=len(records)==expected
    seen=set();counts_by={'jitrl':0,'memrl':0}
    for r in records:
        system=r['system'];key=(system,r['gamma'],r['policy'],r['seed'],r['k'])
        good=good and key not in seen;seen.add(key);counts_by[system]+=1
        parsed=parse(system,r['native_return'])
        good=good and len(parsed)==r['k'] and parsed==r['parsed_selection'] and selection(parsed)==r['metrics']
        funcs=[r['native_function']] if system=='jitrl' else list(r['native_functions'].values())
        for fn in funcs:
            path=Path(fn['file'])
            good=good and path.is_relative_to(SOURCES/system) and sha(path.read_bytes())==fn['file_sha256']
        if system=='jitrl':good=good and funcs[0]['symbol']=='get_top_episodes'
        else:
            good=good and {f['symbol'] for f in funcs}=={'QValueUpdater.update','ValueAwareSelector.select'}
            good=good and r['configuration']['epsilon']==0.0 and r['configuration']['recency_boost']==0.0
    forbidden=[]
    for path in ROOT.rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Call) and ((isinstance(node.func,ast.Attribute) and node.func.attr=='score_action')
               or (isinstance(node.func,ast.Name) and node.func.id=='score_action')):
                forbidden.append(str(path))
    return {'pass':bool(good and not forbidden),'records_by_system':counts_by,
            'expected_records':expected,'legacy_aggregation_calls':forbidden,
            'basis':'native selection return only; updater called 320000 times, selector 640 times, episode ranker 640 times in formal run'}
def evaluate():
    assert_ready()
    rows={s:[json.loads(l) for l in (ROOT/f'results/{s}_native_raw.jsonl').read_text().splitlines()] for s in ('jitrl','memrl')}
    allrows=rows['jitrl']+rows['memrl'];summaries={};dose_out={};k_out={};primary={};tie={}
    for system,records in rows.items():
        ix={(r['gamma'],r['policy'],r['seed'],r['k']):r for r in records}
        grouped={};pairs=[]
        for g in GAMMAS:
            grouped[g]={}
            for k in KS:
                ps=[]
                for seed in SEEDS:
                    pr,qr,br=[ix[(gg,pp,seed,k)] for gg,pp in [(g,'P'),(g,'Q'),('0.50','P')]]
                    pm,qm,bm=[selection(parse(system,r['native_return'])) for r in [pr,qr,br]]
                    pair={'system':system,'gamma':g,'k':k,'seed':seed,
                          'SSP_P':pm['SSP'],'SSP_Q':qm['SSP'],'SSP_BAL':bm['SSP'],
                          'f_A_P':pm['f_A'],'f_A_Q':qm['f_A'],'f_A_BAL':bm['f_A'],
                          'RWP_P':pm['RWP'],'RWP_Q':qm['RWP'],
                          'native_RCD':rcd(pm,qm),'native_PIUR':native_piur(pm,qm),
                          'BAL_reduction':balanced_reduction(pm,qm,bm)}
                    ps.append(pair);pairs.append(pair)
                stats={'n':len(ps),'median_SSP_P':median([r['SSP_P'] for r in ps]),
                       'median_SSP_Q':median([r['SSP_Q'] for r in ps]),
                       'median_RCD':median([r['native_RCD'] for r in ps]),
                       'median_abs_SSP_P_minus_Q':median([abs(r['SSP_P']-r['SSP_Q']) for r in ps]),
                       'reversal_rate':sum(r['native_PIUR'] for r in ps)/len(ps),
                       'policy_aligned_reversal_rate':sum(r['SSP_P']>.1 and r['SSP_Q']<-.1 for r in ps)/len(ps),
                       'median_BAL_reduction':median([r['BAL_reduction'] for r in ps]),
                       'valid_BAL_reductions':sum(r['BAL_reduction'] is not None for r in ps)}
                grouped[g][k]=stats
        primary[system]=grouped['0.95'][20]
        summaries[system]={'system':system,'primary':primary[system],'by_gamma_k':grouped,'all_pairs':pairs}
        dose_out[system]=dose({g:grouped[g][20]['median_RCD'] for g in GAMMAS})
        k_out[system]=k_consistency(grouped['0.95'])
        tie[system]={'all_record_tie_audits':[dict(gamma=r['gamma'],policy=r['policy'],seed=r['seed'],k=r['k'],**r['tie_audit']) for r in records],
                     'definitions':{'selected_tie_fraction':'fraction of selected items whose score occurs more than once within the selected set',
                                    'selected_duplicate_score_fraction':'1 - unique_selected_score_count / selected_count'},
                     'mechanism':'Shuffling is uniform over the fixed input multiset. Native stable tie handling is unchanged. Selection reflects available high-score pool composition; no distinct action utility is inferred.'}
        save(ROOT/f'results/{system}_native_summary.json',summaries[system])
    provenance=native_provenance(allrows);env=exact_environment(allrows)
    gates={'G0':{'pass':provenance['pass'],'detail':provenance},'G1':{'pass':env['pass']},
           'G2':{'pass':reversal_gate(primary['jitrl']),'detail':primary['jitrl']},
           'G3':{'pass':reversal_gate(primary['memrl']),'detail':primary['memrl']},
           'G4':{'pass':all(x['median_BAL_reduction'] is not None and x['median_BAL_reduction']>=.5 for x in primary.values()),
                 'detail':{s:p['median_BAL_reduction'] for s,p in primary.items()}},
           'G5':{'pass':all(d['thresholds_pass'] for d in dose_out.values()) and any(d['spearman_rho']>=.8 for d in dose_out.values()),'detail':dose_out},
           'G6':{'pass':all(d['pass'] for d in k_out.values()),'detail':k_out}}
    gates['G7']={'pass':provenance['pass'] and all(gates[k]['pass'] for k in ['G2','G3','G4','G5']),
                 'detail':'All metrics recomputed directly from native_return; no old adapter import and no bank action mean used.'}
    boundary=json.loads((ROOT/'results/jitrl_state_aware_results.json').read_text())
    gates['G8']={'status':boundary['status'],'hard_gate':False,'detail':boundary}
    verdict=decide(gates,primary)
    save(ROOT/'results/tie_audit.json',tie)
    save(ROOT/'results/dose_response.json',dose_out)
    save(ROOT/'results/k_sensitivity.json',k_out)
    save(ROOT/'results/exact_environment_checks.json',env)
    save(ROOT/'results/gate_results.json',{'gates':gates,'verdict':verdict,'primary':primary})
    print(json.dumps({'verdict':verdict,'gates':{k:v.get('pass',v.get('status')) for k,v in gates.items()},'primary':primary,'dose':dose_out},indent=2))
if __name__=='__main__':evaluate()
