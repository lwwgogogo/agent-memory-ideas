import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from agent_memory.online import model_average
from agent_memory.research_io import ci,contrasts


class DiagnosticsTest(unittest.TestCase):
    def test_prior_weighted_joint_posterior(self):
        # With one observation all model evidences are .5: posterior weights unchanged.
        p,d=model_average([1],[.1,.2],[.1,.4],prior_weights=[1,2,3,4])
        self.assertAlmostEqual(p[0],(.9+2*.6+3*.9+4*.6)/10)
        self.assertAlmostEqual(d[0]['q_mean'],.17)

    def test_forgetting_one_preserves_existing_api(self):
        a=model_average([1,0,0,1],[.01,.1],[.1,.4])[0]
        b=model_average([1,0,0,1],[.01,.1],[.1,.4],forgetting=1)[0]
        np.testing.assert_array_equal(a,b)

    def test_paired_ci_zero(self):
        rows=[dict(seed=s,method=m,accuracy=.5+s*.01) for s in range(5) for m in ['oracle_qr','base']]
        r=contrasts(rows,[],['accuracy'],100)[0]
        self.assertEqual((r['mean'],r['ci_low'],r['ci_high']),(0,0,0))
        self.assertEqual(ci([],100)['n'],0)


if __name__=='__main__': unittest.main()
