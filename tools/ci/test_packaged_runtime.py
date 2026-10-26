"""Safety/identity regressions with synthetic files, never Minecraft execution proof."""
from pathlib import Path
import json,os,tempfile,unittest,zipfile,hashlib,threading,io,stat
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch
from tools.ci.run_packaged_qualification import DIRECTORY_SCAN_ATTEMPTS,digest,guarded_directory,validate_chain
from tools.ci.production_client import LIBRARY_READ_ATTEMPTS,allowed,arguments,library

class PackagedRuntimeGuards(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.home=self.root/'server';self.home.mkdir()
        (self.home/'world').mkdir();(self.home/'world/level.dat').write_bytes(b'synthetic world')
        self.harness=self.root/'harness.jar';self.harness.write_bytes(b'synthetic harness')
        self.candidate=self.root/'candidate.jar'
        with zipfile.ZipFile(self.candidate,'w') as archive:archive.writestr('META-INF/neoforge.mods.toml','[[mods]]\nmodId="immersive_bop_harvest"\nversion="0.1.1"\n')
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
        for field,value in [('phase','baseline-create'),('candidateVersion','0.1.1')]:
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

class DirectoryScanRaces(unittest.TestCase):
    def test_guard_restarts_after_atomic_library_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            directory=root/'libraries/fixture';directory.mkdir(parents=True)
            pending=directory/'library.jar.0123456789abcdef.tmp'
            target=directory/'library.jar';raw=b'verified library bytes'
            pending.write_bytes(raw)
            original_rglob=Path.rglob;scans=[]
            def publish_during_scan(path,pattern):
                snapshot=list(original_rglob(path,pattern));scans.append(snapshot)
                if len(scans)==1:os.replace(pending,target)
                yield from snapshot
            with patch.object(Path,'rglob',publish_during_scan),patch('tools.ci.run_packaged_qualification.time.sleep'):
                self.assertEqual(guarded_directory(root),root)
            self.assertEqual(len(scans),2)
            self.assertIn(pending,scans[0]);self.assertIn(target,scans[1])
            self.assertEqual(target.read_bytes(),raw)
            self.assertFalse(pending.exists())

    def test_guard_rejects_symlink_reparse_or_escape_after_retry(self):
        for kind in ('symlink','reparse','escape'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary).resolve();pending=root/'library.jar.tmp';target=root/'library.jar'
                pending.write_bytes(b'verified library bytes')
                original_rglob=Path.rglob;original_link=Path.is_symlink
                original_lstat=Path.lstat;original_resolve=Path.resolve;scans=[]
                def publish_during_scan(path,pattern):
                    snapshot=list(original_rglob(path,pattern));scans.append(snapshot)
                    if len(scans)==1:os.replace(pending,target)
                    yield from snapshot
                def linked(path):
                    return kind=='symlink' and path==target or original_link(path)
                def attributes(path,*args,**kwargs):
                    result=original_lstat(path,*args,**kwargs)
                    if kind=='reparse' and path==target:
                        return SimpleNamespace(st_mode=result.st_mode,st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
                    return result
                def resolved(path,*args,**kwargs):
                    if kind=='escape' and path==target:return root.parent/'outside'
                    return original_resolve(path,*args,**kwargs)
                with patch.object(Path,'rglob',publish_during_scan),patch.object(Path,'is_symlink',linked),patch.object(Path,'lstat',attributes),patch.object(Path,'resolve',resolved),patch('tools.ci.run_packaged_qualification.time.sleep') as sleep:
                    with self.assertRaisesRegex(ValueError,'Linked or escaping'):guarded_directory(root)
                self.assertEqual(len(scans),2);sleep.assert_called_once()

    def test_guard_rechecks_ancestors_after_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();pending=root/'library.jar.tmp';target=root/'library.jar'
            pending.write_bytes(b'verified library bytes')
            original_rglob=Path.rglob;original_link=Path.is_symlink;scans=[]
            def publish_during_scan(path,pattern):
                snapshot=list(original_rglob(path,pattern));scans.append(snapshot)
                os.replace(pending,target)
                yield from snapshot
            def linked(path):
                return bool(scans) and path==root or original_link(path)
            with patch.object(Path,'rglob',publish_during_scan),patch.object(Path,'is_symlink',linked),patch('tools.ci.run_packaged_qualification.time.sleep') as sleep:
                with self.assertRaisesRegex(ValueError,'Linked/reparse write path'):guarded_directory(root)
            self.assertEqual(len(scans),1);sleep.assert_called_once()

    def test_guard_rejects_a_persistently_unstable_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();pending=root/'library.jar.tmp'
            original_rglob=Path.rglob;scans=[]
            def remove_during_scan(path,pattern):
                pending.write_bytes(b'verified library bytes')
                snapshot=list(original_rglob(path,pattern));scans.append(snapshot)
                pending.unlink()
                yield from snapshot
            with patch.object(Path,'rglob',remove_during_scan),patch('tools.ci.run_packaged_qualification.time.sleep') as sleep:
                with self.assertRaises(FileNotFoundError):guarded_directory(root)
            self.assertEqual(len(scans),DIRECTORY_SCAN_ATTEMPTS)
            self.assertEqual(sleep.call_count,DIRECTORY_SCAN_ATTEMPTS-1)

    def test_guard_does_not_retry_other_filesystem_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            for error in (PermissionError('denied'),NotADirectoryError('not a directory')):
                with self.subTest(error=type(error).__name__),patch.object(Path,'rglob',side_effect=error),patch('tools.ci.run_packaged_qualification.time.sleep') as sleep:
                    with self.assertRaises(type(error)):guarded_directory(root)
                    sleep.assert_not_called()

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
    def test_replace_fallback_retries_transient_shared_library_read(self):
        raw=b'complete pinned library';row={'path':'fixture/library.jar','url':'https://libraries.minecraft.net/fixture.jar','size':len(raw),'sha1':hashlib.sha1(raw).hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();target=root/'libraries/fixture/library.jar'
            def peer_published(_source,destination):
                Path(destination).write_bytes(raw)
                raise PermissionError(13,'transient sharing violation',str(destination))
            with patch('tools.ci.production_client.urllib.request.urlopen',return_value=io.BytesIO(raw)),patch('tools.ci.production_client.os.replace',side_effect=peer_published),patch.object(Path,'read_bytes',side_effect=[PermissionError(13,'transient sharing violation',str(target)),raw,raw]),patch('tools.ci.production_client.time.sleep') as sleep:
                self.assertEqual(library(root,row),target)
            sleep.assert_called_once()
    def test_permanent_shared_library_permission_error_remains_failure(self):
        raw=b'complete pinned library';row={'path':'fixture/library.jar','size':len(raw),'sha1':hashlib.sha1(raw).hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();target=root/'libraries/fixture/library.jar';target.parent.mkdir(parents=True);target.write_bytes(raw)
            with patch.object(Path,'read_bytes',side_effect=PermissionError(13,'permanent sharing violation',str(target))),patch('tools.ci.production_client.time.sleep') as sleep:
                with self.assertRaises(PermissionError):library(root,row)
            self.assertEqual(sleep.call_count,LIBRARY_READ_ATTEMPTS-1)
    def test_permission_retry_does_not_accept_wrong_sha1_shared_library(self):
        raw=b'complete pinned library';row={'path':'fixture/library.jar','size':len(raw),'sha1':hashlib.sha1(raw).hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();target=root/'libraries/fixture/library.jar';target.parent.mkdir(parents=True);target.write_bytes(raw)
            with patch.object(Path,'read_bytes',side_effect=[PermissionError(13,'transient sharing violation',str(target)),b'x'*len(raw)]),patch('tools.ci.production_client.time.sleep') as sleep:
                with self.assertRaisesRegex(ValueError,'Invalid launcher library'):library(root,row)
            sleep.assert_called_once()
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
