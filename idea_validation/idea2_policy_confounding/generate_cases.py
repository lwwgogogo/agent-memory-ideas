import random
from common import ROOT,CONDITIONS,LEVELS,ORDER_SEEDS,ensure_environment,save_json
FAMILIES=['机器控制','资源选择','路径选择','算法策略','任务调度']
def counts(gamma):
    rows=[]
    for state,rate in enumerate([.9,.2]):
        n_a=round(1000*(gamma if state==0 else 1-gamma))
        for action,n in [('A',n_a),('B',1000-n_a)]:
            rows.append({'state':state,'action':action,'trials':n,'successes':round(rate*n),'failures':n-round(rate*n)})
    return rows

def render(rows,states,swap,seed,style):
    display={'A':'B' if swap else 'A','B':'A' if swap else 'B'}
    rng=random.Random(seed)
    if style=='AggregateSummary':
        items=[]
        for a in ['A','B']:
            rr=[r for r in rows if r['action']==a];n=sum(r['trials'] for r in rr);s=sum(r['successes'] for r in rr)
            items.append('Action %s：总执行 %d 次，成功 %d 次，总成功率 %.1f%%。'%(display[a],n,s,100*s/n))
    elif style=='StratifiedOracle':
        items=[]
        for state in [0,1]:
            rr=[r for r in rows if r['state']==state];rng.shuffle(rr)
            text='State '+states[state]+' 内的记录：'
            for r in rr:text+='Action %s 执行 %d 次、成功 %d 次、成功率 %.1f%%；'%(display[r['action']],r['trials'],r['successes'],100*r['successes']/r['trials'])
            items.append(text)
    else:
        items=['State %s；Action %s；执行 %d 次；成功 %d 次；失败 %d 次。'%(states[r['state']],display[r['action']],r['trials'],r['successes'],r['failures']) for r in rows]
    rng.shuffle(items);return items

def build_cases():
    cases=[];rng=random.Random(20261004)
    for family_id,family in enumerate(FAMILIES):
        for level,gamma in enumerate(LEVELS):
            index=family_id*4+level+1;labels=rng.sample(['K7','Z4','Q2','M8','T3','V6','P9','N5'],2)
            rows=counts(gamma);balanced=counts(.5);variants=[]
            for swap in [0,1]:
                for seed in ORDER_SEEDS:
                    memories={'NoMemory':[],'ConfoundedMemory':render(rows,labels,swap,seed,'ConfoundedMemory'),'BalancedMemory':render(balanced,labels,swap,seed,'BalancedMemory'),'StratifiedOracle':render(rows,labels,swap,seed,'StratifiedOracle'),'AggregateSummary':render(rows,labels,swap,seed,'AggregateSummary')}
                    variants.append({'label_swap':swap,'order_seed':seed,'canonical_to_display':{'A':'B' if swap else 'A','B':'A' if swap else 'B'},'memories':memories})
            cases.append({'id':'W%02d'%index,'family':family,'world_name':'单元 '+chr(65+family_id)+str(100+index),'gamma':gamma,'state_labels':labels,'confounded_counts':rows,'balanced_counts':balanced,'ground_truth':{'causal_success_A':.55,'causal_success_B':.55,'causal_gap':0},'variants':variants})
    return cases

def make_prompt(case,variant,condition):
    intro='这是一个中性虚构的%s系统，名称为%s。两种状态为 State %s 和 State %s，两个可选操作为 Action A 和 Action B。响应机制在历史与未来保持不变。\n'%(case['family'],case['world_name'],*case['state_labels'])
    target='下一次任务的状态以各 50%% 的概率抽取。我们将不论抽到哪种状态，都固定执行指定的动作。请分别预测固定执行 Action A 和固定执行 Action B 的成功概率，并选择你认为更好的动作；认为相等时可选 TIE。\n'
    target=target.replace('50%%','50%')
    items=variant['memories'][condition]
    memory='过去执行经验的记忆：\n'+'\n'.join('%d. %s'%(i+1,t) for i,t in enumerate(items)) if items else '没有提供过去执行经验的记忆。'
    return intro+target+memory
if __name__=='__main__':
    ensure_environment();cases=build_cases();save_json(ROOT/'cases/cases.json',cases);print('20 base worlds; 5 conditions; 2 label mappings x 2 order seeds = 400 fixed calls')
