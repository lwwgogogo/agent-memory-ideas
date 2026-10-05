#!/usr/bin/env python3
"""Deterministic source scanner: keyword hits are candidates, not conclusions."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TERMS=['memory','experience','trajectory','reward','return','utility','value','advantage','score','success','failure','retrieve','retrieval','rank','priority','policy','probability','propensity','importance','counterfactual','reflection','lesson','strategy']
SKIP={'third_party','.git','node_modules','.venv','venv','__pycache__','data','datasets','assets','logs','outputs'}
EXT={'.py','.js','.ts','.tsx','.jsx','.java','.go','.rs','.cpp','.h','.md','.yaml','.yml'}
def scan_repo(system,path):
 hits=[]
 for p in Path(path).rglob('*'):
  if not p.is_file() or p.suffix.lower() not in EXT or any(part in SKIP for part in p.parts):continue
  try:lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
  except OSError:continue
  symbol=''
  for i,line in enumerate(lines):
   m=re.match(r'\s*(?:async\s+)?(?:def|class|function)\s+([A-Za-z_]\w*)|\s*([A-Za-z_]\w*)\s*[:=]\s*function',line)
   if m:symbol=next(x for x in m.groups() if x)
   lower=line.lower();matched=[t for t in TERMS if re.search(r'(?<![a-z])'+re.escape(t)+r'(?![a-z])',lower)]
   if matched:
    hits.append({'file':str(p.relative_to(path)),'line_start':i+1,'line_end':i+1,'symbol':symbol or None,'matched_terms':matched,'snippet':line.strip()[:500]})
 out=ROOT/'results'/'static_hits'/f'{system}.json';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps({'system':system,'source_root':str(path),'candidate_hit_count':len(hits),'hits':hits},ensure_ascii=False,indent=2)+'\n')
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('system',nargs='?');args=ap.parse_args()
 systems=[args.system] if args.system else [p.name for p in (ROOT/'third_party').iterdir() if p.is_dir()]
 for sid in systems:
  p=ROOT/'third_party'/sid
  if p.exists():print(scan_repo(sid,p))
if __name__=='__main__':main()
