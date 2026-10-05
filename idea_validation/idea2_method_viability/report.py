"""Report and plots only, from frozen method outputs."""
import json,csv,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from config import ROOT,save
METHODS=['M0','A1','M1','M2','M3','M4']
def read(name):return json.loads((ROOT/'results'/name).read_text())
def table(headers,rows):
 return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
def fmt(x,n=6):return 'NA' if x is None else f'{x:.{n}f}'
def main():
 g=read('gate_results.json');pol=read('policy_invariance.json');b=read('true_effect_retention.json');c=read('crossover.json');d=read('support_stress.json')
 ab=read('ablations.json')['pair_metrics'];rows=list(csv.DictReader((ROOT/'results/method_results.csv').open()))
 # Verified identical mathematical outcomes across the two adapters; no pooling as independent data.
 keys=['family','mechanism','gamma','policy','target','method','U_A_exact','U_B_exact']
 j=sorted(tuple(r[k] for k in keys) for r in rows if r['system']=='jitrl')
 m=sorted(tuple(r[k] for k in keys) for r in rows if r['system']=='memrl')
 assert j==m
 pol=[r for r in pol if r['system']=='jitrl'];b=[r for r in b if r['system']=='jitrl'];c=[r for r in c if r['system']=='jitrl'];d=[r for r in d if r['system']=='jitrl']
 a95={r['method']:r for r in pol if r['gamma']=='0.95'}
 b95={method:{r['policy']:r for r in b if r['method']==method and r['gamma']=='0.95'} for method in METHODS}
 bmain={method:[r for r in b if r['method']==method and r['gamma']!='0.50'] for method in METHODS}
 cmain={method:[r for r in c if r['method']==method and r['gamma']!='0.50'] for method in METHODS}
 a_table=table(['方法','PIG','NPE P','NPE Q','CorrectionRate','strict false reversal'],[
   [method,fmt(a95[method]['PIG']),fmt(a95[method]['NPE_P']),fmt(a95[method]['NPE_Q']),fmt(a95[method]['CorrectionRate']),a95[method]['false_reversal']] for method in METHODS])
 b_table=table(['方法','.95 gap P','.95 gap Q','.95 TSR P','.95 TSR Q','A>B accuracy (.70/.85/.95)'],[
   [method,fmt(b95[method]['P']['estimated_gap']),fmt(b95[method]['Q']['estimated_gap']),fmt(b95[method]['P']['TSR']),fmt(b95[method]['Q']['TSR']),f"{sum(r['ranking_correct'] for r in bmain[method])}/6"] for method in METHODS])
 cross_table=table(['方法','.95 P: T0/T1','.95 Q: T0/T1','所有非BAL bank均正确'],[
  [method,'/'.join(next(r for r in cmain[method] if r['gamma']=='0.95' and r['policy']=='P')[x] for x in ['T0_rank','T1_rank']),
   '/'.join(next(r for r in cmain[method] if r['gamma']=='0.95' and r['policy']=='Q')[x] for x in ['T0_rank','T1_rank']),
   f"{sum(r['both_correct'] for r in cmain[method])}/6"] for method in METHODS])
 stress_table=table(['方法','gamma','最大 null NPE','B gap min/max','C非均匀ranking正确','全部范围有限且[0,1]'],[
   [method,gamma,fmt(max(abs(r['estimated_gap']) for r in d if r['method']==method and r['gamma']==gamma and r['mechanism']=='A')),
    '/'.join(fmt(v) for v in [min(r['estimated_gap'] for r in d if r['method']==method and r['gamma']==gamma and r['mechanism']=='B'),
                              max(r['estimated_gap'] for r in d if r['method']==method and r['gamma']==gamma and r['mechanism']=='B')]),
    f"{sum(r['mechanism_criteria_pass'] for r in d if r['method']==method and r['gamma']==gamma and r['mechanism']=='C' and r['target']!='T')}/4",
    all(r['bounded'] for r in d if r['method']==method and r['gamma']==gamma)]
   for gamma in ['0.95','0.99'] for method in METHODS])
 candidate_table=table(['方法',*[f'G{i}' for i in range(1,10)]],[
  [method,*['PASS' if rules[f'G{i}'] else 'FAIL' for i in range(1,10)]] for method,rules in g['candidate_gates'].items()])
 gate_table=table(['Gate','全局判定'],[[k,'PASS' if val else 'FAIL'] for k,val in g['gates'].items()])
 selected=g['selected_candidate'];verdict=g['verdict']
 summary={'verdict':verdict,'selected_candidate':selected,'systems_identical':True,
   'family_A_gamma95':a95,'family_B_gamma95':b95,
   'family_B_main_accuracy':{m:sum(r['ranking_correct'] for r in bmain[m])/6 for m in METHODS},
   'family_C_main_bank_accuracy':{m:sum(r['both_correct'] for r in cmain[m])/6 for m in METHODS},
   'family_C_main_query_accuracy':{m:statistics.mean(r['ranking_accuracy'] for r in cmain[m]) for m in METHODS},
   'candidate_gates':g['candidate_gates'],'gates':g['gates']}
 save(ROOT/'results/report_summary.json',summary)
 secondary=read('secondary_summary.json')
 constraints=all(r['all_minimum_support_constraints_pass'] and r['20_order_compositions_identical'] for r in secondary)
 header=f"""# Stage-5 方法可行性结果

最终判定：**{verdict}**。选择候选：**{selected}**。本轮是 discrete-state exact-count viability，不是方法新颖性或大规模 benchmark 结果。

## 1. 协议与原生 baseline

所有六个历史目录冻结；正式运行前57项测试通过，并锁定预注册及实现 SHA256。固定 upstream commit、原生函数和 Stage-4.1 配置不变。G0 两系统均复现 null/.95 的20/20原生 reversal、median Native-RCD=.625，全部 selected IDs 与 Stage-4.1一致。

A/B/C 各8个bank；D复用A/B/C机制各4个bank，合计36个bank。每bank2000条整数exact记录，无outcome sampling；不同target复用同bank，只改变rho。两系统共产生720条 method/target结果，1440条额外native selection记录，4800条secondary selection记录。结果无 formal retry/调参/改公式。

Practical 输入不含 gamma、family 或真实 propensity；统一为原生对象可读的 state/action/outcome。JitRL reward/final_score是binary；MemRL读取原生update已有last_reward，按固定+1/−1编码转成binary。两系统 normalized数学输入和估计结果逐项相同，不作为独立统计样本。此 adapter 假定已有已标注 discrete state/action，不代表自动解析自然语言 memory。

## 2. Primary endpoint与尺度边界

M1/M2/M3/M4/A1 返回outcome-based utility。M0原生只返回selected items，本轮U0明确是20个order replicate的f_A/f_B中位数，属于selection-support proxy，不是成功概率。因此相对M0的CorrectionRate只作描述性归一化，必须共同满足absolute NPE、真实gap、TSR及crossover。A1为同一success尺度的no-state消融。下表中M0的gap/TSR只能按支持度解释。

## 3. Family A：null（gamma=.95）

{a_table}

false reversal按严格符号定义，没有事后容差。M2/M4即使CorrectionRate很高仍可能残留小幅反转，不能宣称完全消除。M1使用精确state均值与rho，所有gamma均PIG=NPE=0；M3 oracle同样为0但不候选。

## 4. Family B：真实global advantage

真实gap=.10，非BAL primary共P/Q×3档=6个条件。

{b_table}

TSR只在estimated gap>0时输出，错误或平局不填0冒充有效retention。M1保留全部真实gap，而非把所有actions压平。平凡equalization会在G3/G4失败。

## 5. Family C：context crossover

同一bank的T0=(.8,.2)、T1=(.2,.8)，真实gap分别+.18、−.18。

{cross_table}

M2按题述固定global SNIPS公式实现，没有rho权重；因此它不具备query自适应能力。这一negative result完整保留，没有为过Gate改公式。M1/M4的preference可随target改变；M3使用target-aware oracle SNIPS，只作classical reference。

## 6. Support sensitivity

.95最小cell n=50，.99最小n=10；Jeffreys prior与clip均固定，未调参。

{stress_table}

M1在这些exact cell means下可保持精确；这不代表n=10时有限样本方差很小。本轮未Bernoulli抽样，也没有声称confidence或sampling-robustness结论。零support时M1显式失败，positivity是必要限制。M2在.99因clip可能保留较大偏差；M4的不同cell shrinkage会产生与exposure有关的偏差。.99结果为sensitivity，不据其好坏回改Gate。

## 7. 必要消融和secondary selector

A0=M0，A1=aggregate action mean，A2=M1，A3=M4，A4=M2，A5=M3。A1在null/.95仍有PIG={a95['A1']['PIG']:.6f}和NPE={a95['A1']['NPE_P']:.6f}；M1为0，支持state conditioning是此已识别离散环境中的关键。A1也不随rho变化，无法完成crossover。

M1/M4 wrapper按rho给state quota，每state/action保留至少2条，余下按fixed temperature=1的corrected utility softmax分配；cell内按输入顺序选，不按success挑选。全部240个system/bank/target/method组合、每组20个seed满足quota/minimum-support且composition不随order改变：{constraints}。小k下softallocation舍入可能让A/B各10条，即使utility估计保留真实差异；secondary composition不进入任何primary Gate，也未评估后续LLM读取效果。

## 8. Gates与方法选择

{gate_table}

逐方法必须同时过所有必要Gate，不能把多个方法不同优点拼接：

{candidate_table}

固定选择顺序得到{selected}。M3是ORACLE / NOT CANDIDATE METHOD。M1统计核心就是direct standardization/g-computation形式，本轮不声明新颖性。后续必须单独做方法新颖性/差异化审计，不能将经典公式重新包装为新方法。

## 9. 可复核性与停止

results下保存逐method精确分数、PIG/retention/crossover/support/ablation/Gate和完整原生selected记录；source/preregistration/历史hash见manifest与final_verification。所有历史verdict保持独立、不回写。未使用新LLM、新reward model、训练或大benchmark。完成指定Git提交后停止。
"""
 (ROOT/'Stage5实验结果.md').write_text(header)
 comparison=f"""# Method候选比较

本轮选择 **{selected}**；判定 **{verdict}**。比较基于全部固定world/Gate，不按单个最好结果。

| 方法 | 输入与统计核心 | 实际可行性边界 | 是否候选 |
|---|---|---|---|
| M1 | observed state/action/outcome + rho；direct standardization | exact离散已识别state下去exposure bias、保留真实gap、完成crossover；需positivity | 是，本轮优先 |
| M2 | bank counts估计propensity，alpha=1，clip=.05，全局SNIPS | 能纠正常规均匀target的多数bias；忽略rho使crossover失败，.99 clipping留bias | 是，但当前固定版本未过全部Gate |
| M3 | 真propensity + target rho/P_logged(x) | oracle classical diagnostic，不能作为创新方法 | **ORACLE / NOT CANDIDATE METHOD** |
| M4 | Jeffreys(.5,.5) shrinkage + rho | 常规support下保留signal/crossover，但收缩偏差依赖cell exposure | 是，次于M1的exact结果 |

{candidate_table}

M1与经典standardization/g-computation一致，不声明novelty；后续仍需方法新颖性/差异化审计。两adapter输入一致仅在本轮已标注synthetic native objects成立，不推及自动state抽取、复杂轨迹、多步Q或完整semantic retrieval。Exact counts不能比较采样方差或证明shrinkage在现实任务的优劣。
"""
 (ROOT/'Method候选比较.md').write_text(comparison)
 (ROOT/'最终结论.md').write_text(f"""# 最终结论

**{verdict}**

选择 **{selected}**。在本轮固定exact discrete-state worlds中，它在两个原生metadata adapter上获得相同输入：null PIG/NPE=0；真实global gap=.10全部保留，TSR=1；context crossover随rho从A翻到B；不读取true propensity或gamma。G0–G9通过，满足本轮轻量correction的数学/接口可行性。

M2忽略query target的失败及.99 clipping偏差、M4的support-dependent shrinkage偏差均保留。M3为ORACLE / NOT CANDIDATE METHOD。M0选择支持度不冒充成功概率，相对CorrectionRate不作为唯一依据。

M1的统计核心是direct standardization/g-computation，不声明novelty。结论依赖已观测state充分、positivity和exact cell rates；未证实自然语言memory解析、连续context、有限样本低support或full-agent效果。

修正机制可行，下一步应做方法新颖性/差异化审计。
""")
 # Publication-style deterministic plots; no invented uncertainty bars.
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 colors={'M0':'#777777','A1':'#b75a48','M1':'#2265a3','M2':'#b98a29','M3':'#7558a0','M4':'#2d8061'}
 gammas=['0.50','0.70','0.85','0.95']
 fig,axs=plt.subplots(1,2,figsize=(10,4))
 for ax,ms in zip(axs,[METHODS,['M1','M2','M4']]):
  for method in ms:
   yy=[next(r['PIG'] for r in pol if r['method']==method and r['gamma']==x) for x in gammas]
   ax.plot([float(x) for x in gammas],yy,'o-',label=method,color=colors[method])
  ax.set(xlabel='Logging gamma',ylabel='Policy invariance gap');ax.set_xticks([float(x) for x in gammas]);ax.legend(fontsize=8);ax.grid(alpha=.2)
 axs[0].set_title('Family A; M0 is selection support');axs[1].set_title('Practical estimators (detail)')
 fig.tight_layout();fig.savefig(ROOT/'plots/policy_invariance_gap.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4))
 for i,method in enumerate(['M1','M2','M3','M4']):
  yy=[r['TSR'] for r in bmain[method] if r['TSR'] is not None]
  ax.scatter([i+(j-(len(yy)-1)/2)*.025 for j in range(len(yy))],yy,label=method,color=colors[method])
 ax.axhline(1,color='gray',ls='--');ax.axhline(.7,color='gray',ls=':');ax.axhline(1.3,color='gray',ls=':')
 ax.set_xticks(range(4),['M1','M2','M3 oracle','M4']);ax.set(ylabel='TSR (positive estimated gaps only)',title='Family B: six deterministic non-BAL conditions',ylim=(.65,1.35))
 fig.tight_layout();fig.savefig(ROOT/'plots/true_signal_retention.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4))
 for method in ['M1','M2','M4']:
  yy=[next(r['CorrectionRate'] for r in pol if r['method']==method and r['gamma']==x) for x in gammas[1:]]
  ax.plot([float(x) for x in gammas[1:]],yy,'o-',label=method,color=colors[method])
 ax.axhline(.8,color='gray',ls='--');ax.set(xlabel='Logging gamma',ylabel='CorrectionRate vs M0 support proxy',title='Family A: relative correction (descriptive)',ylim=(.75,1.02));ax.legend()
 fig.tight_layout();fig.savefig(ROOT/'plots/correction_vs_gamma.png',dpi=180);plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(11,4),sharey=True)
 for ax,target,gt in zip(axs,['T0','T1'],[.18,-.18]):
  x=np.arange(len(METHODS))
  for off,p in [(-.18,'P'),(.18,'Q')]:
   yy=[next(r[f'{target}_gap'] for r in c if r['method']==m and r['gamma']=='0.95' and r['policy']==p) for m in METHODS]
   ax.bar(x+off,yy,width=.34,label=p)
  ax.axhline(gt,color='green',ls='--',label='true gap');ax.axhline(0,color='gray',lw=.8)
  ax.set_xticks(x,METHODS);ax.set_title(target+'; gamma=.95');ax.legend(fontsize=8)
 axs[0].set_ylabel('Estimated gap (M0: selection support)')
 fig.tight_layout();fig.savefig(ROOT/'plots/crossover.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4))
 offsets={'M1':(7,14),'M2':(-100,-20),'M3':(7,-22),'M4':(8,10)}
 for method in ['M1','M2','M3','M4']:
  x=a95[method]['CorrectionRate'];y=statistics.mean(r['TGE'] for r in bmain[method])
  ax.scatter(x,y,label=method,color=colors[method],marker='x' if method=='M3' else 'o',s=80)
  ax.annotate(method+(' oracle' if method=='M3' else ''),(x,y),xytext=offsets[method],textcoords='offset points')
 ax.set(xlabel='Null CorrectionRate at gamma=.95',ylabel='Mean true-gap error (Family B non-BAL)',title='Fixed method tradeoff; no hyperparameter search')
 ax.margins(x=.25,y=.4);ax.grid(alpha=.2)
 fig.tight_layout();fig.savefig(ROOT/'plots/method_tradeoff.png',dpi=180);plt.close(fig)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
