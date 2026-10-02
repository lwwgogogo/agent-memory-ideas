import argparse, csv, json, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / 'outputs'
TRACE = OUT / 'case_traces'
OUT.mkdir(parents=True, exist_ok=True); TRACE.mkdir(parents=True, exist_ok=True)

OPTIONS = {
 'C1':(['LOCAL','CLOUD'],'LOCAL'), 'C2':(['LOCAL','CLOUD'],'CLOUD'),
 'C3':(['PYTHON','RUBY'],'PYTHON'), 'C4':(['A','B'],'B'),
 'C5':(['OBSERVATION','INFERENCE'],'OBSERVATION'), 'C6':(['X','Y'],'Y'),
 'C7':(['S','T'],'T'), 'C8':(['A','B'],'B')}

def norm(s): return str(s).strip().upper().replace('"','').replace("'",'')
def canonical(c):
    fam=c['family']; opts, ans=OPTIONS[fam]
    return {'options':opts, 'gold':ans}
def prompt(c, context):
    o=canonical(c)
    return ('你是严格的二选一任务回答器。只输出一个合法 JSON，不要输出解释。\n'
            f"问题：{c['current_query']}\n选项：{', '.join(o['options'])}\n"
            f"上下文：\n{context}\n输出格式：{{\"choice\": \"{o['options'][0]}\"}}")
def parse_choice(raw, opts):
    try:
        x=json.loads(raw); v=norm(x.get('choice',''))
        if v in opts: return v, 'json'
    except Exception: pass
    # Reasoning models may wrap the final protocol in <think>...</think>.
    # Extract JSON only; do not score explanatory prose or answer substrings.
    for m in reversed(list(re.finditer(r'\{[^{}]*"choice"\s*:\s*"?([A-Za-z]+)"?[^{}]*\}', raw, re.S))):
        v=norm(m.group(1))
        if v in opts: return v, 'json_embedded'
    # deterministic fallback only for an exact option token, never free-text answer matching
    hits=[x for x in opts if re.search(r'(?<![A-Z])'+re.escape(x)+r'(?![A-Z])', norm(raw))]
    return (hits[0], 'fallback') if len(hits)==1 else (None, 'unresolved')
def turns(c):
    h=c['raw_history'].split(' 表达版本')[0]
    f=c['family']
    if f=='C4': return ['用户以前使用模型 A。','上周已经迁移到模型 B。','当前配置是模型 B。']
    if f=='C8': return ['前面说推荐 A 是错误的。','更正：真正应推荐 B。','A 不满足最新限制。']
    parts=[x.strip() for x in re.split(r'[；;。]',h) if x.strip()]
    return [x+'。' for x in parts] or [h+'。']
def gold(c, structured=False):
    f=c['family']
    d={
      'C1':['用户重视隐私。','用户平时偏好本地模型。','今天的网络限制是临时情境。'],
      'C2':['当前服务器只能运行 Python。','用户不是因为偏爱 Python 才使用它。','环境允许时用户更愿意使用云 API。'],
      'C3':['通常项目使用 Python。','当前项目因旧依赖使用 Ruby。','该例外只适用于当前项目。'],
      'C4':['过去使用模型 A。','上周已迁移到模型 B。','当前配置是模型 B。'],
      'C5':['工具返回了超时。','服务可能存在过载这一解释。'],
      'C6':['候选 X 价格低且颜色相似。','候选 Y 满足用户要求的续航和重量限制。'],
      'C7':['策略 S 只在网络稳定时有效。','当前网络不稳定。','当前情境使用另一策略。'],
      'C8':['先前的推荐被明确标记为错误。','后续信息对先前推荐进行了更正。','候选 A 不满足最新限制。']}
    if not structured: return '\n'.join('- '+x for x in d[f])
    roles={'C1':['reason=privacy','preference=durable','scope=temporary'], 'C2':['constraint=current','negation=not_preference','preference=conditional'], 'C3':['default=general','exception=current_project','scope=project_only'], 'C4':['time=past','update=recent','state=current'], 'C5':['observation=tool_timeout','inference=possible_overload'], 'C6':['attribute=candidate_X','constraint_satisfaction=candidate_Y'], 'C7':['condition=stable_network','condition=current_unstable','application=current'], 'C8':['status=superseded','update=correction','constraint=latest']}
    return '\n'.join(f'- {r}: {x}' for r,x in zip(roles[f],d[f]))

def ask(client, model, c, context):
    r=client.chat(model=model, messages=[{'role':'user','content':prompt(c,context)}], options={'temperature':0})
    raw=r['message']['content'] if isinstance(r,dict) else r.message.content
    choice,method=parse_choice(raw, canonical(c)['options'])
    return {'raw':raw,'choice':choice,'method':method,'correct':choice==canonical(c)['gold']}

