"""Generate the requested execution note from immutable A2 CSV/JSON."""
import argparse
import csv
import json
from pathlib import Path


def main(root,destination):
    meta=json.loads((root/'run.json').read_text(encoding='utf-8'))
    decision=json.loads((root/'decision.json').read_text(encoding='utf-8'))
    with (root/'summary.csv').open(encoding='utf-8') as f:summary=list(csv.DictReader(f))
    with (root/'contrasts.csv').open(encoding='utf-8') as f:contrasts=list(csv.DictReader(f))
    values={(r['scenario'],r['method'],r['metric']):r for r in summary}
    differences={(r['scenario'],r['method'],r['metric']):r for r in contrasts}
    def fmt(r,scale=100):
        if not r['mean']:return 'missing（无eligible事件）'
        return f"{float(r['mean'])*scale:.4f} [{float(r['ci_low'])*scale:.4f}, {float(r['ci_high'])*scale:.4f}]"
    lines=['# Phase A.2 非平稳验证执行记录','',
           '## 1 做了什么','',
           'D1/D2完成并满足预定stationary停止门槛后，运行冻结的Q increase/decrease、R increase/decrease、100步temporary corruption，以及四个匹配端点的stationary controls。只比较既有方法，无新updater、NIS、LLM/API或GPU。',
           '', '## 2 为什么做','',
           '检查Q/R本身变化时stationary统计是否导致迟滞，以及简单遗忘/窗口估计能否解决大部分问题。目标是判断研究空间，不是证明Idea1正确。',
           '', '## 3 协议与补充定义','',
           '严格沿用phase_a1_a2_plan.md的场景数值、步数、变化范围和种子。原计划未给定的window/rho候选、control数值、retention proxy和control退化阈值已在phase_a2_implementation_frozen_20260929.md中于validation/test前冻结。Q两个方向只计一类，R同理。',
           '新增生成器使用4个独立随机流分别控制初始状态、转移、噪声和变化时刻；同一seed跨方法完全相同，跨场景使用公共随机数。没有改变生成分布以获取正结果；旧generate/API及旧输出保留。',
           '窗口估计通过两栈HMM矩阵乘积精确计算最近W条观测后验，经过逐窗口从头过滤对照测试。Forgetting只折扣模型posterior权重，明确是heuristic。Oracle每步知道Q/R，不读latent truth。',
           '', '## 4 配置与种子','',
           'configs/phase_a2.json：T3000，burn-in100，start在[900,1500]均匀整数；验证200–219，测试300–339；9场景等权validation accuracy选择一次全局方法与各family超参数，不向方法透露test场景类型。5000次paired seed bootstrap。',
           f"实际选参：{json.dumps(decision['selected'],ensure_ascii=False)}。4个CPU workers，每worker BLAS线程为1。",
           '', '## 5 源码hash与环境','',
           f"配置SHA256：{meta['config_sha256']}。",
           f"runner SHA256：{meta['source_sha256']['scripts/run_phase_a2.py']}。",
           f"generator SHA256：{meta['source_sha256']['src/agent_memory/nonstationary.py']}。",
           f"window SHA256：{meta['source_sha256']['src/agent_memory/window.py']}。",
           f"Python {meta['python']}，NumPy {meta['numpy']}；完整环境见environment-lock.txt。运行开始已存source_snapshot.zip、全部source_sha256、config.json及前置D1/D2 run.json哈希。",
           '', '## 6 时间与检查','',
           f"核心运行{meta['elapsed_seconds']:.2f}秒（不含绘图），180条validation轨迹、360条test轨迹。18项unittest本地与服务器通过。audit.json验证源码归档、原始结果hash、方法/场景/seed覆盖、变化时间和污染长度。旧结果未覆盖。",
           '', '## 7 逐场景核心数值','',
           '以下区间均为95% seed bootstrap；accuracy和error使用百分数，gap使用百分点。best指validation选出的Forgetting-BMA rho=.995，非test选优。']
    for spec in meta['config']['scenarios']:
        s=spec['name'];lines+=['',f'### {s}','']
        for m in ['selected_global','online_bma','dense_bma','selected_forgetting','selected_window','oracle_qr']:
            lines.append(f"- {m} accuracy：{fmt(values[s,m,'accuracy'])}%。")
        lines.append(f"- Oracle-best accuracy gap：{fmt(differences[s,'selected_deployable','accuracy'])} pp。")
        for metric in ['brier','false_update_rate','noise_overreaction','adaptation_delay_capped','adaptation_censored_rate','stale_reuse_proxy']:
            lines.append(f"- best {metric}：{fmt(values[s,'selected_deployable',metric],1)}（原指标单位）。")
        if spec['kind']!='control':
            for metric in ['error_50','error_100','error_300']:
                lines.append(f"- {metric}：best {fmt(values[s,'selected_deployable',metric])}%；Oracle {fmt(values[s,'oracle_qr',metric])}%。")
            lines.append(f"- recovery完成10连对延迟：{fmt(values[s,'selected_deployable','recovery_delay'],1)}步；censoring：{fmt(values[s,'selected_deployable','recovery_censored'])}%。")
        if spec['kind']=='corruption':
            for metric in ['corruption_error','post_corruption_error_100','post_corruption_error_remaining','useful_memory_retention_proxy']:
                lines.append(f"- best {metric}：{fmt(values[s,'selected_deployable',metric])}%。")
            lines.append(f"- 污染结束后10连对恢复延迟：{fmt(values[s,'selected_deployable','post_corruption_recovery'],1)}步；censoring：{fmt(values[s,'selected_deployable','post_corruption_censored'])}%。")
    lines+=['','## 8 Failure patterns 与强baseline对比','',
            'Stationary BMA确实迟滞：R increase下Dense stationary全程86.433%，forgetting90.075%；变化后前100步error分别24.50%和22.30%，Oracle11.10%。固定参数posterior累计大量旧证据后适应较慢，但普通forgetting显著缓解全程损失。',
            'Window存在速度/噪声trade-off，证据来自validation：R increase前50步error W50为15.2%、W500为17.6%；control_noisy accuracy W50为83.459%、W500为85.722%。不能把test的不同场景重新选不同W。全局validation选W500，其初期适应不总快于forgetting。',
            'Forgetting存在trade-off：validation control_noisy rho=.95/.995/.999 accuracy为83.231%/85.883%/86.040%，而R increase为89.059%/90.452%/88.300%。rho=.995是全局折中，不是新机制。',
            'Temporary corruption仍有明显局部误差：best污染100步error39.55%，Oracle21.85%，差17.70pp [11.05,23.9006]。但恢复后前100步error仅1.50% vs1.15%；恢复延迟约10.525 vs10.325步（定义下最小10步），没有发现持续被带偏的强证据。全程gap仅0.6483pp，不能事后改以局部指标替代冻结的2pp门槛。',
            '', '## 9 CI与GO门槛审计','',
            '五个变化场景的Oracle-best全程gap为0.7552、0.5491、1.0776、0.5259、0.6483pp；95%上界均<2pp。符合>=2pp的场景为0，更不满足至少两类。Oracle在post-change fixed windows仍更好，但这不满足联合门槛。',
            'best相对Dense stationary在四controls下降0.0853/0.2948/0.0112/0.4534pp，最大paired95%上界0.6906pp，均未达到运行前>1pp的明显退化规则。该规则怎么收紧都无法改变全程gap门槛已失败的事实。',
            '', '## 10 Limitations','',
            '限定于本次binary HMM、单次参数变化/100步污染、有限网格和有限候选。不是所有Agent Memory问题无价值的证明。Oracle拥有真实参数/时刻信息，剩余gap包含信息差，不可直接称可实现创新空间。',
            'Useful-memory retention是有条件state正确率proxy，方法相关分母与缺失seed见原始CSV，非真实memory对象保留。Recovery是10连对首次完成，不能证明参数后验已恢复；短期偶然连续正确也可满足。',
            '区间为seed配对，未校正多重比较；没有改test seed、改环境难度或追加有利场景。冻结门槛看full-trajectory accuracy，因此报告中如实保留污染阶段的大局部差距，而不拿它反转门槛。',
            '', '## 11 Idea 1 Verdict','',
            f"**{decision['verdict']} — 简单方法已经足够。**",
            '现有简单 online/window/forgetting 方法已经足够解释或解决大部分现象，目前没有足够证据支持新的 Noise-or-Change memory updater。',
            '此结论按本次预先设定的工程研究门槛作出。停止Idea1复杂算法路线，不设计NIS/Kalman/neural updater、uncertainty gate、新loss，不进入JitRL。',
            '', '## 12 下一步与复现','',
            '建议把主要研究精力切换到独立的Idea3 Revision Inertia；下一步应先做信息等价的fresh/revision/reset现象验证，不在本轮实施。Idea1保留代码、负结果、图表和审计记录。',
            '输出位于outputs/phase_a2_20260929。原始指标per_seed.csv、验证全候选validation_per_seed.csv、曲线curves.csv、汇总与CI summary.csv/contrasts.csv/curve_summary.csv，选参selection.json，判定decision.json。6张PNG与underlying CSV共同保存；绘图源码单独归档。',
            '```bash',
            '.venv/bin/python scripts/run_phase_a2.py --config configs/phase_a2.json --output outputs/a2_new --diagnostics-d1 outputs/phase_a1_dense_20260929 --diagnostics-d2 outputs/phase_a1_length_diag_20260929',
            '.venv/bin/python scripts/plot_phase_a2.py outputs/a2_new',
            '.venv/bin/python scripts/audit_research_outputs.py outputs/a2_new',
            '```','']
    with destination.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('destination');a=p.parse_args()
    main(Path(a.directory),Path(a.destination))
