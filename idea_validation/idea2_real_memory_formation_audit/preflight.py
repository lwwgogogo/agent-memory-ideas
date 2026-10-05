import hashlib,json,subprocess,sys
from pathlib import Path
from core import ROOT,sha

def main():
    result=subprocess.run([sys.executable,"-m","pytest","-q","tests"],cwd=ROOT,capture_output=True,text=True)
    (ROOT/"results"/"pytest_output.txt").write_text(result.stdout+result.stderr,encoding="utf-8")
    print(result.stdout+result.stderr)
    if result.returncode: raise SystemExit(result.returncode)
    sources=["core.py","formation_prompts.py","generate_source_cases.py","run_formation.py","audit_faithfulness.py","audit_recoverability.py","run_downstream.py","evaluate.py","tests/test_stage3.py","preregistration.md","cases/source_worlds.json","cases/source_manifest.json"]
    metadata={"returncode":result.returncode,"source_sha256":{x:sha(ROOT/x) for x in sources},"python":sys.executable,"version":sys.version,"stage2_source_sha256":sha(ROOT.parents[1]/"idea_validation"/"idea2_causal_sufficiency"/"cases.json")}
    (ROOT/"results"/"tests.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"returncode":result.returncode,"test_output":result.stdout.strip(),"source_files":len(sources),"python":sys.version.split()[0]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
