"""Controlled parameter changes. Algorithms receive only observations."""
import numpy as np


def generate_scenario(spec, steps, seed, start_range=(900,1500)):
    streams=[np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(4)]
    initial=int(streams[0].integers(2))
    change=int(streams[3].integers(start_range[0],start_range[1]+1))
    q=np.full(steps,spec['q_before'],dtype=float)
    r=np.full(steps,spec['r_before'],dtype=float)
    event=spec['kind']!='control'
    if event:
        q[change:]=spec.get('q_after',spec['q_before'])
        r[change:]=spec.get('r_after',spec['r_before'])
    end=None
    if spec['kind']=='corruption':
        end=change+100
        q[end:]=spec['q_before'];r[end:]=spec['r_before']
    flips=streams[1].random(steps)<q;flips[0]=False
    x=np.bitwise_xor(np.cumsum(flips)%2,initial).astype(int)
    u=streams[2].random(steps)
    y=np.bitwise_xor(x,u<r).astype(int)
    return x,y,q,r,dict(change=change if event else None,corruption_end=end)


def oracle_filter(y,q,r):
    p=.5;result=[]
    for obs,qt,rt in zip(y,q,r):
        prior=qt+(1-2*qt)*p
        l1,l0=(1-rt,rt) if obs else (rt,1-rt)
        p=prior*l1/(prior*l1+(1-prior)*l0)
        result.append(p)
    return np.asarray(result)


def recovery(pred,truth,start,end,consecutive=10):
    run=0
    for t in range(start,end):
        run=run+1 if pred[t]==truth[t] else 0
        if run>=consecutive:
            return t-start+1,0  # Earliest observable completion, min 10 steps.
    return end-start,1


def event_metrics(x,p,events):
    pred=(p>=.5).astype(int)
    result={k:None for k in ['error_50','error_100','error_300','recovery_delay','recovery_censored',
                             'corruption_error','post_corruption_error_100','post_corruption_error_remaining',
                             'post_corruption_recovery','post_corruption_censored',
                             'useful_memory_retention_proxy','retention_eligible_steps']}
    start=events['change'];end=events['corruption_end']
    if start is None: return result
    for w in (50,100,300):result[f'error_{w}']=float(np.mean(pred[start:start+w]!=x[start:start+w]))
    result['recovery_delay'],result['recovery_censored']=recovery(pred,x,start,end or len(x))
    if end is not None:
        result['corruption_error']=float(np.mean(pred[start:end]!=x[start:end]))
        result['post_corruption_error_100']=float(np.mean(pred[end:end+100]!=x[end:end+100]))
        result['post_corruption_error_remaining']=float(np.mean(pred[end:]!=x[end:]))
        result['post_corruption_recovery'],result['post_corruption_censored']=recovery(pred,x,end,len(x))
        # A proxy, not memory identity retention: old state continuously valid, previously correct.
        valid=np.logical_and.accumulate(x[start:end+100]==x[start-1])[end-start:]
        valid &= pred[start-1]==x[start-1]
        n=int(valid.sum());result['retention_eligible_steps']=n
        result['useful_memory_retention_proxy']=float(np.mean(pred[end:end+100][valid]==x[end:end+100][valid])) if n else None
    return result
