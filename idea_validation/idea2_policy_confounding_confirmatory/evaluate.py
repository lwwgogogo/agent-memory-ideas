import json,csv,collections
import numpy as np
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from core import ROOT,CONDITIONS,PRIMARY,ORDERED,LEVELS,ensure_env,save,parse,canonical,paired_average

def summary(values):
    x=np.asarray(values,dtype=float)
    if not len(x):return {'n':0,'mean':None,'median':None,'std':None,'ci_low':None,'ci_high':None}
    boot=x[np.random.default_rng(20261005).integers(0,len(x),(10000,len(x)))].mean(axis=1)
    return {'n':len(x),'mean':float(x.mean()),'median':float(np.median(x)),'std':float(x.std(ddof=1)) if len(x)>1 else None,'ci_low':float(np.quantile(boot,.025)),'ci_high':float(np.quantile(boot,.975))}

def assess_gates(metrics,gamma,sensitivity,valid_count,complete_count,counts):
    b=metrics['ConfoundedMemory']['mean'];bal=metrics['BalancedMemory']['mean'];st=metrics['StratifiedOracle']['mean'];none=metrics['NoMemory']['mean']
    bc=metrics['BalancedCorrection']['mean'];sc=metrics['StratifiedCorrection']['mean']
    means=[gamma[str(g)]['ConfoundedMemory']['mean'] for g in LEVELS]
    rho=None;dose=False
    if all(v is not None for v in means) and len(set(means))>1:
        rho=round(float(spearmanr(LEVELS,means)[0]),12);dif=np.diff(means)
        dose=abs(means[0])<=.03 and sum(d<=0 for d in dif)<=1 and bool(np.all(dif>=-.005-1e-12)) and rho>=.8
    def positive_slice(axis,key):
        v=sensitivity[axis][key]['ConfoundedMemory']['mean'];return v is not None and v>.05
    gates={'G0':complete_count>=19 and min(counts.values())>=4 and valid_count/320>=.99,'G1':b is not None and b>=.08 and metrics['ConfoundedMemory']['ci_low']>0,'G2':bool(dose),'G3':b is not None and bal is not None and abs(bal)<=.03 and bc>=.6*b,'G4':b is not None and st is not None and abs(st)<=.03 and sc>=.6*b,'G5':none is not None and abs(none)<=.02,'G6':positive_slice('label','AB') and positive_slice('label','BA'),'G7':positive_slice('order','O1') and positive_slice('order','O2')}
    weak=b is not None and b>0 and bc>0 and sc>0 and abs(none)<b
    verdict='IDEA2_CONFIRM_GO' if all(gates.values()) else ('IDEA2_CONFIRM_WEAK' if weak else 'IDEA2_CONFIRM_NO_GO')
    return {k:bool(v) for k,v in gates.items()},rho,verdict

