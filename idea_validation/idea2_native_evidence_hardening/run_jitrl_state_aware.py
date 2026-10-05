"""Fail-closed boundary: no embeddings, vectors, providers or native retrieval are mocked."""
import json
from common import ROOT,save
from inspect_state_aware_paths import inspect_paths
def run():
    info=inspect_paths()
    if info['status']=='FULL_STATE_AWARE_BLOCKED_BY_DEPENDENCY':
        out={'status':'BLOCKED','detail_status':info['status'],
             'exact_upstream_path_run':False,'reason':info['blocking_reasons'],
             'StateAware_RCD_S0':None,'StateAware_RCD_S1':None,'mitigation_ratio':None,
             'replacement_embeddings_used':False,'provider_calls':0,
             'claim_scope':'Only global episode ranking / value-based selection components have dynamic evidence.'}
        save(ROOT/'results/jitrl_state_aware_results.json',out)
        return out
    raise RuntimeError('Dependencies changed after preflight; do not fabricate a state-aware run or reuse blocked result.')
if __name__=='__main__':print(json.dumps(run(),indent=2))
