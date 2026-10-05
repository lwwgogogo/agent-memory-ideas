import json,pathlib,sys,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
CONDITIONS=['NoMemory','ConfoundedMemory','BalancedMemory','StratifiedOracle','AggregateSummary']
LEVELS=[0.50,0.70,0.85,0.95]
ORDER_SEEDS=[17,43]
def ensure_environment():
    if sys.version_info[:2]!=(3,10) or pathlib.Path(sys.prefix).name!='agentmem_lab':
        raise RuntimeError('Use conda run -n agentmem_lab python; system Python is forbidden')
def save_json(path,value):
    path=pathlib.Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8');tmp.replace(path)
def digest(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
