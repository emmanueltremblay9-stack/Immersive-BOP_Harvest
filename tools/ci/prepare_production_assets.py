"""Prepare pinned production assets without changing shared launcher caches."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import uuid

from tools.ci.prepare_production_runtime import METADATA_SHA256
from tools.ci.run_packaged_qualification import guarded_directory

MAX_OBJECT = 64 * 1024 * 1024


def verified_bytes(url, cached, size, expected):
    if cached.is_file() and cached.stat().st_size == size:
        raw = cached.read_bytes()
        if hashlib.sha1(raw).hexdigest() == expected:
            return raw, True
    with urllib.request.urlopen(url, timeout=60) as response:
        raw = response.read(size + 1)
    if len(raw) != size or hashlib.sha1(raw).hexdigest() != expected:
        raise ValueError('Downloaded production asset differs from pinned bytes')
    return raw, False


def write_new(path, raw):
    if path.exists():
        raise ValueError('Owned production asset destination already exists')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(raw)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def prepare_assets(launcher: Path, cache: Path) -> Path:
    launcher = guarded_directory(launcher)
    root = launcher.parent
    if launcher.name != 'client' or not (root / '.bop-qualification-owner').is_file():
        raise ValueError('Assets require the prepared owned production launcher')
    raw = (launcher / 'versions/1.21.1/1.21.1.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != METADATA_SHA256:
        raise ValueError('Production asset metadata differs from the pinned parent')
    row = json.loads(raw)['assetIndex']
    if (row['id'] != '17' or not re.fullmatch('[0-9a-f]{40}', row['sha1'])
            or type(row['size']) is not int or not 0 < row['size'] <= 1024 * 1024
            or row['url'] != f"https://piston-meta.mojang.com/v1/packages/{row['sha1']}/17.json"):
        raise ValueError('Invalid pinned production asset index reference')
    target = guarded_directory(root / 'assets')
    cache = cache.resolve()
    if cache == target or cache.is_relative_to(target) or target.is_relative_to(cache):
        raise ValueError('Read-only asset cache overlaps the owned destination')
    target.mkdir(exist_ok=False)
    raw, index_cached = verified_bytes(row['url'], cache / 'indexes/17.json', row['size'], row['sha1'])
    index = json.loads(raw)
    if not isinstance(index.get('objects'), dict) or not 0 < len(index['objects']) <= 20000:
        raise ValueError('Production asset object inventory exceeds budget')
    objects = {}
    for entry in index['objects'].values():
        value, size = entry['hash'], entry['size']
        if (not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value)
                or type(size) is not int or not 0 <= size <= MAX_OBJECT
                or (value in objects and objects[value] != size)):
            raise ValueError('Invalid production asset object identity')
        objects[value] = size
    total = sum(objects.values())
    if total > 2 * 1024 * 1024 * 1024:
        raise ValueError('Production asset aggregate exceeds budget')
    write_new(target / 'indexes/17.json', raw)

    def copy_object(item):
        value, size = item
        name = value[:2] + '/' + value
        raw, cached = verified_bytes('https://resources.download.minecraft.net/' + name,
                                     cache / 'objects' / name, size, value)
        write_new(target / 'objects' / name, raw)
        return cached

    with ThreadPoolExecutor(max_workers=8) as pool:
        copied = sum(pool.map(copy_object, objects.items()))
    receipt = {'indexSha1': row['sha1'], 'indexBytes': row['size'],
               'indexCacheHit': index_cached, 'uniqueObjects': len(objects),
               'verifiedObjectBytes': total, 'copiedFromCache': copied,
               'downloadedObjects': len(objects) - copied, 'assetsRoot': str(target)}
    write_new(root / 'asset-preparation.json', (json.dumps(receipt, indent=2) + '\n').encode())
    print('PINNED PRODUCTION ASSETS: ' + json.dumps(receipt), flush=True)
    return target
