import json,collections,statistics,csv,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
from common import ROOT,CONDITIONS,LEVELS,ensure_environment,save_json
from evaluate import describe,write_csv
from run_llm_test import parse,normalized_bias

def main():
    ensure_environment()
    cases=json.loads((ROOT/'cases/cases.json').read_text());rows=json.loads((ROOT/'results/llm_results.json').read_text())
    assert len(rows)==400
    groups=collections.defaultdict(list)
    for r in rows:
        if r['status']=='OK':
            x=parse(r['raw']);groups[(r['case_id'],r['condition'])].append(normalized_bias(x,r['label_swap']))
    values={key:statistics.mean(v) for key,v in groups.items() if len(v)==4}
    conditions={n:describe([values[(c['id'],n)] for c in cases if (c['id'],n) in values]) for n in CONDITIONS}
    comparisons={}
    for name,a,b in [('Delta_confounded','ConfoundedMemory','NoMemory'),('Correction_balanced','ConfoundedMemory','BalancedMemory'),('Correction_stratified','ConfoundedMemory','StratifiedOracle'),('Summary_amplification','AggregateSummary','ConfoundedMemory')]:
        ids=[c['id'] for c in cases if (c['id'],a) in values and (c['id'],b) in values]
        comparisons[name]={'case_ids':ids,**describe([values[(i,a)]-values[(i,b)] for i in ids])}
    by_gamma={str(g):{n:describe([values[(c['id'],n)] for c in cases if c['gamma']==g and (c['id'],n) in values]) for n in CONDITIONS} for g in LEVELS}
    syntax_failures=0;range_failures=0
    for r in rows:
        if r['status']=='OK':continue
        try:
            x=json.loads(r.get('raw',''));range_failures+=int(any(type(x.get(k)) in [int,float] and not 0<=x[k]<=1 for k in ['p_success_A','p_success_B','confidence']))
        except ValueError:syntax_failures+=1
    result={'analysis_type':'POST_HOC_MISSINGNESS_DIAGNOSTIC','note':'仅按每个比较所需条件取四视图完整场景。不同指标 N 不同，不取代预设五条件完整主分析，不修复 UNRESOLVED，不改变 verdict。','conditions':conditions,'comparisons':comparisons,'by_gamma':by_gamma,'invalid_json':syntax_failures,'out_of_range':range_failures}
    save_json(ROOT/'results/available_pairs.json',result)
    write_csv(ROOT/'results/available_pairs.csv',[{'metric':k,**{a:b for a,b in v.items() if a!='case_ids'}} for k,v in {**conditions,**comparisons}.items()])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,5.5))
    for name in CONDITIONS:
        stats=[by_gamma[str(g)][name] for g in LEVELS]
        means=np.array([v['mean'] if v['mean'] is not None else np.nan for v in stats])
        low=np.array([v['ci_low'] if v['ci_low'] is not None else np.nan for v in stats])
        high=np.array([v['ci_high'] if v['ci_high'] is not None else np.nan for v in stats])
        ax.errorbar(LEVELS,means,yerr=np.maximum(0,np.stack([means-low,high-means])),marker='o',capsize=3,label=name,linestyle='--' if name=='AggregateSummary' else '-')
    ax.set(xlabel='Historical policy strength gamma',ylabel='Predicted causal success difference (canonical A - B)',title='Available complete views: post-hoc missingness diagnostic')
    ax.set_xticks(LEVELS);ax.axhline(0,color='black',linewidth=.6);ax.grid(alpha=.2);ax.legend()
    fig.text(.5,.012,'Per level: Confounded n=5,5,4,5; Stratified n=5,0,5,5; others n=5. Missing is not zero.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.03,1,1]);fig.savefig(ROOT/'plots/llm_bias_available_pairs.png',dpi=180);plt.close(fig)
    def fmt(x):return '缺失' if x is None else '%.6f'%x
    text='\n## 完整性门槛与合法配对诊断（事后，不替代主分析）\n\n必须区分“本轮未通过完整性门槛”和“没有发现偏差”。主分析 Confounded MIAB=0.133009，95% 区间 [0.063119, 0.203637]，确实观察到正偏差，两种纠正也为正。程序 NO_GO 的直接原因是预先固定的完整性要求：只有 14/20 场景五条件均完整，γ=0.70 整档被分层条件的格式错误排除。G1/G5 在程序中包含覆盖要求，False 不意味着均值区间包含零或 NoMemory 有强 A 偏好；G2 未通过也不能解释为已证明没有趋势。\n\n400 条响应中 399 条是语法合法 JSON；12 条把概率写成 55/55.0，另 1 条因输出达到上限而截断，均保留 UNRESOLVED。没有换算、截取或推测数值。缺失依赖于条件与 γ，完整案例删除并非随机缺失。\n\n下表只要求相应条件的四视图均合法，避免无关条件缺失使核心比较的合法数据被一并丢弃。它是事后缺失诊断；不改预注册门槛，也不把部分视图当完整场景。\n\n| 指标 | N | 均值 | 95% 区间 |\n|---|---:|---:|---|\n'
    for k,v in {**conditions,**comparisons}.items():text+='| %s | %d | %s | [%s, %s] |\n'%(k,v['n'],fmt(v['mean']),fmt(v['ci_low']),fmt(v['ci_high']))
    text+='\n| γ | Confounded 合法场景 N | Confounded MIAB |\n|---|---:|---:|\n'
    for g,d in by_gamma.items():v=d['ConfoundedMemory'];text+='| %s | %d | %s |\n'%(g,v['n'],fmt(v['mean']))
    text+='\n主分析曲线中 γ=0.70 的缺口是缺失，不是零；其他条件在该档有合法数据，见 available_pairs.json。合法配对诊断显示的正偏差不能被 NO_GO 标签抹去，但它也不补齐预设的完整四档主检验。判定保留 IDEA2_NO_GO，准确解释为本轮未满足推进所需的预设完整证据条件，而非现象被证伪。停止运行，不为获得 GO 重跑或调整提示。\n'
    text+='\n复现时先运行 evaluate.py，再运行 analysis/diagnose_missingness.py。主曲线与补充合法配对曲线分别保存，不把事后诊断混入原定主分析。\n'
    for name in ['Idea2实验结果.md','最终结论.md']:
        f=ROOT/name;f.write_text(f.read_text().split('\n## 完整性门槛与合法配对诊断')[0]+text,encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
