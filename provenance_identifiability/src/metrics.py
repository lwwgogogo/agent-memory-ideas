def scores(pred,true,n):
    p,t=set(pred),set(true); i=len(p&t)
    return {'exact':int(p==t),'precision':i/len(p) if p else 0.0,'recall':i/len(t) if t else 1.0,'f1':2*i/(len(p)+len(t)) if p or t else 1.0,'topk':int(bool(p&t))}
