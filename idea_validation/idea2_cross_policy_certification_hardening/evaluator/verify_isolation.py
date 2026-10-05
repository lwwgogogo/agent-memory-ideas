import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
REPO=BASE.parents[1]
FIELDS={"era_id","state","action","outcome"}
ENV={"LANG":"C.UTF-8","LC_ALL":"C.UTF-8"}
FORBIDDEN=["P95","Q95","R50","P90","P92","W1","W2","W3","W4","gamma",
           "true_propensity","true_utility","ground_truth"]
SAFE_IMPORTS={"json","os","sys","pathlib","re","itertools","statistics",
              "boundary","schema","policy_profile","certification","baselines"}
HISTORY_DIRS=["idea2_policy_confounding","idea2_policy_confounding_confirmatory",
 "idea2_causal_sufficiency","idea2_real_memory_formation_audit","idea2_policy_conditioned_memory_audit",
 "idea2_native_evidence_hardening","idea2_method_viability","idea2_cross_policy_certification"]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()

def write_json(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def history_snapshot():
    out={}
    for name in HISTORY_DIRS:
        for path in sorted((REPO/"idea_validation"/name).rglob("*")):
            rel=str(path.relative_to(REPO))
            if path.is_symlink():out[rel]={"link":os.readlink(path)}
            elif path.is_file():out[rel]={"sha256":sha(path),"size":path.stat().st_size}
    return out

def inspect_sources():
    imports={}; forbidden_imports=[]; forbidden_strings=[]; unsafe_calls=[]
    paths=sorted((BASE/"candidate").glob("*.py"))
    for path in paths:
        source=path.read_text(); tree=ast.parse(source); found=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): found.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom): found.append(node.module or "")
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {"eval","exec","__import__","compile"}:
                unsafe_calls.append({"file":path.name,"call":node.func.id})
        imports[path.name]=sorted(found)
        forbidden_imports.extend({"file":path.name,"module":module} for module in found if module not in SAFE_IMPORTS)
        forbidden_strings.extend({"file":path.name,"token":word} for word in FORBIDDEN if word in source)
    return {"candidate_imports":imports,"forbidden_imports":forbidden_imports,
            "forbidden_strings":forbidden_strings,"unsafe_dynamic_calls":unsafe_calls,
            "candidate_import_isolation_pass":bool(paths) and not forbidden_imports and not unsafe_calls,
            "forbidden_string_audit_pass":bool(paths) and not forbidden_strings}

def check_input(path):
    import re
    count=0; schemas=set(); anonymous=True
    with Path(path).open() as f:
        for line in f:
            row=json.loads(line); count+=1; schemas.add(tuple(sorted(row)))
            if set(row)!=FIELDS or type(row.get("outcome")) is not int or row["outcome"] not in (0,1):
                raise ValueError("invalid export fields/outcome")
            if row.get("state") not in ("S0","S1") or row.get("action") not in ("A","B"):
                raise ValueError("invalid export category")
            anonymous &= type(row["era_id"]) is str and re.fullmatch(r"e[0-9]{3,}",row["era_id"]) is not None
    if not count or not anonymous:raise ValueError("empty export or semantic era")
    return {"path":str(Path(path).relative_to(BASE)),"sha256":sha(path),
            "record_count":count,"schema_fields":sorted(FIELDS),
            "schema_whitelist_pass":schemas=={tuple(sorted(FIELDS))},"anonymous_era_id_pass":anonymous}

