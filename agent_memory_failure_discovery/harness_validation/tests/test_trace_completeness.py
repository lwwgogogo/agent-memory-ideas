def validate_trace(trace):
    turns=trace.get('turns',[]); assert len(turns)==len([x for x in turns if 'add_return' in x])
    uid=trace.get('user_id')
    if uid is not None:
        for t in turns: assert t.get('user_id',uid)==uid
    for t in turns: assert 'memory_after_turn' in t
    assert 'normal_search_query' in trace and 'normal_search_result' in trace
def test_complete_synthetic_trace():
    validate_trace({'user_id':'u','turns':[{'add_return':{},'memory_after_turn':[]}],'normal_search_query':'q','normal_search_result':[]})
def test_o2_ids_subset():
    t={'final_memories':[{'id':'m1'}],'o2_item_ids':['m1']}; assert set(t['o2_item_ids']) <= {x['id'] for x in t['final_memories']}
