"""Primary runner: upstream get_top_episodes returns every analyzed episode."""
import json
from common import ROOT,GAMMAS,SEEDS,KS,canonical,assert_ready
from build_exact_logs import load,multiset_hash,order_hash
from adapters.native_loaders import jitrl,fingerprint
from adapters.objects import episodes
from native_metrics import parse,selection,ties
def run():
    assert_ready();native=jitrl();fn=native.get_top_episodes;origin=fingerprint(fn)
    path=ROOT/'results/jitrl_native_raw.jsonl'
    with path.open('x') as f:
        for g in GAMMAS:
            for policy in ('P','Q'):
                for seed in SEEDS:
                    rows=load(g,policy,seed);objects=episodes(rows)
                    for k in KS:
                        # Sole production call that chooses/orders returned episodes.
                        returned=fn(objects,top_k=k)
                        assert len(returned)==k
                        assert all(any(x is y for y in objects) for x in returned)
                        parsed=parse('jitrl',returned)
                        record={'system':'jitrl','gamma':g,'policy':policy,'seed':seed,'k':k,
                            'input_multiset_sha256':multiset_hash(rows),'input_order_sha256':order_hash(rows),
                            'native_function':origin,'native_return':returned,
                            'parsed_selection':parsed,'metrics':selection(parsed),
                            'tie_audit':ties([x['final_score'] for x in returned],[x['final_score'] for x in objects])}
                        f.write(canonical(record)+'\n')
    return path
if __name__=='__main__':print(run())
