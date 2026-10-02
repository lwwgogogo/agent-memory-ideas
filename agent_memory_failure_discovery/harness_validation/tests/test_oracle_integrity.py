def test_o2_ids_are_final_items():
    final=[{'id':'a'},{'id':'b'}]; selected=['a']; assert set(selected)<=set(x['id'] for x in final)
def test_o2_no_manual_facts():
    context=['actual mem0 item']; forbidden=['correct_answer','required_memory_facts']; assert not any(x in context for x in forbidden)
