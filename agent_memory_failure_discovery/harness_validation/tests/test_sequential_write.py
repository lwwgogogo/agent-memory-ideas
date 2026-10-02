import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from run_validation import turns
def test_c4_order(): assert turns({'family':'C4','raw_history':''})==['用户以前使用模型 A。','上周已经迁移到模型 B。','当前配置是模型 B。']
def test_c8_order(): assert len(turns({'family':'C8','raw_history':''}))==3
