import csv
from collections import Counter
from pathlib import Path
B=Path(__file__).resolve().parent
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main():
 rows=read(B/'formation_matrix_ABC.csv')+read(B/'formation_matrix_D.csv')
 with (B/'formation_matrix.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 lines=['# FormationSanity结果','','本轮只测试 formation，不测试 downstream answer；原 96-case experiment 未重跑。','','## 结果矩阵','','| Condition | Writer | Input | infer | Created | No memory | Error |','|---|---|---|---:|---:|---:|---:|']
 for cond in ['A_current_qwen','B_official_qwen','C_raw_storage','D_official_qwq']:
  rr=[r for r in rows if r['condition']==cond];created=sum(r['status']=='MEMORY_CREATED' for r in rr);no=sum(r['status']=='NO_MEMORY' for r in rr);err=sum(r['status']=='ERROR' for r in rr);x=rr[0];lines.append(f"| {cond} | {x['writer']} | {'official' if x['official_messages']=='True' else 'raw string'} | {x['infer']} | {created}/12 | {no}/12 | {err}/12 |")
 lines += ['','## Decision','', '- C infer=False = 12/12：storage/Qdrant/user_id/get_all 路径通过。','- A current qwen：0/12 created，11 NO_MEMORY，1 ERROR。','- B official qwen：0/12 created，11 NO_MEMORY，1 ERROR。','- D official qwq：0/12 created，12 NO_MEMORY。','- A 与 B 同样失败：没有证据支持 raw-string 与 official message protocol 的差异是主要原因。','- qwen 与 qwq 都无法让简单 positive controls 形成 memory：当前结果不是单纯 qwen writer confound。','- 当前最保守 verdict：`MEM0_LOCAL_INFERENCE_COMPATIBILITY_OR_PROMPT_FAILURE`。','- `FORMATION_SELECTIVITY_SIGNAL`：当前不成立。','', '## P04 特殊错误','', 'qwen A/B 的 P04 报告了 `AttributeError: str has no attribute get`。Mem0 2.2.1 additive path 在 extraction 后按 memory item dict 调用 `m.get("text")`，但该次 writer 返回了字符串元素。','', '## Raw extraction capture','', '首次 matrix wrapper 绑定了旧的 `generate` 名称，而 2.2.1 实际调用的是 `generate_response`；因此没有保存完整 raw response。源码调用链和 P04 traceback 已保存，未修改 site-packages。','', '## 下一步','', '不要重跑原 96，也不要进入 candidate。唯一值得做的是在新的独立诊断中正确包裹 `mem.llm.generate_response`，保存 qwen/qwq 的原始 JSON，并确认是 `memory=[]`、`memory=[string]` 还是 `memory=[{"text":...}]`。']
 (B/'FormationSanity结果.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 (B/'最终结论.md').write_text('# Formation Sanity 最终结论\n\n- C storage positive control：12/12。\n- A current qwen：0/12。\n- B official qwen：0/12。\n- D official qwq：0/12。\n\n结论：storage 路径正常；当前不是简单 input protocol 差异，也不能归因于 qwen 单一 writer confound。两种 writer 对简单 facts 的 infer=True 均未形成 memory，暂判 `MEM0_LOCAL_INFERENCE_COMPATIBILITY_OR_PROMPT_FAILURE`。Formation selectivity signal 不成立，正式 Candidate=0。\n',encoding='utf-8')
if __name__=='__main__':main()
