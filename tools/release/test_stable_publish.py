"""Secret-free mutation, recovery, and final-receipt fixtures."""
from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.parse
import zipfile

import stable_publish as publish


def make_jar() -> bytes:
    stream = io.BytesIO()
    metadata = (
        'modLoader="javafml"\nlicense="All Rights Reserved"\n'
        '[[mods]]\nmodId="immersive_bop_harvest"\nversion="0.1.1"\n'
    ).encode()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_STORED) as jar:
        jar.writestr("META-INF/neoforge.mods.toml", metadata)
    return stream.getvalue()


def archive_with_candidate(raw: bytes) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("candidate.jar", raw)
    return stream.getvalue()


class FakeSourceApi:
    def __init__(self, metadata, archive):
        self.metadata = metadata
        self.archive = archive
        self.receipts = {}
        self.receipt_persists = 0

    def persist_receipt(self, artifact_id: int, name: str, receipt: dict):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_STORED) as archive:
            archive.writestr(
                "stable-publication-receipt.json",
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            )
        self.receipts[artifact_id] = {
            "metadata": {"id": artifact_id, "name": name, "expired": False},
            "archive": stream.getvalue(),
        }
        self.receipt_persists += 1

    def get(self, path: str, *, binary: bool = False):
        if path.startswith("actions/artifacts?name=") and not binary:
            query = urllib.parse.parse_qs(urllib.parse.urlsplit("?" + path.split("?", 1)[1]).query)
            name = query["name"][0]
            artifacts = [
                copy.deepcopy(value["metadata"])
                for value in self.receipts.values()
                if value["metadata"]["name"] == name
            ]
            return {"total_count": len(artifacts), "artifacts": artifacts}
        match = path.removeprefix("actions/artifacts/").removesuffix("/zip")
        if match.isdigit() and int(match) in self.receipts:
            value = self.receipts[int(match)]
            return value["archive"] if binary else copy.deepcopy(value["metadata"])
        if path.endswith("/zip") and binary:
            return self.archive
        if path.startswith("actions/artifacts/") and not binary:
            return self.metadata
        raise AssertionError(path)


class FakeGitHub:
    def __init__(self, source_sha: str):
        self.source_sha = source_sha
        self.tag_ref = None
        self.annotated = {}
        self.release = None
        self.asset_bytes = {}
        self.tag_posts = 0
        self.release_posts = 0
        self.asset_posts = 0

    def get_optional(self, path: str):
        if path == "git/ref/heads/main":
            return {"object": {"type": "commit", "sha": self.source_sha}}
        if path.startswith("git/ref/tags/"):
            return copy.deepcopy(self.tag_ref)
        if path.startswith("git/tags/"):
            return copy.deepcopy(self.annotated.get(path.rsplit("/", 1)[1]))
        if path.startswith("releases/tags/"):
            return copy.deepcopy(self.release)
        raise AssertionError(path)

    def get_public_optional(self, path: str):
        return self.get_optional(path)

    def get_public_bytes(self, url: str):
        return self.asset_bytes[url]

    def post_json(self, path: str, payload):
        if path == "git/refs":
            self.tag_posts += 1
            self.tag_ref = {"object": {"type": "commit", "sha": payload["sha"]}}
            return self.tag_ref
        if path == "releases":
            self.release_posts += 1
            self.release = {
                "id": 501,
                "tag_name": payload["tag_name"],
                "target_commitish": payload["target_commitish"],
                "name": payload["name"],
                "body": payload["body"],
                "draft": payload["draft"],
                "prerelease": payload["prerelease"],
                "html_url": "https://example.invalid/release/501",
                "upload_url": "https://uploads.example.invalid/501/assets{?name,label}",
                "assets": [],
            }
            return self.release
        raise AssertionError(path)

    def upload_asset(self, upload_url: str, name: str, raw: bytes):
        self.asset_posts += 1
        url = "https://example.invalid/assets/601"
        asset = {
            "id": 601,
            "name": name,
            "size": len(raw),
            "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "browser_download_url": url,
        }
        self.release["assets"].append(asset)
        self.asset_bytes[url] = raw
        return asset

    def seed_tag(self):
        self.tag_ref = {"object": {"type": "commit", "sha": self.source_sha}}

    def seed_release(self, notes: str):
        self.seed_tag()
        self.post_json("releases", {
            "tag_name": publish.TAG, "target_commitish": self.source_sha,
            "name": publish.TITLE, "body": notes, "draft": False,
            "prerelease": False,
        })
        self.release_posts = 0

    def seed_complete(self, notes: str, candidate: dict, raw: bytes):
        self.seed_release(notes)
        self.upload_asset(self.release["upload_url"], candidate["name"], raw)
        self.asset_posts = 0


