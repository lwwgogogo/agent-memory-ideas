import csv,json
from collections import defaultdict
from pathlib import Path
BASE=Path(__file__).resolve().parent; OUT=BASE/'outputs'; TRACE=OUT/'case_traces'
def load():
    rows=[]
    for p in sorted(TRACE.glob('*.json')):
        try: rows.append(json.loads(p.read_text(encoding='utf-8')))
        except Exception: pass
    return rows
def acc(rows,key): return sum(bool(r.get('answers',{}).get(key,{}).get('correct')) for r in rows)/len(rows) if rows else None
def main():
    rows=load(); n=len(rows); fam=defaultdict(list)
    for r in rows:fam[r.get('family','?')].append(r)
    o1p=OUT/'o1_qwq_32b.json'; o1={x['case_id']:x['result'] for x in json.loads(o1p.read_text())} if o1p.exists() else {}
    def count(pred): return sum(pred(r) for r in rows)
    stats={'status':'PARTIAL_DO_NOT_INTERPRET' if n<96 else 'COMPLETE','total_cases_seen':n,'expected_cases':96,'valid_cases':n,'accuracy':{k:acc(rows,k) for k in ['O0','O2','O3a','O3b']},'O1_accuracy_seen':(sum(o1.get(r['case_id'],{}).get('correct',False) for r in rows)/n if n else None),'per_family':{f:{'n':len(v),**{k:acc(v,k) for k in ['O0','O2','O3a','O3b']}} for f,v in sorted(fam.items())},'diagnostics':{'O0_wrong_O1_correct':count(lambda r:not r['answers']['O0']['correct'] and o1.get(r['case_id'],{}).get('correct') is True),'availability_NO':count(lambda r:r.get('required_information_present')=='NO'),'availability_PARTIAL':count(lambda r:r.get('required_information_present')=='PARTIAL'),'availability_YES':count(lambda r:r.get('required_information_present')=='YES'),'availability_YES_O2_correct':count(lambda r:r.get('required_information_present')=='YES' and r['answers']['O2']['correct']),'availability_YES_O2_wrong':count(lambda r:r.get('required_information_present')=='YES' and not r['answers']['O2']['correct']),'O2_wrong_O3a_correct':count(lambda r:not r['answers']['O2']['correct'] and r['answers']['O3a']['correct']),'O3a_wrong_O3b_correct':count(lambda r:not r['answers']['O3a']['correct'] and r['answers']['O3b']['correct']),'O3b_still_wrong':count(lambda r:not r['answers']['O3b']['correct'])}}
    (OUT/'analysis_summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'analysis_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f); w.writerow(['scope','metric','value'])
        for k,v in stats['accuracy'].items():w.writerow(['overall',k,v])
        for f,x in stats['per_family'].items():
            for k,v in x.items():w.writerow([f,k,v])
        for k,v in stats['diagnostics'].items():w.writerow(['diagnostic',k,v])
    md=['# 自动分析结果','',f'- 状态：`{stats["status"]}`',f'- 已读取 case：{n}/96（partial 期间不得形成科研结论）','', '## Overall']
    md += [f'- {k}: {v}' for k,v in stats['accuracy'].items()]+[f'- O1（已完成 trace 子集）: {stats["O1_accuracy_seen"]}']
    md += ['','## Per-family']+[f'- {f}: n={x["n"]}, O0={x["O0"]}, O2={x["O2"]}, O3a={x["O3a"]}, O3b={x["O3b"]}' for f,x in stats['per_family'].items()]
    md += ['','## 诊断统计']+[f'- {k}: {v}' for k,v in stats['diagnostics'].items()]
    (BASE/'自动分析结果.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
if __name__=='__main__':main()
