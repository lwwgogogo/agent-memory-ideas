"""Execute upstream modules unchanged; block unused provider imports in component-only runs."""
import importlib.util, sys, types, inspect
from functools import lru_cache
from common import SOURCES,sha,check_sources
sys.dont_write_bytecode=True
def blocked_provider(*args,**kwargs):
    raise RuntimeError('Unused provider boundary was invoked: component run aborted')
def execute(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod
@lru_cache(None)
def jitrl():
    check_sources()
    root=SOURCES/'jitrl/Jericho/src'
    pkg=types.ModuleType('neh_native_jitrl');pkg.__path__=[str(root)]
    helper=types.ModuleType('neh_native_jitrl.openai_helpers')
    helper.claude_completion_with_retries=blocked_provider
    sys.modules[pkg.__name__]=pkg
    sys.modules[helper.__name__]=helper
    return execute('neh_native_jitrl.prompt_update_with_history',root/'prompt_update_with_history.py')
@lru_cache(None)
def memrl():
    check_sources()
    names=['memos','memos.mem_os','memos.mem_os.main']
    old={n:sys.modules.get(n) for n in names}
    try:
        for n in names:
            m=types.ModuleType(n);m.__path__=[];sys.modules[n]=m
        sys.modules[names[-1]].MOS=type('MOSImportTypeBoundary',(),{})
        return execute('neh_native_memrl',SOURCES/'memrl/memrl/service/value_driven.py')
    finally:
        for n in names:
            if old[n] is None:sys.modules.pop(n,None)
            else:sys.modules[n]=old[n]
def fingerprint(function):
    path=inspect.getsourcefile(function)
    return {'module':function.__module__,'symbol':function.__qualname__,
            'file':path,'first_line':function.__code__.co_firstlineno,
            'file_sha256':sha(__import__('pathlib').Path(path).read_bytes()),
            'function_source_sha256':sha(inspect.getsource(function).encode())}
