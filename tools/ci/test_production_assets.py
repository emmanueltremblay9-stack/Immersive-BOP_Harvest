"""Pinned-index/cache isolation regressions; these do not claim client execution."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.ci.prepare_production_assets import prepare_assets


class ProductionAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.launcher = self.root / 'client'
        self.metadata = self.launcher / 'versions/1.21.1/1.21.1.json'
        self.metadata.parent.mkdir(parents=True)
        (self.root / '.bop-qualification-owner').write_text('test owner')
        self.cache = self.root / 'read-only-cache'
        (self.cache / 'indexes').mkdir(parents=True)
        self.object = b'pinned asset'
        self.object_hash = hashlib.sha1(self.object).hexdigest()
        entry = {'hash': self.object_hash, 'size': len(self.object)}
        self.index = json.dumps({'objects': {'sound/a': entry, 'sound/alias': entry}}).encode()
        self.index_hash = hashlib.sha1(self.index).hexdigest()
        self.metadata.write_text(json.dumps({'assetIndex': {'id': '17', 'sha1': self.index_hash,
            'size': len(self.index), 'url': f'https://piston-meta.mojang.com/v1/packages/{self.index_hash}/17.json'}}))
        self.patch = patch('tools.ci.prepare_production_assets.METADATA_SHA256', hashlib.sha256(self.metadata.read_bytes()).hexdigest())
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_different_index_revision_uses_pinned_download_and_preserves_cache(self):
        cached_index = self.cache / 'indexes/17.json'
        cached_index.write_bytes(b'other official revision')
        obj = self.cache / 'objects' / self.object_hash[:2] / self.object_hash
        obj.parent.mkdir(parents=True)
        obj.write_bytes(self.object)
        with patch('tools.ci.prepare_production_assets.urllib.request.urlopen', return_value=io.BytesIO(self.index)) as download:
            target = prepare_assets(self.launcher, self.cache)
        self.assertEqual(download.call_count, 1)
        self.assertEqual(cached_index.read_bytes(), b'other official revision')
        self.assertEqual((target / 'indexes/17.json').read_bytes(), self.index)
        self.assertEqual((target / 'objects' / self.object_hash[:2] / self.object_hash).read_bytes(), self.object)
        receipt = json.loads((self.root / 'asset-preparation.json').read_text())
        self.assertEqual((receipt['uniqueObjects'], receipt['copiedFromCache'], receipt['downloadedObjects']), (1, 1, 0))

    def test_corrupt_cached_object_is_a_miss_and_is_not_replaced(self):
        (self.cache / 'indexes/17.json').write_bytes(self.index)
        obj = self.cache / 'objects' / self.object_hash[:2] / self.object_hash
        obj.parent.mkdir(parents=True)
        corrupt = b'x' * len(self.object)
        obj.write_bytes(corrupt)
        with patch('tools.ci.prepare_production_assets.urllib.request.urlopen', return_value=io.BytesIO(self.object)):
            prepare_assets(self.launcher, self.cache)
        self.assertEqual(obj.read_bytes(), corrupt)
        self.assertEqual(json.loads((self.root / 'asset-preparation.json').read_text())['downloadedObjects'], 1)

    def test_invalid_download_never_publishes_receipt(self):
        with patch('tools.ci.prepare_production_assets.urllib.request.urlopen', return_value=io.BytesIO(b'corrupt')):
            with self.assertRaisesRegex(ValueError, 'pinned bytes'):
                prepare_assets(self.launcher, self.cache)
        self.assertFalse((self.root / 'asset-preparation.json').exists())

    def test_unpinned_metadata_rejected_before_asset_writes(self):
        self.metadata.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'pinned parent'):
            prepare_assets(self.launcher, self.cache)
        self.assertFalse((self.root / 'assets').exists())

    def test_shared_cache_overlap_rejected_before_writes(self):
        for cache in (self.root, self.root / 'assets', self.root / 'assets/child'):
            with self.subTest(cache=cache), self.assertRaisesRegex(ValueError, 'overlaps'):
                prepare_assets(self.launcher, cache)
        self.assertFalse((self.root / 'assets').exists())


if __name__ == '__main__':
    unittest.main()
