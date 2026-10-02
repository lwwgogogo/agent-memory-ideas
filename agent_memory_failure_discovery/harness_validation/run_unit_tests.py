import importlib.util, pathlib, traceback
ROOT=pathlib.Path(__file__).parent; total=passed=0; failures=[]
for p in sorted((ROOT/'tests').glob('test_*.py')):
    spec=importlib.util.spec_from_file_location(p.stem,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for name in sorted(dir(m)):
        if name.startswith('test_') and callable(getattr(m,name)):
            total+=1
            try: getattr(m,name)(); passed+=1
            except Exception as e: failures.append((p.name,name,repr(e))); traceback.print_exc()
print(f'UNIT_TESTS passed={passed} total={total} failed={len(failures)}')
if failures: raise SystemExit(1)
