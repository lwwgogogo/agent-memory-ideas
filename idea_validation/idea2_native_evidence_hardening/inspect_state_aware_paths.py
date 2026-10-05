"""Static native path audit and non-secret dependency probes; no imports of providers."""
import ast,importlib.util,os
from common import ROOT,SOURCES,COMMITS,sha,save,check_sources
def evidence(relative,symbol=None,lines=None):
    path=SOURCES/relative;text=path.read_text()
    if symbol:
        name=symbol.split('.')[-1]
        node=next(n for n in ast.walk(ast.parse(text)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
        lines=[node.lineno,node.end_lineno]
        signature=ast.unparse(node.args)
    else:signature=None
    return {'file':str(path),'source_sha256':sha(path.read_bytes()),'symbol':symbol,
            'lines':lines,'signature':signature}
def inspect_paths():
    check_sources()
    dependency={p:('AVAILABLE' if importlib.util.find_spec(p) else 'MISSING')
                for p in ['numpy','openai','tiktoken','dotenv','faiss','memos']}
    # Only booleans; never load dotenv or serialize/print a secret value.
    env={k:('SET' if k in os.environ and bool(os.environ.get(k)) else 'NOT_SET')
         for k in ['OPENAI_API_KEY','OPENAI_API_KEY2','OPENAI_BASE_URL']}
    j='jitrl/Jericho/src/'
    result={'system':'jitrl','commit':COMMITS['jitrl'],
        'functions':[evidence(j+'cross_episode_memory.py',s) for s in
                     ['CrossEpisodeMemory.retrieve_similar_with_vector','_encode_trajectory_context','_init_vector_database']],
        'candidate_recall':{'formula':'recall_size=min(max(k*10,100),history_index.ntotal)',
                            'mechanism':'union of dual FAISS IndexFlatIP history/state recalls',
                            'evidence':evidence(j+'cross_episode_memory.py',lines=[390,412])},
        'similarity':{'formula':'0.3 * history_Jaccard(ngram=1) + 0.7 * current_state_Jaccard(ngram=4)',
                      'note':'FAISS cosine used for recall; final similarity is Jaccard, not cosine.',
                      'evidence':evidence(j+'cross_episode_memory.py',lines=[424,432])},
        'reward_order':{'formula':'sort descending by (similarity, discounted_future_reward)',
                        'evidence':evidence(j+'cross_episode_memory.py',lines=[434,482]),
                        'note':'all high-similarity >0.98 items are retained before filling k; return need not be size k'},
        'embedding':{'model_default':'text-embedding-ada-002','vector_dim_default':1536,
                     'credential_name':'OPENAI_API_KEY2',
                     'evidence':evidence(j+'openai_helpers.py','get_embedding_with_retries')},
        'context_generation':{'provider':'LLM provider via openai_helpers; OPENAI_API_KEY',
                              'evidence':evidence(j+'cross_episode_memory.py',lines=[198,234])},
        'dependencies':dependency,'environment_presence':env,
        'credential_values_read_or_recorded':False,'dotenv_loaded':False,
        'exact_upstream_state_path_invoked':False}
    missing=[p for p in ['openai','tiktoken','dotenv','faiss'] if dependency[p]=='MISSING']
    result['blocking_reasons']=['Missing required Python package: '+p for p in missing]
    result['blocking_reasons'] += ['Required environment variable is NOT_SET: '+k for k in
                                  ['OPENAI_API_KEY','OPENAI_API_KEY2'] if env[k]=='NOT_SET']
    result['status']='FULL_STATE_AWARE_BLOCKED_BY_DEPENDENCY' if result['blocking_reasons'] else 'PREFLIGHT_DEPENDENCIES_PRESENT'
    save(ROOT/'results/jitrl_state_aware_static.json',result)
    mem={'system':'memrl','commit':COMMITS['memrl'],'status':'MEMRL_FULL_RETRIEVAL_NOT_RUN',
         'candidate_generation_exists':True,'dependencies':dependency,
         'evidence':[evidence('memrl/memrl/service/retrievers.py','QueryRetriever.retrieve',lines=None),
                     evidence('memrl/memrl/service/retrievers.py',lines=[197,218]),
                     evidence('memrl/memrl/service/retrievers.py',lines=[238,337]),
                     evidence('memrl/memrl/service/memory_service.py',lines=[269,307])],
         'mechanism':'QueryRetriever uses MOS.search_score/search(task_description); AveFactRetriever may use keyword/embedding vector recall. Provider and MemOS integration precede value selection.',
         'blocked_reasons':['memos package missing; full configured MemOS/provider/vector store unavailable'],
         'inference':'The value selector audit passes a fixed candidate pool with identical similarity=0.5. It is not semantic/state-aware candidate retrieval.'}
    # Avoid ambiguous AST selection where multiple classes have the name retrieve.
    mem['evidence']=mem['evidence'][1:]
    save(ROOT/'results/memrl_full_retrieval_static.json',mem)
    return result
if __name__=='__main__':
    r=inspect_paths();print(r['status']);print('\n'.join(r['blocking_reasons']))
