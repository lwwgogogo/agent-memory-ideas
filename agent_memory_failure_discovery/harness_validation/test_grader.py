import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from canonical_grader import parse_choice_strict
def test_json(): assert parse_choice_strict('{"choice":"LOCAL"}',['LOCAL','CLOUD'])[0]=='LOCAL'
def test_think_json(): assert parse_choice_strict('<think>LOCAL</think>\n{"choice":"LOCAL"}',['LOCAL','CLOUD'])[0]=='LOCAL'
def test_prose_not_score(): assert parse_choice_strict('I think CLOUD is discussed but no protocol.', ['LOCAL','CLOUD'])[0] is None
def test_invalid_unresolved(): assert parse_choice_strict('no valid answer', ['LOCAL','CLOUD'])[1]=='unresolved'
