import json
from pathlib import Path
BASE=Path(__file__).resolve().parent; cases=json.loads((BASE.parent/'cases/cases.json').read_text(encoding='utf-8'))
def main():
 chosen=[]
 for fam in sorted({x['family'] for x in cases}): chosen += [x for x in cases if x['family']==fam][:3]
 lines=['# Case质量审计','', '不修改原 case；这是固定每 family 前 3 个 case 的离线审计。','']
 for c in chosen:
  facts=' '.join(c.get('required_memory_facts',[])); labels=[]
  labels.append('VALID' if c.get('correct_answer') and c.get('current_query') and c.get('raw_history') else 'GOLD_TOO_WEAK')
  if not c.get('required_memory_facts'): labels.append('GOLD_TOO_WEAK')
  if c.get('correct_answer') in facts: labels.append('GOLD_TOO_STRONG')
  lines += [f'## {c["case_id"]}',f'- 标记：`{" / ".join(dict.fromkeys(labels))}`',f'- 问题：{c["current_query"]}',f'- required_memory_facts：{facts}', '- O3a/O3b：模板字段级泄漏需在完整运行后复核。','']
 (BASE/'Case质量审计.md').write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__':main()