def write_csv(path,rows):
    if rows:
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def analyze(cases,rows):
    expected={r['run_id'] for c in cases for r in c['runs']}
    assert len(rows)==320 and {r['run_id'] for r in rows}==expected and len(expected)==320
    groups=collections.defaultdict(list)
    for r in rows:
        if r['final_status']=='VALID':
            last=r['retry_attempt'] if r['retry_attempt'] is not None else r['first_attempt']
            x=parse(last['raw']);assert x==r['parsed'];a,b=canonical(x,r['version']);assert abs(r['miab']-(a-b))<1e-12
        groups[(r['case_id'],r['condition'])].append(r)
    agg={(c['id'],n):paired_average(groups[(c['id'],n)],n) for c in cases for n in CONDITIONS}
    cohort=[c for c in cases if all(agg[(c['id'],n)] is not None for n in PRIMARY)]
    scenario=[]
    for c in cases:
        d={'case_id':c['id'],'family':c['family'],'gamma':c['gamma'],'primary_complete':c in cohort}
        for n in CONDITIONS:
            a=agg[(c['id'],n)]
            for key in ['miab','AB','BA']+(['O1','O2'] if n in ORDERED else []):d[n+'_'+key]=a[key] if a is not None else None
        scenario.append(d)
    metrics={n:summary([agg[(c['id'],n)]['miab'] for c in cohort if agg[(c['id'],n)] is not None]) for n in CONDITIONS}
    for metric,a,b in [('BalancedCorrection','ConfoundedMemory','BalancedMemory'),('StratifiedCorrection','ConfoundedMemory','StratifiedOracle'),('DeltaConfounded','ConfoundedMemory','NoMemory'),('AggregateAmplification','AggregateSummary','ConfoundedMemory')]:
        metrics[metric]=summary([agg[(c['id'],a)]['miab']-agg[(c['id'],b)]['miab'] for c in cohort if agg[(c['id'],a)] is not None and agg[(c['id'],b)] is not None])
    gamma={str(g):{n:summary([agg[(c['id'],n)]['miab'] for c in cohort if c['gamma']==g and agg[(c['id'],n)] is not None]) for n in CONDITIONS} for g in LEVELS}
    sensitivity={}
    for axis,keys,names in [('label',['AB','BA'],CONDITIONS),('order',['O1','O2'],ORDERED)]:
        sensitivity[axis]={key:{n:summary([agg[(c['id'],n)][key] for c in cohort if agg[(c['id'],n)] is not None]) for n in names} for key in keys}
    counts={str(g):sum(c['gamma']==g for c in cohort) for g in LEVELS}
    valid=sum(r['final_status']=='VALID' for r in rows);gates,rho,verdict=assess_gates(metrics,gamma,sensitivity,valid,len(cohort),counts)
    retried=sum(r['retry_attempt'] is not None for r in rows)
    rates={n:dict(collections.Counter(r['final_status'] for r in rows if r['condition']==n)) for n in CONDITIONS}
    raw_none=[r['parsed']['p_success_left']-r['parsed']['p_success_right'] for r in rows if r['condition']=='NoMemory' and r['final_status']=='VALID']
    b=metrics['ConfoundedMemory']['mean']
    result={'verdict':verdict,'gates':gates,'planned_runs':320,'valid_runs':valid,'retried_runs':retried,'invalid_runs':320-valid,'formal_attempts':320+retried,'complete_scenarios':len(cohort),'complete_by_gamma':counts,'excluded_scenarios':[c['id'] for c in cases if c not in cohort],'metrics':metrics,'by_gamma':gamma,'spearman_rho':rho,'sensitivity':sensitivity,'balanced_correction_percent':100*metrics['BalancedCorrection']['mean']/b if b is not None and b>0 else None,'stratified_correction_percent':100*metrics['StratifiedCorrection']['mean']/b if b is not None and b>0 else None,'status_by_condition':rates,'first_attempt_valid':sum(r['first_attempt']['valid'] for r in rows),'raw_NoMemory_left_minus_right':summary(raw_none),'families':{f:{n:summary([agg[(c['id'],n)]['miab'] for c in cohort if c['family']==f and agg[(c['id'],n)] is not None]) for n in CONDITIONS} for f in sorted({c['family'] for c in cases})}}
    return result,scenario

