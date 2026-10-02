import itertools
import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from agent_memory.online import model_average
from agent_memory.baselines import predict


class OnlineTest(unittest.TestCase):
    def test_joint_enumeration(self):
        qs,rs=[.03,.3],[.1,.4]
        y=[0,1,1,0]
        actual, diag=model_average(y,qs,rs)
        previous_evidence=1.
        for t in range(1,len(y)+1):
            total=positive=q_sum=r_sum=0.
            for q,r in itertools.product(qs,rs):
                for states in itertools.product([0,1],repeat=t):
                    mass=.5/(len(qs)*len(rs))
                    for i,x in enumerate(states):
                        mass*=1-r if x==y[i] else r
                        if i: mass*=1-q if x==states[i-1] else q
                    total+=mass
                    positive+=mass*states[-1]
                    q_sum+=mass*q
                    r_sum+=mass*r
            self.assertAlmostEqual(actual[t-1],positive/total)
            self.assertAlmostEqual(diag[t-1]['q_mean'],q_sum/total)
            self.assertAlmostEqual(diag[t-1]['r_mean'],r_sum/total)
            self.assertAlmostEqual(diag[t-1]['predictive_nll'],-np.log(total/previous_evidence))
            previous_evidence=total

    def test_single_model_and_causality(self):
        y=[0,0,1,0,1,1]
        a,_=model_average(y,[.1],[.2])
        np.testing.assert_allclose(a,predict(y,dict(kind='bayes',q=.1,r=.2)))
        for t in range(1,len(y)):
            np.testing.assert_allclose(model_average(y,[.01,.2],[0,.4])[0][:t],
                                       model_average(y[:t],[.01,.2],[0,.4])[0])

    def test_long_sequence_numerical_stability(self):
        a,d=model_average([0,1]*3000,[0,.001,.5],[0,.2,.5])
        self.assertTrue(np.isfinite(a).all())
        self.assertTrue(((a>=0)&(a<=1)).all())
        self.assertTrue(np.isfinite(d[-1]['predictive_nll']))


if __name__=='__main__': unittest.main()
