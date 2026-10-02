import json
from pathlib import Path
from ollama import Client
root=Path(__file__).parent; cases={x['case_id']:x for x in json.loads((root/'cases/cases.json').read_text(encoding='utf-8'))}; results=json.loads((root/'outputs/mem0_pilot_results.json').read_text(encoding='utf-8')); client=Client(host='http://127.0.0.1:11434')
def ask(context,q):
    return client.chat(model='qwen2.5:14b',messages=[{'role':'user','content':f'只根据给定 memory facts 回答问题，简短回答，不要补充未给出的事实。\nMemory facts:\n{context}\n问题：{q}'}],options={'temperature':0})['message']['content']
for x in results:
 c=cases[x['case_id']]; structured='\n'.join([f"role={c['condition']}",f"required_fact={c['correct_answer']}",f"expected_update={c['expected_update']}","scope=当前问题；旧信息不能覆盖当前事实"]); x['o3_gold_memory_rescore']=ask(structured,c['current_query']); x['o3_rescore_correct']=c['correct_answer'] in x['o3_gold_memory_rescore']
(root/'outputs/mem0_pilot_results_rescored.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'o3_rescore':sum(x['o3_rescore_correct'] for x in results),'total':len(results)},ensure_ascii=False))