def plot_results(s):
    def errors(stats):
        means=np.array([x['mean'] if x['mean'] is not None else np.nan for x in stats]);low=np.array([x['ci_low'] if x['ci_low'] is not None else np.nan for x in stats]);high=np.array([x['ci_high'] if x['ci_high'] is not None else np.nan for x in stats]);return means,np.maximum(0,np.stack([means-low,high-means]))
    fig,ax=plt.subplots(figsize=(8.5,5.2))
    for n in CONDITIONS:
        means,err=errors([s['by_gamma'][str(g)][n] for g in LEVELS]);ax.errorbar(LEVELS,means,yerr=err,marker='o',capsize=3,label=n,linestyle='--' if n=='AggregateSummary' else '-')
    ax.set(xlabel='Historical policy strength gamma',ylabel='Canonical A - B success probability',title='Confirmatory paired scenario averages');ax.set_xticks(LEVELS);ax.axhline(0,color='black',linewidth=.6);ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(ROOT/'plots/bias_vs_gamma.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.5,5.2));means,err=errors([s['metrics'][n] for n in CONDITIONS]);ax.bar(CONDITIONS,means,yerr=err,capsize=4,color=['#7d8795','#d55e00','#009e73','#0072b2','#9467bd']);ax.set_ylabel('Canonical MIAB; scenario bootstrap 95% CI');ax.set_title('Primary complete scenarios n='+str(s['complete_scenarios']));ax.tick_params(axis='x',rotation=25);ax.axhline(0,color='black',linewidth=.6);fig.tight_layout();fig.savefig(ROOT/'plots/condition_comparison.png',dpi=180);plt.close(fig)
    for axis,keys,names,filename in [('label',['AB','BA'],CONDITIONS,'label_sensitivity.png'),('order',['O1','O2'],ORDERED,'order_sensitivity.png')]:
        fig,ax=plt.subplots(figsize=(8.5,5.2));positions=np.arange(len(names))
        for i,key in enumerate(keys):
            means,err=errors([s['sensitivity'][axis][key][n] for n in names]);ax.bar(positions+(i-.5)*.36,means,.36,yerr=err,capsize=3,label=key)
        ax.set_xticks(positions,names,rotation=20);ax.set(ylabel='Canonical MIAB; scenario bootstrap 95% CI',title='Confirmatory '+axis+' sensitivity');ax.axhline(0,color='black',linewidth=.6);ax.legend();fig.tight_layout();fig.savefig(ROOT/'plots'/filename,dpi=180);plt.close(fig)

def main():
    ensure_env();cases=json.loads((ROOT/'cases/cases.json').read_text());rows=json.loads((ROOT/'results/llm_results.json').read_text());s,scenario=analyze(cases,rows)
    save(ROOT/'results/statistics.json',s);write_csv(ROOT/'results/scenario_level.csv',scenario);write_csv(ROOT/'results/summary.csv',[{'metric':n,**v} for n,v in s['metrics'].items()]);plot_results(s)
    def fmt(v):return '不可估计' if v is None else '%.6f'%v
    lines=['# Idea 2 确认性复现结果','',s['verdict'],'','## 运行与完整性','',f'固定 20 个世界、320 planned runs；有效 {s["valid_runs"]}，retry {s["retried_runs"]}，INVALID {s["invalid_runs"]}；完整主场景 {s["complete_scenarios"]}/20。正式 API 尝试 {s["formal_attempts"]} 次；格式探测单独记录，不计入研究数据。','', '每个场景先配对还原 AB/BA，再平均 O1/O2。Aggregate 是次要条件，不导致主 cohort 排除，但计入总体有效率。每个 γ 的完整数为 '+str(s['complete_by_gamma'])+'。','', '## 主要估计','','| 指标 | N | 均值 | 中位数 | 样本标准差 | 95% 区间 |','|---|---:|---:|---:|---:|---|']
    for n,v in s['metrics'].items():lines.append('| '+n+' | '+str(v['n'])+' | '+' | '.join(fmt(v[k]) for k in ['mean','median','std'])+' | ['+fmt(v['ci_low'])+', '+fmt(v['ci_high'])+'] |')
    lines+=['','Balanced 纠正比例：'+fmt(s['balanced_correction_percent'])+'%；Stratified：'+fmt(s['stratified_correction_percent'])+'%。','', '## 混杂强度曲线','','| γ | N | Confounded mean | 95% 区间 |','|---|---:|---:|---|']
    for g,d in s['by_gamma'].items():v=d['ConfoundedMemory'];lines.append('| '+g+' | '+str(v['n'])+' | '+fmt(v['mean'])+' | ['+fmt(v['ci_low'])+', '+fmt(v['ci_high'])+'] |')
    lines+=['','Spearman ρ='+fmt(s['spearman_rho'])+'，仅四个 γ 均值，不作夸张显著性解释。','', '## 标签与顺序敏感性','','| 视图 | Confounded mean | 95% 区间 |','|---|---:|---|']
    for axis,keys in [('label',['AB','BA']),('order',['O1','O2'])]:
        for key in keys:
            v=s['sensitivity'][axis][key]['ConfoundedMemory'];lines.append('| '+key+' | '+fmt(v['mean'])+' | ['+fmt(v['ci_low'])+', '+fmt(v['ci_high'])+'] |')
    lines+=['','NoMemory 字面 Left−Right 均值='+fmt(s['raw_NoMemory_left_minus_right']['mean'])+'。配对均值可能抵消固定侧偏，因此保留此诊断，不擅自增加硬门槛。','', '## G0—G7','','| 门槛 | 结果 |','|---|---|']
    for gate,passed in s['gates'].items():lines.append('| '+gate+' | '+('PASS' if passed else 'FAIL')+' |')
    lines+=['','## 解析与 retry','','| 条件 | VALID | INVALID |','|---|---:|---:|']
    for n,d in s['status_by_condition'].items():lines.append('| '+n+' | '+str(d.get('VALID',0))+' | '+str(d.get('INVALID',0))+' |')
    lines+=['','首次有效 '+str(s['first_attempt_valid'])+'/320。所有 retry 使用完全相同语义、模型、参数和 schema；不将百分数改成概率、不提取截断 JSON、不补跑最终 INVALID。first_attempt、retry_attempt、final_status 和全部原始响应保存在结果文件。','', '## 边界与 Run 1','', 'Run 1 永久保留 IDEA2_RUN1_NO_GO（原记录 IDEA2_NO_GO，完整性门槛未通过）。本轮独立预注册、独立目录，不改判历史。复用世界保证 outcome 机制没有被增强，但不构成独立现实任务泛化；五家族仅为表面语境。C3 给出计算后的率，C4 删除状态，不能将 C4 的强偏差单独当作可识别因果推理失败。只检验输入经验记忆后的行为，没有实际存储、检索或长期反馈循环。','', '## 停止','', '不查论文、不设计 IPS、propensity weighting 或 causal memory architecture，不进入 Idea 3。达到当前 verdict 后只完成报告、索引和 Git。']
    (ROOT/'Confirmatory结果.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    failed=[g for g,v in s['gates'].items() if not v]
    conclusion='# 最终结论\n\n'+s['verdict']+'\n\n'+('全部 G0—G7 通过。' if not failed else '未通过门槛：'+', '.join(failed)+'。')+'\n\nConfounded mean='+fmt(s['metrics']['ConfoundedMemory']['mean'])+'，95% 区间 ['+fmt(s['metrics']['ConfoundedMemory']['ci_low'])+', '+fmt(s['metrics']['ConfoundedMemory']['ci_high'])+']。Balanced 纠正 '+fmt(s['balanced_correction_percent'])+'%；Stratified 纠正 '+fmt(s['stratified_correction_percent'])+'%。完整主场景 '+str(s['complete_scenarios'])+'/20，有效运行 '+str(s['valid_runs'])+'/320。\n\n判定严格使用运行前 preregistration.md，不因次要 AggregateSummary 放大而放宽。Run 1 仍为 IDEA2_RUN1_NO_GO / IDEA2_NO_GO，未改动历史。当前只表示本模型、固定机制和输入协议下的结果，不是新颖性或现实长期 Agent 泛化结论。\n\n已停止，不自动查重、设计方法或执行 Idea 3。\n'
    (ROOT/'最终结论.md').write_text(conclusion,encoding='utf-8')
    print(json.dumps({k:s[k] for k in ['verdict','gates','valid_runs','retried_runs','invalid_runs','complete_scenarios','spearman_rho','balanced_correction_percent','stratified_correction_percent']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
