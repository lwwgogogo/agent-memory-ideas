"""Evaluator-side launcher. Never copied into the scientific candidate."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE=Path(__file__).resolve().parent
REPO=BASE.parents[1]
LEGACY=BASE.parent/"idea2_cross_policy_certification_hardening"
ENV={"PATH":str(Path(sys.executable).parent)+":/usr/bin:/bin",
     "LANG":"C.UTF-8","LC_ALL":"C.UTF-8","OPENBLAS_NUM_THREADS":"1",
     "OMP_NUM_THREADS":"1","PYTHONHASHSEED":"0"}
CANDIDATE_FILES=("transfer_probe.py","schema.py","policy_geometry.py","baselines.py")

def sha_bytes(data): return hashlib.sha256(data).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def _copy(src,dst,manifest):
    shutil.copyfile(src,dst)
    if sha(src)!=sha(dst): raise RuntimeError("copy hash mismatch")
    manifest[str(src.relative_to(REPO))]=sha(src)

def launch(source_bytes,target_bytes=None,official=False):
    with tempfile.TemporaryDirectory(prefix="envelope_") as tmp:
        root=Path(tmp);copies={}
        if official:
            for p in sorted((LEGACY/"candidate").glob("*.py")): _copy(p,root/p.name,copies)
            _copy(LEGACY/"public_config.json",root/"public_config.json",copies)
            (root/"input.jsonl").write_bytes(source_bytes)
            args=[sys.executable,"-I","-B",str(root/"cli.py"),"input.jsonl","output.json"]
        else:
            for name in CANDIDATE_FILES: _copy(BASE/name,root/name,copies)
            _copy(LEGACY/"candidate/boundary.py",root/"boundary.py",copies)
            _copy(LEGACY/"public_config.json",root/"global_config.json",copies)
            package=root/"global_candidate";package.mkdir()
            for p in sorted((LEGACY/"candidate").glob("*.py")):
                _copy(p,package/p.name,copies)
            (root/"source.jsonl").write_bytes(source_bytes)
            (root/"target.jsonl").write_bytes(target_bytes)
            args=[sys.executable,"-I","-B",str(root/"transfer_probe.py"),
                  "source.jsonl","target.jsonl","output.json"]
        process=subprocess.run(args,cwd=root,env=ENV,capture_output=True,text=True,timeout=60)
        result={"returncode":process.returncode,"stderr":process.stderr,
                "source_copy_hash_match":True,"copied_hashes":copies,
                "arguments":[Path(args[3]).name,*args[4:]],"environment_keys":sorted(ENV)}
        if process.returncode==0:
            raw=(root/"output.json").read_bytes()
            output=json.loads(raw)
            audit=output["execution_audit"]
            result.update(output=output,output_sha256=sha_bytes(raw),
               environment_isolation_pass=audit["environment_keys"]==sorted(ENV),
               filesystem_isolation_pass=all(not p.startswith("/") and ".." not in p.split("/")
                                            for p in audit["read_paths"]))
        return result

def success(result):
    if result["returncode"]!=0: raise RuntimeError(result["stderr"])
    return result["output"]

def denial_probe():
    with tempfile.TemporaryDirectory(prefix="envelope_denial_") as tmp:
        root=Path(tmp)
        shutil.copyfile(LEGACY/"candidate/boundary.py",root/"boundary.py")
        code=("from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path.cwd()))\n"
              "from boundary import install\ninstall(Path.cwd(),'output.json')\n"
              "try:\n Path('/etc/hostname').read_text()\n"
              "except PermissionError:\n print('DENIED')\n"
              "else:\n raise RuntimeError('read allowed')\n")
        r=subprocess.run([sys.executable,"-I","-B","-c",code],cwd=root,env=ENV,
                         capture_output=True,text=True,timeout=10)
        return r.returncode==0 and r.stdout.strip()=="DENIED"
