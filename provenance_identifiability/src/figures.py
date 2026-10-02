import csv
from pathlib import Path
try:
 import matplotlib.pyplot as plt
except Exception:
 raise SystemExit('MATPLOTLIB_UNAVAILABLE')
root=Path(__file__).resolve().parent.parent; rows=list(csv.DictReader(open(root/'outputs/per_seed_results.csv'))); rows=[r for r in rows if r['source']=='ALL']
def mean(key,group):
 x=[float(r[key]) for r in rows if r['compression']==str(group)]
 return sum(x)/len(x)
for name,key,title,y in [('图1_ProvenanceF1_随压缩强度变化.png','identifiability_upper_bound','可识别性上界随压缩强度变化','上界'),('图2_ProvenanceF1_随Trace完整度变化.png','identifiability_upper_bound','可识别性上界随 Trace 完整度变化','上界')]:
 xs=[0,.2,.4,.6,.8] if '压缩' in title else [0,.2,.5,.8,1.0]
 ys=[mean(key,x) for x in xs] if '压缩' in title else [sum(float(r[key]) for r in rows if r['trace']==str(x))/len([r for r in rows if r['trace']==str(x)]) for x in xs]
 plt.figure(); plt.plot(xs,ys,marker='o'); plt.xlabel('压缩强度' if '压缩' in title else 'Trace 完整度'); plt.ylabel(y); plt.title(title); plt.grid(True); plt.tight_layout(); plt.savefig(root/'figures'/name,dpi=140); plt.close()
for idx,(title,field) in enumerate([('歧义率随压缩强度变化','ambiguity_rate'),('不同 Source Structure 的可识别性上界','identifiability_upper_bound'),('歧义率随 Transformation 深度变化','ambiguity_rate')],3):
 groups=sorted(set(r['compression'] for r in rows)) if idx==3 else sorted(set(r['source'] for r in csv.DictReader(open(root/'outputs/per_seed_results.csv')) if r['source']!='ALL')) if idx==4 else sorted(set(r['transformation'] for r in csv.DictReader(open(root/'outputs/per_seed_results.csv')) if r['source']!='ALL'))
 vals=[]
 allr=list(csv.DictReader(open(root/'outputs/per_seed_results.csv')))
 for g in groups:
  z=[float(r[field]) for r in allr if (r['compression']==g if idx==3 else r['source']==g if idx==4 else r['transformation']==g)]
  vals.append(sum(z)/len(z))
 plt.figure(figsize=(7,4)); plt.bar(range(len(groups)),vals); plt.xticks(range(len(groups)),groups,rotation=35,ha='right'); plt.ylabel(field); plt.title(title); plt.tight_layout(); plt.savefig(root/'figures'/f'图{idx}_{title}.png',dpi=140); plt.close()
