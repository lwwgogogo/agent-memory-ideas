from __future__ import annotations
import collections, json, math, statistics
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from core import (ROOT,load_source,FORMATION_TYPES,WRITERS,recovery_accuracy,full_structure_retained,state_label_retained,
                  action_conditional_structure_retained,canonical_probabilities,regret,pair_resolution,save,bootstrap_mean_ci)

def safe_mean(xs): return float(statistics.mean(xs)) if xs else None

def boot_diff_world(records_by_world, seed=20261005, draws=10000):
    worlds=sorted(records_by_world);rng=np.random.default_rng(seed);vals=[]
    if not worlds:return {"difference":None,"ci_low":None,"ci_high":None,"bootstrap_method":"world-cluster bootstrap"}
    for _ in range(draws):
        sampled=rng.choice(worlds,size=len(worlds),replace=True);lost=[];kept=[]
        for wid in sampled:
            for r in records_by_world[wid]:
                (kept if r["full"] else lost).append(r["regret"])
        if lost and kept: vals.append(float(np.mean(lost)-np.mean(kept)))
    if not vals:return {"difference":None,"ci_low":None,"ci_high":None,"bootstrap_method":"world-cluster bootstrap"}
    lost=[r["regret"] for x in records_by_world.values() for r in x if not r["full"]]
    kept=[r["regret"] for x in records_by_world.values() for r in x if r["full"]]
    return {"lost_regret":safe_mean(lost),"retained_regret":safe_mean(kept),"difference":float(np.mean(lost)-np.mean(kept)),
            "ci_low":float(np.quantile(vals,.025)),"ci_high":float(np.quantile(vals,.975)),"valid_bootstrap_draws":len(vals),"bootstrap_method":"world-cluster bootstrap","seed":seed,"draws":draws}

def bootstrap_pair_diff(values_by_pair, seed=20261005, draws=10000):
    pairs=sorted(values_by_pair);rng=np.random.default_rng(seed);diffs=[]
    for _ in range(draws):
        samp=rng.choice(pairs,size=len(pairs),replace=True)
        diffs.append(float(np.mean([values_by_pair[p][0]-values_by_pair[p][1] for p in samp])))
    vals=[values_by_pair[p][0]-values_by_pair[p][1] for p in pairs]
    return {"mean":safe_mean(vals),"ci_low":float(np.quantile(diffs,.025)),"ci_high":float(np.quantile(diffs,.975)),"n":len(vals),"seed":seed,"draws":draws}

