import json
from pathlib import Path
BASE=Path(__file__).resolve().parent; TRACE=BASE/'outputs/case_traces'; CASES=BASE.parent/'cases/cases.json'
def main():
    cases={x['case_id']:x for x in json.loads(CASES.read_text(encoding='utf-8'))}; lines=['# Trace审计','', '本报告只读审计当前已有 trace；完整 96 case 未结束前不形成科研结论。','']
    files=sorted(TRACE.glob('*.json')); lines += [f'- 审计数量：{len(files)}','- 当前状态：`PARTIAL_DO_NOT_INTERPRET`（只有 96/96 才可解释）','']
    counts={'PASS':0,'WARNING':0,'FAIL':0}
    for p in files:
        d=json.loads(p.read_text(encoding='utf-8')); findings=[]
        turns=d.get('turns',[]); ids={x.get('id') for x in d.get('final_memories',[]) if isinstance(x,dict)}
        findings.append(('PASS' if turns and [x.get('turn_index') for x in turns]==list(range(len(turns))) else 'FAIL','sequential turn index'))
        findings.append(('PASS' if all(x.get('memory_after_turn') is not None for x in turns) else 'FAIL','每轮 get_all snapshot'))
        selected=set(d.get('o2_item_ids',[])); findings.append(('PASS' if selected<=ids else 'FAIL','O2 IDs subset of final memory IDs'))
        sr=d.get('normal_search_result',[]); srids={x.get('id') for x in sr if isinstance(x,dict)}; findings.append(('PASS' if srids<=ids else 'WARNING','normal search result IDs'))
        for status,msg in findings: counts[status]+=1
        lines += [f'## {d.get("case_id")}', '']+[f'- `{s}`：{m}' for s,m in findings]
        if len(d.get('final_memories',[]))==0: lines.append('- `WARNING`：final_memories 为空，需结合 Mem0 add/get_all 返回检查。'); counts['WARNING']+=1
        if d.get('required_information_present')=='YES' and not d.get('final_memories'): lines.append('- `FAIL`：availability=YES 但 final memory 为空。'); counts['FAIL']+=1
        lines.append('')
    lines += ['## 汇总','',f'- PASS：{counts["PASS"]}',f'- WARNING：{counts["WARNING"]}',f'- FAIL：{counts["FAIL"]}','', '说明：O3a/O3b 字段级泄漏与 grader 稳定性由离线 unit tests 和完整结果分析脚本检查；本审计不调用 LLM。']
    (BASE/'Trace审计.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__': main()
