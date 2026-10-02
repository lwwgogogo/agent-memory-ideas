import sys,unittest,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1])); from src.run import pair,info
class TestV2(unittest.TestCase):
 def test_balance(self):
  r=random.Random(1); rows=[pair(r,'S1_single','L0_raw','T_full',0),pair(r,'S1_single','L0_raw','T_full',1)]; self.assertEqual([x['label'] for x in rows],[0,1])
 def test_exact_collision(self):
  r=random.Random(1); rows=[pair(r,'S1_single','L5_exact_collision','T_final_only',0),pair(r,'S1_single','L5_exact_collision','T_final_only',1)]; self.assertEqual(info(rows)[2],0.0); self.assertEqual(info(rows)[4],.5)
 def test_entropy(self):
  r=random.Random(1); rows=[pair(r,'S1_single','L0_raw','T_full',0),pair(r,'S1_single','L0_raw','T_full',1)]; self.assertGreater(info(rows)[2],.9)