class FakeCurseForge:
    def __init__(self, candidate: dict, contract: dict):
        self.candidate = candidate
        self.contract = contract
        self.intent_persists = 0
        self.posts = 0
        self.file_id = None
        self.public = None
        self.readback_calls = 0

    def complete(self):
        if self.file_id is None:
            self.intent_persists += 1
            self.posts += 1
            self.file_id = 7001
        relations = [
            {"projectId": project, "slug": slug, "type": kind}
            for project, slug, kind in publish.EXPECTED_RELATIONS
        ]
        self.public = {
            "fileId": self.file_id,
            "projectId": self.contract["projectId"],
            "fileName": self.candidate["name"],
            "releaseType": 1, "status": 4,
            "gameVersions": ["Client", "Server", "1.21.1", "NeoForge"],
            "relations": relations, "size": self.candidate["size"],
            "sha256": self.candidate["sha256"],
        }
        return {
            "status": "PUBLISHED_VERIFIED" if self.posts else "ALREADY_PUBLISHED",
            "verdict": "PASS", "fileId": self.file_id,
            "publicHashMatch": True,
            "publicReadback": copy.deepcopy(self.public),
        }

    def readback_public_release(self, file_id):
        self.readback_calls += 1
        if self.public is None or file_id != self.file_id:
            raise publish.MutationError("CURSEFORGE_FRESH_READBACK_MISSING")
        return copy.deepcopy(self.public)


class StablePublishTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="stable-publish-test-")
        self.root = Path(self.temporary.name)
        self.notes = "# Immersive BOP Harvest 0.1.1\n\nFixture notes.\n"
        notes_path = self.root / publish.stable_autopublish.EXPECTED_NOTES
        notes_path.parent.mkdir(parents=True)
        notes_path.write_text(self.notes, encoding="utf-8")
        self.notes = notes_path.read_bytes().decode("utf-8")
        self.manifest = {
            "curseforge": {
                "gameVersionNames": ["Client", "Server", "1.21.1", "NeoForge"]
            }
        }
        manifest_raw = json.dumps(self.manifest, sort_keys=True).encode()
        manifest_path = self.root / publish.stable_autopublish.EXPECTED_MANIFEST
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_bytes(manifest_raw)
        self.raw = make_jar()
        self.candidate = {
            **publish.candidate_evidence.jar_identity(self.raw),
            "name": "immersive_bop_harvest-0.1.1.jar",
            "size": len(self.raw),
            "sha256": hashlib.sha256(self.raw).hexdigest(),
        }
        self.source_sha = "a" * 40
        self.tree = "b" * 40
        self.archive = archive_with_candidate(self.raw)
        self.source = {
            "runId": 123, "runAttempt": 1, "sourceCommit": self.source_sha,
            "sourceTree": self.tree, "artifactId": 456,
            "archiveSha256": hashlib.sha256(self.archive).hexdigest(),
        }
        self.contract = {
            "path": publish.stable_autopublish.EXPECTED_MANIFEST,
            "sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "notesPath": publish.stable_autopublish.EXPECTED_NOTES,
            "notesSha256": hashlib.sha256(notes_path.read_bytes()).hexdigest(),
            "tag": publish.TAG,
            "projectId": 1609013,
            "projectSlug": "immersive-bop-harvest",
            "historicalFileRelations": 3,
            "historicalProjectRelations": 0,
            "targetRelations": 5,
        }
        self.identity = {
            "runId": 123, "runAttempt": 1, "sourceCommit": self.source_sha,
            "sourceTree": self.tree, "artifactId": 456,
            "archiveSha256": self.source["archiveSha256"],
            "candidateSha256": self.candidate["sha256"],
            "manifestSha256": self.contract["sha256"],
            "notesSha256": self.contract["notesSha256"],
        }
        self.report = {
            "repository": publish.REPOSITORY,
            "sourceReady": True, "stableReady": True, "autoPublishEligible": True,
            "publicationComplete": False,
            "publicationAuthority": "AUTHORIZED_WHEN_ELIGIBLE",
            "releasePolicy": {"targets": ["github", "curseforge"],
                              "modrinth": "FORBIDDEN_BY_PROJECT_POLICY"},
            "workflowRun": {"headSha": self.source_sha},
            "authenticatedSource": self.source,
            "candidate": self.candidate, "releaseContract": self.contract,
            "idempotenceKey": hashlib.sha256(
                publish.final_release_bundle.canonical_json(self.identity)
            ).hexdigest(),
        }
        metadata = {
            "id": 456, "expired": False,
            "workflow_run": {"id": 123, "head_sha": self.source_sha},
        }
        self.source_api = FakeSourceApi(metadata, self.archive)
        self.verify = patch.object(publish.stable_autopublish, "verify_checkout")
        self.verify.start()

    def tearDown(self):
        self.verify.stop()
        self.temporary.cleanup()

    def machine(self, github, curseforge=None):
        return publish.StablePublication(
            self.root, github, self.source_api, curseforge_public=curseforge
        )

    def mutate(self, github):
        return self.machine(github).mutate_github(
            self.report, self.root / self.candidate["name"]
        )

    def test_publication_key_uses_shared_producer_canonicalization(self):
        producer_key = hashlib.sha256(
            publish.final_release_bundle.canonical_json(self.identity)
        ).hexdigest()
        consumer_key = hashlib.sha256(
            publish.canonical_json(self.identity)
        ).hexdigest()

        self.assertNotEqual(producer_key, consumer_key)
        self.assertEqual(producer_key, self.report["idempotenceKey"])
        validated = self.machine(FakeGitHub(self.source_sha)).validate_source_report(
            self.report
        )
        self.assertEqual(producer_key, validated["publicationKey"])

        wrong = copy.deepcopy(self.report)
        wrong["idempotenceKey"] = consumer_key
        with self.assertRaisesRegex(
            publish.MutationError, "PUBLICATION_KEY_MISMATCH"
        ):
            self.machine(FakeGitHub(self.source_sha)).validate_source_report(wrong)

    def test_absent_tag_creates_exactly_once(self):
        github = FakeGitHub(self.source_sha)
        self.mutate(github)
        self.assertEqual(1, github.tag_posts)

    def test_exact_tag_does_not_recreate(self):
        github = FakeGitHub(self.source_sha); github.seed_tag()
        self.mutate(github)
        self.assertEqual(0, github.tag_posts)

    def test_divergent_tag_stops(self):
        github = FakeGitHub(self.source_sha)
        github.tag_ref = {"object": {"type": "commit", "sha": "c" * 40}}
        with self.assertRaisesRegex(publish.MutationError, "TAG_DIVERGENT_STOP"):
            self.mutate(github)
        self.assertEqual((0, 0, 0), (github.tag_posts, github.release_posts, github.asset_posts))

    def test_annotated_tag_exact_dereference_is_accepted(self):
        github = FakeGitHub(self.source_sha)
        github.tag_ref = {"object": {"type": "tag", "sha": "d" * 40}}
        github.annotated["d" * 40] = {
            "object": {"type": "commit", "sha": self.source_sha}
        }
        self.mutate(github)
        self.assertEqual(0, github.tag_posts)

    def test_absent_release_creates_once(self):
        github = FakeGitHub(self.source_sha); github.seed_tag()
        self.mutate(github)
        self.assertEqual(1, github.release_posts)

    def test_exact_release_and_asset_reconcile_without_mutation(self):
        github = FakeGitHub(self.source_sha)
        github.seed_complete(self.notes, self.candidate, self.raw)
        result = self.mutate(github)
        self.assertEqual([], result["operations"])
        self.assertEqual((0, 0, 0), (github.tag_posts, github.release_posts, github.asset_posts))

    def test_draft_or_prerelease_release_stops(self):
        for field in ("draft", "prerelease"):
            github = FakeGitHub(self.source_sha); github.seed_release(self.notes)
            github.release[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(
                publish.MutationError, "RELEASE_DIVERGENT_STOP"
            ):
                self.mutate(github)

    def test_divergent_notes_stop(self):
        github = FakeGitHub(self.source_sha); github.seed_release("wrong")
        with self.assertRaisesRegex(publish.MutationError, "RELEASE_DIVERGENT_STOP"):
            self.mutate(github)

    def test_missing_asset_uploads_once(self):
        github = FakeGitHub(self.source_sha); github.seed_release(self.notes)
        self.mutate(github)
        self.assertEqual(1, github.asset_posts)

    def test_same_name_wrong_hash_stops(self):
        github = FakeGitHub(self.source_sha); github.seed_release(self.notes)
        github.upload_asset(github.release["upload_url"], self.candidate["name"], b"wrong")
        github.asset_posts = 0
        with self.assertRaisesRegex(publish.MutationError, "ASSET_DIVERGENT_STOP"):
            self.mutate(github)

    def test_duplicate_or_extra_assets_stop(self):
        for extra_name in (self.candidate["name"], "unexpected-extra.jar"):
            github = FakeGitHub(self.source_sha)
            github.seed_complete(self.notes, self.candidate, self.raw)
            github.release["assets"].append({
                **github.release["assets"][0], "id": 602, "name": extra_name
            })
            with self.subTest(extra=extra_name), self.assertRaisesRegex(
                publish.MutationError, "ASSET_DIVERGENT_STOP"
            ):
                self.mutate(github)

    def test_completed_github_retry_has_zero_mutations(self):
        github = FakeGitHub(self.source_sha)
        first = self.mutate(github)
        counts = (github.tag_posts, github.release_posts, github.asset_posts)
        second = self.mutate(github)
        self.assertEqual(counts, (github.tag_posts, github.release_posts, github.asset_posts))
        self.assertEqual([], second["operations"])
        self.assertEqual(first["publicationKey"], second["publicationKey"])

    def test_github_timeout_after_remote_commit_reconciles_each_mutation(self):
        for phase in ("tag", "release", "asset"):
            github = FakeGitHub(self.source_sha)
            if phase == "release":
                github.seed_tag()
            elif phase == "asset":
                github.seed_release(self.notes)
            if phase in {"tag", "release"}:
                original = github.post_json

                def uncertain(path, payload, *, target=phase, delegate=original):
                    value = delegate(path, payload)
                    if (target == "tag" and path == "git/refs") or (
                        target == "release" and path == "releases"
                    ):
                        raise TimeoutError("simulated response loss")
                    return value

                patched = patch.object(github, "post_json", side_effect=uncertain)
            else:
                original_upload = github.upload_asset

                def uncertain_upload(upload_url, name, raw, *, delegate=original_upload):
                    delegate(upload_url, name, raw)
                    raise TimeoutError("simulated response loss")

                patched = patch.object(github, "upload_asset", side_effect=uncertain_upload)
            with self.subTest(phase=phase), patched:
                result = self.mutate(github)
                self.assertEqual("GITHUB_PUBLICATION_VERIFIED", result["status"])
                expected = {
                    "tag": (1, 1, 1),
                    "release": (0, 1, 1),
                    "asset": (0, 0, 1),
                }[phase]
                self.assertEqual(expected, (
                    github.tag_posts, github.release_posts, github.asset_posts,
                ))

    def test_stale_main_and_invalid_policy_block_before_mutation(self):
        github = FakeGitHub("f" * 40)
        with self.assertRaisesRegex(publish.MutationError, "CURRENT_MAIN_DRIFT_STOP"):
            self.mutate(github)
        bad = copy.deepcopy(self.report); bad["publicationAuthority"] = "INVALID"
        github = FakeGitHub(self.source_sha)
        with self.assertRaisesRegex(publish.MutationError, "STANDING_POLICY_INVALID"):
            self.machine(github).mutate_github(bad, self.root / "candidate.jar")

    def test_finalizer_rejects_hash_and_relation_mismatches(self):
        github = FakeGitHub(self.source_sha)
        gh_report = self.mutate(github)
        curseforge = FakeCurseForge(self.candidate, self.contract)
        cf = curseforge.complete()
        for mutation in ("hash", "relations", "file-id"):
            wrong = copy.deepcopy(cf)
            if mutation == "hash":
                wrong["publicReadback"]["sha256"] = "0" * 64
            elif mutation == "relations":
                wrong["publicReadback"]["relations"].pop()
            else:
                wrong["publicReadback"]["fileId"] = wrong["fileId"] + 1
            with self.subTest(mutation=mutation), self.assertRaisesRegex(
                publish.MutationError,
                "CURSEFORGE_REPORT_FRESH_READBACK_MISMATCH|CURSEFORGE_FILE_ID_INVALID",
            ):
                self.machine(github, curseforge).finalize(
                    self.report, gh_report, wrong
                )

    def test_finalizer_requires_fresh_curseforge_public_readback(self):
        github = FakeGitHub(self.source_sha)
        gh_report = self.mutate(github)
        report = FakeCurseForge(self.candidate, self.contract).complete()
        with self.assertRaisesRegex(
            publish.MutationError, "CURSEFORGE_FRESH_READBACK_UNAVAILABLE"
        ):
            self.machine(github).finalize(self.report, gh_report, report)

    def test_secret_free_end_to_end_and_completed_retry_are_idempotent(self):
        github = FakeGitHub(self.source_sha)
        curseforge = FakeCurseForge(self.candidate, self.contract)
        gh_first = self.mutate(github)
        cf_first = curseforge.complete()
        receipt_first = self.machine(github, curseforge).finalize(
            self.report, gh_first, cf_first
        )
        counts = (github.tag_posts, github.release_posts, github.asset_posts,
                  curseforge.intent_persists, curseforge.posts)
        gh_second = self.mutate(github)
        cf_second = curseforge.complete()
        receipt_second = self.machine(github, curseforge).finalize(
            self.report, gh_second, cf_second
        )
        receipt_state = self.machine(github).reconcile_receipt(receipt_first)
        self.assertTrue(receipt_state["uploadRequired"])
        self.source_api.persist_receipt(9001, receipt_state["artifactName"], receipt_first)
        verified = self.machine(github).verify_receipt(receipt_first, 9001)
        retry_state = self.machine(github).reconcile_receipt(receipt_second)
        self.assertTrue(receipt_first["publicationComplete"])
        self.assertEqual(receipt_first, receipt_second)
        self.assertEqual(counts, (github.tag_posts, github.release_posts, github.asset_posts,
                                  curseforge.intent_persists, curseforge.posts))
        self.assertEqual((1, 1, 1, 1, 1), counts)
        self.assertEqual(2, curseforge.readback_calls)
        self.assertEqual("RECEIPT_PERSISTENCE_VERIFIED", verified["status"])
        self.assertFalse(retry_state["uploadRequired"])
        self.assertEqual(1, self.source_api.receipt_persists)
        self.assertEqual(
            "FORBIDDEN_BY_PROJECT_POLICY", receipt_first["releasePolicy"]["modrinth"]
        )

    def test_final_receipt_normalizes_public_relation_order(self):
        github = FakeGitHub(self.source_sha)
        gh_report = self.mutate(github)
        curseforge = FakeCurseForge(self.candidate, self.contract)
        first = curseforge.complete()
        second = copy.deepcopy(first)
        second["publicReadback"]["relations"].reverse()
        receipt_first = self.machine(github, curseforge).finalize(
            self.report, gh_report, first
        )
        receipt_second = self.machine(github, curseforge).finalize(
            self.report, gh_report, second
        )
        self.assertEqual(receipt_first, receipt_second)


if __name__ == "__main__":
    unittest.main()
