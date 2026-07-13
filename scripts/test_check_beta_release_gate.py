from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_beta_release_gate as gate


class ManifestFileLedgerTests(unittest.TestCase):
    def test_rejects_non_object_entry_without_crashing(self) -> None:
        failures: list[str] = []

        gate.validate_manifest_file_ledger({"files": ["not-an-object"]}, failures)

        self.assertEqual(["manifest file entry 0 is not an object"], failures)

    def test_rejects_path_outside_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            failures: list[str] = []
            with patch.object(gate, "ROOT", Path(temp_dir)):
                gate.validate_manifest_file_ledger(
                    {"files": [{"path": "../outside.txt", "size_bytes": 0, "sha256": ""}]},
                    failures,
                )

        self.assertEqual(["manifest file path escapes project root: ../outside.txt"], failures)

    def test_accepts_matching_file_inside_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "docs" / "proof.txt"
            file_path.parent.mkdir(parents=True)
            file_path.write_text("verified\n", encoding="utf-8")
            failures: list[str] = []

            with patch.object(gate, "ROOT", root):
                gate.validate_manifest_file_ledger(
                    {
                        "files": [
                            {
                                "path": "docs/proof.txt",
                                "size_bytes": file_path.stat().st_size,
                                "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
                            }
                        ]
                    },
                    failures,
                )

        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
