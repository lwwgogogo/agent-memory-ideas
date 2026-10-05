import sys
from pathlib import Path

def install(root,output_name):
    root=Path(root).resolve()
    library=Path(sys.base_prefix).resolve()
    reads=set()

    def check(event,args):
        if event in ("subprocess.Popen","os.system","os.exec","os.posix_spawn","socket.__new__","socket.connect"):
            raise PermissionError("external execution and networking disabled")
        if event!="open" or isinstance(args[0],int):
            return
        path=Path(args[0]).resolve()
        mode=args[1]; flags=args[2]
        writing=(isinstance(mode,str) and any(c in mode for c in "wax+")) or bool(flags & 3)
        local=path.is_relative_to(root)
        standard=path.is_relative_to(library)
        if writing:
            if path!=root/output_name: raise PermissionError("write outside permitted output")
        elif not (local or standard):
            raise PermissionError("read outside isolated source/input and interpreter library")
        if not writing:
            reads.add(str(path.relative_to(root)) if local else "stdlib/"+str(path.relative_to(library)))
    sys.addaudithook(check)
    return reads
