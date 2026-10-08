import json
from pathlib import Path

from retrieval_probe import run_probe

REPO = Path(__file__).resolve().parents[3]
STAGE8C_VERDICT = REPO / "idea_validation/idea2_jitrl_real_failure/results/final_verification.json"


def test_offline_probe_blocks_on_missing_index():
    payload = run_probe()
    probe = payload["unit_probe"]
    assert payload["verdict"] == "RETRIEVAL_INFRA_BLOCKED"
    assert payload["dependencies"]["faiss_importable"] is False
    assert payload["dependencies"]["openai_api_key2_set"] is False
    assert probe["llm_called"] is False
    assert probe["thresholds_modified"] is False
    assert probe["memory_created"] is True
    assert probe["memory_persisted"] is True
    assert probe["embedding_generated"] is False
    assert probe["index_insertion_called"] is False
    assert probe["index_after"]["history_ntotal"] is None
    assert probe["exact_query_search_executed"] is False
    assert probe["index_unavailable_guard"] is True
    assert probe["final_returned"] == 0
    assert probe["self_retrieval"] == "FAIL"
    assert probe["near_identical_retrieval"] == "NOT_RUN"
    assert payload["stage8c_zero"]["earliest_layer"] == "index_initialization"
    assert all(payload["anchors"].values())


def test_stage8c_verdict_remains_no_go():
    recorded = json.loads(STAGE8C_VERDICT.read_text(encoding="utf-8"))
    assert recorded["final_verdict"] == "REAL_JITRL_FAILURE_NO_GO"
