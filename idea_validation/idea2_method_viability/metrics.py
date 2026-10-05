from fractions import Fraction as F
def pig(p,q):return sum(abs(p[a]-q[a]) for a in ('A','B'))
def gap(u):return u['A']-u['B']
def npe(u):return abs(gap(u))
def tge(u,true_gap):return abs(gap(u)-true_gap)
def tsr(u,true_gap=F(1,10)):return gap(u)/true_gap if gap(u)>0 else None
def correction(value,baseline):return None if baseline==0 else 1-value/baseline
def rank(u):return 'A' if gap(u)>0 else 'B' if gap(u)<0 else 'TIE'
def reversal(p,q):return gap(p)*gap(q)<0
def crossover(t0,t1):return rank(t0)=='A' and rank(t1)=='B'
def null_gate(rate,np_p,np_q):return rate is not None and rate>=F(4,5) and max(np_p,np_q)<=F(3,100)
def signal_gate(ranks,ratios):
 import statistics
 return all(x=='A' for x in ranks) and all(x is not None for x in ratios) and F(7,10)<=statistics.median(ratios)<=F(13,10)
