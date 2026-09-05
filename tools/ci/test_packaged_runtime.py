"""Safety/identity regressions with synthetic files, never Minecraft execution proof."""
from pathlib import Path
import json,os,tempfile,unittest,zipfile,hashlib,threading,io
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from tools.ci.run_packaged_qualification import digest,guarded_directory,validate_chain
from tools.ci.production_client import allowed,arguments,library

class PackagedRuntimeGuards(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.home=self.root/'server';self.home.mkdir()
        (self.home/'world').mkdir();(self.home/'world/level.dat').write_bytes(b'synthetic world')
        self.harness=self.root/'harness.jar';self.harness.write_bytes(b'synthetic harness')
        self.candidate=self.root/'candidate.jar'
        with zipfile.ZipFile(self.candidate,'w') as archive:archive.writestr('META-INF/neoforge.mods.toml','[[mods]]\nmodId="immersive_bop_harvest"\nversion="0.1.1-alpha.10"\n')
        self.log=self.root/'previous.log';self.log.write_text('synthetic prior log')
        self.previous=self.root/'previous.json'
        self.receipt={'passed':True,'exitCode':0,'timeout':False,'aborted':False,'cwd':str(self.home),'log':str(self.log),'logSha256':digest(self.log),'runtime':{'phaseStatus':'PASS','phase':'baseline-restart','candidateVersion':'0.1.1-alpha.9','nonce':'test-nonce','saveCalled':True,'loadedJarIdentities':[{'modId':'bop_harvest_qa','sha256':digest(self.harness)}],'savedSnapshot':{}}}
        (self.home/'bop-qa-plan.json').write_text(json.dumps({'nonce':'test-nonce'}))
        self.save()
    def save(self):self.previous.write_text(json.dumps(self.receipt))
    def check(self):return validate_chain('candidate-upgrade',self.previous,self.home,self.candidate,self.harness,None)
    def test_upgrade_requires_predecessor_and_existing_world(self):
        with self.assertRaisesRegex(ValueError,'predecessor'):validate_chain('candidate-upgrade',None,self.home,self.candidate,self.harness,None)
    def test_failed_predecessor_rejected(self):
        self.receipt['passed']=False;self.save()
        with self.assertRaisesRegex(ValueError,'did not pass'):self.check()
    def test_aborted_or_boolean_exit_predecessor_rejected(self):
        for field,value in [('aborted',True),('exitCode',False)]:
            with self.subTest(field=field):
                old=self.receipt[field];self.receipt[field]=value;self.save()
                with self.assertRaisesRegex(ValueError,'did not pass'):self.check()
                self.receipt[field]=old
    def test_active_world_cannot_serve_as_its_own_backup(self):
        record=self.root/'backup.json'
        record.write_text(json.dumps({'source':str(self.home/'world'),'backup':str(self.home/'world')}))
        with self.assertRaisesRegex(ValueError,'separate copy'):
            validate_chain('candidate-upgrade',self.previous,self.home,self.candidate,self.harness,record)
    def test_wrong_phase_and_version_rejected(self):
        for field,value in [('phase','baseline-create'),('candidateVersion','0.1.1-alpha.10')]:
            with self.subTest(field=field):
                old=self.receipt['runtime'][field];self.receipt['runtime'][field]=value;self.save()
                with self.assertRaisesRegex(ValueError,'phase/version'):self.check()
                self.receipt['runtime'][field]=old
    def test_stale_log_or_nonce_rejected(self):
        self.log.write_text('changed')
        with self.assertRaisesRegex(ValueError,'log bytes'):self.check()
        self.receipt['logSha256']=digest(self.log);self.receipt['runtime']['nonce']='stale';self.save()
        with self.assertRaisesRegex(ValueError,'Stale'):self.check()
    def test_changed_harness_rejected(self):
        self.harness.write_bytes(b'new driver')
        with self.assertRaisesRegex(ValueError,'Harness changed'):self.check()
    def test_upgrade_requires_backup(self):
        with self.assertRaisesRegex(ValueError,'backup'):self.check()
    def test_linked_world_rejected_before_writes(self):
        outside=self.root/'outside';outside.mkdir();link=self.home/'linked-world'
        try:link.symlink_to(outside,target_is_directory=True)
        except OSError as exc:self.skipTest('Host does not permit test symlinks: '+str(exc))
        with self.assertRaisesRegex(ValueError,'Linked'):guarded_directory(self.home)

class LauncherRules(unittest.TestCase):
    def test_concurrent_clients_receive_complete_shared_library(self):
        raw=b'complete pinned library'*65536
        row={'path':'fixture/library.jar','url':'https://libraries.minecraft.net/fixture.jar','size':len(raw),'sha1':hashlib.sha1(raw).hexdigest()}
        barrier=threading.Barrier(2)
        class Response(io.BytesIO):
            def read(self,size=-1):
                barrier.wait(timeout=5)
                return super().read(size)
        with tempfile.TemporaryDirectory() as temporary, patch('tools.ci.production_client.urllib.request.urlopen',side_effect=lambda *a,**k:Response(raw)):
            root=Path(temporary).resolve()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures=[pool.submit(library,root,row) for _ in range(2)]
                for future in futures:self.assertEqual(future.result(timeout=10).read_bytes(),raw)
            self.assertEqual([p.name for p in (root/'libraries/fixture').iterdir()],['library.jar'])
    def test_launcher_library_path_escape_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            for path in ('../escape.jar','C:/escape.jar','/escape.jar','a\\escape.jar'):
                with self.subTest(path=path),self.assertRaisesRegex(ValueError,'Unsafe'):library(Path(temporary),{'path':path})
    def test_platform_rules_and_order(self):
        linux={'name':'linux','arch':'x86_64','version':'6.8','features':{}}
        windows={'name':'windows','arch':'amd64','version':'10.0','features':{}}
        rules=[{'action':'allow','os':{'name':'linux'}}]
        self.assertTrue(allowed(rules,linux));self.assertFalse(allowed(rules,windows))
        self.assertFalse(allowed(rules+[{'action':'disallow'}],linux))
        self.assertTrue(allowed([{'action':'allow'}],linux))
    def test_unset_features_are_false(self):
        context={'name':'linux','arch':'x86_64','version':'6.8','features':{}}
        self.assertFalse(allowed([{'action':'allow','features':{'is_demo_user':True}}],context))
        self.assertTrue(allowed([{'action':'allow','features':{'is_demo_user':False}}],context))
    def test_unresolved_launch_placeholder_rejected(self):
        with self.assertRaises(KeyError):arguments(['${unknown}'],{})

if __name__=='__main__':unittest.main()
