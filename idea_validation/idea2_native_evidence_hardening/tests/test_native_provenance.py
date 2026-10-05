from pathlib import Path
import pytest
from adapters.native_loaders import jitrl,memrl,fingerprint,blocked_provider
from adapters.objects import episodes
from native_metrics import parse,selection
from run_memrl_native import prepare
from common import SOURCES,sha
def fixture_rows():
    return [
      {'id':'a0','state':'S0','action':'A','outcome':0},
      {'id':'b1','state':'S1','action':'B','outcome':1},
      {'id':'a1','state':'S0','action':'A','outcome':1},
      {'id':'b0','state':'S1','action':'B','outcome':0}]
def test_jitrl_actual_return_identity_and_stable_ties():
    rows=episodes(fixture_rows());mod=jitrl()
    returned=mod.get_top_episodes(rows,top_k=2)
    assert returned[0] is rows[1] and returned[1] is rows[2]
    assert [x['action'] for x in parse('jitrl',returned)]==['B','A']
    assert [x['native_score'] for x in parse('jitrl',returned)]==[1,1]
    fn=fingerprint(mod.get_top_episodes)
    path=SOURCES/'jitrl/Jericho/src/prompt_update_with_history.py'
    assert Path(fn['file']).resolve()==path.resolve()
    assert fn['file_sha256']==sha(path.read_bytes()) and fn['first_line']==22
def test_memrl_native_update_and_selected_parser():
    selector,bank,cfg=prepare(fixture_rows())
    native=memrl()
    assert type(selector) is native.ValueAwareSelector
    assert selector.select.__func__ is native.ValueAwareSelector.select
    assert cfg.epsilon==0 and cfg.alpha==.1 and cfg.gamma==0 and cfg.recency_boost==0
    assert [c['metadata']['q_value'] for c in bank]==[-.1,.1,.1,-.1]
    before=[dict(c) for c in bank]
    ret=selector.select(bank,2)
    assert [r['memory_id'] for r in ret['selected']]==['b1','a1']
    assert bank==before
    parsed=parse('memrl',ret)
    assert [x['action'] for x in parsed]==['B','A']
    assert [x['state'] for x in parsed]==['S1','S0']
    assert [x['native_score'] for x in parsed]==[.1,.1]
    assert [x['similarity'] for x in parsed]==[.5,.5]
    assert selection(parsed)['SSP']==0
    for fn in [native.ValueAwareSelector.select,native.QValueUpdater.update]:
        assert Path(fingerprint(fn)['file']).resolve()==(SOURCES/'memrl/memrl/service/value_driven.py').resolve()
def test_unused_provider_boundary_fail_closed():
    with pytest.raises(RuntimeError):blocked_provider()
