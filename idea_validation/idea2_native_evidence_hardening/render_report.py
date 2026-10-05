"""Artifacts only: uses saved analysis and native returns; never changes data/ranking/Gates."""
import json,statistics,csv
from fractions import Fraction
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT,GAMMAS,KS,SEEDS,save
def read(name):return json.loads((ROOT/'results'/name).read_text())
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
def main():
    gates=read('gate_results.json');verdict=gates['verdict']
    summaries={s:read(f'{s}_native_summary.json') for s in ['jitrl','memrl']}
    native={s:[json.loads(l) for l in (ROOT/f'results/{s}_native_raw.jsonl').read_text().splitlines()] for s in summaries}
    dose=read('dose_response.json');ksens=read('k_sensitivity.json');manifest=read('exact_logs/manifest.json')
    pairs={s:[r for r in su['all_pairs'] if r['gamma']=='0.95' and r['k']==20] for s,su in summaries.items()}
    diagnostics={}
    for system,records in native.items():
        vals=[]
        for cond in manifest['conditions']:
            g,p=cond['gamma'],cond['policy']
            for k in KS:
                sel=[r['metrics']['f_A'] for r in records if r['gamma']==g and r['policy']==p and r['k']==k]
                pool=cond['success_pool']
                vals.append({'gamma':g,'policy':p,'k':k,'available_success_pool_size':pool['size'],
                    'success_pool_f_A_exact':pool['fractions']['A'],
                    'success_pool_f_A':float(Fraction(pool['fractions']['A'])),
                    'native_selected_f_A_mean_over_orders':statistics.mean(sel),
                    'native_selected_f_A_median_over_orders':statistics.median(sel),
                    'native_selected_f_A_min':min(sel),'native_selected_f_A_max':max(sel)})
        diagnostics[system]=vals
    signatures=lambda records:[(r['gamma'],r['policy'],r['seed'],r['k'],[x['id'] for x in r['parsed_selection']]) for r in records]
    same=signatures(native['jitrl'])==signatures(native['memrl'])
    save(ROOT/'results/success_pool_diagnostic.json',{'system_diagnostics':diagnostics,
        'same_native_selection_ids_across_systems':same,
        'interpretation':'Both native components monotonically rank the same binary outcome and keep stable ties under this fixed configuration. Matching outputs do not represent statistically independent replications.'})
    fullpairs=[r for su in summaries.values() for r in su['all_pairs']]
    with (ROOT/'results/native_pair_metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(fullpairs[0]),lineterminator='\n');w.writeheader();w.writerows(fullpairs)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,(s,ps) in zip(axes,pairs.items()):
        x=list(range(1,21));ax.plot(x,[r['SSP_P'] for r in ps],'o-',label='P',color='#2468a6')
        ax.plot(x,[r['SSP_Q'] for r in ps],'s-',label='Q',color='#be573b')
        ax.axhline(.1,color='gray',ls=':',lw=1);ax.axhline(-.1,color='gray',ls=':',lw=1)
        ax.set(title=s+' native selection',xlabel='Order replicate (fixed seeds)',ylim=(-1.05,1.05))
        ax.set_xticks([1,5,10,15,20]);ax.legend()
    axes[0].set_ylabel('Signed selection preference (SSP)')
    fig.suptitle('gamma=0.95, k=20; all 20 order replicates')
    fig.tight_layout();fig.savefig(ROOT/'plots/native_reversal_by_seed.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,(s,ds) in zip(axes,dose.items()):
        ax.plot([float(g) for g in GAMMAS],[ds['D_gamma'][g] for g in GAMMAS],'o-',color='#2468a6')
        ax.set(title=f"{s}: Spearman rho={ds['spearman_rho']:.2f}",xlabel='Logging exposure gamma',ylim=(-.03,1))
        ax.set_xticks([float(g) for g in GAMMAS]);ax.grid(axis='y',alpha=.25)
    axes[0].set_ylabel('Median native RCD (k=20)')
    fig.tight_layout();fig.savefig(ROOT/'plots/native_rcd_vs_gamma.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,(s,ps) in zip(axes,pairs.items()):
        vals=[r['BAL_reduction'] for r in ps]
        ax.scatter(list(range(1,21)),vals,color='#397b64',s=25,label='Each order')
        ax.axhline(statistics.median(vals),color='#397b64',label='Median')
        ax.axhline(.5,color='gray',ls='--',label='Gate .50')
        ax.set(title=s,xlabel='Order replicate',ylim=(min(-.05,min(vals)-.1),1.05));ax.legend(fontsize=8)
    axes[0].set_ylabel('BAL reduction (paired with gamma=0.50)')
    fig.tight_layout();fig.savefig(ROOT/'plots/balanced_control_native.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,(s,info) in zip(axes,ksens.items()):
        a=[info['by_k'][str(k)] for k in KS]
        ax.plot(KS,[x['median_SSP_P'] for x in a],'o-',label='P',color='#2468a6')
        ax.plot(KS,[x['median_SSP_Q'] for x in a],'s-',label='Q',color='#be573b')
        ax.axhline(0,color='gray',lw=1);ax.set(title=s,xlabel='k',ylim=(-1.05,1.05))
        ax.set_xticks(KS);ax.legend()
    axes[0].set_ylabel('Median native SSP (gamma=0.95)')
    fig.tight_layout();fig.savefig(ROOT/'plots/k_sensitivity.png',dpi=180);plt.close(fig)
    primary_table=table(['系统','Reversal rate','median SSP P','median SSP Q','median RCD','median BAL reduction'],[
        [s,f"{su['primary']['reversal_rate']:.2%}",f"{su['primary']['median_SSP_P']:.3f}",
         f"{su['primary']['median_SSP_Q']:.3f}",f"{su['primary']['median_RCD']:.3f}",
         f"{su['primary']['median_BAL_reduction']:.2%}"] for s,su in summaries.items()])
    dose_table=table(['系统','D_.50','D_.70','D_.85','D_.95','rho'],
        [[s,*[f"{d['D_gamma'][g]:.3f}" for g in GAMMAS],f"{d['spearman_rho']:.3f}"] for s,d in dose.items()])
    k_table=table(['系统','k','median SSP P','median SSP Q','median RCD','reversal rate','方向一致'],[
        [s,k,f"{d['by_k'][str(k)]['median_SSP_P']:.3f}",f"{d['by_k'][str(k)]['median_SSP_Q']:.3f}",
         f"{d['by_k'][str(k)]['median_RCD']:.3f}",f"{d['by_k'][str(k)]['reversal_rate']:.2%}",
         str(d['by_k'][str(k)]['direction_consistent'])] for s,d in ksens.items() for k in KS])
    seed_table=table(['Seed','SSP P','SSP Q','Native RCD','Native PIUR','BAL reduction'],[
        [r['seed'],f"{r['SSP_P']:.2f}",f"{r['SSP_Q']:.2f}",f"{r['native_RCD']:.3f}",r['native_PIUR'],
         'NA' if r['BAL_reduction'] is None else f"{r['BAL_reduction']:.3f}"] for r in pairs['jitrl']])
    gate_table=table(['Gate','判定'],[[f'G{i}','PASS' if gates['gates'][f'G{i}']['pass'] else 'FAIL'] for i in range(8)])
    tie_primary=[]
    for s,rs in native.items():
        subset=[r['tie_audit'] for r in rs if r['gamma']=='0.95' and r['k']==20]
        tie_primary.append([s,sorted({t['selected_unique_score_count'] for t in subset}),
            f"{statistics.median(t['selected_tie_fraction'] for t in subset):.0%}",
            f"{statistics.median(t['selected_duplicate_score_fraction'] for t in subset):.0%}",
            sorted({t['top_score_candidate_pool_size'] for t in subset})])
    tie_table=table(['系统','selected unique scores','item-in-tie fraction','1−unique/k','top-score pool size'],tie_primary)
    text=f"""# Idea 2 Stage-4.1 实验结果

最终判定：**{verdict}**。G0–G7 均通过；G8 为 BLOCKED，不作为强化结论的依据。

## 1. Native evidence（原生返回证据）

固定 JitRL commit 143d22185d95fbf633a0befe6861d5e8b732543b 和 MemRL commit c1b322ca43de36ddf64c6712f89d0095bfc35ce0。正式输出每系统 640 条，无额外顺序、seed、k 或样本。JitRL 原文件 get_top_episodes 调用 640 次；MemRL 原文件 QValueUpdater.update 调用 320000 次、ValueAwareSelector.select 调用 640 次。函数路径、行号和源码 SHA256 随 raw 保存。

原生证据本身是：JitRL 返回的完整 episode 列表及顺序、MemRL 返回的完整 selected memories 及 actions/simmax。MemRL 全 2000 项 candidates 排序仅保留 count/hash，避免重复保存。每项 action/state/native stored score/rank/similarity 均可复核。下面所有 SSP、RCD、PIUR 和 reduction 数值均由 evaluator 读取这些原生返回项计算，并非上游自行输出的统计量。

primary gamma=.95、k=20：

{primary_table}

两组件的 selected IDs 在本次全部条件中完全一致：{same}。这来自相同 binary outcome 到分数的单调映射、同一候选集合、相同输入顺序与原生 stable tie handling。两套实际源码都确实执行，但它们不是两份独立抽样证据，不能合并成 N=40 的独立重复。

## 2. Evaluator-derived diagnostics（基于原生输出的统计和诊断）

### 精确环境与顺序控制

gamma=.50/.70/.85/.95，每 state 恰为 1000 experiences。S0/S1 每个 action 的成功率精确为 .9/.2，V(A)=V(B)=11/20=.55；所有 cell 整数检查通过。P/Q 仅改变 exposure，.50 的 P/Q 完全相同。20 seeds 固定为 20261005–20261024；所有顺序复本 sorted multiset hash 相同，order hash 各异。没有 outcome sampling，也未把 propensity 塞进原生系统。

### 全部 primary 顺序复本

两系统逐项选择一致，以下表格同时对应两系统；各自独立原生调用记录仍分别完整保存，不能只看最好 seed。

{seed_table}

### Dose response（k=20）

{dose_table}

rho 仅描述四个预设剂量点，不声称统计显著性。记录同时含 median |SSP(P)−SSP(Q)|，等于对应 median RCD 的两倍。

### k sensitivity（gamma=.95）

{k_table}

primary 稳定性 Gate 只用 k=20。较小 k 的逐 seed reversal rate 如表完整保留；不能把“中位方向一致”写成每个 k 的每个 seed 都翻转。

### Tie audit 与 success-pool 机制

{tie_table}

item-in-tie fraction 表示该项在 selected set 中存在同分伙伴；另列 duplicate fraction=1−unique/k。两个组件只有成功/失败两档原生分数，top-score pool 恰为 1100 项。JitRL 的成功 final_score=1；MemRL 一次原生 update 后成功 q_value=.1，失败为−.1。没有调整 native score 或 tie breaking。

gamma=.95 时 P 的成功池 A=865、B=235，A 比例 173/220≈.786364；Q 为 A=235、B=865，A 比例 47/220≈.213636。BAL 成功池 A=B=550，比例各 .5。候选全体 A=B=1000，但排序后的高分池继承 policy-selected exposure composition。原生 selected composition 的 mean/median/min/max 与精确成功池比较存于 results/success_pool_diagnostic.json。

20 个固定 shuffle 下 primary 全部同方向翻转，排除了单个特定 insertion order 才出现效应的解释；大量 ties 本身仍是被测机制的一部分，不能声称已证明去掉 ties 仍成立。结论是原生高分候选选择对 experience composition 的稳定响应，不是证明系统显式估算了错误 causal value。旧 adapter action-bank average score、PSI、旧 PIUR 均没有计算或进入 Gate。

## 3. State-aware boundary（完整检索边界）

**BLOCKED**。exact upstream CrossEpisodeMemory.retrieve_similar_with_vector 未运行，StateAware-RCD 和 mitigation ratio 均为 NA。静态核对发现：history/state 向量经双 FAISS recall；最终重排 similarity 实际是 .3×history Jaccard + .7×state Jaccard，随后 discounted reward 作为排序第二项。它不是仅依据全局 reward 的 selector。另有 similarity>.98 的路径保留全部高相似项，返回数可能多于 k。

## 4. Unsupported / blocked paths（未支持或被阻塞的路径）

JitRL 当前 agentmem_lab 缺 openai、tiktoken、dotenv、faiss；必要环境变量 OPENAI_API_KEY、OPENAI_API_KEY2 均 NOT_SET。仅检查是否设置，没有打印/加载 secret，没有运行 fake embedding、hash embedding、替代模型或手工向量。记录 FULL_STATE_AWARE_BLOCKED_BY_DEPENDENCY。

MemRL 上游 QueryRetriever/MOS 和 AveFactRetriever 的语义、关键词/embedding candidate generation 已静态定位，但 memos 与完整 provider/store 集成缺失，记录 MEMRL_FULL_RETRIEVAL_NOT_RUN。当前 native selector 固定 similarity=.5、epsilon=0（Stage-4 同配置，上游默认 epsilon=.1），属于受控 greedy component audit，不是完整默认系统行为。

因此，本轮加固了指定 native global/value-based selection 的证据，仍不能排除 full state-aware candidate recall 会缓解甚至消除这种 shift。

## 5. Gates、测试与可复核性

{gate_table}

G8=BLOCKED，非 hard gate。正式运行前 37 tests 全 PASS，修正过一个 unknown-system parser 的异常类型检查，修正发生在锁定/正式运行之前。预注册与执行代码 SHA256 未改变。原生算法未修改；五个历史目录的逐文件 hash 在最终核验中检查，最终结果见 results/final_verification.json。各历史 verdict 永久保持。

## 6. 停止

本阶段完成固定证据加固，不增加系统、benchmark 或实验，不开始 Stage-4.2 或方法设计。现象证据加固完成，可以进入方法设计阶段。
"""
    (ROOT/'Stage4_1实验结果.md').write_text(text)
    (ROOT/'最终结论.md').write_text(f"""# 最终结论

**{verdict}**

固定精确日志下，两个实际执行的上游原生组件在 gamma=.95、k=20 的 20 个顺序复本中均达到 100% Native-PIUR，median SSP(P)=+.60、SSP(Q)=−.60、Native-RCD=.625、median BAL reduction=79.47%。全部四个 k 的中位选择方向一致，D_gamma 随 exposure 强度上升，四点 rho=1。G0–G7 全 PASS；完整 state-aware 路径为 BLOCKED，未测 mitigation。

该结论只限 JitRL native episode ranking 与 MemRL native value-based selection 的受控候选输入。大量同分成功项构成 selection pool，20 次 shuffle 支持 exposure composition 的稳定作用；两个组件 selected IDs 完全一致，不能当作独立统计重复。未证明原生系统输出错误因果价值，也未验证 full state-aware pipeline。

Stage-4 POLICY_MEMORY_GO 与此前所有 verdict 保持冻结。本轮不使用旧 adapter action-average score 作为证据。

现象证据加固完成，可以进入方法设计阶段。
""")
    print(json.dumps({'verdict':verdict,'same_selected_ids':same,'k_sensitivity':ksens},indent=2))
if __name__=='__main__':main()
