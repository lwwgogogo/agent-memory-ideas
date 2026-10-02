import json,os
from pathlib import Path
BASE=Path(__file__).resolve().parent; OUT=BASE/'raw_outputs'; OUT.mkdir(exist_ok=True)
def main():
 for model in ['qwen2.5:14b','qwq:32b']:
  os.environ['HOME']=str(BASE/('runtime/capture_home_'+model.replace(':','_'))); (BASE/('runtime/capture_home_'+model.replace(':','_'))).mkdir(parents=True,exist_ok=True)
  from mem0 import Memory
  cfg={'llm':{'provider':'ollama','config':{'model':model,'ollama_base_url':os.environ.get('OLLAMA_HOST','http://127.0.0.1:11434')}},'embedder':{'provider':'ollama','config':{'model':'nomic-embed-text','ollama_base_url':os.environ.get('OLLAMA_HOST','http://127.0.0.1:11434')}},'vector_store':{'provider':'qdrant','config':{'path':str(BASE/('runtime/capture_qdrant_'+model.replace(':','_'))),'collection_name':'capture','embedding_model_dims':768}}}
  m=Memory.from_config(cfg); old=m.llm.generate_response; captured={}
  def wrapped(*args,**kwargs):
   try: out=old(*args,**kwargs); captured['response']=out; return out
   except Exception as e: captured['error']=repr(e); raise
  m.llm.generate_response=wrapped
  try: add=m.add([{'role':'user','content':'我是一名素食主义者。'}],user_id='capture_'+model.replace(':','_'),infer=True); status='ok'
  except Exception as e: add={'error':repr(e)};status='error'
  (OUT/('capture_'+model.replace(':','_')+'.json')).write_text(json.dumps({'model':model,'status':status,'raw_extraction_response':captured,'add_return':add},ensure_ascii=False,indent=2,default=str),encoding='utf-8')
if __name__=='__main__':main()
