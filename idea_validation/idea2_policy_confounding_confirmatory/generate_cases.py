import json,random
from core import ROOT,RUN1,CONDITIONS,ORDERED,LEVELS,ensure_env,save,sha

def world_counts(gamma):
    result=[]
    for state,rate in enumerate([.9,.2]):
        na=round(1000*(gamma if state==0 else 1-gamma))
        for a,n in [('A',na),('B',1000-na)]:result.append({'state':state,'action':a,'trials':n,'successes':round(n*rate),'failures':n-round(n*rate)})
    return result

def permutations(index,n):
    first=list(range(n));second=list(range(n));random.Random(index).shuffle(first);random.Random(index+10000).shuffle(second)
    adjusted=second==first
    if adjusted:second=second[1:]+second[:1]
    return {'O1':{'seed':index,'indices':first,'collision_rotation':False},'O2':{'seed':index+10000,'indices':second,'collision_rotation':adjusted}}

def evidence(case,condition,version):
    mapping={'A':'Left' if version=='AB' else 'Right','B':'Right' if version=='AB' else 'Left'}
    rows=case['balanced_counts'] if condition=='BalancedMemory' else case['confounded_counts']
    if condition=='NoMemory':return []
    if condition=='AggregateSummary':
        out=[]
        for a in ['A','B']:
            rr=[r for r in rows if r['action']==a];n=sum(r['trials'] for r in rr);s=sum(r['successes'] for r in rr)
            out.append('操作 %s：总执行 %d 次，成功 %d 次，总成功率 %.1f%%。'%(mapping[a],n,s,100*s/n))
        return out
    if condition=='StratifiedOracle':
        out=[]
        for state in [0,1]:
            text='State '+case['state_labels'][state]+' 内的记录：'
            for r in rows:
                if r['state']==state:text+='操作 %s 执行 %d 次、成功 %d 次、成功率 %.1f%%；'%(mapping[r['action']],r['trials'],r['successes'],100*r['successes']/r['trials'])
            out.append(text)
        return out
    return ['State %s；操作 %s；执行 %d 次；成功 %d 次；失败 %d 次。'%(case['state_labels'][r['state']],mapping[r['action']],r['trials'],r['successes'],r['failures']) for r in rows]

def prompt(case,condition,version,order):
    intro='这是一个中性虚构的%s系统，名称为%s。两种状态为 State %s 和 State %s，两个可选操作为 Left 和 Right。响应机制在历史与未来保持不变。\n'%(case['family'],case['world_name'],*case['state_labels'])
    target='下一次任务的状态以各 50% 的概率抽取。我们将不论抽到哪种状态，都固定执行指定的操作。请分别预测固定执行 Left 和固定执行 Right 的成功概率。\n'
    items=evidence(case,condition,version)
    if condition in ORDERED:items=[items[i] for i in case['permutations'][condition][order]['indices']]
    memory='过去执行经验的记忆：\n'+'\n'.join('%d. %s'%(i+1,t) for i,t in enumerate(items)) if items else '没有提供过去执行经验的记忆。'
    return intro+target+memory+'\n输出仅含 p_success_left 和 p_success_right，值必须是 0 到 1 的小数概率，禁止百分数和文字解释。'

def build_cases():
    source=json.loads((RUN1/'cases/cases.json').read_text());assert len(source)==20
    out=[]
    for i,old in enumerate(source,1):
        case={k:old[k] for k in ['id','family','world_name','gamma','state_labels','ground_truth']}
        case['confounded_counts']=world_counts(old['gamma']);case['balanced_counts']=world_counts(.5)
        assert case['confounded_counts']==old['confounded_counts'] and case['balanced_counts']==old['balanced_counts']
        case['permutations']={n:permutations(i,2 if n=='StratifiedOracle' else 4) for n in ORDERED}
        case['versions']={'AB':{'A':'Left','B':'Right'},'BA':{'A':'Right','B':'Left'}}
        case['runs']=[]
        for n in CONDITIONS:
            for v in ['AB','BA']:
                for o in (['O1','O2'] if n in ORDERED else ['NONE']):
                    case['runs'].append({'run_id':':'.join([case['id'],n,v,o]),'condition':n,'version':v,'order':o,'prompt':prompt(case,n,v,o)})
        out.append(case)
    return out
if __name__=='__main__':
    ensure_env();cases=build_cases();save(ROOT/'cases/cases.json',cases)
    save(ROOT/'cases/source.json',{'run1_cases_sha256':sha(RUN1/'cases/cases.json'),'base_worlds_identical_to_run1':True,'planned_runs':sum(len(c['runs']) for c in cases)})
    print('20 unchanged base worlds; 320 planned runs; permutations saved')
