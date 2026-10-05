import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_experiment import *
def test01():assert truth("W3")=={"A":F(4,5),"B":F(2,5)}
def test02():assert truth("W1")["A"]==F(11,20)
def test03():assert all(r["success"]+r["failure"]==r["n"] for r in rows("W3",["P95"],"x"))
def test04():assert calc("W3",["P95"],"x")["profile"]["x-0"]=={"S0":.95,"S1":.05}
def test05():assert sum(abs(.9-v) for v in (.9,))/2==0
def test06():assert abs((abs(.95-.05)+abs(.05-.95))/2-.9)<1e-12
def test07():assert abs(calc("W4",["P90","P92","P95"],"x")["D_policy"]-1/30)<1e-12
def test08():assert calc("W3",["P95","Q95","R50"],"x")["D_policy"]==.6
def test09():assert calc("W1",["P95"]*4,"x")["D_policy"]==0
def test10():assert calc("W3",["P95","Q95","R50"],"x")["C_pos"]==1
def test11():assert calc("W3",["P95","Q95","R50"],"x")["C_neg"]==0
def test12():assert calc("W2",["P95","Q95"],"x")["C_conflict"]==1
def test13():assert calc("W1",["P95"]*2,"x")["diagnostic"]=="NO_EFFECTIVE_POLICY_DIVERSITY"
def test14():assert calc("W3",["P95","Q95","R50"],"x")["status"]=="PRESCRIPTIVE"
def test15():
 from schema import validate
 try:validate([{"era_id":"e","state":"S0","action":"A","outcome":1,"gamma":.4}])
 except ValueError:return
 assert False
def test16():assert calc("W1",["P95"]*3,"x")["sign_pattern"]==["+","+","+"]
def test17():assert calc("W2",["P95","Q95"],"x")["sign_pattern"]==["+","-"]
def test18():assert calc("W3",["P95","Q95","R50"],"x")["sign_pattern"]==["+","+","+"]
def test19():assert calc("W4",["P90","P92","P95"],"x")["D_policy"]<.6
def test20():assert calc("W3",["P95","Q95","R50"],"x")["M1_target_utility"]=={"A":.8,"B":.4}
def test21():
 a=calc("W3",["P95"]*20,"a");b=calc("W3",["P95","Q95","R50"],"b")
 assert a["M1_target_gap"]==b["M1_target_gap"] and a["status"]!=b["status"]
def test22():assert calc("W3",["P95","Q95","R50"],"x")["D_policy"]>=.2
def test23():assert calc("W3",["P95","Q95","R50"],"x")==calc("W3",["P95","Q95","R50"],"x")
def test24():assert all(calc("W1",["P95"]*k,"x")["status"]!="PRESCRIPTIVE" for k in (1,2,5,10,20))
