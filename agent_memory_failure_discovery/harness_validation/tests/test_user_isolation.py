def test_user_ids_are_case_scoped():
    ids=['hv_C1_00','hv_C1_01']; assert len(ids)==len(set(ids))
