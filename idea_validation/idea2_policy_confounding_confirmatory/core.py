import pathlib,json,math,sys,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
RUN1=ROOT.parent/'idea2_policy_confounding'
CONDITIONS=['NoMemory','ConfoundedMemory','BalancedMemory','StratifiedOracle','AggregateSummary']
PRIMARY=CONDITIONS[:4]
ORDERED=CONDITIONS[1:4]
LEVELS=[.50,.70,.85,.95]
MODEL='qwq:32b'
OPTIONS={'temperature':0,'top_p':1.0,'seed':20261005,'num_ctx':4096,'num_predict':128}
SCHEMA={'type':'object','properties':{'p_success_left':{'type':'number','minimum':0,'maximum':1},'p_success_right':{'type':'number','minimum':0,'maximum':1}},'required':['p_success_left','p_success_right'],'additionalProperties':False}
SYSTEM='只输出 JSON 对象，且只能有 p_success_left 和 p_success_right 两个字段。每个值必须是 0 到 1 之间的小数概率，例如 0.55，禁止写成百分数 55。不输出 choice、confidence、reason 或任何解释。'
def ensure_env():
    if sys.version_info[:3]!=(3,10,21) or pathlib.Path(sys.prefix).name!='agentmem_lab':raise RuntimeError('Requires agentmem_lab Python 3.10.21')
def save(path,value):
    path=pathlib.Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8');tmp.replace(path)
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def parse(raw):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('duplicate_field')
            d[k]=v
        return d
    x=json.loads(raw,object_pairs_hook=pairs)
    if not isinstance(x,dict) or set(x)!=set(SCHEMA['required']):raise ValueError('missing_or_extra_field')
    for v in x.values():
        if type(v) not in [int,float] or not math.isfinite(v) or not 0<=v<=1:raise ValueError('invalid_probability')
    return x
def canonical(x,version):
    left,right=x['p_success_left'],x['p_success_right']
    if version=='AB':return left,right
    if version=='BA':return right,left
    raise ValueError(version)
def validate_response(response):
    result=dict(response)
    if result.get('transport_error'):
        result.update(valid=False,retryable=False);return result
    try:result['parsed']=parse(result.get('raw',''));result.update(valid=True,retryable=False)
    except (ValueError,TypeError) as e:result.update(valid=False,retryable=True,validation_error=str(e))
    return result
def run_with_retry(prompt,invoke):
    first=validate_response(invoke(prompt,0));retry=None
    if not first['valid'] and first['retryable']:retry=validate_response(invoke(prompt,1))
    last=retry if retry is not None else first
    return {'first_attempt':first,'retry_attempt':retry,'final_status':'VALID' if last['valid'] else 'INVALID','parsed':last.get('parsed') if last['valid'] else None}
def paired_average(rows,condition):
    orders=['O1','O2'] if condition in ORDERED else ['NONE']
    expected={(v,o) for v in ['AB','BA'] for o in orders}
    lookup={(r['version'],r['order']):r for r in rows}
    if len(rows)!=len(expected) or set(lookup)!=expected or any(r['final_status']!='VALID' for r in rows):return None
    label={v:sum(lookup[(v,o)]['miab'] for o in orders)/len(orders) for v in ['AB','BA']}
    order={o:(lookup[('AB',o)]['miab']+lookup[('BA',o)]['miab'])/2 for o in orders}
    return {'miab':sum(order.values())/len(orders),'AB':label['AB'],'BA':label['BA'],**order}
