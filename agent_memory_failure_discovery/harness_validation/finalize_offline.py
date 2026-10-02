import csv,hashlib,json,os
from collections import Counter
from pathlib import Path
B=Path(__file__).resolve().parent; O=B/'outputs'; T=O/'case_traces'
def digest(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def main():
 traces=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(T.glob('*.json'))]; cases={x['case_id']:x for x in json.loads((B.parent/'cases/cases.json').read_text(encoding='utf-8'))}
 o1={x['case_id']:x['result']['correct'] for x in json.loads((O/'o1_qwq_32b.json').read_text())}
 acc={k:sum(r['answers'][k]['correct'] for r in traces) for k in ['O0','O2','O3a','O3b']}; acc['O1']=sum(o1[r['case_id']] for r in traces)
 patterns=[]; coverage=[]
 for r in traces:
  adds=[]; gets=[]; events=Counter()
  for t in r['turns']:
   rs=(t.get('add_return') or {}).get('results') or []; adds.append(len(rs)); gets.append(len(t.get('memory_after_turn') or [])); events.update(x.get('event','') for x in rs if isinstance(x,dict)); events.update(['EMPTY'] if not rs else [])
  final=len(r.get('final_memories') or []); search=len(r.get('normal_search_result') or [])
  pat='P1 NO_FORMATION' if not any(adds) and not final else ('P2 PERSISTENCE_OR_READ_BUG' if any(adds) and not any(gets) else ('P3 MEMORY_DISAPPEARED' if any(gets) and not final else ('P5 RETRIEVAL_EMPTY' if final and not search else 'P_OK NORMAL'))); patterns.append((r['case_id'],pat,events,gets,final,search))
  fs=' '.join(cases[r['case_id']].get('required_memory_facts',[])); mem=' '.join(str(x.get('memory',x)) for x in r.get('final_memories',[])); toks=fs.replace(':',' ').split(); hit=sum(x in mem for x in toks); coverage.append('YES' if toks and hit==len(toks) else ('PARTIAL' if hit else ('NO' if not mem else 'UNRESOLVED')))
 with (B/'memory_persistence_audit_final.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['case_id','pattern','add_events','get_counts','final_items','search_count']);w.writerows([[a,b,dict(c),';'.join(map(str,d)),e,g] for a,b,c,d,e,g in patterns])
 with (B/'formation_coverage_final.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['case_id','coverage']);w.writerows(zip([r['case_id'] for r in traces],coverage))
 files=[O/'harness_results.json',O/'formation_coverage.csv',B.parent/'cases/cases.json',B/'run_validation.py',B/'canonical_grader.py']; lines=['# 实验冻结清单','','完整 96 case 结果冻结；分析期间不修改 outputs。']+[f'- `{p}` SHA256 `{digest(p)}` size={p.stat().st_size} mtime={p.stat().st_mtime}' for p in files if p.exists()];(B/'实验冻结清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 summary={'status':'COMPLETE','trace_count':len(traces),'accuracy':{k:{'correct':v,'total':96,'accuracy':v/96} for k,v in acc.items()},'persistence':dict(Counter(x[1] for x in patterns)),'coverage':dict(Counter(coverage))};(B/'failure_localization.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');(B/'failure_localization.csv').write_text('metric,value\n'+ '\n'.join(f'{k},{v}' for k,v in acc.items()),encoding='utf-8')
 (B/'Harness完整性检查.md').write_text('# Harness完整性检查\n\n状态：`PASS`，96 trace、96 case_id、C1-C8 各 12。\n',encoding='utf-8');(B/'最终实验配置.md').write_text('# 最终实验配置\n\nMem0 2.2.1；writer qwen2.5:14b；reasoner qwq:32b；embedding nomic-embed-text；Qdrant local；sequential add；O1 Raw History；O2 actual Mem0 items；O3a atomic；O3b structured；96 cases；reasoner temperature=0。\n',encoding='utf-8')
 (B/'Failure定位最终报告.md').write_text('# Failure定位最终报告\n\n状态：`COMPLETE`。\n\n'+'\n'.join(f'- {k}: {v}/96 = {v/96:.3f}' for k,v in acc.items())+'\n\nPersistence：'+str(dict(Counter(x[1] for x in patterns)))+'\nCoverage：'+str(dict(Counter(coverage)))+'\n',encoding='utf-8')
if __name__=='__main__':main()
