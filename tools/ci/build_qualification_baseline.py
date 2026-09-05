"""Rebuild the fixed reviewed alpha.9 source in a new disposable directory."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.ci.run_packaged_qualification import digest, guarded_directory
from tools.ci.candidate_evidence import jar_identity

COMMIT = 'ee525b9d9406b030e17d87249219c007f97af47c'
TREE = 'd2554e12f732ee13496246823afe78f156d2fd2b'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = guarded_directory(args.output)
    output.mkdir(parents=True, exist_ok=False)
    present = subprocess.run(['git', 'cat-file', '-e', COMMIT], cwd=ROOT, capture_output=True)
    if present.returncode:
        subprocess.run(['git', 'fetch', '--no-tags', 'origin', COMMIT], cwd=ROOT, check=True, timeout=120)
    actual = subprocess.check_output(['git', 'rev-parse', COMMIT+'^{tree}'], cwd=ROOT, text=True).strip()
    if actual != TREE:
        raise ValueError('Historical baseline source tree mismatch')
    archive = output/'source.zip'
    subprocess.run(['git', 'archive', '--format=zip', '--output='+str(archive), COMMIT], cwd=ROOT, check=True)
    source = output/'source'
    source.mkdir()
    with zipfile.ZipFile(archive) as bundle:
        if len(bundle.infolist()) > 1000 or sum(i.file_size for i in bundle.infolist()) > 32*1024*1024:
            raise ValueError('Historical source archive exceeds budget')
        seen = set()
        for item in bundle.infolist():
            name = item.filename.rstrip('/')
            if (not name or name in seen or '\\' in name or ':' in name or PurePosixPath(name).is_absolute()
                    or any(part in {'', '.', '..'} for part in name.split('/'))
                    or (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('Unsafe historical source entry')
            seen.add(name)
            target = source/name
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(bundle.read(item))
    command = ([str(source/'gradlew.bat')] if os.name == 'nt' else ['bash', str(source/'gradlew')])
    command += ['--no-configuration-cache', 'clean', 'build', '--stacktrace']
    log = output/'baseline-build.log'
    with log.open('wb') as stream:
        result = subprocess.run(command, cwd=source, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    if result.returncode != 0:
        raise ValueError('Historical baseline build failed: '+str(log))
    jar = source/'build/libs/immersive_bop_harvest-0.1.1-alpha.9.jar'
    identity = jar_identity(jar.read_bytes())
    if identity['version'] != '0.1.1-alpha.9':
        raise ValueError('Historical source built a different version')
    target = output/jar.name
    target.write_bytes(jar.read_bytes())
    receipt = {'schemaVersion': 1, 'sourceCommit': COMMIT, 'sourceTree': TREE,
               'sourceArchiveSha256': digest(archive), 'command': command, 'exitCode': result.returncode,
               'logSha256': digest(log), 'logBytes': log.stat().st_size,
               'candidate': {**identity, 'name': target.name, 'size': target.stat().st_size, 'sha256': digest(target)}}
    (output/'baseline-build.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
