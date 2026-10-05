import ast
import json
import math
from fractions import Fraction
from pathlib import Path
from evaluator.verify_isolation import BASE, REPO

EXPECTED_CONFIG={"epsilon":1e-12,"min_eras":3,"min_effective_pairs":2,
                 "min_diversity":.2,"min_agreement":.8,"max_conflict":.1}

def legacy_science_check():
    from generator.private_worlds import POLICIES, NULL, INVARIANT, CASES
    source=(REPO/"idea_validation/idea2_cross_policy_certification/run_experiment.py").read_text()
    tree=ast.parse(source); assignments={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            assignments[node.targets[0].id]=node.value
    def value(node):
        if isinstance(node,ast.Constant):return node.value
        if isinstance(node,ast.Tuple):return tuple(value(x) for x in node.elts)
        if isinstance(node,ast.Dict):return {value(k):value(v) for k,v in zip(node.keys,node.values)}
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="F":
            return Fraction(*(value(x) for x in node.args))
        raise ValueError("unexpected historical constant expression")
    old_policy={k:tuple(Fraction(str(x)) for x in v) for k,v in value(assignments["P"]).items()}
    comparisons={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Compare) and len(node.ops)==1 and isinstance(node.comparators[0],ast.Constant):
            comparisons.setdefault(ast.unparse(node.left),[]).append((type(node.ops[0]).__name__,node.comparators[0].value))
    thresholds={"len(p)":("GtE",3),"ep":("GtE",2),"D":("GtE",.2),
                "max(cp, cn)":("GtE",.8),"cc":("LtE",.1)}
    expected_cases=[(f"W1_K{k}",["P95"]*k) for k in (1,2,5,10,20)]+[
      ("W2_PQ",["P95","Q95"]),("W2_PQPQ",["P95","Q95","P95","Q95"]),
      ("W3",["P95","Q95","R50"]),("W4",["P90","P92","P95"]),
      ("M1_ECHO",["P95"]*20),("M1_DIVERSE",["P95","Q95","R50"])]
    checks={"policy_tables_equal":old_policy==POLICIES,
        "outcome_tables_equal":value(assignments["N"])==NULL and value(assignments["I"])==INVARIANT,
        "epsilon_equal":value(assignments["EPS"])==EXPECTED_CONFIG["epsilon"],
        "thresholds_equal":all(v in comparisons.get(k,[]) for k,v in thresholds.items()),
        "public_config_equal":json.loads((BASE/"public_config.json").read_text())==EXPECTED_CONFIG,
        "cases_equal":[(name,seq) for name,_,seq in CASES]==expected_cases}
    return {"checks":checks,"pass":all(checks.values())}

def m1_from_observations(path):
    cells={}
    for line in Path(path).read_text().splitlines():
        r=json.loads(line);v=cells.setdefault((r["state"],r["action"]),[0,0]);v[0]+=1;v[1]+=r["outcome"]
    utility={a:sum(Fraction(1,2)*Fraction(cells[(s,a)][1],cells[(s,a)][0]) for s in ("S0","S1")) for a in ("A","B")}
    return {"A":float(utility["A"]),"B":float(utility["B"]),
            "gap":float(utility["A"]-utility["B"]),
            "exact":{a:str(v) for a,v in utility.items()}}

def reproduction(outputs,private):
    old=json.loads((REPO/"idea_validation/idea2_cross_policy_certification/results/formal_results.json").read_text())["results"]
    metrics=["D_policy","D_min","D_median","D_max","C_pos","C_neg","C_conflict",
             "raw_support_count","era_count","mean_observed_gap","success_support","effective_distinct_policy_pairs"]
    cases={}; all_checks=[]
    for filename,meta in private["cases"].items():
        name=meta["historical_case"];new=outputs[filename];prior=old[name];checks={}
        for metric in metrics:
            checks[metric]=math.isclose(new[metric],prior[metric],rel_tol=0,abs_tol=1e-12)
        for metric in ("status","diagnostic","sign_pattern"):checks[metric]=new[metric]==prior[metric]
        checks["profiles"]=list(new["profile"].values())==list(prior["profile"].values())
        checks["gaps"]=all(math.isclose(x,y,rel_tol=0,abs_tol=1e-12)
            for x,y in zip(new["gaps"].values(),prior["gaps"].values())) and len(new["gaps"])==len(prior["gaps"])
        counts_ok=all(new["cells"][r["era_id"]][r["state"]][r["action"]]==[r["n"],r["success"]] for r in meta["cells"])
        checks["exact_cell_counts"]=counts_ok
        m1=m1_from_observations(BASE/"export"/filename)
        checks["M1"]=all(math.isclose(m1[a],prior["M1_target_utility"][a],rel_tol=0,abs_tol=1e-12) for a in ("A","B"))
        cases[name]={"anonymous_input":filename,"checks":checks,"pass":all(checks.values()),
            "status":new["status"],"D_policy":new["D_policy"],"C_pos":new["C_pos"],"C_conflict":new["C_conflict"],
            "sign_pattern":new["sign_pattern"],"M1":m1,"raw_support_count":new["raw_support_count"],"era_count":new["era_count"]}
        all_checks.extend(checks.values())
    echo=cases["M1_ECHO"];diverse=cases["M1_DIVERSE"]
    ratio=cases["W3"]["D_policy"]/cases["W4"]["D_policy"]
    m1_ok=(abs(echo["M1"]["gap"]-.4)<=1e-12 and abs(diverse["M1"]["gap"]-.4)<=1e-12
           and abs(echo["M1"]["gap"]-diverse["M1"]["gap"])<=.02
           and echo["status"]!="PRESCRIPTIVE" and diverse["status"]=="PRESCRIPTIVE")
    return {"cases":cases,"all_match":len(cases)==11 and all(all_checks),
            "D_true_over_D_false":ratio,"ratio_match":abs(ratio-18)<=1e-12,
            "M1_non_substitutability_pass":m1_ok}

def compute_gates(history,rep,audit,metamorphic,science,lock_pass):
    checks={
      "H0":history["history_hash_match"],
      "H1":rep["all_match"] and rep["ratio_match"],
      "H2":audit["schema_whitelist_pass"] and audit["anonymous_era_id_pass"] and audit["missing_field_rejection_pass"],
      "H3":audit["candidate_import_isolation_pass"] and audit["forbidden_string_audit_pass"],
      "H4":audit["filesystem_isolation_pass"] and audit["subprocess_isolation_pass"] and audit["environment_isolation_pass"],
      "H5":metamorphic["private_metadata_mutations_tested"]>=5 and metamorphic["input_sha_equality"]
            and metamorphic["output_bitwise_equality"] and metamorphic["canonical_output_equality"] and metamorphic["all_isolated"],
      "H6":audit["forbidden_field_rejection_pass"],
      "H7":rep["M1_non_substitutability_pass"],
      "H8":science["pass"] and lock_pass,
      "H9":audit["G5"],
    }
    return {"gates":{k:"PASS" if v else "FAIL" for k,v in checks.items()},
            "verdict":"ORACLE_FREE_HARDENING_GO" if all(checks.values()) else "ORACLE_FREE_HARDENING_NO_GO"}
