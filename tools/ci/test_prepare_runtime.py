import copy
import hashlib
import io
import json
import unittest
import zipfile
from pathlib import Path
from prepare_runtime import ROOT, properties, validate_lock, validate_bytes

class RuntimeLockTests(unittest.TestCase):
    def setUp(self):
        self.lock=json.loads((ROOT/'tools/ci/runtime-dependencies.lock.json').read_text())
        self.props=properties(ROOT/'gradle.properties')
    def test_lock_matches_all_five_pins(self):
        self.assertEqual(5,len(validate_lock(self.lock,self.props)))
    def test_hash_is_mandatory(self):
        self.lock['dependencies'][0]['sha256']=None
        with self.assertRaises(ValueError): validate_lock(self.lock,self.props)
    def test_version_drift_rejected(self):
        self.props['biomesoplenty_version']='wrong'
        with self.assertRaises(ValueError): validate_lock(self.lock,self.props)
    def test_unofficial_download_host_rejected(self):
        self.lock['dependencies'][0]['url']='https://example.invalid/download'
        with self.assertRaises(ValueError): validate_lock(self.lock,self.props)
    def test_dependency_basename_traversal_rejected(self):
        self.lock['dependencies'][0]['filename']='../bad.jar'
        with self.assertRaises(ValueError): validate_lock(self.lock,self.props)
    def test_duplicate_mod_identity_rejected(self):
        self.lock['dependencies'][1]=copy.deepcopy(self.lock['dependencies'][0])
        with self.assertRaises(ValueError): validate_lock(self.lock,self.props)
    def test_changed_bytes_rejected_before_metadata_read(self):
        with self.assertRaises(ValueError): validate_bytes(self.lock['dependencies'][0],b'not a jar')
    def test_fixture_metadata_is_validated(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            archive.writestr('META-INF/neoforge.mods.toml','[[mods]]\nmodId="fixture_mod"\nversion="1.0"\n')
        raw=stream.getvalue(); row={'modId':'fixture_mod','version':'1.0','projectId':1,'fileId':2,'filename':'fixture.jar','size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        self.assertEqual('1.0',validate_bytes(row,raw)['version'])
        row['version']='wrong'
        with self.assertRaises(ValueError): validate_bytes(row,raw)
if __name__=='__main__': unittest.main()
