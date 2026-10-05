#!/usr/bin/env python3
"""Discover official repo metadata, attempt shallow git clone, and pin exact source archives."""
from __future__ import annotations
import argparse, datetime as dt, json, shutil, subprocess, tarfile, tempfile, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
THIRD=ROOT/'third_party'
TARGETS=json.loads((ROOT/'results'/'targets.json').read_text()) if (ROOT/'results'/'targets.json').exists() else {}
REPOS={
 'jitrl':('liushiliushi/JitRL','https://arxiv.org/abs/2601.18510',True),
 'memrl':('MemTensor/MemRL','https://arxiv.org/abs/2601.03192',True),
 'reasoningbank':('google-research/reasoning-bank','https://arxiv.org/abs/2509.25140',True),
 'expel':('LeapLabTHU/ExpeL','https://arxiv.org/abs/2308.10144',True),
 'reflexion':('noahshinn/reflexion','https://arxiv.org/abs/2303.11366',True),
}
PAPER_ONLY={'memento':{'paper':'Selective Memory Retention for Long-Horizon LLM Agents','paper_url':'https://arxiv.org/abs/2606.29178','official_repo':None,'status':'OFFICIAL_CODE_NOT_FOUND'}}
def api(url):
 req=urllib.request.Request(url,headers={'User-Agent':'policy-conditioned-memory-audit/1.0','Accept':'application/vnd.github+json'})
 with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fetch',action='store_true');args=ap.parse_args()
 THIRD.mkdir(parents=True,exist_ok=True);records=[]
 for sid,(repo,paper,official) in REPOS.items():
  url='https://github.com/'+repo; started=dt.datetime.now(dt.timezone.utc).isoformat()
  row={'system':sid,'paper_url':paper,'official_repo':url,'official':official,'clone_time_utc':started,'clone_status':'NOT_ATTEMPTED','snapshot_status':'NOT_ATTEMPTED'}
  try:
   meta=api('https://api.github.com/repos/'+repo);branch=meta['default_branch'];commit=api('https://api.github.com/repos/'+repo+'/commits/'+branch)['sha']
   row.update({'paper':meta.get('description') or sid,'default_branch':branch,'commit':commit,'license':(meta.get('license') or {}).get('spdx_id'),'repo_api_confirmed':True})
   if args.fetch:
    dest=THIRD/sid
    if dest.exists():shutil.rmtree(dest)
    proc=subprocess.run(['git','clone','--depth','1',url+'.git',str(dest)],capture_output=True,text=True,timeout=40)
    row['git_clone_exit_code']=proc.returncode
    row['git_clone_stderr']=proc.stderr[-1200:]
    if proc.returncode==0:
     row['clone_status']='GIT_CLONE_SUCCESS';row['commit']=subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD'],text=True).strip()
    else:
     if dest.exists():shutil.rmtree(dest)
     row['clone_status']='GIT_CLONE_FAILED'
     archive_url=f'https://api.github.com/repos/{repo}/tarball/{commit}'
     with tempfile.NamedTemporaryFile(suffix='.tar.gz',delete=False) as tmp: archive=Path(tmp.name)
     try:
      req=urllib.request.Request(archive_url,headers={'User-Agent':'policy-conditioned-memory-audit/1.0'})
      with urllib.request.urlopen(req,timeout=90) as r:archive.write_bytes(r.read())
      dest.mkdir(parents=True)
      with tarfile.open(archive,'r:gz') as tf:
       members=tf.getmembers();top=members[0].name.split('/')[0] if members else ''
       for member in members:
        parts=Path(member.name).parts
        if len(parts)<2:continue
        member.name=str(Path(*parts[1:]))
        if member.name=='.':continue
        target=(dest/member.name).resolve()
        target.relative_to(dest.resolve())
        tf.extract(member,dest)
      row.update({'snapshot_status':'PINNED_API_ARCHIVE_SUCCESS','snapshot_bytes':archive.stat().st_size})
     finally:archive.unlink(missing_ok=True)
  except Exception as e:
   row.update({'metadata_error':type(e).__name__+': '+str(e),'clone_status':'CODE_UNAVAILABLE' if '404' in str(e) else row['clone_status']})
  records.append(row)
 records.extend({'system':k,**v,'official':False,'clone_status':v['status'],'snapshot_status':'NOT_APPLICABLE'} for k,v in PAPER_ONLY.items())
 out={'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'repo_count':len(records),'repositories':records}
 (ROOT/'results'/'repo_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
