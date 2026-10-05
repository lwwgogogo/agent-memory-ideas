import json,csv,collections,statistics,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT,CONDITIONS,LEVELS,ensure_environment,save_json
from run_llm_test import parse,normalized_bias

def describe(values):
    x=np.asarray(values,dtype=float)
    if len(x)==0:return {'n':0,'mean':None,'median':None,'std':None,'ci_low':None,'ci_high':None}
    rng=np.random.default_rng(20261004);boot=x[rng.integers(0,len(x),size=(10000,len(x)))].mean(axis=1)
    return {'n':len(x),'mean':float(x.mean()),'median':float(np.median(x)),'std':float(x.std(ddof=1)) if len(x)>1 else None,'ci_low':float(np.quantile(boot,.025)),'ci_high':float(np.quantile(boot,.975))}

def write_csv(path,rows):
    if not rows:return
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def positive_ci(s):return s['ci_low'] is not None and s['ci_low']>0

def main():
    ensure_environment()
    cases=json.loads((ROOT/'cases/cases.json').read_text());rows=json.loads((ROOT/'results/llm_results.json').read_text())
    if len(rows)!=400 or len({(r['case_id'],r['condition'],r['label_swap'],r['order_seed']) for r in rows})!=400:raise RuntimeError('Fixed run not complete')
    groups=collections.defaultdict(list)
    for r in rows:
        if r['status']=='OK':
            parsed=parse(r['raw']);assert parsed==r['parsed'];assert abs(normalized_bias(parsed,r['label_swap'])-r['miab'])<1e-12
            groups[(r['case_id'],r['condition'])].append(r)
    valid=[c for c in cases if all(len(groups[(c['id'],n)])==4 for n in CONDITIONS)]
    ids={c['id'] for c in valid};paired=[]
    for c in valid:
        row={'case_id':c['id'],'family':c['family'],'gamma':c['gamma']}
        for n in CONDITIONS:row[n]=statistics.mean(r['miab'] for r in groups[(c['id'],n)])
        row['Delta_confounded']=row['ConfoundedMemory']-row['NoMemory']
        row['Correction_balanced']=row['ConfoundedMemory']-row['BalancedMemory']
        row['Correction_stratified']=row['ConfoundedMemory']-row['StratifiedOracle']
        row['Summary_amplification']=row['AggregateSummary']-row['ConfoundedMemory']
        paired.append(row)
    metrics=CONDITIONS+['Delta_confounded','Correction_balanced','Correction_stratified','Summary_amplification']
    summaries={n:describe([r[n] for r in paired]) for n in metrics}
    levels={str(g):{n:describe([r[n] for r in paired if r['gamma']==g]) for n in metrics} for g in LEVELS}
    families={f:{n:describe([r[n] for r in paired if r['family']==f]) for n in metrics} for f in sorted({c['family'] for c in cases})}
    slopes=[]
    for f in families:
        rr=sorted([r for r in paired if r['family']==f],key=lambda r:r['gamma'])
        if [r['gamma'] for r in rr]==LEVELS:slopes.append({'family':f,'slope':float(np.polyfit(LEVELS,[r['ConfoundedMemory'] for r in rr],1)[0])})
    trend=describe([r['slope'] for r in slopes])
    slices={}
    for key,values in [('label_swap',[0,1]),('order_seed',[17,43])]:
        slices[key]={}
        for value in values:
            records=[]
            for c in valid:
                d={n:statistics.mean(r['miab'] for r in groups[(c['id'],n)] if r[key]==value) for n in CONDITIONS}
                d['Delta_confounded']=d['ConfoundedMemory']-d['NoMemory'];records.append(d)
            slices[key][str(value)]={n:describe([r[n] for r in records]) for n in CONDITIONS+['Delta_confounded']}
    order_diffs={};label_diffs={}
    for n in CONDITIONS:
        order_values=[];label_values=[]
        for c in valid:
            rr=groups[(c['id'],n)]
            order_values.append(abs(statistics.mean(r['miab'] for r in rr if r['order_seed']==17)-statistics.mean(r['miab'] for r in rr if r['order_seed']==43)))
            label_values.append(abs(statistics.mean(r['miab'] for r in rr if r['label_swap']==0)-statistics.mean(r['miab'] for r in rr if r['label_swap']==1)))
        order_diffs[n]=describe(order_values);label_diffs[n]=describe(label_values)
    no_memory_raw=[r['parsed']['p_success_A']-r['parsed']['p_success_B'] for r in rows if r['status']=='OK' and r['condition']=='NoMemory' and r['case_id'] in ids]
    raw_letter_bias=describe(no_memory_raw);raw_letter_abs=float(np.mean(np.abs(no_memory_raw))) if no_memory_raw else None
    coverage=len(valid)>=16 and all(levels[str(g)]['ConfoundedMemory']['n']>=4 for g in LEVELS)
    slice_positive=all(part['Delta_confounded']['mean'] is not None and part['Delta_confounded']['mean']>0 and part['ConfoundedMemory']['mean']>0 for axis in slices.values() for part in axis.values())
    stable=coverage and positive_ci(summaries['Delta_confounded']) and positive_ci(summaries['ConfoundedMemory']) and slice_positive
    group_means=[levels[str(g)]['ConfoundedMemory']['mean'] for g in LEVELS]
    trend_ok=all(v is not None for v in group_means) and all(b>=a-.02 for a,b in zip(group_means,group_means[1:])) and group_means[-1]>group_means[0] and len(slopes)>=3 and positive_ci(trend)
    abs_bal=float(np.mean([abs(r['BalancedMemory']) for r in paired])) if paired else None
    abs_strat=float(np.mean([abs(r['StratifiedOracle']) for r in paired])) if paired else None
    replicated=[f for f,v in families.items() if v['ConfoundedMemory']['mean'] is not None and v['ConfoundedMemory']['mean']>.03 and v['Correction_balanced']['mean']>0 and v['Correction_stratified']['mean']>0]
    gates={'G1_stable_extra_bias':bool(stable),'G2_gamma_trend':bool(trend_ok),'G3_balanced_correction':bool(positive_ci(summaries['Correction_balanced']) and abs_bal is not None and abs_bal<=.05),'G4_stratified_correction':bool(positive_ci(summaries['Correction_stratified']) and abs_strat is not None and abs_strat<=.05),'G5_no_memory_control':bool(raw_letter_abs is not None and raw_letter_abs<=.05 and stable),'G6_multiple_families':len(replicated)>=3}
    verdict='IDEA2_GO' if all(gates.values()) else ('IDEA2_WEAK' if stable else 'IDEA2_NO_GO')
    reason='全部预设门槛通过，支持本模板中的策略混杂经验偏差。' if verdict=='IDEA2_GO' else ('有稳定额外偏差，但趋势、纠正或对照门槛未全部通过。' if verdict=='IDEA2_WEAK' else ('未发现满足预设标准的稳定额外动作偏差。' if coverage else '完整配对覆盖不足，不足以确认现象；不能解释为证明现象不存在。'))
    parser={n:dict(collections.Counter(r['status'] for r in rows if r['condition']==n)) for n in CONDITIONS}
    inconsistency={n:sum(r['status']=='OK' and not r['choice_probability_consistent'] for r in rows if r['condition']==n) for n in CONDITIONS}
    report={'verdict':verdict,'reason':reason,'total_calls':len(rows),'valid_runs':sum(r['status']=='OK' for r in rows),'complete_cases':len(valid),'coverage_ok':coverage,'metrics':summaries,'by_gamma':levels,'by_family':families,'family_slopes':slopes,'trend_slope':trend,'gates':gates,'replicated_families':replicated,'slices':slices,'order_absolute_change':order_diffs,'label_absolute_change':label_diffs,'no_memory_raw_letter_bias':raw_letter_bias,'no_memory_raw_mean_absolute_bias':raw_letter_abs,'balanced_mean_absolute_bias':abs_bal,'stratified_mean_absolute_bias':abs_strat,'parser':parser,'choice_probability_inconsistency':inconsistency,'excluded_cases':[c['id'] for c in cases if c['id'] not in ids]}
    save_json(ROOT/'results/statistics.json',report)
    write_csv(ROOT/'results/summary.csv',[{'metric':n,**s} for n,s in summaries.items()])
    write_csv(ROOT/'results/paired_differences.csv',paired)
    write_csv(ROOT/'results/by_gamma.csv',[{'gamma':g,'metric':n,**s} for g,d in levels.items() for n,s in d.items()])
    write_csv(ROOT/'results/by_family.csv',[{'family':f,'metric':n,**s} for f,d in families.items() for n,s in d.items()])
    if valid:
        fig,ax=plt.subplots(figsize=(9,5.5))
        for name in CONDITIONS:
            means=np.array([levels[str(g)][name]['mean'] if levels[str(g)][name]['mean'] is not None else np.nan for g in LEVELS])
            lo=np.array([levels[str(g)][name]['ci_low'] if levels[str(g)][name]['ci_low'] is not None else np.nan for g in LEVELS]);hi=np.array([levels[str(g)][name]['ci_high'] if levels[str(g)][name]['ci_high'] is not None else np.nan for g in LEVELS])
            ax.errorbar(LEVELS,means,yerr=np.maximum(0,np.stack([means-lo,hi-means])),marker='o',linestyle='--' if name=='AggregateSummary' else '-',capsize=3,label=name)
        ax.axhline(0,color='black',linewidth=.8);ax.set(xlabel='Historical policy strength gamma',ylabel='Predicted causal success difference (canonical A - B)',title='Case means; case-bootstrap 95% CI; 5 worlds per level planned');ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(ROOT/'plots/llm_bias_vs_confounding.png',dpi=180);plt.close(fig)
    def fmt(x):return '不可估计' if x is None else '%.6f'%x
    lines=['# Idea 2 实验结果','',verdict+'：'+reason,'','## 执行与统计口径','',f'20 个基础场景、五条件、两种动作标签映射×两个顺序种子；计划与实际调用均为 400。合法响应 {report["valid_runs"]}/400，完整配对场景 {len(valid)}/20。只使用 agentmem_lab Python 3.10；qwq:32b /api/chat；模型与提示从首个调用开始固定，无追加模型或选择性重试。','', '四个视图先按场景聚合；配对差和 bootstrap 的单位是场景，非调用。趋势以完整 family 的四点斜率为单位。γ=0.5 为无混杂对照。所有区间仅描述这组同构模板表面变化。','', '## MIAB 与配对纠正','','| 指标 | N | 均值 | 中位数 | 样本标准差 | 95% 区间 |','|---|---:|---:|---:|---:|---|']
    for n,s in summaries.items():lines.append('| '+n+' | '+str(s['n'])+' | '+' | '.join(fmt(s[k]) for k in ['mean','median','std'])+' | ['+fmt(s['ci_low'])+', '+fmt(s['ci_high'])+'] |')
    lines+=['','## 混杂强度趋势','','| γ | NoMemory | ConfoundedMemory | BalancedMemory | StratifiedOracle | AggregateSummary |','|---|---:|---:|---:|---:|---:|']
    for g,d in levels.items():lines.append('| '+g+' | '+' | '.join(fmt(d[n]['mean']) for n in CONDITIONS)+' |')
    lines+=['','family 斜率均值 '+fmt(trend['mean'])+'，95% 区间 ['+fmt(trend['ci_low'])+', '+fmt(trend['ci_high'])+']。','', '## 门槛','','| 门槛 | 通过 |','|---|---|']
    for gate,passed in gates.items():lines.append('| '+gate+' | '+str(passed)+' |')
    lines+=['','## 替代解释与诊断','','| 条件 | 合法 | 未解析 | 选择/概率不一致（仅诊断） | 平均顺序绝对变化 | 平均标签绝对变化 |','|---|---:|---:|---:|---:|---:|']
    for n in CONDITIONS:lines.append('| '+n+' | '+str(parser[n].get('OK',0))+' | '+str(parser[n].get('UNRESOLVED',0))+' | '+str(inconsistency[n])+' | '+fmt(order_diffs[n]['mean'])+' | '+fmt(label_diffs[n]['mean'])+' |')
    lines+=['','- parser：完整 JSON 校验，无 substring grading；choice/TIE 或选择与概率不一致不会丢弃合法概率。没有填补 UNRESOLVED。','- order：顺序与标签映射交叉，分层结果保存在 statistics.json，不能据两个种子排除全部位置效应。','- label bias：NoMemory 未还原字母差均值 '+fmt(raw_letter_bias['mean'])+'，平均绝对差 '+fmt(raw_letter_abs)+'；标签对换后的零均值不能单独证明无字母偏好。','- scenario-family dependence：达到 family 复现门槛的家族为 '+('、'.join(replicated) if replicated else '无')+'。五家族共享一个因果结构，不能宣称机制泛化。','- information：C1 与 C3 使用同一计数，C3 额外把百分比显式算出；改进可能来自计算与展示便利。C4 丢失状态信息，聚合偏差不能单独归因为模型因果推理失败。','- data：精确整数频率排除了有限样本噪声，但不能代表自然经验分布。C0 无数据时的绝对成功率不可识别，只检查动作不对称。','- memory：未使用真实存储、检索或模型自主形成记忆；这里只检验提供经验记录后的行为，不声称已复现完整长期反馈循环。','', '## 数学结果','','观测差公式为 1.4γ−0.7；γ=.50/.60/.70/.80/.90/.95 对应 0/.14/.28/.42/.56/.63。干预成功率均为 .55、因果差恒为 0。31 项 pytest 门控结果见 results/pytest_output.txt。','', '## 停止边界','','不查论文、不做 IPS 或 propensity weighting、不设计 causal memory architecture，不扩大场景，不进入 Idea 3。当前结论只作用于本模型、本固定模板与本生成机制。']
    (ROOT/'Idea2实验结果.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    final='# 最终结论\n\n'+verdict+'\n\n'+reason+'\n\nConfounded MIAB='+fmt(summaries['ConfoundedMemory']['mean'])+'；Δ_confounded='+fmt(summaries['Delta_confounded']['mean'])+'，95% 区间 ['+fmt(summaries['Delta_confounded']['ci_low'])+', '+fmt(summaries['Delta_confounded']['ci_high'])+']。Balanced correction='+fmt(summaries['Correction_balanced']['mean'])+'；Stratified correction='+fmt(summaries['Correction_stratified']['mean'])+'。\n\n'+f'合法响应 {report["valid_runs"]}/400，完整场景 {len(valid)}/20。'+'门槛详见 Idea2实验结果.md。数学反例成立不等于行为假设成立；聚合摘要的信息缺失不能单独作为因果推理失败证据。五种语境共用机制，结果不构成通用性或新颖性判断。\n\n执行到 verdict 后停止，不救结果、不进入 Idea 3。\n'
    (ROOT/'最终结论.md').write_text(final,encoding='utf-8')
    print(json.dumps({'verdict':verdict,'valid_runs':report['valid_runs'],'complete_cases':len(valid),'metrics':{n:s['mean'] for n,s in summaries.items()},'gates':gates,'trend':group_means},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