def main():
    source=load_source();worlds={w["world_id"]:w for w in source["worlds"]};pairs=collections.defaultdict(list)
    for w in source["worlds"]:pairs[w["pair_id"]].append(w)
    tier_stats={};tier_records={};completeness={}
    all_forms={}
    for tier in WRITERS:
        forms=json.loads((ROOT/"results"/f"formation_{tier}.json").read_text())
        faithful=json.loads((ROOT/"results"/f"faithfulness_{tier}.json").read_text())
        recovery=json.loads((ROOT/"results"/f"recoverability_{tier}.json").read_text())
        downstream=json.loads((ROOT/"results"/f"downstream_{tier}.json").read_text())
        all_forms[tier]=forms
        faithful_by={x["run_id"]:[] for x in forms}
        for x in faithful: faithful_by.setdefault(x["formation_run_id"],[]).append(x)
        recover_by={x["formation_run_id"]:x for x in recovery}
        down_by=collections.defaultdict(list)
        for x in downstream: down_by[x["formation_run_id"]].append(x)
        per_memory=[]
        formation_summaries={}
        for typ in FORMATION_TYPES:
            selected=[x for x in forms if x["formation_type"]==typ]
            for f in selected:
                audits=faithful_by.get(f["run_id"],[])
                valid_audits=[a for a in audits if a["final_status"]=="VALID" and isinstance(a.get("audit"),dict)]
                if len(valid_audits)<2: strict=False;audit_state="AUDIT_INVALID"
                else:
                    flags=[a["audit"]["faithful"] and not a["audit"]["contradiction"] and not a["audit"]["unsupported_specific_claim"] and not a["audit"]["numeric_error"] for a in valid_audits]
                    strict=all(flags)
                    audit_state="STRICT_FAITHFUL" if strict else ("UNFAITHFUL" if not any(flags) else "AUDIT_DISAGREEMENT")
                rec=recover_by.get(f["run_id"]);world=worlds[f["world_id"]]
                recovery_valid=bool(rec and rec["final_status"]=="VALID")
                cra=recovery_accuracy(rec["recovered"],world) if recovery_valid else None
                full=bool(recovery_valid and full_structure_retained(rec["recovered"],world))
                labels=[x for x in down_by.get(f["run_id"],[]) if x["final_status"]=="VALID" and x.get("prediction")]
                diffs=[]
                for row in labels:
                    a,b=canonical_probabilities(row["prediction"],row["version"]);diffs.append(a-b)
                pred_diff=safe_mean(diffs) if len(diffs)==2 else None
                predicted="A" if pred_diff is not None and pred_diff>=0 else ("B" if pred_diff is not None else None)
                opt=world["optimal_action"]
                acc=(predicted==opt) if predicted else None
                reg=regret(pred_diff,world) if pred_diff is not None else None
                true_diff=world["target_value"]["A"]-world["target_value"]["B"]
                per_memory.append({"run_id":f["run_id"],"writer":tier,"formation_type":typ,"world_id":f["world_id"],"pair_id":f["pair_id"],
                    "final_formation_status":f["final_status"],"memory_char_length":f.get("memory_char_length"),"faithfulness_status":audit_state,
                    "faithfulness_audits":valid_audits,"strict_faithful":strict,"recovery_valid":recovery_valid,"recovery":rec.get("recovered") if rec else None,
                    "cra":cra,"state_label_retained":bool(recovery_valid and state_label_retained(rec["recovered"],world)),
                    "action_conditional_structure_retained":bool(recovery_valid and action_conditional_structure_retained(rec["recovered"],world)),
                    "full_structure_retained":full,"downstream_valid_calls":len(labels),"predicted_difference":pred_diff,"predicted_action":predicted,
                    "optimal_action":opt,"decision_accuracy":acc,"regret":reg,"signed_preference_error":pred_diff-true_diff if pred_diff is not None else None})
            selected_records=[r for r in per_memory if r["formation_type"]==typ]
            generated=len(selected);valid_form=sum(x["final_status"]=="VALID" for x in selected)
            stricts=[r for r in selected_records if r["strict_faithful"]]
            strict_n=len(stricts);recs=[r for r in stricts if r["cra"] is not None]
            downs=[r for r in selected_records if r["decision_accuracy"] is not None]
            bypair=collections.defaultdict(list)
            for r in selected_records:bypair[r["pair_id"]].append(r)
            pair_classes={"PAIR_BOTH_SUFFICIENT":0,"PAIR_ONE_SUFFICIENT":0,"PAIR_BOTH_INSUFFICIENT":0}
            pair_res=[];pair_resolution_rows={}
            for pid,rs in bypair.items():
                rs=sorted(rs,key=lambda z:z["world_id"])
                if len(rs)!=2:continue
                retained=[x["full_structure_retained"] for x in rs]
                label="PAIR_BOTH_SUFFICIENT" if all(retained) else ("PAIR_ONE_SUFFICIENT" if any(retained) else "PAIR_BOTH_INSUFFICIENT")
                pair_classes[label]+=1
                if all(x["decision_accuracy"] is not None for x in rs):
                    resolved=all(x["decision_accuracy"] for x in rs);pair_res.append(resolved)
                    pair_resolution_rows[pid]={"both_insufficient":not any(retained),"resolved":bool(resolved)}
            strict_n=max(1,strict_n)
            formation_summaries[typ]={"n_generated":generated,"n_valid_formation":valid_form,"formation_valid_rate":valid_form/generated if generated else None,
                "n_strict_faithful":len(stricts),"faithfulness_rate":len(stricts)/generated if generated else None,
                "audit_disagreement":sum(r["faithfulness_status"]=="AUDIT_DISAGREEMENT" for r in selected_records),
                "audit_invalid":sum(r["faithfulness_status"]=="AUDIT_INVALID" for r in selected_records),
                "mean_cra_strict":safe_mean([r["cra"] for r in recs]),
                "full_structure_retained_rate_strict":safe_mean([float(r["full_structure_retained"]) for r in recs]),
                "fbir":sum(not r["full_structure_retained"] for r in recs)/len(recs) if recs else None,
                "mean_cra_all":safe_mean([r["cra"] for r in selected_records if r["cra"] is not None]),
                "state_label_retained_rate_strict":safe_mean([float(r["state_label_retained"]) for r in recs]),
                "action_conditional_structure_retained_rate_strict":safe_mean([float(r["action_conditional_structure_retained"]) for r in recs]),
                "decision_accuracy":safe_mean([float(r["decision_accuracy"]) for r in downs]),
                "regret":safe_mean([r["regret"] for r in downs]),
                "signed_preference_error":safe_mean([r["signed_preference_error"] for r in downs if r["signed_preference_error"] is not None]),
                "pair_resolution_rate":safe_mean([float(x) for x in pair_res]),"pair_resolution_n":len(pair_res),
                "pair_classes":pair_classes,"pair_both_insufficient_rate":pair_classes["PAIR_BOTH_INSUFFICIENT"]/20}
        # Retention/regret association among strict faithful records.
        strict_records=[r for r in per_memory if r["strict_faithful"] and r["cra"] is not None and r["regret"] is not None]
        cluster=collections.defaultdict(list)
        for r in strict_records:cluster[r["world_id"]].append({"full":r["full_structure_retained"],"regret":r["regret"]})
        retention=boot_diff_world(cluster)
        by_world=collections.defaultdict(list)
        for r in strict_records:by_world[r["world_id"]].append(r)
        cvals=[];rvals=[]
        for wid,rs in by_world.items():
            cvals.append(safe_mean([x["cra"] for x in rs]));rvals.append(safe_mean([x["regret"] for x in rs]))
        rho=float(spearmanr(cvals,rvals).statistic) if len(cvals)>2 and len(set(cvals))>1 and len(set(rvals))>1 else None
        tier_stats[tier]={"formation_types":formation_summaries,"retention_vs_regret":retention,"cra_regret_spearman_rho":rho,
                          "n_strict_faithful_world_memories":len(strict_records),"n_strict_faithful_worlds":len(by_world)}
        tier_records[tier]=per_memory
        expected=160
        formation_valid_total=sum(x["final_status"]=="VALID" for x in forms)
        completeness[tier]={"formation_planned":expected,"formation_valid":formation_valid_total,"faithfulness_expected":formation_valid_total*2,
            "faithfulness_valid":sum(x["final_status"]=="VALID" for x in faithful),"recovery_expected":formation_valid_total,
            "recovery_valid":sum(x["final_status"]=="VALID" for x in recovery),"downstream_expected":formation_valid_total*2,
            "downstream_valid":sum(x["final_status"]=="VALID" for x in downstream)}
    calibration=json.loads((ROOT/"results"/"recovery_calibration.json").read_text())
    control_down=json.loads((ROOT/"results"/"downstream_controls.json").read_text())
    control_metrics={}
    for condition in ["C1_StatePreservingOracle","C2_FaithfulLossyAggregate"]:
        group=[r for r in control_down if r["condition"]==condition and r["final_status"]=="VALID"]
        by_world=collections.defaultdict(list)
        for row in group:
            a,b=canonical_probabilities(row["prediction"],row["version"]);by_world[row["world_id"]].append(a-b)
        metrics=[]
        for wid,diffs in by_world.items():
            w=worlds[wid];d=safe_mean(diffs);pred="A" if d>=0 else "B"
            metrics.append({"accuracy":pred==w["optimal_action"],"regret":regret(d,w)})
        control_metrics[condition]={"recovery_calibration":calibration[condition],"downstream_accuracy":safe_mean([float(x["accuracy"]) for x in metrics]),
             "downstream_regret":safe_mean([x["regret"] for x in metrics]),"downstream_n":len(metrics),"downstream_valid_calls":len(group)}
    primary=tier_stats["primary"];pforms=primary["formation_types"]
    comp=completeness
    pcomp=comp["primary"]
    valid_rate=lambda key: pcomp[key+"_valid"]/pcomp[key+"_expected"] if pcomp[key+"_expected"] else 0
    g0=all([pcomp["formation_valid"]/160>=.99,valid_rate("faithfulness")>=.99,valid_rate("recovery")>=.99,valid_rate("downstream")>=.99])
    strict_types=sum(pforms[t]["faithfulness_rate"] is not None and pforms[t]["faithfulness_rate"]>=.80 for t in FORMATION_TYPES)
    g2=strict_types>=3
    fbir_types=[t for t in FORMATION_TYPES if pforms[t]["fbir"] is not None and pforms[t]["fbir"]>=.30]
    g3=len(fbir_types)>=2
    g4=sum(pforms[t]["fbir"] is not None and pforms[t]["fbir"]>=.30 and pforms[t]["n_strict_faithful"]>=30 for t in FORMATION_TYPES)>=2
    ret=primary["retention_vs_regret"];g5=ret["ci_low"] is not None and ret["ci_low"]>0
    control_pair_res={}
    for condition in ["C1_StatePreservingOracle","C2_FaithfulLossyAggregate"]:
        byp=collections.defaultdict(dict)
        for row in control_down:
            if row["condition"]!=condition or row["final_status"]!="VALID":continue
            a,b=canonical_probabilities(row["prediction"],row["version"]);byp[row["pair_id"]].setdefault(row["world_id"],[]).append(a-b)
        out={}
        for pid,ws in byp.items():
            ordered=sorted(ws);decisions=[]
            for wid in ordered:
                d=safe_mean(ws[wid]);decisions.append("A" if d>=0 else "B")
            if len(decisions)==2:out[pid]=pair_resolution(decisions[0],decisions[1],worlds[ordered[0]]["optimal_action"],worlds[ordered[1]]["optimal_action"])
        control_pair_res[condition]=out
    g6_types=[];g6_effects={}
    for typ in FORMATION_TYPES:
        fm=pforms[typ]
        resolution={}
        recs=[r for r in tier_records["primary"] if r["formation_type"]==typ]
        byp=collections.defaultdict(list)
        for r in recs:byp[r["pair_id"]].append(r)
        for pid,rs in byp.items():
            rs=sorted(rs,key=lambda x:x["world_id"])
            if len(rs)==2 and all(x["decision_accuracy"] is not None for x in rs):resolution[pid]=all(x["decision_accuracy"] for x in rs)
        eligible=[pid for pid in resolution if fm["pair_classes"]["PAIR_BOTH_INSUFFICIENT"]>0 and all(not x["full_structure_retained"] for x in sorted([r for r in recs if r["pair_id"]==pid],key=lambda x:x["world_id"]))]
        rate=len(eligible)/20
        common=[pid for pid in eligible if pid in control_pair_res["C1_StatePreservingOracle"]]
        diffs={pid:(float(control_pair_res["C1_StatePreservingOracle"][pid]),float(resolution[pid])) for pid in common}
        effect=bootstrap_pair_diff(diffs) if diffs else {"mean":None,"ci_low":None,"ci_high":None,"n":0}
        g6_effects[typ]={"pair_both_insufficient_rate":rate,"n_pairs":len(eligible),"oracle_minus_formation_pair_resolution":effect}
        if rate>=.25 and effect["ci_low"] is not None and effect["ci_low"]>0:g6_types.append(typ)
    g6=len(g6_types)>=2
    secondary= tier_stats["secondary"]["formation_types"]
    g7=any(secondary[t]["fbir"] is not None and secondary[t]["fbir"]>=.25 and secondary[t]["faithfulness_rate"]>=0 for t in FORMATION_TYPES)
    budget=json.loads((ROOT/"cases"/"source_manifest.json").read_text())["memory_budget"]
    all_natural=[f for tier in ["primary","secondary"] for f in all_forms[tier] if f["final_status"]=="VALID"]
    hit_rate=sum((f.get("memory_char_length") or 0)>=.9*budget for f in all_natural)/len(all_natural) if all_natural else 0
    oracle_fit=all(len(__import__("core").oracle_summary(w))<=budget for w in worlds.values())
    cap_confounded=hit_rate>.10
    g8=oracle_fit and not cap_confounded
    rec_cal=calibration
    g1=(rec_cal["C1_StatePreservingOracle"]["mean_cra"]>=.95 and rec_cal["C1_StatePreservingOracle"]["full_retention_rate"]>=.90 and rec_cal["C2_FaithfulLossyAggregate"]["mean_cra"]<=.50)
    gates={"G0":g0,"G1":g1,"G2":g2,"G3":g3,"G4":g4,"G5":g5,"G6":g6,"G7":g7,"G8":g8}
    pipeline_invalid=not g1
    go=all(gates.values())
    strong_signal=g3 or g4 or g5 or g6 or g7
    verdict="STAGE3_RECOVERY_PIPELINE_INVALID" if pipeline_invalid else ("REAL_FORMATION_GO" if go else ("REAL_FORMATION_WEAK" if strong_signal or not g0 or cap_confounded else "REAL_FORMATION_NO_GO"))
    stats={"verdict":verdict,"gates":gates,"primary":primary,"secondary":tier_stats["secondary"],"completeness":completeness,"controls":control_metrics,
      "pair_resolution_vs_oracle":g6_effects,"pair_resolution_control":{k:safe_mean([float(v) for v in x.values()]) for k,x in control_pair_res.items()},
      "memory_budget":{"value":budget,"max_oracle_char_length":json.loads((ROOT/"cases"/"source_manifest.json").read_text())["max_oracle_char_length"],"oracle_all_fit":oracle_fit,"natural_ceiling_hit_rate":hit_rate,"capacity_confounded":cap_confounded},
      "gate_details":{"G2_faithful_types":strict_types,"G3_fbir_types":fbir_types,"G4_types":sum(pforms[t]["fbir"] is not None and pforms[t]["fbir"]>=.30 and pforms[t]["n_strict_faithful"]>=30 for t in FORMATION_TYPES),"G6_types":g6_types,"G7_secondary_types":[t for t in FORMATION_TYPES if secondary[t]["fbir"] is not None and secondary[t]["fbir"]>=.25]},
      "records":tier_records}
    save(ROOT/"results"/"statistics.json",stats)
    save(ROOT/"results"/"formation_results.json",{tier:json.loads((ROOT/"results"/f"formation_{tier}.json").read_text()) for tier in WRITERS})
    save(ROOT/"results"/"faithfulness_audit.json",{tier:json.loads((ROOT/"results"/f"faithfulness_{tier}.json").read_text()) for tier in WRITERS})
    save(ROOT/"results"/"recoverability_audit.json",{"controls":json.loads((ROOT/"results"/"recoverability_controls.json").read_text()),"primary":json.loads((ROOT/"results"/"recoverability_primary.json").read_text()),"secondary":json.loads((ROOT/"results"/"recoverability_secondary.json").read_text())})
    save(ROOT/"results"/"downstream_results.json",{"controls":control_down,"primary":json.loads((ROOT/"results"/"downstream_primary.json").read_text()),"secondary":json.loads((ROOT/"results"/"downstream_secondary.json").read_text())})
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    (ROOT/"plots").mkdir(exist_ok=True)
    typ_names=["GenericSummary","ReflectionLesson","StrategyMemory","ConsolidatedExperience"]
    typ_labels=["Generic","Reflection","Strategy","Consolidated"]
    primary=tier_stats["primary"]["formation_types"]
    secondary=tier_stats["secondary"]["formation_types"]
    fig,ax=plt.subplots(figsize=(9,5))
    x=np.arange(4);width=.36
    ax.bar(x-width/2,[primary[t]["faithfulness_rate"] or 0 for t in typ_names],width,label="Primary")
    ax.bar(x+width/2,[secondary[t]["faithfulness_rate"] or 0 for t in typ_names],width,label="Secondary")
    ax.set_xticks(x,typ_labels);ax.set_ylim(0,1);ax.set_ylabel("STRICT_FAITHFUL rate");ax.legend();fig.tight_layout();fig.savefig(ROOT/"plots"/"faithfulness_by_formation.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5))
    ax.bar(x-width/2,[primary[t]["full_structure_retained_rate_strict"] or 0 for t in typ_names],width,label="Primary")
    ax.bar(x+width/2,[secondary[t]["full_structure_retained_rate_strict"] or 0 for t in typ_names],width,label="Secondary")
    ax.set_xticks(x,typ_labels);ax.set_ylim(0,1);ax.set_ylabel("Full structure retention among strict faithful");ax.legend();fig.tight_layout();fig.savefig(ROOT/"plots"/"causal_sufficiency_retention.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5))
    ax.bar(x-width/2,[primary[t]["fbir"] or 0 for t in typ_names],width,label="Primary")
    ax.bar(x+width/2,[secondary[t]["fbir"] or 0 for t in typ_names],width,label="Secondary")
    ax.axhline(.30,color="black",linestyle="--",linewidth=.8);ax.set_xticks(x,typ_labels);ax.set_ylim(0,1);ax.set_ylabel("Faithful-but-insufficient rate");ax.legend();fig.tight_layout();fig.savefig(ROOT/"plots"/"faithful_but_insufficient_rate.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5))
    ret=tier_stats["primary"]["retention_vs_regret"]
    ax.bar(["Full structure retained","Structure lost"],[ret.get("retained_regret",0) or 0,ret.get("lost_regret",0) or 0],color=["#009e73","#d55e00"])
    ax.set_ylabel("Mean action value regret");fig.tight_layout();fig.savefig(ROOT/"plots"/"regret_by_retention.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5))
    ax.bar(x-width/2,[primary[t]["pair_resolution_rate"] or 0 for t in typ_names],width,label="Primary")
    ax.bar(x+width/2,[secondary[t]["pair_resolution_rate"] or 0 for t in typ_names],width,label="Secondary")
    ax.set_xticks(x,typ_labels);ax.set_ylim(0,1);ax.set_ylabel("Matched-pair resolution rate");ax.legend();fig.tight_layout();fig.savefig(ROOT/"plots"/"pair_resolution.png",dpi=180);plt.close(fig)
    lines=["# Stage-3 实验结果","",verdict,"","## 环境与完整性","",
      "Python 3.10.21；Primary writer qwen2.5:14b；Secondary writer qwq:32b；reader qwq:32b。模型及 GPU 信息见 results/environment.json。",
      f"输入 20 pairs / 40 worlds，source SHA256 {json.loads((ROOT/'cases'/'source_manifest.json').read_text())['source_sha256']}。MEMORY_BUDGET={budget} 字符，max oracle 长度={stats['memory_budget']['max_oracle_char_length']}，自然输出 ceiling hit rate={hit_rate:.3f}。",
      f"Primary 完整性 formation {comp['primary']['formation_valid']}/160；faithfulness {comp['primary']['faithfulness_valid']}/{comp['primary']['faithfulness_expected']}；recovery {comp['primary']['recovery_valid']}/{comp['primary']['recovery_expected']}；downstream {comp['primary']['downstream_valid']}/{comp['primary']['downstream_expected']}。",
      f"Secondary 完整性 formation {comp['secondary']['formation_valid']}/160；faithfulness {comp['secondary']['faithfulness_valid']}/{comp['secondary']['faithfulness_expected']}；recovery {comp['secondary']['recovery_valid']}/{comp['secondary']['recovery_expected']}；downstream {comp['secondary']['downstream_valid']}/{comp['secondary']['downstream_expected']}。","",
      "## 记忆形成结果","","| Writer | Formation | N generated | Strict faithful | Faithfulness rate | mean CRA | Full retention | FBIR | Accuracy | Regret | Pair resolution |","|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    def ff(v):return "NA" if v is None else f"{v:.4f}"
    for tier,label in [("primary","Primary"),("secondary","Secondary")]:
      for typ in typ_names:
        z=tier_stats[tier]["formation_types"][typ]
        lines.append("| "+label+" | "+typ+" | "+str(z["n_generated"])+" | "+str(z["n_strict_faithful"])+" | "+ff(z["faithfulness_rate"])+" | "+ff(z["mean_cra_strict"])+" | "+ff(z["full_structure_retained_rate_strict"])+" | "+ff(z["fbir"])+" | "+ff(z["decision_accuracy"])+" | "+ff(z["regret"])+" | "+ff(z["pair_resolution_rate"])+" |")
    lines+=["","## Controls","","| Control | CRA | Full retention | Downstream accuracy | Downstream regret |","|---|---:|---:|---:|---:|"]
    for name,z in control_metrics.items():
      lines.append("| "+name+" | "+ff(z["recovery_calibration"]["mean_cra"])+" | "+ff(z["recovery_calibration"]["full_retention_rate"])+" | "+ff(z["downstream_accuracy"])+" | "+ff(z["downstream_regret"])+" |")
    lines+=["","## Faithfulness 与结构恢复","","Primary STRICT_FAITHFUL memory 总数："+str(sum(primary[t]["n_strict_faithful"] for t in typ_names))+"；Faithful-but-insufficient 数量："+str(sum(round((primary[t]["fbir"] or 0)*primary[t]["n_strict_faithful"]) for t in typ_names))+"。FBIR 以各 formation 内 strict faithful 为分母。","",
      "## 结构保留与 regret","","Lost-minus-retained regret difference="+ff(ret["difference"])+"；world-cluster bootstrap 95% CI ["+ff(ret["ci_low"])+", "+ff(ret["ci_high"])+"；CRA/regret world-level Spearman rho="+ff(tier_stats["primary"]["cra_regret_spearman_rho"])+"。","",
      "## Matched pairs","","pair-level both sufficient / one sufficient / both insufficient 分类及 resolution 见 statistics.json。C1 oracle 的 downstream pair resolution="+ff(stats["pair_resolution_control"]["C1_StatePreservingOracle"])+"。","",
      "## Gates","","| Gate | Result |","|---|---|"]
    for gate,passed in gates.items():lines.append("| "+gate+" | "+("PASS" if passed else "FAIL")+" |")
    lines+=["","Run1、Confirmatory、Stage-2 的历史目录及 verdict 未修改。结果只适用于固定 toy worlds、提示和所列模型，不外推至所有 Agent 或真实长期部署。没有查论文、使用 Mem0、设计新方法或执行 Idea 3。",""]
    (ROOT/"Stage3实验结果.md").write_text("\n".join(lines),encoding="utf-8")
    conclusion="# 最终结论\n\n"+verdict+"\n\n"+("所有预注册 G0-G8 均通过。" if verdict=="REAL_FORMATION_GO" else ("Recovery calibration 未通过，无法对 formation 作结论。" if pipeline_invalid else "结果未满足全部 GO 门槛；各项证据与限制见 Stage3实验结果.md。"))+"\n\nPrimary 与 Secondary 分开报告；未根据结果更换模型、提示或样本。已停止本轮。\n"
    (ROOT/"最终结论.md").write_text(conclusion,encoding="utf-8")
    print(json.dumps({"verdict":verdict,"gates":gates,"primary":{k:{"faithfulness_rate":v["faithfulness_rate"],"CRA":v["mean_cra_strict"],"full":v["full_structure_retained_rate_strict"],"FBIR":v["fbir"],"accuracy":v["decision_accuracy"],"regret":v["regret"],"pair_resolution":v["pair_resolution_rate"]} for k,v in pforms.items()},"secondary":{k:{"faithfulness_rate":v["faithfulness_rate"],"CRA":v["mean_cra_strict"],"full":v["full_structure_retained_rate_strict"],"FBIR":v["fbir"],"accuracy":v["decision_accuracy"],"regret":v["regret"],"pair_resolution":v["pair_resolution_rate"]} for k,v in secondary.items()},"controls":control_metrics,"retention_vs_regret":ret,"memory_budget":stats["memory_budget"],"completeness":completeness},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
