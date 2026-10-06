"""Deterministic reporting/plots; never part of candidate."""
import json
from fractions import Fraction
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCOPE="""本轮只构造 target-relative matched counterexamples，表明 global/source-only evidence summary 不足以表达当前 probe 的 transfer decision。
Convex hull 是 minimal diagnostic probe，不证明其最佳或方法新颖性。
Inside hull 不意味着 causal safety；outside hull 不意味着一定不能 transfer。
本轮 invariant world 中 OUT 的真实 utility gap 也为 +.40；没有验证实际迁移失败或安全收益。
不排除 target-aware uncertainty、provenance、boundary-aware reuse、ICP/OPE 或 support geometry 方法表达同类决策。"""

def scope_ok():
    return all(term in SCOPE for term in ("minimal diagnostic probe","不证明","不意味着 causal safety",
                                         "不意味着一定不能 transfer","不排除 target-aware"))

def point(values): return [float(Fraction(v)) for v in values]
def panel(ax,row,title):
    out=row["probe"]
    points=[point(v) for v in out["source_policy_vectors"].values()]
    target=point(out["target_policy_vector"])
    # Display the fixed three source vertices only; decision was computed by LP.
    xy=points+[points[0]]
    ax.plot([p[0] for p in xy],[p[1] for p in xy],color="#236B8E",lw=2)
    ax.fill([p[0] for p in points],[p[1] for p in points],color="#91CAE0",alpha=.35)
    ax.scatter(*zip(*points),color="#236B8E",s=48,label="Source (observed)")
    ax.scatter([target[0]],[target[1]],marker="*",s=170,color="#D8573C",label="Target (observed)")
    ax.set(xlim=(0,1),ylim=(0,1),xlabel="P(A | S0)",ylabel="P(A | S1)",title=title)
    ax.set_aspect("equal");ax.grid(alpha=.18)

def render(base,rows,gates,decision):
    base=Path(base);plots=base/"plots";plots.mkdir(exist_ok=True)
    fig,axs=plt.subplots(2,2,figsize=(9,8),constrained_layout=True)
    for ax,row in zip(axs.flat,[rows[0],rows[1],rows[6],rows[7]]):
        panel(ax,row,row["pair"]+" "+row["side"]+" — "+row["probe"]["interpolation_diagnostic"])
    fig.suptitle("Target-relative support geometry (diagnostic only)")
    fig.savefig(plots/"policy_geometry_pairs.png",dpi=150);plt.close(fig)
    for filename,selected,title in [
      ("target_inside_outside.png",rows[:2],"Same source evidence, different targets"),
      ("nearest_distance_counterexample.png",rows[6:],"Same target and nearest TV = 0.10, different hull membership")]:
        fig,axs=plt.subplots(1,2,figsize=(9,4.5),constrained_layout=True)
        for ax,row in zip(axs,selected): panel(ax,row,row["side"])
        axs[0].legend(loc="upper left",fontsize=8);fig.suptitle(title)
        fig.savefig(plots/filename,dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,3),constrained_layout=True)
    matrix=[]
    for i in range(0,8,2):
        a,b=rows[i]["probe"],rows[i+1]["probe"]
        matrix.append([int(a["global"]["status"]!=b["global"]["status"]),
          int(a["source_summary_sha256"]!=b["source_summary_sha256"]),
          int(a["provenance_summary_sha256"]!=b["provenance_summary_sha256"]),
          int(a["target_min_TV_exact"]!=b["target_min_TV_exact"]),
          int(a["transfer_decision"]!=b["transfer_decision"])])
    ax.imshow(matrix,cmap=matplotlib.colors.ListedColormap(["#D5D8DC","#F3D5A2","#6CBF9D"]),vmin=-1,vmax=1,aspect="auto")
    ax.set_xticks(range(5),["Global","Source summary","Provenance","Nearest TV","Envelope"])
    ax.set_yticks(range(4),["P1","P2","P3","P4"])
    for i,row in enumerate(matrix):
        for j,value in enumerate(row):
            label="different" if value==1 else "not matched" if value==-1 else "same"
            ax.text(j,i,label,ha="center",va="center",fontsize=9)
    ax.set_title("Information projections: same vs different (not accuracy)")
    fig.savefig(plots/"reduction_summary.png",dpi=150);plt.close(fig)
    lines=["# Stage-6C 实验结果", "", "## 背景与对象",
      "Stage-6B保持STAGE6B_NARROW。U1为漂移/不变性化约，U2为已有使用门控替换证据，U3为证据感知confidence/support化约。本轮从C(m)改为C(m,b*)，只测试固定信息投影的可区分性，未消除所有target-aware近邻风险。",
      "", "## 输入、认证与probe",
      "source只含era_id/state/action/outcome，target只含state/action。每state1000计数恢复二维descriptor；不输入构造参数。复用冻结Stage6A.1代码，并与原CLI逐字段比较。PRESCRIPTIVE之后用HiGHS等式可行性判断凸支持，残差1e-10；独立Fraction仿射消元枚举最多3顶点核验geometry。",
      "", "## 配对结果", "| Pair | Side | Target | Global | Nearest TV | Hull | Transfer |",
      "|---|---|---|---|---|---|---|"]
    for r in rows:
        o=r["probe"]
        lines.append("| "+" | ".join([r["pair"],r["side"],str(o["target_policy_vector"]),
          o["global"]["status"],o["target_min_TV_exact"],str(o["target_in_convex_hull"]),o["transfer_decision"]])+" |")
    lines += ["", "## P1：invariance reduction","相同source SHA、global和M1，target位置不同。B0/B1不读取target，所以相同；probe的IN/OUT不同。",
      "## P2：provenance reduction","固定source provenance SHA相同，probe不同。只排除source-only provenance，不排除target-aware扩展。",
      "## P3：confidence/support reduction","完整source summary及SHA相同：utility/counts/variance/agreement/diversity/global均相同。任何f(S_source)无法区分；不声称所有target-aware uncertainty都不行。",
      "## P4：nearest-distance reduction","两个source set围绕同一target的布局不同。最近TV均为1/10且独立rational验证相等，而凸包成员关系不同。排除nearest-scalar-only规则，不排除完整几何方法。",
      "## M1比较与逻辑边界","所有case逐state标准化得到U(A)=4/5、U(B)=2/5、gap=2/5。M1没有估错；当前不同标签来自支持几何定义。P1/P2/P3重用相同数值，不是三个独立统计重复；不计算p值或假装样本扩张。",
      "## G0–G9","| Gate | Result |","|---|---|"]
    lines += [f"| {k} | {'PASS' if v else 'FAIL'} |" for k,v in gates.items()]
    lines += ["", "## 解释纪律",SCOPE,"", "## 局限",
      "synthetic discrete states；exact counts；known source eras；假设target已有最近trace；观测descriptor不等于真实future policy distribution；无finite-sample noise；无natural-language memory；无automatic era detection；无full-agent integration；无dynamic memory-policy feedback；无method novelty claim；尚未重新审计transportability/support geometry文献。",
      "", "## Verdict",decision,"", "## 下一步与停止",
      "若GO，仅建议针对target-relative transportability、support geometry、multi-logger OPE、boundary-aware reuse和target-aware gating做精确collision audit。本轮不自动查论文，不进入Stage7。"]
    (base/"Stage6C实验结果.md").write_text("\n".join(lines)+"\n")
    (base/"最终结论.md").write_text("# 最终结论\n\n"+decision+"\n\n"+SCOPE+"\n\n历史Stage-6B STAGE6B_NARROW永久保留。本轮停止，不开始后续研究。\n")
