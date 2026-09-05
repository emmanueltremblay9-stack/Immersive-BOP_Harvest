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

        self.assertEqual(["Malformed source ledger entry"], failures)

    def test_rejects_path_outside_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            failures: list[str] = []
            with patch.object(gate, "ROOT", Path(temp_dir)):
                gate.validate_manifest_file_ledger(
                    {"files": [{"path": "../outside.txt", "size_bytes": 0, "sha256": ""}]},
                    failures,
                )

        self.assertEqual(["Unsafe or self-referencing source ledger path"], failures)

    def test_accepts_matching_file_inside_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "docs" / "proof.txt"
            file_path.parent.mkdir(parents=True)
            file_path.write_bytes(b"verified\n")
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


class LiveClientGateTests(unittest.TestCase):
    def test_accepts_proven_client_smoke(self) -> None:
        failures: list[str] = []

        gate.validate_live_client_gate(
            {
                "live_client_smoke_tested": True,
                "live_client_smoke_waived_by_owner": False,
            },
            failures,
        )

        self.assertEqual([], failures)

    def test_accepts_explicit_owner_waiver_without_claiming_test(self) -> None:
        failures: list[str] = []

        gate.validate_live_client_gate(
            {
                "live_client_smoke_tested": False,
                "live_client_smoke_waived_by_owner": True,
                "live_client_smoke_level": "not_performed_owner_waived",
                "live_client_smoke_waiver_reason": "Owner instructed Codex to skip this test phase.",
                "live_client_smoke_waiver_scope": "fresh alpha.9 Prism title-screen smoke",
            },
            failures,
        )

        self.assertEqual([], failures)

    def test_rejects_implicit_or_incomplete_waiver(self) -> None:
        failures: list[str] = []

        gate.validate_live_client_gate(
            {
                "live_client_smoke_tested": False,
                "live_client_smoke_waived_by_owner": True,
                "live_client_smoke_level": "not_performed_owner_waived",
            },
            failures,
        )

        self.assertEqual(["live client smoke owner waiver is incomplete or ambiguous"], failures)

    def test_rejects_contradictory_pass_and_waiver(self) -> None:
        failures: list[str] = []

        gate.validate_live_client_gate(
            {
                "live_client_smoke_tested": True,
                "live_client_smoke_waived_by_owner": True,
            },
            failures,
        )

        self.assertEqual(["live client smoke cannot be both tested and owner-waived"], failures)


if __name__ == "__main__":
    unittest.main()
