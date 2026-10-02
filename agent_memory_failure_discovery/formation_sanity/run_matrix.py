import csv,json,logging,os,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE=Path(__file__).resolve().parent; RAW=BASE/'raw_outputs'; RAW.mkdir(parents=True,exist_ok=True)
CONTROLS=[('P01','我是一名素食主义者。'),('P02','我对花生严重过敏。'),('P03','我住在重庆。'),('P04','我的生日是 5 月 12 日。'),('P05','我平时喜欢喝无糖咖啡。'),('P06','我工作时默认使用 Python。'),('P07','我的狗叫 Lucky。'),('P08','我不喜欢恐怖电影。'),('P09','我计划下个月去东京。'),('P10','我每天早上七点跑步。'),('P11','我更喜欢靠窗座位。'),('P12','我当前项目使用 PostgreSQL。')]
def cfg(model,home,qpath,collection):
 return {'llm':{'provider':'ollama','config':{'model':model,'ollama_base_url':os.environ.get('OLLAMA_HOST','http://127.0.0.1:11434')}},'embedder':{'provider':'ollama','config':{'model':'nomic-embed-text','ollama_base_url':os.environ.get('OLLAMA_HOST','http://127.0.0.1:11434')}},'vector_store':{'provider':'qdrant','config':{'path':str(qpath),'collection_name':collection,'embedding_model_dims':768}}}
def wrap_llm(mem,logpath,condition,caseid):
 try: old=mem.llm.generate
 except Exception: return False
 def traced(*args,**kwargs):
  rec={'condition':condition,'case_id':caseid,'args':repr(args)[:10000],'kwargs':repr(kwargs)[:10000]}
  try:
   out=old(*args,**kwargs); rec['response']=repr(out)[:30000]; rec['ok']=True; return out
  except Exception as e:
   rec['error']=repr(e); rec['ok']=False; raise
  finally:
   with logpath.open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
 mem.llm.generate=traced; return True
def run_condition(name,writer,infer,official,home,qpath,collection):
 from mem0 import Memory
 mem=Memory.from_config(cfg(writer,home,qpath,collection)); log=RAW/f'{name}_writer_calls.jsonl'; wrapped=0; rows=[]
 for cid,text in CONTROLS:
  uid=f'formation_sanity_{name}_{cid}'; wrapped += int(wrap_llm(mem,log,name,cid))
  inp=[{'role':'user','content':text}] if official else text
  try:
   add=mem.add(inp,user_id=uid,infer=infer); allr=mem.get_all(filters={'user_id':uid}); items=allr.get('results',allr) if isinstance(allr,dict) else allr; sr=mem.search(text,filters={'user_id':uid}); sr=sr.get('results',sr) if isinstance(sr,dict) else sr
   created=len(items)>0; status='MEMORY_CREATED' if created else 'NO_MEMORY'
   rows.append({'condition':name,'case_id':cid,'text':text,'user_id':uid,'writer':writer,'infer':infer,'official_messages':official,'add_return':add,'get_all':items,'search':sr,'memory_count':len(items),'search_count':len(sr),'status':status})
  except Exception as e:
   rows.append({'condition':name,'case_id':cid,'text':text,'user_id':uid,'writer':writer,'infer':infer,'official_messages':official,'status':'ERROR','error':repr(e),'traceback':traceback.format_exc()})
  (RAW/f'{name}_{cid}.json').write_text(json.dumps(rows[-1],ensure_ascii=False,indent=2,default=str),encoding='utf-8')
  print(name,cid,rows[-1]['status'],flush=True)
 return rows
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--run-d',action='store_true');p.add_argument('--only-d',action='store_true');a=p.parse_args(); home=BASE/'runtime/home';qpath=BASE/('runtime/qdrant_matrix_D' if a.only_d else 'runtime/qdrant_matrix');home.mkdir(parents=True,exist_ok=True);qpath.mkdir(parents=True,exist_ok=True);os.environ['HOME']=str(home)
 allrows=[]
 if not a.only_d:
  allrows += run_condition('A_current_qwen','qwen2.5:14b',True,False,home,qpath,'formation_A')
  allrows += run_condition('B_official_qwen','qwen2.5:14b',True,True,home,qpath,'formation_B')
  allrows += run_condition('C_raw_storage','qwen2.5:14b',False,True,home,qpath,'formation_C')
 cpass=sum(x['status']=='MEMORY_CREATED' for x in allrows if x['condition']=='C_raw_storage')==12
 if (a.run_d or a.only_d) and (cpass or a.only_d): allrows += run_condition('D_official_qwq','qwq:32b',True,True,home,qpath,'formation_D')
 elif a.run_d: print('D_SKIPPED_STORAGE_GATE',flush=True)
 with (BASE/'formation_matrix.csv').open('w',newline='',encoding='utf-8-sig') as f:
  fields=['condition','case_id','writer','infer','official_messages','memory_count','search_count','status'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k) for k in fields} for r in allrows])
 (BASE/'matrix_results.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
if __name__=='__main__':main()
