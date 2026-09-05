"""Synthetic bundles test integrity only; no fixture can certify runtime."""
import copy
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts import check_stable_release_gate as gate
from scripts import refresh_project_manifest as source


class StableGateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in ("docs", "spec", "tools/ci", "build/evidence", "build/mods"):
            (self.root / name).mkdir(parents=True)
        self.write(".gitignore", "build/\n")
        self.write("LICENSE", "All Rights Reserved\n")
        self.write("CHANGELOG.md", "# 0.1.1\nSynthetic fixture only.\n")
        self.write("docs/QA_ACCEPTANCE.md", "## Build\n- [ ] Build passes.\n## Harvest behavior\n- [ ] No bonus by hand.\n")
        self.write("spec/sample.json", '{"rules":["fixture"]}')
        props = "mod_id=sample_mod\nmod_version=0.1.1\nmod_license=All Rights Reserved\n"
        rows = []
        for index, mod in enumerate(("biomesoplenty", "glitchcore", "terrablender", "farmersdelight", "immersiveengineering"), 1):
            props += f"{mod}_version=1.0\n"
            name = f"{mod}-1.0.jar"
            self.jar(f"build/mods/{name}", mod, "1.0")
            ref = self.ref(f"build/mods/{name}")
            rows.append({"modId": mod, "version": "1.0", "projectId": index, "fileId": index + 10,
                         "filename": name, "size": ref["size"], "sha256": ref["sha256"],
                         "url": f"https://www.curseforge.com/api/v1/mods/{index}/files/{index+10}/download"})
        self.write("gradle.properties", props)
        self.write_json("tools/ci/runtime-dependencies.lock.json", {"schemaVersion": 1, "dependencies": rows})
        self.run_git("init", "-q")
        self.run_git("add", ".")
        manifest = {"mod_id": "sample_mod", "version": "0.1.1", "files": [source.file_entry(p, self.root) for p in source.tracked_paths(self.root)]}
        self.write_json("PROJECT_MANIFEST.json", manifest)
        self.run_git("add", "PROJECT_MANIFEST.json")
        self.run_git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
        self.jar("build/sample_mod-0.1.1.jar", "sample_mod", "0.1.1")
        self.write("build/mods/sample_mod-0.1.1.jar", (self.root / "build/sample_mod-0.1.1.jar").read_bytes())
        self.candidate = {"id": "fixture", "version": "0.1.1", "modId": "sample_mod", "license": "All Rights Reserved",
                          "commit": gate.git(self.root, "rev-parse", "HEAD"), "tree": gate.git(self.root, "rev-parse", "HEAD^{tree}"),
                          "jarSha256": gate.digest(self.root / "build/sample_mod-0.1.1.jar"),
                          "lockSha256": gate.digest(self.root / "tools/ci/runtime-dependencies.lock.json")}
        self.receipts = {}
        catalog = gate.acceptance_catalog(self.root)
        for kind in sorted(gate.KINDS):
            self.write(f"build/evidence/{kind}.log", "Synthetic test log, not Minecraft evidence.\n")
            self.receipts[kind] = {"kind": kind, "candidate": copy.deepcopy(self.candidate), "tested": True, "waived": False,
                                   "command": ["synthetic-fixture"], "exitCode": 0, "startedAt": "2026-01-01T00:00:00Z", "finishedAt": "2026-01-01T00:00:01Z",
                                   "log": self.ref(f"build/evidence/{kind}.log"), "coverage": [k for k, v in catalog.items() if v["kind"] == kind]}
        self.bundle = {"schemaVersion": 1, "candidate": self.candidate, "jar": self.ref("build/sample_mod-0.1.1.jar"),
                       "dependencyLock": self.ref("tools/ci/runtime-dependencies.lock.json"), "sourceManifest": self.ref("PROJECT_MANIFEST.json"),
                       "changelog": self.ref("CHANGELOG.md"), "installedModsDir": "build/mods", "receipts": [], "defects": [], "publicationBlockers": ["NO_AUTHORITY"]}
        self.save_receipts()

    def run_git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, timeout=30)

    def write(self, name, value):
        (self.root / name).write_bytes(value if isinstance(value, bytes) else value.encode())

    def write_json(self, name, value):
        self.write(name, json.dumps(value))

    def ref(self, name):
        p = self.root / name
        return {"path": name, "size": p.stat().st_size, "sha256": gate.digest(p)}

    def jar(self, name, mod, version):
        with zipfile.ZipFile(self.root / name, "w") as z:
            z.writestr("META-INF/neoforge.mods.toml", f'license="All Rights Reserved"\n[[mods]]\nmodId="{mod}"\nversion="{version}"\n')

    def save_receipts(self):
        refs = []
        for kind, receipt in self.receipts.items():
            name = f"build/evidence/{kind}.json"
            self.write_json(name, receipt)
            refs.append(self.ref(name))
        self.bundle["receipts"] = refs
        self.write_json("build/bundle.json", self.bundle)

    def test_consistent_bundle_integrity_passes_but_cli_never_certifies_runtime(self):
        gate.validate_bundle(self.root, self.bundle)
        with patch.object(gate, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(2, gate.main(["--bundle", str(self.root / "build/bundle.json")]))
        self.assertEqual("BLOCKED_UNTRUSTED_RUNTIME_PROVENANCE", json.loads(output.getvalue())["status"])

    def test_candidate_waiver_and_stale_identity_rejected(self):
        for key, value in (("version", "0.1.1-alpha.9"), ("commit", "0"*40), ("tree", "0"*40), ("jarSha256", "0"*64), ("lockSha256", "0"*64)):
            changed = copy.deepcopy(self.bundle); changed["candidate"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): gate.validate_bundle(self.root, changed)

    def test_receipts_reject_waiver_strings_boolean_exit_missing_log_and_missing_coverage(self):
        original = copy.deepcopy(self.receipts["gameplay"])
        for key, value in (("waived", True), ("tested", "true"), ("exitCode", False), ("exitCode", 1), ("coverage", []),
                           ("finishedAt", "2000-01-01T00:00:00Z"), ("candidate", {}), ("log", {"path":"missing","size":1,"sha256":"0"*64})):
            self.receipts["gameplay"] = copy.deepcopy(original); self.receipts["gameplay"][key] = value; self.save_receipts()
            with self.subTest(key=key,value=value), self.assertRaises(ValueError): gate.validate_bundle(self.root, self.bundle)

    def test_missing_receipt_or_extra_trust_flag_rejected(self):
        changed=copy.deepcopy(self.bundle); changed["receipts"].pop()
        with self.assertRaises(ValueError): gate.validate_bundle(self.root,changed)
        changed=copy.deepcopy(self.bundle); changed["trusted"]=True
        with self.assertRaises(ValueError): gate.validate_bundle(self.root,changed)

    def test_altered_log_rejected_even_when_receipt_claims_pass(self):
        self.write("build/evidence/client.log", "forged")
        with self.assertRaises(ValueError): gate.validate_bundle(self.root,self.bundle)

    def test_forged_log_with_updated_hash_still_cannot_certify_runtime(self):
        self.write("build/evidence/client.log", "Invented title-screen PASS")
        self.receipts["client"]["log"] = self.ref("build/evidence/client.log"); self.save_receipts()
        with patch.object(gate,"ROOT",self.root), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(2,gate.main(["--bundle",str(self.root/"build/bundle.json")]))

    def test_wrong_jar_version_cannot_be_borrowed_from_another_record(self):
        with zipfile.ZipFile(self.root / "build/sample_mod-0.1.1.jar", "w") as z:
            z.writestr("META-INF/neoforge.mods.toml", 'license="All Rights Reserved"\n[[mods]]\nmodId="sample_mod"\nversion="wrong"\n[[mods]]\nmodId="other"\nversion="0.1.1"\n')
        self.bundle["jar"] = self.ref("build/sample_mod-0.1.1.jar"); self.candidate["jarSha256"] = self.bundle["jar"]["sha256"]
        with self.assertRaisesRegex(ValueError,"same-record"): gate.validate_bundle(self.root,self.bundle)

    def test_install_missing_extra_or_changed_bytes_rejected(self):
        path = self.root / "build/mods/sample_mod-0.1.1.jar"; raw = path.read_bytes()
        path.unlink()
        with self.assertRaises(ValueError): gate.validate_bundle(self.root,self.bundle)
        path.write_bytes(raw + b"altered")
        with self.assertRaises(ValueError): gate.validate_bundle(self.root,self.bundle)
        path.write_bytes(raw)
        self.write("build/mods/extra.jar", raw)
        with self.assertRaises(ValueError): gate.validate_bundle(self.root,self.bundle)

    def test_paths_and_strict_raw_identity_rejected(self):
        for key,value in (("path","../outside"),("path","/etc/passwd"),("path","C:/outside"),("size",True),("sha256","invalid")):
            ref=copy.deepcopy(self.bundle["jar"]); ref[key]=value
            with self.subTest(key=key), self.assertRaises(ValueError): gate.reference(self.root,ref)

    def test_duplicate_json_keys_rejected(self):
        self.write("build/ambiguous.json", '{"a":1,"a":2}')
        with self.assertRaises(ValueError): gate.read_json(self.root/"build/ambiguous.json")

    def test_dirty_source_cannot_reuse_candidate_identity(self):
        self.write("LICENSE", "different")
        with self.assertRaisesRegex(ValueError,"clean"): gate.validate_bundle(self.root,self.bundle)

    def test_committed_manifest_identity_must_match_candidate(self):
        original = gate.read_json(self.root / "PROJECT_MANIFEST.json")
        for field, value in (("version", "0.1.1-alpha.9"), ("mod_id", "wrong_mod")):
            changed = copy.deepcopy(original); changed[field] = value
            self.write_json("PROJECT_MANIFEST.json", changed)
            self.run_git("add", "PROJECT_MANIFEST.json")
            self.run_git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "stale manifest fixture")
            self.candidate["commit"] = gate.git(self.root, "rev-parse", "HEAD")
            self.candidate["tree"] = gate.git(self.root, "rev-parse", "HEAD^{tree}")
            self.bundle["sourceManifest"] = self.ref("PROJECT_MANIFEST.json")
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Source manifest identity"):
                gate.validate_bundle(self.root, self.bundle)


class ProvenanceModeTests(unittest.TestCase):
    def test_authenticated_development_evidence_still_cannot_pass_stable_gate(self):
        with patch("tools.ci.candidate_evidence.verify", return_value={"authenticatedExecution": True, "stableReady": False}) as verify:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                result = gate.main(["--ci-run-id", "10", "--ci-attempt", "2", "--expected-commit", "a" * 40])
        self.assertEqual(2, result)
        self.assertFalse(json.loads(output.getvalue())["stableReady"])
        verify.assert_called_once_with(10, 2, "a" * 40)

    def test_partial_or_mixed_provenance_arguments_fail_before_readback(self):
        for args in ([], ["--ci-attempt", "1"], ["--ci-run-id", "10"],
                     ["--bundle", "local.json", "--ci-run-id", "10", "--ci-attempt", "1", "--expected-commit", "a" * 40]):
            with self.subTest(args=args), patch("tools.ci.candidate_evidence.verify") as verify:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(1, gate.main(args))
                verify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
