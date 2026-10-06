"""Observed-count descriptors and fixed LP membership diagnostic."""
from collections import Counter
from fractions import Fraction
import numpy as np
from scipy.optimize import linprog

RESIDUAL_TOLERANCE=1e-10
METHOD="highs"

def descriptor(rows):
    counts=Counter((r["state"],r["action"]) for r in rows)
    output=[]
    for s in ("S0","S1"):
        n=counts[(s,"A")]+counts[(s,"B")]
        if n!=1000: raise ValueError("1000 state observations required")
        output.append(Fraction(counts[(s,"A")],n))
    return tuple(output)

def source_descriptors(rows):
    eras=sorted({r["era_id"] for r in rows})
    return {e:descriptor([r for r in rows if r["era_id"]==e]) for e in eras}

def tv(a,b):
    return sum((abs(x-y) for x,y in zip(a,b)),Fraction(0))/2

def nearest(points,target):
    if not points: raise ValueError("empty source")
    return min(tv(p,target) for p in points)

def membership(points,target):
    if not points: raise ValueError("empty source")
    matrix=np.vstack([np.ones(len(points)),np.array(points,dtype=float).T])
    rhs=np.array([1.,*map(float,target)])
    result=linprog(np.zeros(len(points)),A_eq=matrix,b_eq=rhs,
        bounds=[(0,None)]*len(points),method=METHOD,
        options={"primal_feasibility_tolerance":RESIDUAL_TOLERANCE,
                 "dual_feasibility_tolerance":RESIDUAL_TOLERANCE})
    if result.status==2:
        return {"inside":False,"weights":None,"residual":None,"solver_status":2}
    if not result.success:
        raise RuntimeError("unresolved LP status "+str(result.status))
    weights=result.x
    residual=max(float(np.max(np.abs(matrix@weights-rhs))),max(0.,-float(weights.min())))
    if residual>RESIDUAL_TOLERANCE:
        raise RuntimeError("LP residual exceeds fixed tolerance")
    return {"inside":True,"weights":list(map(float,weights)),"residual":residual,"solver_status":0}

def decision(global_status,inside):
    if global_status!="PRESCRIPTIVE": return "GLOBAL_NOT_CERTIFIED"
    return "TRANSFERABLE" if inside else "OUT_OF_ENVELOPE"
