import itertools
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from agent_memory.environment import generate
from agent_memory.baselines import candidates, predict
from agent_memory.metrics import evaluate


class PhaseATest(unittest.TestCase):
    def test_reproducible_clean_environment(self):
        x,y=generate(0,0,100,8)
        np.testing.assert_array_equal(x,y)
        self.assertEqual(len(set(x)),1)
        np.testing.assert_array_equal(generate(.2,.3,100,8)[1],generate(.2,.3,100,8)[1])

    def test_all_filters_are_causal(self):
        y=np.array([0,1,1,0,1,0,0])
        for s in candidates()+[dict(kind="bayes",q=.1,r=.2)]:
            for t in range(1,len(y)):
                np.testing.assert_allclose(predict(y,s)[:t],predict(y[:t],s))

    def test_bayes_matches_exhaustive_posterior(self):
        y=[1,0,1,1]
        q,r=.13,.27
        actual=predict(y,dict(kind="bayes",q=q,r=r))
        for t in range(1,len(y)+1):
            total,positive=0.,0.
            for states in itertools.product([0,1],repeat=t):
                weight=.5
                for i,state in enumerate(states):
                    weight *= 1-r if state==y[i] else r
                    if i: weight *= 1-q if state==states[i-1] else q
                total+=weight
                positive+=weight*states[-1]
            self.assertAlmostEqual(actual[t-1],positive/total)

    def test_metrics_false_update_and_censoring(self):
        x=np.array([0,0,0,1,1,0,0])
        y=np.array([0,1,0,1,1,0,0])
        p=np.zeros(7)
        m=evaluate(x,y,p,1)
        self.assertEqual(m["false_update_rate"],0)
        self.assertEqual(m["adaptation_delay_capped"],1)
        self.assertEqual(m["adaptation_censored_rate"],.5)
        self.assertEqual(m["stale_reuse_proxy"],.5)
        p[1]=1
        self.assertEqual(evaluate(x,y,p,1)["false_update_rate"],1)

    def test_undefined_events_are_missing(self):
        m=evaluate(np.zeros(5),np.zeros(5),np.zeros(5),1)
        self.assertIsNone(m["false_update_rate"])
        self.assertIsNone(m["adaptation_delay_capped"])

    def test_uninformative_observations_preserve_uniform_belief(self):
        np.testing.assert_allclose(predict([1,1,0,1,0],dict(kind="bayes",q=.2,r=.5)),.5)

    def test_configuration_rejects_leaked_seeds(self):
        import importlib.util
        import json
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location("runner",root/"scripts/run_phase_a.py")
        runner=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        config=json.loads((root/"configs/smoke.json").read_text())
        config["validation_seeds"]=config["test_seeds"]
        with self.assertRaises(ValueError): runner.validate(config)


if __name__=="__main__": unittest.main()
