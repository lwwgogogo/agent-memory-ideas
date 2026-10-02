import json,time,os
from pathlib import Path
from mem0 import Memory
root=Path(__file__).parent; out=root/'outputs'; out.mkdir(exist_ok=True)
cfg={'vector_store':{'provider':'qdrant','config':{'path':str(root/'runtime/mem0/qdrant_smoke4'),'on_disk':True,'embedding_model_dims':768}},'llm':{'provider':'ollama','config':{'model':'qwen2.5:14b','temperature':0,'top_p':0.1,'ollama_base_url':'http://127.0.0.1:11434'}},'embedder':{'provider':'ollama','config':{'model':'nomic-embed-text:latest','embedding_dims':768,'ollama_base_url':'http://127.0.0.1:11434'}},'history_db_path':str(root/'runtime/mem0/history_smoke4.db')}
events=[]
def record(stage,value):
    events.append({'stage':stage,'value':value,'time':time.time()})
try:
    m=Memory.from_config(cfg); record('initialized',True)
    record('add',m.add('用户平时喜欢无糖咖啡。用户最近因为胃不舒服暂时改喝茶。用户说胃已经好了。',user_id='smoke-user'))
    all_items=m.get_all(filters={'user_id':'smoke-user'}); record('get_all',all_items)
    record('search',m.search('用户现在更适合喝什么？',filters={'user_id':'smoke-user'}))
    items=all_items.get('results',[]) if isinstance(all_items,dict) else []
    if items:
        mid=items[0].get('id'); record('update',m.update(mid,'用户胃部不适已经恢复；无糖咖啡是长期偏好，暂时喝茶的原因已经结束。')); record('post_update',m.get_all(filters={'user_id':'smoke-user'}))
    (out/'mem0_smoke.json').write_text(json.dumps({'config':cfg,'events':events},ensure_ascii=False,indent=2,default=str)); print(json.dumps({'status':'PASS','events':len(events)},ensure_ascii=False),flush=True); os._exit(0)
except Exception as e:
    (out/'mem0_smoke.json').write_text(json.dumps({'config':cfg,'events':events,'error':repr(e)},ensure_ascii=False,indent=2,default=str)); print(json.dumps({'status':'FAIL','error':repr(e)},ensure_ascii=False)); raise
