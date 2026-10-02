import csv,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent; TRACE=BASE/'outputs/case_traces'; OUT=BASE/'outputs'
def tokens(x):
    return [t for t in re.findall(r'[\u4e00-\u9fffA-Za-z]{2,}',x or '') if t not in {'长期','当前','用户','信息'}]
def classify(c):
    facts=' '.join(c.get('required_memory_facts',[])); mem=' '.join(str(x.get('memory',x)) for x in c.get('final_memories',[])); ts=tokens(facts); hits=sum(t in mem for t in ts)
    return 'YES' if ts and hits==len(ts) else ('PARTIAL' if hits else ('NO' if mem else 'UNRESOLVED'))
def main():
    cases={x['case_id']:x for x in json.loads((BASE.parent/'cases/cases.json').read_text(encoding='utf-8'))}; rows=[]
    for p in sorted(TRACE.glob('*.json')):
        c=json.loads(p.read_text()); rows.append({'case_id':c['case_id'],'family':c['family'],'coverage':classify({**cases[c['case_id']],**c})})
    with (OUT/'formation_coverage_offline.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['case_id','family','coverage']); w.writeheader(); w.writerows(rows)
if __name__=='__main__':main()
