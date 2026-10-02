"""Exact HMM parameter/state posterior on the last W observations.

Two-stack sliding matrix products give amortized O(T*M), not O(T*W*M).
Each window starts with uniform state and fixed parameter prior.
"""
import numpy as np


def product(a,b):
    """Scaled batched 2x2 product, newest matrix on the left."""
    am,al=a;bm,bl=b
    m=np.empty_like(am)
    m[:,0]=am[:,0]*bm[:,0]+am[:,1]*bm[:,2]
    m[:,1]=am[:,0]*bm[:,1]+am[:,1]*bm[:,3]
    m[:,2]=am[:,2]*bm[:,0]+am[:,3]*bm[:,2]
    m[:,3]=am[:,2]*bm[:,1]+am[:,3]*bm[:,3]
    scale=m.max(axis=1)
    with np.errstate(divide='ignore'):
        log=al+bl+np.log(scale)
    m=np.divide(m,scale[:,None],out=np.zeros_like(m),where=scale[:,None]>0)
    return m,log


def sliding_bma(y,q_grid,r_grid,window):
    y=np.asarray(y)
    if y.ndim!=1 or not np.isin(y,[0,1]).all() or not isinstance(window,int) or window<1:
        raise ValueError('Binary observations and positive integer window required')
    q,r=np.asarray([(q,r) for q in q_grid for r in r_grid]).T
    if ((q<=0)|(q>.5)|(r<0)|(r>.5)).any():raise ValueError('Require 0<Q<=.5, 0<=R<=.5')
    left=[];right=[];count=0;result=[]
    for obs in y:
        l1,l0=(1-r,r) if obs else (r,1-r)
        item=(np.stack([(1-q)*l0,q*l0,q*l1,(1-q)*l1],axis=1),np.zeros(len(q)))
        aggregate=product(item,right[-1][1]) if right else item
        right.append((item,aggregate));count+=1
        if count>window:
            if not left:
                while right:
                    value=right.pop()[0]
                    agg=product(left[-1][1],value) if left else value
                    left.append((value,agg))
            left.pop();count-=1
        aggregate=product(right[-1][1],left[-1][1]) if left and right else (left[-1][1] if left else right[-1][1])
        mat,scale=aggregate
        total=mat.sum(axis=1)*.5
        with np.errstate(divide='ignore'):log_evidence=np.log(total)+scale
        w=np.exp(log_evidence-np.max(log_evidence));w/=w.sum()
        prob=np.divide((mat[:,2]+mat[:,3])*.5,total,out=np.full_like(total,.5),where=total>0)
        result.append(w@prob)
    return np.asarray(result)
