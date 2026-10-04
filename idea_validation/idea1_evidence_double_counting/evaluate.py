import json,csv,pathlib,collections,statistics,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from run_llm_test import parse
P=pathlib.Path(__file__).resolve().parent
NAMES=['OneSource','Derived3','Derived5','Independent3','ProvenanceAware5','IrrelevantLengthControl']
def summary(x):
 x=np.asarray(x,dtype=float)
 if not len(x):return {'n':0,'mean':None,'median':None,'std':None,'ci_low':None,'ci_high':None}
 rng=np.random.RandomState(20261004);bs=x[rng.randint(0,len(x),(10000,len(x)))].mean(axis=1)
 return {'n':len(x),'mean':float(x.mean()),'median':float(np.median(x)),'std':float(x.std(ddof=1)) if len(x)>1 else None,'ci_low':float(np.percentile(bs,2.5)),'ci_high':float(np.percentile(bs,97.5))}
def main():
 cases=json.loads((P/'cases/cases.json').read_text());rows=json.loads((P/'results/llm_results.json').read_text())
 assert len(rows)==240 and len({(r['case_id'],r['condition'],r['order_seed']) for r in rows})==240
 for r in rows:
  if r['status']=='OK':assert parse(r['raw'])==r['parsed']
 groups=collections.defaultdict(list)
 for r in rows:
  if r['status']=='OK':groups[(r['case_id'],r['condition'])].append(r['parsed']['confidence'])
 valid=[c for c in cases if c['audit']['status']=='NO_NEW_INFORMATION' and all(len(groups[(c['id'],n)])==2 for n in NAMES)]
 ids=[c['id'] for c in valid]
 matrix=np.array([[statistics.mean(groups[(c['id'],n)]) for n in NAMES] for c in valid]).reshape((-1,6))
 summaries={n:summary(matrix[:,i]) for i,n in enumerate(NAMES)}
 effects={'CI3':matrix[:,1]-matrix[:,0],'CI5':matrix[:,2]-matrix[:,0],'IEG':matrix[:,3]-matrix[:,0],'PC':matrix[:,2]-matrix[:,4],'D5_minus_D3':matrix[:,2]-matrix[:,1],'LengthGain':matrix[:,5]-matrix[:,0],'D5_minus_LengthControl':matrix[:,2]-matrix[:,5]}
 es={k:summary(v) for k,v in effects.items()}
 ratio=None;ratio_ci=None
 if len(ids) and abs(effects['IEG'].mean())>1e-12:
  ratio=float(effects['CI5'].mean()/effects['IEG'].mean())
  idx=np.random.RandomState(20261004).randint(0,len(ids),(10000,len(ids)));den=effects['IEG'][idx].mean(axis=1);num=effects['CI5'][idx].mean(axis=1)
  if es['IEG']['ci_low']>0 or es['IEG']['ci_high']<0:ratio_ci=[float(x) for x in np.percentile(num[abs(den)>1e-12]/den[abs(den)>1e-12],[2.5,97.5])]
 paired=[]
 for i,c in enumerate(valid):
  rec={'case_id':c['id'],'family':c['family'],**{n:float(matrix[i,j]) for j,n in enumerate(NAMES)},**{k:float(v[i]) for k,v in effects.items()}}
  rec['DCR']=rec['CI5']/rec['IEG'] if abs(rec['IEG'])>1e-12 else None;paired.append(rec)
 if paired:
  with (P/'results/paired_differences.csv').open('w') as f:
   w=csv.DictWriter(f,lineterminator='\n',fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
 order={}
 for seed in [17,43]:
  lookup={(r['case_id'],r['condition']):r['parsed']['confidence'] for r in rows if r['status']=='OK' and r['order_seed']==seed}
  order[str(seed)]={k:summary([lookup[(i,a)]-lookup[(i,b)] for i in ids]) for k,a,b in [('CI3','Derived3','OneSource'),('CI5','Derived5','OneSource'),('IEG','Independent3','OneSource'),('PC','Derived5','ProvenanceAware5')]}
 spread={}
 for n in NAMES:spread[n]=summary([abs(groups[(i,n)][0]-groups[(i,n)][1]) for i in ids])
 families={f:summary([r['CI5'] for r in paired if r['family']==f]) for f in sorted({c['family'] for c in cases})}
 parser={n:dict(collections.Counter(r['status'] for r in rows if r['condition']==n)) for n in NAMES}
 tokens={n:summary([r.get('provider_metadata',{}).get('prompt_eval_count',0) for r in rows if r['condition']==n]) for n in NAMES}
 stable=len(ids)>=16 and es['CI5']['ci_low']>0 and all(v['CI5']['mean']>0 for v in order.values())
 verdict='IDEA1_WEAK' if stable else 'IDEA1_NO_GO'
 reason='发现稳定膨胀，但近重复和模板措辞未被独立排除。' if stable else ('未满足预先固定的稳定派生记忆膨胀标准。' if len(ids)>=16 else '完整场景不足，输出不稳定导致行为证据不足；不能解释为已证明无效应。')
 report={'verdict':verdict,'reason':reason,'valid_cases':len(ids),'audit_passed':len(cases),'total_calls':len(rows),'conditions':summaries,'effects':es,'DCR':ratio,'DCR_bootstrap_ci':ratio_ci,'order_seeds':order,'absolute_order_difference':spread,'families_CI5':families,'parser':parser,'prompt_tokens':tokens,'excluded_case_ids':[c['id'] for c in cases if c['id'] not in ids]}
 (P/'results/statistics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 records=[{'metric':k,'type':'condition',**v} for k,v in summaries.items()]+[{'metric':k,'type':'paired_difference',**v} for k,v in es.items()]
 records.append({'metric':'DCR','type':'ratio_of_means','n':len(ids),'mean':ratio,'median':None,'std':None,'ci_low':ratio_ci[0] if ratio_ci else None,'ci_high':ratio_ci[1] if ratio_ci else None})
 with (P/'results/summary.csv').open('w') as f:
  w=csv.DictWriter(f,lineterminator='\n',fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 def fmt(x):return '不可估计' if x is None else '%.4f'%x
 lines=['# Idea 1 实验结果','',verdict+'：'+reason,'','## 样本与解析','',f'审计通过 {len(cases)} / 20；完整场景 {len(ids)} / 20；正式调用 {len(rows)}。解析失败不猜测，不混入主统计。两个顺序先在场景内平均；重采样单位为场景，非调用。','', '## 置信度与配对差值','','| 指标 | N | 均值 | 中位数 | 样本标准差 | 自助法 95% 区间 |','|---|---:|---:|---:|---:|---|']
 for r in records:lines.append('| '+r['metric']+' | '+str(r['n'])+' | '+' | '.join(fmt(r[x]) for x in ['mean','median','std'])+' | ['+fmt(r['ci_low'])+', '+fmt(r['ci_high'])+'] |')
 lines+=['','DCR 为群体均值之比；个体比值见 paired_differences.csv。分母区间覆盖零时不报告有限比值置信区间。模型置信度为自报概率，本实验无真实标签，因此不是校准误差测量。','', '## 替代解释','','- 长度：字符总数匹配，提示 token 数见下表；比较 D5−长度控制，不能仅凭字符相同宣称已控制 token 数。','- 重复：无整条完全相同的五条记忆，但包含原事实核心，属于近重复；无额外重复对照，不能完全排除。','- 措辞：不添加确定性或因果结论，仅用中性表述；缺少独立风格操纵，措辞效应仍有限制。','- 顺序：两个固定种子的逐种子差值与绝对变化如下；仅两个顺序不足以穷尽位置效应。','- 解析：首轮普通 JSON 163/240 失败并单独归档；正式 Schema 轮严格校验，所有失败逐条件报告。','', '| 条件 | 成功 | 未解析 | 平均提示 token | 平均顺序绝对差 |','|---|---:|---:|---:|---:|']
 for n in NAMES:lines.append('| '+n+' | '+str(parser[n].get('OK',0))+' | '+str(parser[n].get('UNRESOLVED',0))+' | '+fmt(tokens[n]['mean'])+' | '+fmt(spread[n]['mean'])+' |')
 lines+=['','| 顺序种子 | CI3 | CI5 | IEG | PC |','|---|---:|---:|---:|---:|']
 for seed,v in order.items():lines.append('| '+seed+' | '+' | '.join(fmt(v[k]['mean']) for k in ['CI3','CI5','IEG','PC'])+' |')
 lines+=['','## 领域一致性','','| 领域 | N | CI5 均值 | 95% 区间 |','|---|---:|---:|---|']
 for f,v in families.items():lines.append('| '+f+' | '+str(v['n'])+' | '+fmt(v['mean'])+' | ['+fmt(v['ci_low'])+', '+fmt(v['ci_high'])+'] |')
 lines+=['','## 解释边界','','数学阶段验证计数假设下的必然膨胀，行为阶段检验该模型是否出现稳定趋势。领域是五个低风险模拟领域，但事实均采用同一语法构造，不能推广为所有自然记忆或其他模型。独立条件具有明确独立性提示，可能产生提示效应。Schema 是格式约束，也构成本结论的适用条件。所有比较是本次固定小样本探索，无多重检验校正；不会为显著性扩样。','', '## 复现','','模型和模板见 README.md、run_llm_test.py 与 results/config.json。原始响应、提示、顺序种子、时间、token 数和解析结果见 results/llm_results.json。数学核验结果见 results/math_gate.json。']
 (P/'Idea1实验结果.md').write_text('\n'.join(lines)+'\n')
 (P/'最终结论.md').write_text('# 最终结论\n\n'+verdict+'\n\n'+reason+'\n\n数学阶段 PHASE_A_GO；行为结论仅适用于本次 qwq:32b、固定模板与 20 个虚构场景。有效完整场景 '+str(len(ids))+'。CI5 均值 '+fmt(es['CI5']['mean'])+'，95% 区间 ['+fmt(es['CI5']['ci_low'])+', '+fmt(es['CI5']['ci_high'])+']；IEG '+fmt(es['IEG']['mean'])+'；PC '+fmt(es['PC']['mean'])+'。\n\n近重复、共享模板、来源提示和 token 长度仍限定解释范围。无论结果如何，不转 Idea 2、不设计架构、不查文献，等待人工审阅。\n')
 if len(ids):
  plt.figure(figsize=(9,5));means=[summaries[n]['mean'] for n in NAMES];err=np.array([[means[i]-summaries[n]['ci_low'] for i,n in enumerate(NAMES)],[summaries[n]['ci_high']-means[i] for i,n in enumerate(NAMES)]])
  plt.bar(NAMES,means,yerr=err,capsize=4);plt.title('Strict complete-case analysis (n=%d)'%len(ids));plt.xticks(rotation=25,ha='right');plt.ylabel('Mean reported P(H1), case bootstrap 95% CI');plt.ylim(0,1);plt.tight_layout();plt.savefig(P/'plots/llm_confidence.png',dpi=180);plt.close()
 print(json.dumps({'verdict':verdict,'valid_cases':len(ids),'means':{k:v['mean'] for k,v in summaries.items()},'effects':{k:v['mean'] for k,v in es.items()},'DCR':ratio,'parser':parser},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