def run_o1(cases, model):
    import ollama; client=ollama.Client(host=os.environ.get('OLLAMA_HOST','http://127.0.0.1:11434'))
    out=[]
    for i,c in enumerate(cases):
        out.append({'case_id':c['case_id'],'family':c['family'],'result':ask(client,model,c,c['raw_history'])})
        if (i+1)%12==0: print('O1',model,i+1,flush=True)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['o1','full'],default='full'); ap.add_argument('--model',default='qwen2.5:14b'); ap.add_argument('--memory-model',default='qwen2.5:14b'); args=ap.parse_args()
    cases=json.loads((ROOT/'cases/cases.json').read_text(encoding='utf-8'))
    if len(cases)!=96: raise RuntimeError('case count changed')
    if args.mode=='o1':
        r=run_o1(cases,args.model); (OUT/f'o1_{args.model.replace(":","_")}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8'); return
    import ollama
    from mem0 import Memory
    home=Path(__file__).parent/'runtime/home'; qpath=Path(__file__).parent/'runtime/qdrant_v3'; home.mkdir(parents=True,exist_ok=True); qpath.mkdir(parents=True,exist_ok=True)
    os.environ['HOME']=str(home)
    cfg={'llm':{'provider':'ollama','config':{'model':args.memory_model,'ollama_base_url':os.environ.get('OLLAMA_HOST','http://127.0.0.1:11434')}},'embedder':{'provider':'ollama','config':{'model':'nomic-embed-text','ollama_base_url':os.environ.get('OLLAMA_HOST','http://127.0.0.1:11434')}},'vector_store':{'provider':'qdrant','config':{'path':str(qpath),'collection_name':'harness_validation','embedding_model_dims':768}}}
    cfg['vector_store']['config']['collection_name']='harness_validation_v2'
    mem=Memory.from_config(cfg); client=ollama.Client(host=os.environ.get('OLLAMA_HOST','http://127.0.0.1:11434')); summary=[]
    for idx,c in enumerate(cases):
        uid='hv_'+c['case_id']; ts=[]; all_items=[]
        for ti,t in enumerate(turns(c)):
            add=mem.add(t,user_id=uid); snap=mem.get_all(filters={'user_id':uid}); items=snap.get('results',snap) if isinstance(snap,dict) else snap; all_items=items
            ts.append({'turn_index':ti,'text':t,'add_return':add,'memory_after_turn':items})
        query=c['current_query']; sr=mem.search(query,filters={'user_id':uid}); sr=sr.get('results',sr) if isinstance(sr,dict) else sr
        texts='\n'.join(str(x.get('memory',x)) for x in all_items)
        # O2 uses only actual final items; source-turn annotation is used only to pick IDs already present.
        selected=all_items if all_items else []
        o2ctx='\n'.join(str(x.get('memory',x)) for x in selected)
        joined=' '.join(str(x.get('memory',x)) for x in all_items)
        needed=' '.join(c.get('required_memory_facts',[])); present='YES' if needed and all(k in joined for k in re.findall(r'[\u4e00-\u9fffA-Za-z]+',needed)) else ('PARTIAL' if joined else 'NO')
        r0=ask(client,args.model,c, '\n'.join(str(x.get('memory',x)) for x in sr))
        r2=ask(client,args.model,c,o2ctx); r3a=ask(client,args.model,c,gold(c)); r3b=ask(client,args.model,c,gold(c,True));
        tr={'case_id':c['case_id'],'family':c['family'],'turns':ts,'final_memories':all_items,'normal_search_query':query,'normal_search_result':sr,'o2_item_ids':[x.get('id') for x in selected if isinstance(x,dict)],'o2_context':o2ctx,'required_information_present':present,'o3a_context':gold(c),'o3b_context':gold(c,True),'answers':{'O0':r0,'O2':r2,'O3a':r3a,'O3b':r3b}}
        (TRACE/f'{c["case_id"]}.json').write_text(json.dumps(tr,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        summary.append({'case_id':c['case_id'],'family':c['family'],'turns':len(ts),'memory_items':len(all_items),'required_information_present':present,'O0':r0,'O2':r2,'O3a':r3a,'O3b':r3b})
        if (idx+1)%4==0: print('FULL',idx+1,flush=True)
    (OUT/'harness_results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'formation_coverage.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['case_id','family','turns','memory_items','required_information_present']); w.writeheader(); w.writerows(summary)
    os._exit(0)
if __name__=='__main__': main()
