import csv,json
from pathlib import Path
BASE=Path(__file__).resolve().parent; TRACE=BASE/'outputs/case_traces'
def main():
 rows=[]
 for p in sorted(TRACE.glob('*.json')):
  d=json.loads(p.read_text(encoding='utf-8')); a=d.get('answers',{})
  rows.append({'case_id':d.get('case_id'),'family':d.get('family'),'O0_correct':bool(a.get('O0',{}).get('correct')),'O2_correct':bool(a.get('O2',{}).get('correct')),'O3a_correct':bool(a.get('O3a',{}).get('correct')),'O3b_correct':bool(a.get('O3b',{}).get('correct')),'info':d.get('required_information_present')})
 op=BASE/'outputs/o1_qwq_32b.json'; o1={x['case_id']:x['result']['correct'] for x in json.loads(op.read_text())} if op.exists() else {}
 for r in rows:r['O1_correct']=o1.get(r['case_id'])
 def calc(rs):
  n=lambda f:sum(1 for r in rs if f(r))
  return {'n':len(rs),'O0_correct':n(lambda r:r['O0_correct']),'O0_wrong_O1_wrong':n(lambda r:not r['O0_correct'] and r['O1_correct'] is False),'O0_wrong_O1_correct':n(lambda r:not r['O0_correct'] and r['O1_correct'] is True),'O1_correct_info_NO':n(lambda r:r['O1_correct'] is True and r['info']=='NO'),'O1_correct_info_YES_O2_correct':n(lambda r:r['O1_correct'] is True and r['info']=='YES' and r['O2_correct']),'O1_correct_info_YES_O2_wrong':n(lambda r:r['O1_correct'] is True and r['info']=='YES' and not r['O2_correct']),'O2_wrong_O3a_correct':n(lambda r:not r['O2_correct'] and r['O3a_correct']),'O3a_wrong_O3b_correct':n(lambda r:not r['O3a_correct'] and r['O3b_correct']),'O3b_wrong':n(lambda r:not r['O3b_correct'])}
 groups={'overall':rows}; groups.update({f:[r for r in rows if r['family']==f] for f in sorted({r['family'] for r in rows})}); out={k:calc(v) for k,v in groups.items()}
 (BASE/'localization_summary.json').write_text(json.dumps({'status':'PARTIAL_DO_NOT_INTERPRET' if len(rows)<96 else 'COMPLETE','groups':out},ensure_ascii=False,indent=2),encoding='utf-8')
 with (BASE/'localization_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['group','metric','value']);[w.writerow([g,k,v]) for g,x in out.items() for k,v in x.items()]
 (BASE/'Failure定位自动分析.md').write_text('# Failure定位自动分析\n\n状态：`PARTIAL_DO_NOT_INTERPRET`（若未完成 96 case）。\n\n本工具只读单 case traces 与 O1 case-level 文件，不读取 monolithic results。\n',encoding='utf-8')
if __name__=='__main__':main()
