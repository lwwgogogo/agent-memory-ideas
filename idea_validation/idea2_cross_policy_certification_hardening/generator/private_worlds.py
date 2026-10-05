from fractions import Fraction as F

POLICIES = {
    "P95": (F(95,100),F(5,100)), "Q95": (F(5,100),F(95,100)),
    "R50": (F(1,2),F(1,2)), "P90": (F(9,10),F(1,10)),
    "P92": (F(92,100),F(8,100)),
}
NULL = {"S0":{"A":F(9,10),"B":F(9,10)}, "S1":{"A":F(1,5),"B":F(1,5)}}
INVARIANT = {"S0":{"A":F(9,10),"B":F(1,2)}, "S1":{"A":F(7,10),"B":F(3,10)}}
CASES = [(f"W1_K{k}",NULL,["P95"]*k) for k in (1,2,5,10,20)] + [
    ("W2_PQ",NULL,["P95","Q95"]), ("W2_PQPQ",NULL,["P95","Q95","P95","Q95"]),
    ("W3",INVARIANT,["P95","Q95","R50"]), ("W4",INVARIANT,["P90","P92","P95"]),
    ("M1_ECHO",INVARIANT,["P95"]*20), ("M1_DIVERSE",INVARIANT,["P95","Q95","R50"]),
]

def generate_cells(table, policies):
    for index, policy in enumerate(policies):
        for si, state in enumerate(("S0","S1")):
            n_a = POLICIES[policy][si]*1000
            assert n_a.denominator == 1
            for action, n in (("A",int(n_a)),("B",1000-int(n_a))):
                success = n*table[state][action]
                assert success.denominator == 1
                yield {"era_id":f"e{index:03d}", "state":state, "action":action,
                       "n":n, "success":int(success)}

def observed_records(table, policies):
    for cell in generate_cells(table, policies):
        for outcome, n in ((1,cell["success"]),(0,cell["n"]-cell["success"])):
            for _ in range(n):
                yield {"era_id":cell["era_id"],"state":cell["state"],
                       "action":cell["action"],"outcome":outcome}