def launch(input_path,output_path=None):
    runtime=BASE/"runtime"; runtime.mkdir(exist_ok=True)
    sources=sorted((BASE/"candidate").glob("*.py"))
    with tempfile.TemporaryDirectory(prefix="isolated_",dir=runtime) as directory:
        root=Path(directory)
        for source in sources: shutil.copyfile(source,root/source.name)
        shutil.copyfile(BASE/"public_config.json",root/"public_config.json")
        shutil.copyfile(input_path,root/"input.jsonl")
        initial=sorted(p.name for p in root.iterdir())
        expected=sorted([p.name for p in sources]+["public_config.json","input.jsonl"])
        command=[sys.executable,"-I","-S","-B","cli.py","input.jsonl","output.json"]
        process=subprocess.Popen(command,cwd=root,env=dict(ENV),stdin=subprocess.DEVNULL,close_fds=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        stdout,stderr=process.communicate(timeout=60)
        result={"returncode":process.returncode,"stdout":stdout,"stderr":stderr,
                "formal_cli_args":command,"environment_whitelist":sorted(ENV),
                "parent_pid":os.getpid(),"child_pid":process.pid,
                "subprocess_isolation_pass":process.pid!=os.getpid() and command[1:4]==["-I","-S","-B"],
                "copied_files":initial,"filesystem_copy_pass":initial==expected,
                "input_sha256":sha(root/"input.jsonl"),
                "source_copy_hash_match":all(sha(p)==sha(root/p.name) for p in sources)}
        output=root/"output.json"
        if output.exists():
            data=output.read_bytes(); result["output_bytes"]=data
            result["output_sha256"]=sha(output); result["output"]=json.loads(data)
            if output_path:
                Path(output_path).parent.mkdir(parents=True,exist_ok=True)
                Path(output_path).write_bytes(data)
            audit=result["output"]["execution_audit"]
            result["environment_isolation_pass"]=audit["environment_keys"]==sorted(ENV)
            result["filesystem_isolation_pass"]=(initial==expected and audit["initial_files"]==expected
                and sorted(p.name for p in root.iterdir())==sorted(expected+["output.json"])
                and all(Path(p).parts[0]=="stdlib" or p.split("/")[0] in expected+["__pycache__"]
                        for p in audit["read_paths"]))
        else:
            result["environment_isolation_pass"]=False
            result["filesystem_isolation_pass"]=False
        return result

def read_denial_probe():
    with tempfile.TemporaryDirectory(prefix="probe_",dir=BASE/"runtime") as directory:
        parent=Path(directory); root=parent/"isolated";root.mkdir()
        shutil.copyfile(BASE/"candidate/boundary.py",root/"boundary.py")
        (parent/"outside.txt").write_text("synthetic boundary sentinel")
        code=("import sys;sys.path.insert(0,'.');from boundary import install;install('.', 'output.json');"
              "open('../outside.txt').read()")
        r=subprocess.run([sys.executable,"-I","-S","-B","-c",code],cwd=root,env=dict(ENV),capture_output=True,text=True)
        return {"returncode":r.returncode,"blocked":r.returncode!=0 and "read outside isolated" in r.stderr}

def negative_checks(input_path):
    original=Path(input_path).read_text().splitlines()
    first=json.loads(original[0]); results=[]
    probes=[("extra_"+field,"extra",field) for field in
            ("gamma","policy_name","world","true_utility","ground_truth","expected_status")]
    probes += [("missing_"+field,"missing",field) for field in sorted(FIELDS)]
    probes += [("semantic_era_"+str(i),"era",value) for i,value in enumerate(("P95-era-1","W3-Q95"))]
    with tempfile.TemporaryDirectory(prefix="invalid_",dir=BASE/"runtime") as directory:
        for name,kind,field in probes:
            row=dict(first)
            if kind=="extra":row[field]="forbidden"
            elif kind=="missing":del row[field]
            else:row["era_id"]=field
            path=Path(directory)/"invalid.jsonl"
            path.write_text(json.dumps(row)+"\n"+"\n".join(original[1:])+"\n")
            run=launch(path)
            reason="era identifier must be anonymous" if kind=="era" else "record fields must exactly match the whitelist"
            results.append({"probe":name,"returncode":run["returncode"],
                "rejected":run["returncode"]!=0 and "output" not in run and reason in run["stderr"]})
    return results

def metadata_checks(input_path,save_dir=None):
    original=Path(input_path).read_bytes()
    metadata=[
      {"world":"W3","gamma":.95,"true_label":"TRUE_INVARIANT","secret_note":"A"},
      {"world":"FAKE_WORLD","gamma":.123456,"true_label":"NONSENSE","secret_note":"B"},
      {"world":"OTHER_LABEL","gamma":.95,"true_label":"TRUE_INVARIANT","secret_note":"A"},
      {"world":"W3","gamma":.95,"true_label":"REVERSED_EFFECT_LABEL","secret_note":"A"},
      {"world":"W3","gamma":.314159,"true_label":"TRUE_INVARIANT","secret_note":"A"},
      {"world":"W3","gamma":.95,"true_label":"TRUE_INVARIANT","secret_note":"A","generator_internal_identifier":"mutated_005"},
    ]
    root=Path(save_dir) if save_dir else BASE/"runtime"
    root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="metadata_",dir=root) as directory:
        work=Path(directory); records=[]
        for i,meta in enumerate(metadata):
            write_json(work/"private_manifest.json",meta)
            path=work/f"input_{i:03d}.jsonl";path.write_bytes(original)
            run=launch(path)
            if run["returncode"]!=0: raise RuntimeError(run["stderr"])
            if save_dir:
                (root/f"input_{i:03d}.jsonl").write_bytes(original)
                (root/f"output_{i:03d}.json").write_bytes(run["output_bytes"])
                write_json(root/f"metadata_{i:03d}.json",meta)
            canonical=json.dumps(run["output"],sort_keys=True,separators=(",",":")).encode()
            records.append({"mutation_index":i,"input_sha256":sha(path),
                "private_manifest_sha256":sha(work/"private_manifest.json"),
                "output_sha256":run["output_sha256"],
                "canonical_output_sha256":hashlib.sha256(canonical).hexdigest(),
                "isolated":run["filesystem_isolation_pass"] and run["environment_isolation_pass"]
                and run["subprocess_isolation_pass"]})
    return {"private_metadata_mutations_tested":len(metadata)-1,"records":records,
        "input_sha_equality":len({r["input_sha256"] for r in records})==1,
        "output_bitwise_equality":len({r["output_sha256"] for r in records})==1,
        "canonical_output_equality":len({r["canonical_output_sha256"] for r in records})==1,
        "all_isolated":all(r["isolated"] for r in records)}

def verify_lock():
    lock=json.loads((BASE/"results/preregistration_manifest.json").read_text())
    match={rel:sha(BASE/rel)==digest for rel,digest in lock["sha256"].items()}
    if not match or not all(match.values()): raise RuntimeError("preregistration SHA mismatch")
    return match
