from __future__ import annotations
import json, math, shutil
from core import ROOT, STAGE2, make_source_copy, oracle_summary, source_sha, save

def main():
    data=make_source_copy()
    out=ROOT/"cases"/"source_worlds.json"; out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(STAGE2/"cases.json",out)
    lengths=[len(oracle_summary(w)) for w in data["worlds"]]
    max_len=max(lengths)
    budget=max(512,math.ceil(1.25*max_len))
    meta={"source_path":"idea_validation/idea2_causal_sufficiency/cases.json","source_sha256":source_sha(),"copied_sha256":source_sha(),"pairs":20,"worlds":40,"max_oracle_char_length":max_len,"oracle_char_lengths":lengths,"memory_budget":budget,"budget_formula":"max(512, ceil(1.25 * max_oracle_char_length))"}
    save(ROOT/"cases"/"source_manifest.json",meta)
    (ROOT/"cases"/"oracle_examples.json").write_text(json.dumps([{"world_id":w["world_id"],"oracle_summary":oracle_summary(w),"char_length":len(oracle_summary(w))} for w in data["worlds"]],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:meta[k] for k in ["source_sha256","pairs","worlds","max_oracle_char_length","memory_budget"]},indent=2))
if __name__=="__main__":main()
