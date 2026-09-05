"""Both manifest consumers must agree on LF/CRLF and exact binary identity."""
import copy
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import refresh_project_manifest as refresh
from scripts import check_beta_release_gate as beta


class ManifestConsumerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "gradle.properties").write_bytes(b"mod_id=sample\nmod_version=1.0\n")
        (self.root / "source.txt").write_bytes(b"hello\n")
        (self.root / "payload.jar").write_bytes(b"binary\r\n")
        self.manifest = {"mod_id": "sample", "version": "1.0", "files": [
            refresh.file_entry(Path(name), self.root)
            for name in ("gradle.properties", "source.txt", "payload.jar")]}

    def outcomes(self):
        with patch.object(refresh, "ROOT", self.root), patch.object(beta, "ROOT", self.root):
            try:
                refresh.check_manifest(self.manifest, refresh.read_properties(self.root / "gradle.properties"))
                source_ok = True
            except (OSError, ValueError):
                source_ok = False
            errors = []
            with contextlib.redirect_stdout(io.StringIO()):
                beta.validate_manifest_file_ledger(self.manifest, errors)
            return source_ok, not errors

    def test_both_accept_lf_and_crlf_without_mutating_ledger(self):
        before = copy.deepcopy(self.manifest)
        for raw in (b"hello\n", b"hello\r\n"):
            (self.root / "source.txt").write_bytes(raw)
            self.assertEqual((True, True), self.outcomes())
        self.assertEqual(before, self.manifest)

    def test_both_reject_binary_newline_changes_and_raw_asset_hash_differs(self):
        before = beta.sha256_file(self.root / "payload.jar")
        (self.root / "payload.jar").write_bytes(b"binary\n")
        self.assertNotEqual(before, beta.sha256_file(self.root / "payload.jar"))
        self.assertEqual((False, False), self.outcomes())

    def test_both_reject_empty_duplicate_missing_unsafe_and_wrong_type_entries(self):
        original = copy.deepcopy(self.manifest)
        variants = [[], original["files"] * 2, ["bad"]]
        for field, value in (("path", "../outside"), ("path", "missing"),
                             ("size_bytes", True), ("sha256", "0" * 64)):
            entries = copy.deepcopy(original["files"])
            entries[0][field] = value
            variants.append(entries)
        for entries in variants:
            with self.subTest(entries=entries):
                self.manifest["files"] = entries
                self.assertEqual((False, False), self.outcomes())

    def test_both_reject_omitted_tracked_file(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True, capture_output=True)
        self.assertEqual((True, True), self.outcomes())
        self.manifest["files"].pop()
        self.assertEqual((False, False), self.outcomes())
