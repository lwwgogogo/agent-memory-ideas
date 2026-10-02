from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from run_validation import gold
def test_gold_has_no_answer_fields():
    text=gold({'family':'C1'})+gold({'family':'C1'},True); assert 'correct_answer' not in text and 'choice' not in text
def test_gold_is_structured_not_answer_field(): assert 'preference=' in gold({'family':'C1'},True) and 'correct_answer' not in gold({'family':'C1'})
