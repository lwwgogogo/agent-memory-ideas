import json,os,time
from pathlib import Path
from mem0 import Memory
from ollama import Client
root=Path(__file__).parent; out=root/'outputs'; out.mkdir(exist_ok=True); cases=json.loads((root/'cases/cases.json').read_text())
cfg={'vector_store':{'provider':'qdrant','config':{'path':str(root/'runtime/mem0/qdrant_pilot'),'on_disk':True,'embedding_model_dims':768,'collection_name':'pilot'}},'llm':{'provider':'ollama','config':{'model':'qwen2.5:14b','temperature':0,'top_p':0.1,'ollama_base_url':'http://127.0.0.1:11434'}},'embedder':{'provider':'ollama','config':{'model':'nomic-embed-text:latest','embedding_dims':768,'ollama_base_url':'http://127.0.0.1:11434'}},'history_db_path':str(root/'runtime/mem0/history_pilot.db')}
client=Client(host='http://127.0.0.1:11434'); memory=Memory.from_config(cfg); results=[]
def ask(context,query):
    prompt=f'只根据上下文回答用户问题。请给出简短答案，不要解释。\n上下文：{context}\n问题：{query}'
    return client.chat(model='qwen2.5:14b',messages=[{'role':'user','content':prompt}],options={'temperature':0})['message']['content']
for idx,c in enumerate(cases):
    uid='pilot-'+c['case_id']; add=memory.add(c['raw_history'],user_id=uid); got=memory.search(c['current_query'],filters={'user_id':uid});
    retrieved=got.get('results',[]) if isinstance(got,dict) else []; ctx='\n'.join(str(x.get('memory','')) for x in retrieved)
    o0=ask(ctx,c['current_query']); o1=ask(c['raw_history'],c['current_query']); o2=ask('\n'.join(c['required_memory_facts']),c['current_query']); o3=o2
    results.append({'case_id':c['case_id'],'family':c['family'],'correct':c['correct_answer'],'written_memory':add,'retrieved_memory':got,'o0_answer':o0,'o1_raw_answer':o1,'o2_retrieval_oracle':o2,'o3_gold_memory':o3,'o0_correct':c['correct_answer'] in o0,'o1_correct':c['correct_answer'] in o1,'o2_correct':c['correct_answer'] in o2,'o3_correct':c['correct_answer'] in o3})
    if idx%8==0: print(idx, c['case_id'], flush=True)
(out/'mem0_pilot_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2,default=str)); print(json.dumps({'cases':len(results),'o0':sum(x['o0_correct'] for x in results),'o1':sum(x['o1_correct'] for x in results),'o2':sum(x['o2_correct'] for x in results)},ensure_ascii=False))
