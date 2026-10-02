import csv,json
from pathlib import Path
BASE=Path(__file__).resolve().parent; TRACE=BASE/'outputs/case_traces'
def main():
 rows=[]
 for p in sorted(TRACE.glob('*.json')):
  d=json.loads(p.read_text(encoding='utf-8')); events={'ADD':0,'UPDATE':0,'DELETE':0,'EMPTY':0}; adds=[]; gets=[]
  for t in d.get('turns',[]):
   rs=(t.get('add_return') or {}).get('results') or []; ev=[str(x.get('event','')) for x in rs if isinstance(x,dict)]
   for e in ev:
    if e in events: events[e]+=1
   if not rs: events['EMPTY']+=1
   adds.append(len(rs)); gets.append(len(t.get('memory_after_turn') or []))
  final=len(d.get('final_memories') or []); search=len(d.get('normal_search_result') or [])
  if all(x==0 for x in adds) and final==0: pattern='P1 NO_FORMATION'
  elif any(x>0 for x in adds) and all(x==0 for x in gets): pattern='P2 PERSISTENCE_OR_READ_BUG'
  elif any(x>0 for x in gets) and final==0: pattern='P3 MEMORY_DISAPPEARED'
  elif final==0 and any(x>0 for x in gets): pattern='P4 TRACE_SERIALIZATION_BUG'
  elif final>0 and search==0: pattern='P5 RETRIEVAL_EMPTY'
  else: pattern='NONE_OR_UNRESOLVED'
  rows.append({'case_id':d.get('case_id'),'family':d.get('family'),'turns':len(d.get('turns',[])),'add_created':events['ADD'],'add_updated':events['UPDATE'],'add_deleted':events['DELETE'],'add_empty':events['EMPTY'],'get_all_counts':';'.join(map(str,gets)),'final_get_all_items':final,'normal_search_results':search,'persistence_pattern':pattern})
 if rows:
  with (BASE/'memory_persistence_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 from collections import Counter
 c=Counter(x['persistence_pattern'] for x in rows); lines=['# Memory持久化审计','','状态：`PARTIAL_DIAGNOSTIC_ONLY`；主实验未完成前不得形成科研结论。','',f'- 已读取完整单 case trace：{len(rows)}']+[f'- {k}：{v}' for k,v in sorted(c.items())]
 (BASE/'Memory持久化审计.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__':main()
