import sys,random,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.generator import make_episode
from src.identifiability import upper_bound
from src.metrics import scores

class TestCore(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(make_episode(random.Random(1),'S1_single','T0_identity',.4,.5),make_episode(random.Random(1),'S1_single','T0_identity',.4,.5))
    def test_support_metric(self):
        self.assertEqual(scores([0,1],[0,1],4)['f1'],1.0)
    def test_collision_bound(self):
        ub,amb,_=upper_bound([{'observation':'x','support':[0]},{'observation':'x','support':[1]}])
        self.assertEqual(ub,.5); self.assertEqual(amb,1.0)
    def test_hidden_not_observation(self):
        e=make_episode(random.Random(1),'S1_single','T5_multistep',.8,0.0)
        self.assertNotIn('support:',e['observation'])
