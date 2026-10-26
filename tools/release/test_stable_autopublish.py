"""Read-only stable workflow-run and authority-policy regressions."""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import stable_autopublish as auto


class FakeApi:
    def __init__(self, main_sha: str):
        self.main_sha = main_sha

    def get(self, path: str, *, binary: bool = False):
        if path == "git/ref/heads/main" and not binary:
            return {"object": {"type": "commit", "sha": self.main_sha}}
        raise AssertionError(f"unexpected API call: {path}")


class StableAutopublishTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.event = {
            "repository": {"full_name": auto.EXPECTED_REPOSITORY},
            "workflow_run": {
                "id": 123,
                "run_attempt": 2,
                "name": auto.EXPECTED_WORKFLOW_NAME,
                "path": auto.EXPECTED_WORKFLOW_PATH,
                "event": "push",
                "head_branch": "main",
                "head_sha": self.sha,
                "head_repository": {"full_name": auto.EXPECTED_REPOSITORY},
                "status": "completed",
                "conclusion": "success",
            },
        }
        self.candidate = {
            "modId": "immersive_bop_harvest",
            "version": "0.1.1",
            "license": "All Rights Reserved",
            "name": "immersive_bop_harvest-0.1.1.jar",
            "size": 1606577,
            "sha256": "edcedc52d8b0fc2952bcffb7c54f3737ed144227350a5b46ea71620dd3859394",
        }
        self.evidence = {
            "authenticatedExecution": True,
            "status": "AUTHENTICATED_PACKAGED_EXECUTION",
            "runId": 123,
            "runAttempt": 2,
            "sourceCommit": self.sha,
            "sourceTree": "b" * 40,
            "artifactId": 456,
            "archiveSha256": "c" * 64,
            "candidate": self.candidate,
        }

    @staticmethod
    def all_gates():
        return {name: True for name in auto.AUTO_PUBLISH_GATE_NAMES}

    def evaluate(self, gates=None):
        with (
            patch.object(auto, "verify_checkout"),
            patch.object(auto.candidate_evidence, "verify", return_value=self.evidence),
            patch.object(auto.final_release_bundle, "build_authenticated", return_value=b"bundle"),
            patch.object(auto.final_release_bundle, "validate_authenticated", return_value={"stableReady": True}),
        ):
            return auto.evaluate_source_readiness(
                self.event,
                auto.ROOT,
                api=FakeApi(self.sha),
                credential_available=True,
                _runtime_gate_evidence=self.all_gates() if gates is None else gates,
            )

    def test_standing_policy_all_gates_pass_is_eligible_and_deterministic(self):
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first, second)
        self.assertTrue(first["sourceReady"])
        self.assertTrue(first["stableReady"])
        self.assertTrue(first["autoPublishEligible"])
        self.assertFalse(first["publicationComplete"])
        self.assertEqual("AUTHORIZED_WHEN_ELIGIBLE", first["publicationAuthority"])
        self.assertEqual([], first["autoPublishBlockers"])
        self.assertEqual("PASS", first["verdict"])
        self.assertEqual("FORBIDDEN_BY_PROJECT_POLICY", first["releasePolicy"]["modrinth"])

    def test_no_one_off_owner_approval_gate_exists(self):
        result = auto.evaluate_auto_publish_eligibility(self.all_gates())
        self.assertTrue(result["autoPublishEligible"])
        self.assertNotIn("ownerApproval", result["runtimeGates"])
        self.assertNotIn("PUBLICATION_AUTHORITY_NOT_GRANTED", json.dumps(result))

    def test_wrong_workflow_source_never_qualifies(self):
        changes = {
            "name": "Other",
            "path": ".github/workflows/other.yml",
            "event": "pull_request",
            "head_branch": "feature",
            "status": "queued",
            "conclusion": "failure",
            "run_attempt": 0,
            "head_sha": "bad",
            "head_repository": {"full_name": "other/repo"},
        }
        for field, value in changes.items():
            event = copy.deepcopy(self.event)
            event["workflow_run"][field] = value
            with self.subTest(field=field), self.assertRaises(auto.ReadinessError):
                auto.validate_workflow_run(event)

    def test_stale_current_main_blocks_before_candidate_authentication(self):
        with (
            patch.object(auto, "verify_checkout") as checkout,
            patch.object(auto.candidate_evidence, "verify") as verify,
            self.assertRaisesRegex(auto.ReadinessError, "current main"),
        ):
            auto.evaluate_source_readiness(
                self.event, auto.ROOT, api=FakeApi("d" * 40)
            )
        checkout.assert_not_called()
        verify.assert_not_called()

    def test_candidate_run_attempt_artifact_or_digest_mismatch_blocks(self):
        for reason in (
            "Run/attempt/source identity mismatch",
            "Missing, duplicate or expired candidate artifact",
            "Service digest missing or artifact altered",
        ):
            with (
                self.subTest(reason=reason),
                patch.object(auto, "verify_checkout"),
                patch.object(auto.candidate_evidence, "verify", side_effect=ValueError(reason)),
                self.assertRaisesRegex(ValueError, reason),
            ):
                auto.evaluate_source_readiness(
                    self.event, auto.ROOT, api=FakeApi(self.sha)
                )

    def test_manifest_candidate_and_notes_mismatches_block(self):
        wrong = copy.deepcopy(self.candidate)
        wrong["sha256"] = "0" * 64
        with self.assertRaisesRegex(auto.ReadinessError, "candidate bytes"):
            auto.validate_release_contract(auto.ROOT, wrong)
        with tempfile.TemporaryDirectory(prefix="stable-contract-test-") as temporary:
            root = Path(temporary)
            manifest = root / auto.EXPECTED_MANIFEST
            notes = root / auto.EXPECTED_NOTES
            manifest.parent.mkdir(parents=True)
            notes.parent.mkdir(parents=True)
            manifest.write_bytes((auto.ROOT / auto.EXPECTED_MANIFEST).read_bytes())
            notes.write_text("0.1.1 changed notes", encoding="utf-8")
            with self.assertRaisesRegex(auto.ReadinessError, "notes path or hash"):
                auto.validate_release_contract(root, self.candidate)

    def test_template_manifest_never_qualifies(self):
        with tempfile.TemporaryDirectory(prefix="stable-template-test-") as temporary:
            root = Path(temporary)
            manifest = root / auto.EXPECTED_MANIFEST
            notes = root / auto.EXPECTED_NOTES
            manifest.parent.mkdir(parents=True)
            notes.parent.mkdir(parents=True)
            manifest.write_bytes(
                (auto.ROOT / "tools/release/curseforge_release_TEMPLATE.json").read_bytes()
            )
            notes.write_bytes((auto.ROOT / auto.EXPECTED_NOTES).read_bytes())
            with self.assertRaises(auto.publish_curseforge.PublicationError):
                auto.validate_release_contract(root, self.candidate)

    def test_any_unstable_or_unverified_gate_is_ineligible(self):
        for gate in (
            "authenticatedStableGate",
            "credentialAvailable",
            "curseForgeProjectIdentity",
            "historicalFileRelations",
            "historicalProjectRelations",
            "targetRelations",
            "gitTagNonDivergent",
            "githubReleaseNonDivergent",
            "githubAssetNonDivergent",
            "curseForgeArtifactNonDivergent",
        ):
            gates = self.all_gates()
            gates[gate] = False
            with self.subTest(gate=gate):
                result = auto.evaluate_auto_publish_eligibility(gates)
                self.assertFalse(result["autoPublishEligible"])
                self.assertIn(f"GATE_NOT_VERIFIED:{gate}", result["autoPublishBlockers"])

    def test_missing_unknown_or_non_boolean_gate_fails_closed(self):
        cases = []
        missing = self.all_gates()
        missing.pop("versionedManifest")
        cases.append(missing)
        unknown = self.all_gates()
        unknown["ownerApproval"] = True
        cases.append(unknown)
        non_boolean = self.all_gates()
        non_boolean["releaseNotesHash"] = "UNKNOWN"
        cases.append(non_boolean)
        for gates in cases:
            with self.subTest(keys=sorted(gates)):
                self.assertFalse(
                    auto.evaluate_auto_publish_eligibility(gates)["autoPublishEligible"]
                )

    def test_identity_http_403_is_ineligible(self):
        blocked = auto.publish_curseforge.PublicationError(
            "CURSEFORGE_PROJECT_IDENTITY_BLOCKED",
            "fixture 403",
            auto.publish_curseforge.EXIT_CONFLICT,
        )
        with patch.object(
            auto.publish_curseforge.Publisher,
            "_validate_previous_public_baseline",
            side_effect=blocked,
        ):
            gates, _states, blockers = auto.collect_runtime_gate_evidence(
                auto.ROOT,
                run={"headSha": self.sha},
                candidate=self.candidate,
                contract={"targetRelations": 5},
                credential_available=True,
            )
        result = auto.evaluate_auto_publish_eligibility(
            gates, extra_blockers=blockers
        )
        self.assertFalse(result["autoPublishEligible"])
        self.assertIn("CURSEFORGE_PROJECT_IDENTITY_BLOCKED", result["autoPublishBlockers"])

    def test_modrinth_and_nonstable_or_manual_exception_do_not_inherit_policy(self):
        for gate in ("modrinthNotApplicable", "stableRelease", "automaticInvocation"):
            gates = self.all_gates()
            gates[gate] = False
            with self.subTest(gate=gate):
                self.assertFalse(
                    auto.evaluate_auto_publish_eligibility(gates)["autoPublishEligible"]
                )

    def test_exact_targets_reconcile_and_divergence_stops(self):
        expected = {"sha": self.sha}
        self.assertEqual(
            "ABSENT_READY",
            auto.reconcile_exact("GITHUB_TAG", None, expected),
        )
        self.assertEqual(
            "EXACT_RECONCILED",
            auto.reconcile_exact("GITHUB_RELEASE", expected, expected),
        )
        for kind in ("GITHUB_TAG", "GITHUB_RELEASE", "CURSEFORGE_FILE"):
            with self.subTest(kind=kind), self.assertRaisesRegex(
                auto.ReadinessError, "DIVERGENT_STOP"
            ):
                auto.reconcile_exact(kind, {"sha": "wrong"}, expected)

    def test_nested_annotated_tag_dereference_and_cycle_guard(self):
        first, second = "b" * 40, "c" * 40
        exact = {
            "git/ref/tags/v0.1.1": {"object": {"type": "tag", "sha": first}},
            f"git/tags/{first}": {"object": {"type": "tag", "sha": second}},
            f"git/tags/{second}": {"object": {"type": "commit", "sha": self.sha}},
        }
        with patch.object(auto, "_github_optional", side_effect=exact.__getitem__):
            self.assertEqual("EXACT_RECONCILED", auto._github_tag_state(self.sha))
        cyclic = copy.deepcopy(exact)
        cyclic[f"git/tags/{second}"] = {"object": {"type": "tag", "sha": first}}
        with (
            patch.object(auto, "_github_optional", side_effect=cyclic.__getitem__),
            self.assertRaisesRegex(auto.ReadinessError, "GITHUB_TAG_AMBIGUOUS_STOP"),
        ):
            auto._github_tag_state(self.sha)

    def test_github_release_with_unexpected_extra_asset_is_divergent(self):
        release = {
            "tag_name": auto.EXPECTED_TAG,
            "target_commitish": self.sha,
            "draft": False,
            "prerelease": False,
            "name": "Immersive BOP Harvest 0.1.1",
            "body": "exact notes",
            "assets": [
                {
                    "name": self.candidate["name"],
                    "size": self.candidate["size"],
                    "digest": f"sha256:{self.candidate['sha256']}",
                },
                {
                    "name": "unexpected-extra.jar",
                    "size": 1,
                    "digest": "sha256:" + "0" * 64,
                },
            ],
        }
        with (
            patch.object(auto, "_github_optional", return_value=release),
            self.assertRaisesRegex(auto.ReadinessError, "GITHUB_ASSET_DIVERGENT_STOP"),
        ):
            auto._github_release_state(
                tag_state="EXACT_RECONCILED",
                candidate={**self.candidate, "sourceCommit": self.sha},
                notes="exact notes",
            )

    def test_github_release_with_malformed_asset_is_divergent(self):
        release = {
            "tag_name": auto.EXPECTED_TAG,
            "target_commitish": self.sha,
            "draft": False,
            "prerelease": False,
            "name": "Immersive BOP Harvest 0.1.1",
            "body": "exact notes",
            "assets": [
                {
                    "name": self.candidate["name"],
                    "size": self.candidate["size"],
                    "digest": f"sha256:{self.candidate['sha256']}",
                },
                "malformed-extra",
            ],
        }
        with (
            patch.object(auto, "_github_optional", return_value=release),
            self.assertRaisesRegex(auto.ReadinessError, "GITHUB_RELEASE_DIVERGENT_STOP"),
        ):
            auto._github_release_state(
                tag_state="EXACT_RECONCILED",
                candidate={**self.candidate, "sourceCommit": self.sha},
                notes="exact notes",
            )

    def test_exact_release_with_missing_asset_is_resumable(self):
        release = {
            "tag_name": auto.EXPECTED_TAG,
            "target_commitish": self.sha,
            "draft": False,
            "prerelease": False,
            "name": "Immersive BOP Harvest 0.1.1",
            "body": "exact notes",
            "assets": [],
        }
        with patch.object(auto, "_github_optional", return_value=release):
            states = auto._github_release_state(
                tag_state="EXACT_RECONCILED",
                candidate={**self.candidate, "sourceCommit": self.sha},
                notes="exact notes",
            )
        self.assertEqual(("RELEASE_EXACT", "ASSET_ABSENT_READY"), states)

    def test_cli_separates_eligible_and_packet_stop_states(self):
        eligible = {"autoPublishEligible": True, "status": "AUTO_PUBLISH_ELIGIBLE"}
        blocked = {"autoPublishEligible": False, "status": "AUTO_PUBLISH_BLOCKED"}
        with tempfile.TemporaryDirectory(prefix="stable-cli-test-") as temporary:
            event = Path(temporary) / "event.json"
            output = Path(temporary) / "report.json"
            event.write_text(json.dumps(self.event), encoding="utf-8")
            for report, expected in ((eligible, 0), (blocked, 2)):
                with (
                    self.subTest(report=report),
                    patch.object(auto, "evaluate_source_readiness", return_value=report),
                    patch("sys.stdout", new_callable=io.StringIO),
                ):
                    code = auto.main([
                        "--event", str(event), "--repo-root", str(auto.ROOT),
                        "--report", str(output),
                    ])
                self.assertEqual(expected, code)
                self.assertEqual(report, json.loads(output.read_text(encoding="utf-8")))

    def test_source_evaluator_has_no_public_mutation_or_secret_value_path(self):
        text = Path(auto.__file__).read_text(encoding="utf-8")
        self.assertNotIn("CURSEFORGE_API_TOKEN", text)
        self.assertNotIn("post_json", text)
        self.assertNotIn('"POST"', text)
        self.assertNotIn("modrinth.com", text.lower())


if __name__ == "__main__":
    unittest.main()
