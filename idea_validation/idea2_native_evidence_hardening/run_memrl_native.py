"""Native update and selection; action-bank average utility does not exist here."""
import random
from dataclasses import asdict
from common import ROOT,GAMMAS,SEEDS,KS,canonical,sha,assert_ready
from build_exact_logs import load,multiset_hash,order_hash
from adapters.native_loaders import memrl,fingerprint
from adapters.objects import storage,candidates
from native_metrics import parse,selection,ties
def prepare(rows):
    native=memrl()
    # Same fixed controlled-greedy configuration as Stage-4; upstream default epsilon is 0.1.
    # All other fields retain defaults. No semantic retrieval or embedding is simulated.
    cfg=native.RLConfig(epsilon=0.0)
    mos=storage(rows)
    updater=native.QValueUpdater(mos,'audit',cfg,default_cube_id='audit')
    for r in rows:
        updater.update(r['id'],cfg.success_reward if r['outcome'] else cfg.failure_reward)
    return native.ValueAwareSelector(cfg),candidates(rows,mos),cfg
def run():
    assert_ready();native=memrl()
    origin={'update':fingerprint(native.QValueUpdater.update),'select':fingerprint(native.ValueAwareSelector.select)}
    path=ROOT/'results/memrl_native_raw.jsonl'
    with path.open('x') as f:
        for g in GAMMAS:
            for policy in ('P','Q'):
                for seed in SEEDS:
                    rows=load(g,policy,seed)
                    selector,bank,cfg=prepare(rows)
                    for k in KS:
                        random.seed(seed)
                        returned=selector.select(bank,top_k=k)
                        assert len(returned['selected'])==k
                        parsed=parse('memrl',returned)
                        # Preserve COMPLETE selected list/actions/simmax; the 2000-element
                        # native candidate ranking is committed by hash/count, not repeated.
                        compact={key:returned[key] for key in ('selected','actions','simmax')}
                        record={'system':'memrl','gamma':g,'policy':policy,'seed':seed,'k':k,
                            'input_multiset_sha256':multiset_hash(rows),'input_order_sha256':order_hash(rows),
                            'native_functions':origin,'configuration':asdict(cfg),'update_calls':len(rows),
                            'native_return':compact,'native_candidate_count':len(returned['candidates']),
                            'native_candidates_sha256':sha(canonical(returned['candidates']).encode()),
                            'parsed_selection':parsed,'metrics':selection(parsed),
                            'tie_audit':ties([x['metadata']['q_value'] for x in returned['selected']],
                                            [x['metadata']['q_value'] for x in returned['candidates']])}
                        f.write(canonical(record)+'\n')
    return path
if __name__=='__main__':print(run())
