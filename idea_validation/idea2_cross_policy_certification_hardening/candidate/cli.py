import json
import os
import sys
from pathlib import Path

def main():
    if len(sys.argv)!=3 or sys.argv[1]!="input.jsonl" or sys.argv[2]!="output.json":
        raise ValueError("exactly two fixed anonymous input/output paths are required")
    root=Path(__file__).resolve().parent
    if Path.cwd().resolve()!=root:
        raise ValueError("unexpected working directory")
    sys.path.insert(0,str(root))
    from boundary import install
    reads=install(root,"output.json")
    from schema import read_records
    from policy_profile import reconstruct,pair_distances,diversity
    from certification import certify
    from baselines import observed_baselines
    config=json.loads((root/"public_config.json").read_text(encoding="utf-8"))
    cells,profiles,gaps,count=reconstruct(read_records("input.jsonl"))
    pairs=pair_distances(profiles); div=diversity(pairs)
    result={**div,**certify(profiles,gaps,pairs,div,config),
            **observed_baselines(cells,gaps,count,config["epsilon"]),
            "profile":profiles,"gaps":gaps,"cells":cells}
    result["execution_audit"]={"environment_keys":sorted(os.environ),
        "initial_files":sorted(p.name for p in root.iterdir()),
        "read_paths":sorted(reads)}
    Path("output.json").write_text(json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
