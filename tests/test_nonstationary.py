import itertools
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from agent_memory.nonstationary import generate_scenario,oracle_filter,recovery,event_metrics
from agent_memory.window import sliding_bma
from agent_memory.online import model_average


class NonstationaryTest(unittest.TestCase):
    def test_window_matches_naive_restarts(self):
        y=np.random.default_rng(32).integers(2,size=37)
        q,r=[.001,.1,.5],[0,.2,.5]
        for window in [1,3,10,50]:
            expected=[model_average(y[max(0,t-window+1):t+1],q,r)[0][-1] for t in range(len(y))]
            np.testing.assert_allclose(sliding_bma(y,q,r,window),expected,atol=1e-13)

    def test_window_causality(self):
        y=[1,1,0,0,1,0,1]
        np.testing.assert_allclose(sliding_bma(y,[.1],[.2],3)[:4],sliding_bma(y[:4],[.1],[.2],3))

    def test_schedule_and_pairing(self):
        spec=dict(kind='corruption',q_before=.01,r_before=.05,r_after=.45)
        a=generate_scenario(spec,3000,300)
        b=generate_scenario(spec,3000,300)
        for i in range(4):np.testing.assert_array_equal(a[i],b[i])
        self.assertEqual(np.sum(a[3]==.45),100)
        self.assertTrue(900<=a[4]['change']<=1500)
        control=generate_scenario(dict(kind='control',q_before=.01,r_before=.05),3000,300)
        np.testing.assert_array_equal(a[0],control[0])

    def test_time_varying_oracle_enumeration(self):
        y=[1,0,1,1];q=[.1,.2,.05,.4];r=[.1,.4,.3,.05]
        actual=oracle_filter(y,q,r)
        for n in range(1,5):
            total=positive=0
            for states in itertools.product([0,1],repeat=n):
                w=.5
                for t,x in enumerate(states):
                    w*=1-r[t] if x==y[t] else r[t]
                    if t:w*=1-q[t] if x==states[t-1] else q[t]
                total+=w;positive+=w*states[-1]
            self.assertAlmostEqual(actual[n-1],positive/total)

    def test_recovery_completion_and_censoring(self):
        x=np.zeros(30,dtype=int);p=x.copy();p[5]=1
        self.assertEqual(recovery(p,x,0,30),(16,0))
        self.assertEqual(recovery(p,x,0,8),(8,1))
        d=event_metrics(x,np.zeros(30),dict(change=None,corruption_end=None))
        self.assertIsNone(d['recovery_delay'])


if __name__=='__main__':unittest.main()
