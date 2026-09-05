#!/usr/bin/env python3
"""Download only reviewed dependency bytes for isolated CI; never install to Prism."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tomllib
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 60 * 1024 * 1024


def properties(path: Path) -> dict[str, str]:
    return dict(line.split('=', 1) for line in path.read_text().splitlines()
                if '=' in line and not line.lstrip().startswith('#'))


def validate_lock(lock: dict, props: dict[str, str]) -> list[dict]:
    if not isinstance(lock, dict) or lock.get('schemaVersion') != 1:
        raise ValueError('Invalid runtime lock schema')
    rows = lock.get('dependencies')
    required = {'biomesoplenty', 'glitchcore', 'terrablender', 'farmersdelight', 'immersiveengineering'}
    if not isinstance(rows, list) or len(rows) != len(required):
        raise ValueError('Runtime lock must contain all five declared required mods')
    seen = set()
    for item in rows:
        mod = item.get('modId')
        if mod not in required or mod in seen or item.get('version') != props.get(mod+'_version'):
            raise ValueError('Runtime lock differs from the pinned Gradle dependency contract')
        seen.add(mod)
        for field in ['projectId', 'fileId', 'size']:
            if type(item.get(field)) is not int or item[field] <= 0:
                raise ValueError('Invalid numeric runtime identity')
        if item['size'] > MAX_BYTES:
            raise ValueError('Runtime dependency exceeds bounded size')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+-]*\.jar', str(item.get('filename',''))):
            raise ValueError('Unsafe dependency basename')
        if not re.fullmatch(r'[0-9a-f]{64}', str(item.get('sha256',''))):
            raise ValueError('Runtime dependency has no verified hash')
        expected = f"https://www.curseforge.com/api/v1/mods/{item['projectId']}/files/{item['fileId']}/download"
        if item.get('url') != expected:
            raise ValueError('Runtime dependency URL is not its exact official project/file endpoint')
    if seen != required or len({x['filename'] for x in rows}) != len(rows):
        raise ValueError('Ambiguous runtime lock')
    return rows


def validate_bytes(item: dict, raw: bytes) -> dict:
    if len(raw) != item['size'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('Runtime dependency bytes differ from the reviewed lock')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        info = archive.getinfo('META-INF/neoforge.mods.toml')
        if info.file_size > 65536:
            raise ValueError('Dependency metadata is oversized')
        metadata = tomllib.loads(archive.read(info).decode('utf-8'))
        records = [x for x in metadata['mods'] if x.get('modId') == item['modId']]
        if len(records) != 1:
            raise ValueError('Dependency has an ambiguous mod ID')
        version = records[0].get('version')
        if version == '${file.jarVersion}':
            info = archive.getinfo('META-INF/MANIFEST.MF')
            if info.file_size > 65536:
                raise ValueError('Dependency manifest is oversized')
            manifest = archive.read(info).decode('utf-8')
            versions = [x.split(': ', 1)[1] for x in manifest.splitlines()
                        if x.startswith('Implementation-Version: ')]
            if len(versions) != 1:
                raise ValueError('Dependency implementation version is ambiguous')
            version = versions[0]
        if version != item['version']:
            raise ValueError('Dependency version does not match the lock')
    return {key: item[key] for key in ['modId','version','projectId','fileId','filename','size','sha256']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'build/runtime-deps')
    parser.add_argument('--evidence-dir', type=Path, default=ROOT/'build/ci-evidence')
    args = parser.parse_args()
    lock = json.loads((ROOT/'tools/ci/runtime-dependencies.lock.json').read_text())
    rows = validate_lock(lock, properties(ROOT/'gradle.properties'))
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    expected = {row['filename'] for row in rows}
    if {p.name for p in output.glob('*.jar')} - expected:
        raise ValueError('Unexpected JARs exist in the isolated CI runtime directory')
    reports = []
    for row in rows:
        destination = output/row['filename']
        if destination.exists():
            raw = destination.read_bytes()
        elif args.check_only:
            raise ValueError('Pinned runtime dependency is missing')
        else:
            request = urllib.request.Request(row['url'], headers={'User-Agent':'BOP-Harvest-CI/1'})
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read(MAX_BYTES+1)
        reports.append(validate_bytes(row,raw))
        if not args.check_only:
            temporary = destination.with_suffix('.tmp')
            temporary.write_bytes(raw); temporary.replace(destination)
        print('VERIFIED', row['modId'], row['version'], row['sha256'])
    evidence = args.evidence_dir.resolve(); evidence.mkdir(parents=True, exist_ok=True)
    (evidence/'runtime-dependencies.json').write_text(json.dumps({'status':'PASS','scope':'isolated CI runtime, not a Prism install','dependencies':reports},indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
