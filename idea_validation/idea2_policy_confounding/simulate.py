import csv,sys,subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT,ensure_environment,save_json
GAMMAS=[.50,.60,.70,.80,.90,.95]
def numerical(gamma):
    # Sum the joint distribution P(X,A,Y) explicitly; state outcome rates do not depend on action.
    joint=np.zeros((2,2,2))
    for state,rate in enumerate([.9,.2]):
        for action,pa in enumerate([gamma if state==0 else 1-gamma,1-gamma if state==0 else gamma]):
            for y,py in enumerate([1-rate,rate]):joint[state,action,y]=.5*pa*py
    obs=[float(joint[:,a,1].sum()/joint[:,a,:].sum()) for a in [0,1]]
    causal=[sum(.5*rate for rate in [.9,.2]) for a in [0,1]]
    return dict(gamma=gamma,observational_success_A=obs[0],observational_success_B=obs[1],observational_gap=obs[0]-obs[1],causal_success_A=causal[0],causal_success_B=causal[1],causal_gap=causal[0]-causal[1])
def analytic(gamma):return .2+.7*gamma,.9-.7*gamma,1.4*gamma-.7

def main():
    ensure_environment();rows=[numerical(g) for g in GAMMAS]
    with (ROOT/'results/simulation.csv').open('w',newline='') as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    for both,name in [(False,'observational_gap_vs_confounding'),(True,'observational_vs_causal_gap')]:
        fig,ax=plt.subplots(figsize=(7.5,4.8))
        ax.plot(GAMMAS,[r['observational_gap'] for r in rows],'o-',label='Observational gap')
        if both:ax.plot(GAMMAS,[r['causal_gap'] for r in rows],'s--',label='Causal gap (ground truth)')
        ax.set(xlabel='Historical policy strength gamma',ylabel='Success probability difference A - B',ylim=(-.03,.68));ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(ROOT/('plots/'+name+'.png'),dpi=180);plt.close(fig)
    test=subprocess.run([sys.executable,'-m','pytest','-q','tests'],cwd=ROOT,text=True,capture_output=True)
    (ROOT/'results/pytest_output.txt').write_text(test.stdout+test.stderr)
    gate='PHASE_A_GO' if test.returncode==0 else 'IDEA2_MATH_NO_GO'
    save_json(ROOT/'results/math_gate.json',{'gate':gate,'pytest_returncode':test.returncode,'python':sys.executable,'version':sys.version,'simulation_rows':len(rows)})
    print(test.stdout);print(gate)
    if test.returncode:raise SystemExit(test.returncode)
if __name__=='__main__':main()
