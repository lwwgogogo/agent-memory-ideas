import datetime,json,sys
from pathlib import Path
from core import ROOT,PRIMARY_WRITER,SECONDARY_WRITER,READER,OPTIONS_WRITER,OPTIONS_AUDIT,OPTIONS_READER,sha,verify_frozen

def main():
    verify_frozen()
    tests=json.loads((ROOT/"results"/"tests.json").read_text())
    probes=json.loads((ROOT/"results"/"capability_probes.json").read_text())
    if not all(x["supported"] for x in probes):raise RuntimeError("capability schema probe failed")
    manifest=json.loads((ROOT/"cases"/"source_manifest.json").read_text())
    config={"created_before_primary_formation":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "python":sys.version,"executable":sys.executable,"conda_env":"agentmem_lab",
      "primary_writer":PRIMARY_WRITER,"secondary_writer":SECONDARY_WRITER,"downstream_reader":READER,"structural_reader":READER,
      "faithfulness_auditors":{"A":SECONDARY_WRITER,"B":PRIMARY_WRITER},
      "options":{"formation":OPTIONS_WRITER,"faithfulness":OPTIONS_AUDIT,"recovery":{"temperature":0,"top_p":1.0,"seed":20261005,"num_ctx":8192,"num_predict":256},"downstream":{"temperature":0,"top_p":1.0,"seed":20261005,"num_ctx":8192,"num_predict":256}},
      "schemas":{"formation":"one memory string; additionalProperties=false","faithfulness":"four boolean fields; additionalProperties=false","recovery":"eight integer-or-null fields; additionalProperties=false","downstream":"two bounded probability fields; additionalProperties=false"},
      "retry_max":1,"transport_error_reissue":False,"memory_budget":manifest["memory_budget"],"max_oracle_char_length":manifest["max_oracle_char_length"],
      "source_sha256":manifest["source_sha256"],"preregistration_sha256":sha(ROOT/"preregistration.md"),
      "test_manifest":tests["source_sha256"],"capability_probes":probes,
      "planned":{"formation_per_writer":160,"faithfulness_calls_per_writer":320,"recovery_calls_per_writer":160,"downstream_calls_per_writer":320,"primary_plus_secondary_formations":320}}
    (ROOT/"results"/"config.json").write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"config_frozen":True,"memory_budget":config["memory_budget"],"primary":config["primary_writer"],"secondary":config["secondary_writer"],"reader":config["downstream_reader"],"source_sha256":config["source_sha256"],"preregistration_sha256":config["preregistration_sha256"]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
