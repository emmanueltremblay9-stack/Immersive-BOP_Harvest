"""Source ZIP checks must work without Git and must never certify a binary release."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "scripts/refresh_project_manifest.py"


class SourceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "scripts").mkdir()
        shutil.copyfile(ROOT / SCRIPT, self.root / SCRIPT)
        (self.root / "gradle.properties").write_text("mod_version=1.0\nmod_id=test_mod\n", encoding="utf-8")
        (self.root / "source.txt").write_text("original source\n", encoding="utf-8")
        self.manifest = {"version": "1.0", "mod_id": "test_mod",
                         "build_summary": {"live_client_smoke_tested": False,
                                           "live_client_smoke_waived_by_owner": True},
                         "files": []}
        for name in (SCRIPT, "gradle.properties", "source.txt"):
            raw = (self.root / name).read_bytes()
            self.manifest["files"].append({"path": name, "size_bytes": len(raw),
                                           "sha256": hashlib.sha256(raw).hexdigest()})
        self.save()

    def save(self):
        (self.root / "PROJECT_MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def run_check(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=self.root,
                              capture_output=True, text=True, timeout=15)

    def test_archive_check_without_git_is_read_only(self):
        before = (self.root / "PROJECT_MANIFEST.json").read_bytes()
        result = self.run_check("--check")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("not a release gate", result.stdout)
        self.assertEqual(before, (self.root / "PROJECT_MANIFEST.json").read_bytes())

    def test_refresh_without_git_refuses_to_rebaseline(self):
        before = (self.root / "PROJECT_MANIFEST.json").read_bytes()
        result = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn("use --check", result.stdout)
        self.assertEqual(before, (self.root / "PROJECT_MANIFEST.json").read_bytes())

    def test_changed_and_missing_source_are_rejected(self):
        (self.root / "source.txt").write_text("changed\n", encoding="utf-8")
        self.assertEqual(1, self.run_check("--check").returncode)
        (self.root / "source.txt").unlink()
        self.assertEqual(1, self.run_check("--check").returncode)

    def test_unsafe_and_self_referencing_paths_are_rejected(self):
        for path in ("../outside", "/etc/passwd", "C:/outside", "a\\b", "a//b", "PROJECT_MANIFEST.json"):
            with self.subTest(path=path):
                self.manifest["files"][-1]["path"] = path
                self.save()
                self.assertEqual(1, self.run_check("--check").returncode)

    def test_duplicate_entries_and_json_keys_are_rejected(self):
        self.manifest["files"].append(self.manifest["files"][-1])
        self.save()
        self.assertEqual(1, self.run_check("--check").returncode)
        (self.root / "PROJECT_MANIFEST.json").write_text('{"files": [], "files": []}', encoding="utf-8")
        self.assertEqual(1, self.run_check("--check").returncode)

    def test_version_drift_is_rejected(self):
        self.manifest["version"] = "2.0"
        self.save()
        self.assertEqual(1, self.run_check("--check").returncode)

    def test_invalid_sizes_and_empty_ledger_are_rejected(self):
        for value in (True, -1, "16"):
            self.manifest["files"][-1]["size_bytes"] = value
            self.save()
            self.assertEqual(1, self.run_check("--check").returncode)
        self.manifest["files"] = []
        self.save()
        self.assertEqual(1, self.run_check("--check").returncode)

    @unittest.skipUnless(shutil.which("git"), "Git is needed only for refresh testing")
    def test_git_refresh_preserves_waiver_and_covers_staged_sources(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        result = self.run_check()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        updated = json.loads((self.root / "PROJECT_MANIFEST.json").read_text())
        self.assertEqual(self.manifest["build_summary"], updated["build_summary"])
        self.assertEqual(0, self.run_check("--check").returncode)
        (self.root / "new.txt").write_text("new\n", encoding="utf-8")
        subprocess.run(["git", "add", "new.txt"], cwd=self.root, check=True)
        self.assertEqual(1, self.run_check("--check").returncode)

    def test_repository_uses_active_metadata_not_bootstrap_examples(self):
        self.assertFalse((ROOT / "templates").exists())
        self.assertTrue((ROOT / "src/main/templates/META-INF/neoforge.mods.toml").is_file())
        self.assertTrue((ROOT / "gradle/wrapper/gradle-wrapper.jar").is_file())


if __name__ == "__main__":
    unittest.main()
