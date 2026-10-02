"""Capture plotting/audit source and checksums without rewriting inference metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directories',nargs='+');args=parser.parse_args()
    project=Path(__file__).resolve().parents[1]
    files=sorted((project/'scripts').glob('*.py'))
    for directory in args.directories:
        root=Path(directory)
        with zipfile.ZipFile(root/'postprocessing_source.zip','x',zipfile.ZIP_DEFLATED) as z:
            for file in files:z.write(file,file.relative_to(project).as_posix())
        hashes={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob('*') if p.is_file() and p.name!='artifact_manifest.json'}
        with (root/'artifact_manifest.json').open('x',encoding='utf-8') as f:
            json.dump(dict(sha256=hashes,plot_source_archive='postprocessing_source.zip',
                           note='Additional derived artifacts; inference run.json is unchanged.'),f,indent=2)
        print(root,'sealed',len(hashes),'artifacts')
