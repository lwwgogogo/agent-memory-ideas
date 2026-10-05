import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from private_worlds import CASES, observed_records, generate_cells
from fractions import Fraction

def generate(output_dir, manifest_path):
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    private={"access":"EVALUATOR ONLY","cases":{}}
    for i,(name,table,policies) in enumerate(CASES,1):
        filename=f"case_{i:03d}.jsonl"
        with (output_dir/filename).open("x",encoding="utf-8",newline="\n") as f:
            for record in observed_records(table,policies):
                f.write(json.dumps(record,sort_keys=True,separators=(",",":"))+"\n")
        private["cases"][filename]={"historical_case":name,"policies":policies,
            "cells":list(generate_cells(table,policies)),
            "truth":{a:str(sum(Fraction(1,2)*table[s][a] for s in ("S0","S1"))) for a in ("A","B")}}
    Path(manifest_path).parent.mkdir(parents=True,exist_ok=True)
    Path(manifest_path).write_text(json.dumps(private,sort_keys=True,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    parser.add_argument("--private-manifest",required=True)
    args=parser.parse_args()
    generate(args.output_dir,args.private_manifest)
