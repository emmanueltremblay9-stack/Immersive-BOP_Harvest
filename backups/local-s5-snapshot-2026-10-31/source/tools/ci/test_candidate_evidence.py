"""Service readback is mocked only inside tests; no local-file CLI trust path."""
import base64
import copy
import io
import json
from pathlib import Path
import sys
import subprocess
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import candidate_evidence as evidence


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.commit = "a" * 40
        self.tree = "b" * 40
        self.run = {"id": 10, "run_attempt": 2, "head_sha": self.commit, "repository": {"full_name": evidence.REPOSITORY},
                    "path": evidence.WORKFLOW, "event": "push", "head_branch": "main", "status": "completed", "conclusion": "success"}
        self.jobs = {"total_count": 2, "jobs": [
            {"name": "Gradle validation", "conclusion": "success", "steps": [{"name": name, "conclusion": "success"} for name in evidence.REQUIRED_STEPS]},
            {"name": "Windows manifest regressions", "conclusion": "success", "steps": [{"name": name, "conclusion": "success"} for name in evidence.WINDOWS_STEPS]}]}
        jar = io.BytesIO()
        with zipfile.ZipFile(jar, "w") as z:
            z.writestr("META-INF/neoforge.mods.toml", 'license="All Rights Reserved"\n[[mods]]\nmodId="immersive_bop_harvest"\nversion="0.1.1-alpha.10"\n')
        self.lock = (evidence.ROOT / 'tools/ci/runtime-dependencies.lock.json').read_bytes()
        keys=['modId','version','projectId','fileId','filename','size','sha256']
        dependencies=[{k:r[k] for k in keys} for r in json.loads(self.lock)['dependencies']]
        self.files = {"candidate.jar": jar.getvalue(), "runtime.log": b"All 3 required tests passed\nBUILD SUCCESSFUL",
                      "gradle-build.log": b"BUILD SUCCESSFUL", "datagen-repeat.log": b"BUILD SUCCESSFUL",
                      "runtime-dependencies.json": json.dumps({"status":"PASS", "dependencies":dependencies}).encode()}
        self.receipt = {"schemaVersion": 1, "repository": evidence.REPOSITORY, "workflowPath": evidence.WORKFLOW,
                        "workflowRef": f"{evidence.REPOSITORY}/{evidence.WORKFLOW}@refs/heads/main", "workflowSha": self.commit,
                        "runId":10,"runAttempt":2,"event":"push","sourceCommit":self.commit,"sourceTree":self.tree,
                        "dependencyLockSha256":evidence.sha(self.lock),"executionMode":"development-classpath",
                        "candidate": {**evidence.jar_identity(jar.getvalue()),"name":"immersive_bop_harvest-0.1.1-alpha.10.jar", "size":len(jar.getvalue()),"sha256":evidence.sha(jar.getvalue())},
                        "capabilities":evidence.report_capabilities(self.files),
                        "files":{k:{"size":len(v),"sha256":evidence.sha(v)} for k,v in self.files.items()}}
        self.artifact = {"id":11,"name":"candidate-evidence-10-2","expired":False,"workflow_run":{"id":10,"head_sha":self.commit}}
        self.repack()

    def repack(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w") as z:
            for k,v in self.files.items(): z.writestr(k,v)
            z.writestr("receipt.json",json.dumps(self.receipt))
        self.archive=stream.getvalue();self.artifact["digest"]="sha256:"+evidence.sha(self.archive)
        self.artifact["size_in_bytes"]=len(self.archive)

    def get(self,path,*,binary=False):
        if path=="actions/runs/10/attempts/2":return self.run
        if path=="actions/runs/10/attempts/2/jobs?per_page=100":return self.jobs
        if path==f"git/commits/{self.commit}":return {"tree":{"sha":self.tree}}
        if path=="actions/runs/10/artifacts?per_page=100":return {"total_count":1,"artifacts":[self.artifact]}
        if path=="actions/artifacts/11/zip":return self.archive
        if path==f"contents/tools/ci/runtime-dependencies.lock.json?ref={self.commit}":return {"content":base64.b64encode(self.lock).decode()}
        raise AssertionError(path)

    def verify(self):return evidence.verify(10,2,self.commit,api=self)

    def test_authenticated_source_evidence_cannot_promote_runtime(self):
        result=self.verify()
        self.assertTrue(result['authenticatedExecution'])
        self.assertFalse(result['stableReady'])
        self.assertFalse(result['capabilities']['packagedRuntime'])
        self.assertFalse(result['capabilities']['client'])

    def test_wrong_service_identity_and_failed_or_pr_runs_rejected(self):
        original=copy.deepcopy(self.run)
        for key,value in [('head_sha','c'*40),('run_attempt',1),('event','pull_request'),('head_branch','other'),('conclusion','failure'),('path','.github/workflows/other.yml')]:
            self.run=copy.deepcopy(original);self.run[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.verify()

    def test_missing_required_step_and_windows_failure_rejected(self):
        original=copy.deepcopy(self.jobs)
        self.jobs['jobs'][0]['steps'].pop()
        with self.assertRaises(ValueError):self.verify()
        self.jobs=original;self.jobs['jobs'][1]['conclusion']='failure'
        with self.assertRaises(ValueError):self.verify()

    def test_skipped_or_absent_required_steps_rejected_in_each_job(self):
        original=copy.deepcopy(self.jobs)
        for job in range(2):
            for step in range(len(original['jobs'][job]['steps'])):
                for conclusion in ('skipped','failure'):
                    self.jobs=copy.deepcopy(original)
                    self.jobs['jobs'][job]['steps'][step]['conclusion']=conclusion
                    with self.subTest(job=job,step=step,conclusion=conclusion),self.assertRaises(ValueError):self.verify()
            self.jobs=copy.deepcopy(original);self.jobs['jobs'][job]['steps']=[]
            with self.assertRaises(ValueError):self.verify()

    def test_oversized_service_artifact_rejected_before_download(self):
        self.artifact['size_in_bytes']=evidence.LIMIT+1
        with patch.object(self,'get',wraps=self.get) as get, self.assertRaises(ValueError):self.verify()
        self.assertFalse(any(call.kwargs.get('binary') for call in get.call_args_list))

    def test_download_stream_is_bounded_even_if_service_size_lies(self):
        real_popen=subprocess.Popen
        def process(*args,**kwargs):
            return real_popen([sys.executable,'-c','import sys; sys.stdout.buffer.write(b"x"*10000)'],**kwargs)
        with patch.object(evidence,'LIMIT',100),patch.object(evidence.subprocess,'Popen',side_effect=process):
            with self.assertRaisesRegex(ValueError,'Downloaded archive exceeds limit'):
                evidence.GitHub().get('fixture',binary=True)

    def test_missing_digest_expired_and_wrong_run_artifacts_rejected(self):
        original=copy.deepcopy(self.artifact)
        for key,value in [('digest',None),('expired',True),('name','candidate-evidence-10-1'),('workflow_run',{'id':99,'head_sha':self.commit})]:
            self.artifact=copy.deepcopy(original);self.artifact[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.verify()

    def test_forged_receipt_claims_rejected_even_with_updated_archive_hash(self):
        original=copy.deepcopy(self.receipt)
        for key,value in [('sourceCommit','f'*40),('sourceTree','e'*40),('runAttempt','2'),('workflowSha','d'*40),('dependencyLockSha256','0'*64),('executionMode','packaged-jar')]:
            self.receipt=copy.deepcopy(original);self.receipt[key]=value;self.repack()
            with self.subTest(key=key),self.assertRaises(ValueError):self.verify()

    def test_arbitrary_pass_and_missing_logs_rejected(self):
        self.receipt['capabilities']['client']=True;self.repack()
        with self.assertRaises(ValueError):self.verify()
        self.receipt['capabilities']['client']=False
        self.files['runtime.log']=b'PASS';self.repack()
        with self.assertRaises(ValueError):self.verify()

    def test_unsafe_zip_and_duplicate_entries_rejected(self):
        for name in ['../outside','/absolute','C:/outside','a\\b']:
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,'w') as z:
                info=zipfile.ZipInfo('placeholder');info.filename=name
                z.writestr(info,b'x')
            with self.assertRaises(ValueError):evidence.contents(stream.getvalue())

    def test_local_collection_without_ci_is_rejected(self):
        with patch.dict(evidence.os.environ,{},clear=True), self.assertRaises(ValueError):evidence.collect()


if __name__=='__main__':unittest.main()
