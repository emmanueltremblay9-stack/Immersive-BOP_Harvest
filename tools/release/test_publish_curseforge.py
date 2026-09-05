# Synthetic fixture IDs and bytes below are never release configuration.
from __future__ import annotations

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from publish_curseforge import (
    EXIT_AUTHORIZATION,
    EXIT_CONFLICT,
    EXIT_PROCESSING,
    EXIT_TOKEN_MISSING,
    HttpClient,
    PERSIST_INTENT_STEP_NAME,
    PublicationError,
    Publisher,
    build_multipart,
    state_artifact_prefix,
)


VERSION = "0.4.2-fixture"
TAG = f"v{VERSION}"
ASSET_NAME = f"sample_mod-{VERSION}.jar"
MOD_ID = "sample_mod"
PROJECT_ID = 100001
PREVIOUS_FILE_ID = 100002
NEW_FILE_ID = 9001001
ARTIFACT_PREFIX = state_artifact_prefix(TAG)
UPLOAD_RELATIONS = [
    {
        "projectID": 100013,
        "slug": "required-mod",
        "type": "requiredDependency",
    }
]
EXPECTED_RELATIONS = [
    {"projectId": 100010, "slug": "source-a", "type": "Include"},
    {"projectId": 100011, "slug": "source-b", "type": "Include"},
    {
        "projectId": 100012,
        "slug": "source-c",
        "type": "Include",
    },
    {
        "projectId": 100013,
        "slug": "required-mod",
        "type": "RequiredDependency",
    },
]


def make_jar(version: str = VERSION) -> bytes:
    stream = io.BytesIO()
    metadata = (
        'modLoader="javafml"\n'
        "[[mods]]\n"
        f'modId="{MOD_ID}"\n'
        f'version="{version}"\n'
    ).encode("utf-8")
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        info = zipfile.ZipInfo("META-INF/neoforge.mods.toml", (2026, 8, 12, 12, 0, 0))
        info.external_attr = 0o644 << 16
        archive.writestr(info, metadata)
    return stream.getvalue()


def parse_metadata(body: bytes, content_type: str) -> dict:
    boundary = content_type.split("boundary=", 1)[1].encode("ascii")
    for part in body.split(b"--" + boundary):
        if b'name="metadata"' not in part:
            continue
        _, _, payload = part.partition(b"\r\n\r\n")
        return json.loads(payload.rstrip(b"\r\n").decode("utf-8"))
    raise AssertionError("metadata part not found")


class FakeState:
    def __init__(self, jar_bytes: bytes):
        self.jar_bytes = jar_bytes
        self.files: dict[int, dict] = {}
        self.downloads: dict[int, bytes] = {}
        self.artifacts: list[dict] = []
        self.workflow_runs: list[dict] = []
        self.workflow_jobs: dict[tuple[int, int], list[dict]] = {}
        self.publish_visible = False
        self.upload_status = 200
        self.upload_response: dict = {"id": NEW_FILE_ID}
        self.upload_response_mode = "json"
        self.post_count = 0
        self.upload_body = b""
        self.upload_content_type = ""
        self.upload_token = ""
        self.game_version_token = ""
        self.release_authorization = ""
        self.asset_authorization = ""
        self.list_page_size = 0
        self.requested_page_indexes: list[int] = []
        self.project_relations = public_relations()
        self.game_versions = [
            {"id": 33, "gameVersionTypeID": 2, "name": "1.21.1"},
            {"id": 3, "gameVersionTypeID": 1, "name": "1.21.1"},
        ]

    @staticmethod
    def prior_file() -> dict:
        return {
            "id": PREVIOUS_FILE_ID,
            "projectId": PROJECT_ID,
            "displayName": "sample_mod-0.4.1-fixture.jar",
            "fileName": "sample_mod-0.4.1-fixture.jar",
            "fileLength": 2679330,
            "status": 4,
            "releaseType": 1,
            "gameVersions": ["Client", "1.21.1", "NeoForge", "Server"],
        }

    def current_file(self, file_id: int = NEW_FILE_ID) -> dict:
        return {
            "id": file_id,
            "projectId": PROJECT_ID,
            "displayName": ASSET_NAME,
            "fileName": ASSET_NAME,
            "fileLength": len(self.jar_bytes),
            "status": 4,
            "releaseType": 1,
            "gameVersions": ["Client", "1.21.1", "NeoForge", "Server"],
        }


class Handler(BaseHTTPRequestHandler):
    state: FakeState
    base_url: str

    def log_message(self, _format: str, *_args) -> None:
        return

    def _json(self, value: object, status: int = 200) -> None:
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _bytes(self, value: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(value)))
        self.end_headers()
        self.wfile.write(value)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        if path == f"/repos/test-owner/test-repo/releases/tags/{TAG}":
            self.state.release_authorization = self.headers.get("Authorization", "")
            digest = hashlib.sha256(self.state.jar_bytes).hexdigest()
            self._json(
                {
                    "tag_name": TAG,
                    "draft": False,
                    "prerelease": False,
                    "assets": [
                        {
                            "id": 511687758,
                            "name": ASSET_NAME,
                            "size": len(self.state.jar_bytes),
                            "digest": f"sha256:{digest}",
                            "browser_download_url": f"{self.base_url}/github-asset",
                        }
                    ],
                }
            )
            return
        if path == "/github-asset":
            self.state.asset_authorization = self.headers.get("Authorization", "")
            self._bytes(self.state.jar_bytes)
            return
        if path == "/api/game/versions":
            token = self.headers.get("X-Api-Token", "")
            self.state.game_version_token = token
            if token == "rejected-secret":
                self._json({"error": "unauthorized"}, 401)
                return
            if token == "forbidden-secret":
                self._json({"error": "forbidden"}, 403)
                return
            self._json(self.state.game_versions)
            return
        artifacts_path = "/repos/test-owner/test-repo/actions/artifacts"
        workflow_runs_path = (
            "/repos/test-owner/test-repo/actions/workflows/"
            "publish-curseforge.yml/runs"
        )
        if path == workflow_runs_path:
            page = int(query.get("page", ["1"])[0])
            per_page = int(query.get("per_page", ["100"])[0])
            start = (page - 1) * per_page
            self._json(
                {
                    "total_count": len(self.state.workflow_runs),
                    "workflow_runs": self.state.workflow_runs[start : start + per_page],
                }
            )
            return
        workflow_jobs_prefix = "/repos/test-owner/test-repo/actions/runs/"
        if path.startswith(workflow_jobs_prefix) and path.endswith("/jobs"):
            tail = path[len(workflow_jobs_prefix) :].split("/")
            if len(tail) == 4 and tail[1] == "attempts" and tail[3] == "jobs":
                run_id = int(tail[0])
                attempt = int(tail[2])
                jobs = self.state.workflow_jobs.get((run_id, attempt), [])
                page = int(query.get("page", ["1"])[0])
                per_page = int(query.get("per_page", ["100"])[0])
                start = (page - 1) * per_page
                self._json(
                    {
                        "total_count": len(jobs),
                        "jobs": jobs[start : start + per_page],
                    }
                )
                return
        if path == artifacts_path:
            page = int(query.get("page", ["1"])[0])
            per_page = int(query.get("per_page", ["100"])[0])
            start = (page - 1) * per_page
            self._json(
                {
                    "total_count": len(self.state.artifacts),
                    "artifacts": self.state.artifacts[start : start + per_page],
                }
            )
            return
        if path == f"/api/v1/mods/{PROJECT_ID}/dependencies":
            self._json(
                {
                    "data": self.state.project_relations,
                    "pagination": {
                        "index": 0,
                        "pageSize": 50,
                        "totalCount": len(self.state.project_relations),
                    },
                }
            )
            return
        if path.startswith(artifacts_path + "/"):
            artifact_id = int(path.rsplit("/", 1)[1])
            matches = [item for item in self.state.artifacts if item.get("id") == artifact_id]
            if len(matches) == 1:
                self._json(matches[0])
            else:
                self._json({"error": "not found"}, 404)
            return
        prefix = f"/api/v1/mods/{PROJECT_ID}/files"
        if path == prefix:
            values = list(self.state.files.values())
            page_index = int(query.get("pageIndex", ["0"])[0])
            self.state.requested_page_indexes.append(page_index)
            page_size = self.state.list_page_size or int(query.get("pageSize", ["50"])[0])
            start = page_index * page_size
            self._json(
                {
                    "data": values[start : start + page_size],
                    "pagination": {
                        "index": page_index,
                        "pageSize": page_size,
                        "totalCount": len(values),
                    },
                }
            )
            return
        if path == f"{prefix}/{PREVIOUS_FILE_ID}":
            self._json({"data": self.state.prior_file()})
            return
        if path == f"{prefix}/{PREVIOUS_FILE_ID}/dependencies":
            self._json({"data": public_relations()})
            return
        if path.startswith(prefix + "/"):
            tail = path[len(prefix) + 1 :]
            if tail.endswith("/dependencies"):
                file_id = int(tail[: -len("/dependencies")])
                if file_id in self.state.files or (
                    file_id == NEW_FILE_ID and self.state.publish_visible
                ):
                    self._json({"data": public_relations()})
                else:
                    self._json({"error": "not found"}, 404)
                return
            if tail.endswith("/download"):
                file_id = int(tail[: -len("/download")])
                if file_id in self.state.downloads:
                    self._bytes(self.state.downloads[file_id])
                elif file_id == NEW_FILE_ID and self.state.publish_visible:
                    self._bytes(self.state.jar_bytes)
                else:
                    self._json({"error": "not found"}, 404)
                return
            file_id = int(tail)
            if file_id in self.state.files:
                self._json({"data": self.state.files[file_id]})
            elif file_id == NEW_FILE_ID and self.state.publish_visible:
                self._json({"data": self.state.current_file()})
            else:
                self._json({"error": "not found"}, 404)
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if self.path != f"/api/projects/{PROJECT_ID}/upload-file":
            self._json({"error": "not found"}, 404)
            return
        self.state.post_count += 1
        self.state.upload_token = self.headers.get("X-Api-Token", "")
        self.state.upload_content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", "0"))
        self.state.upload_body = self.rfile.read(length)
        if self.state.upload_status != 200:
            self._json({"error": "upload rejected"}, self.state.upload_status)
            return
        metadata = parse_metadata(self.state.upload_body, self.state.upload_content_type)
        valid_contract = (
            metadata.get("relations") == {"projects": UPLOAD_RELATIONS}
            and metadata.get("gameVersionNames") == ["Client", "Server", "1.21.1", "NeoForge"]
            and "gameVersions" not in metadata
            and metadata.get("isMarkedForManualRelease") is False
        )
        if not valid_contract:
            self._json({"error": "invalid upload metadata contract"}, 400)
            return
        if self.state.upload_response_mode == "malformed":
            self._bytes(b"not-json")
            return
        if self.state.upload_response_mode == "disconnect":
            self.close_connection = True
            self.connection.close()
            return
        self._json(self.state.upload_response)


def public_relations() -> list[dict]:
    return [
        {"id": item["projectId"], "slug": item["slug"], "type": item["type"]}
        for item in EXPECTED_RELATIONS
    ]


class PublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="curseforge-publisher-test-")
        self.repo_root = Path(self.temporary.name)
        changelog = b"# Test release\n\nDeterministic changelog.\n"
        (self.repo_root / "docs/releases").mkdir(parents=True)
        (self.repo_root / "docs/releases/0.4.2-fixture.md").write_bytes(changelog)
        self.jar_bytes = make_jar()
        self.asset_sha = hashlib.sha256(self.jar_bytes).hexdigest()
        self.manifest = {
            "schemaVersion": 1,
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "release": {
                "tag": TAG,
                "version": VERSION,
                "modId": MOD_ID,
                "assetName": ASSET_NAME,
                "assetSize": len(self.jar_bytes),
                "assetSha256": self.asset_sha,
                "changelogPath": "docs/releases/0.4.2-fixture.md",
                "changelogSha256": hashlib.sha256(changelog).hexdigest(),
            },
            "curseforge": {
                "projectId": PROJECT_ID,
                "previousPublicFileId": PREVIOUS_FILE_ID,
                "displayName": ASSET_NAME,
                "releaseType": "release",
                "isMarkedForManualRelease": False,
                "gameVersionNames": ["Client", "Server", "1.21.1", "NeoForge"],
                "gameVersionLookupNames": ["1.21.1"],
                "uploadRelations": UPLOAD_RELATIONS,
                "expectedPublicRelations": EXPECTED_RELATIONS,
            },
        }
        self.state = FakeState(self.jar_bytes)
        handler = type("BoundHandler", (Handler,), {})
        handler.state = self.state
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"
        handler.base_url = self.base_url
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def publisher(self) -> Publisher:
        return Publisher(
            self.repo_root,
            self.manifest,
            http=HttpClient(timeout=2, get_attempts=1),
            github_api=self.base_url,
            curseforge_public_api=self.base_url + "/api/v1",
            curseforge_upload_api=self.base_url,
        )

    def run_publisher(
        self,
        *,
        mode: str = "dry-run",
        token: str = "",
        github_token: str = "",
        resume_file_id: int | None = None,
        poll_attempts: int = 1,
        run_key: str = "",
        intent_report: dict | None = None,
        intent_artifact_id: int | None = None,
    ) -> dict:
        return self.publisher().run(
            mode=mode,
            curseforge_token=token,
            github_token=github_token,
            resume_file_id=resume_file_id,
            poll_attempts=poll_attempts,
            poll_interval=0,
            run_key=run_key,
            intent_report=intent_report,
            intent_artifact_id=intent_artifact_id,
        )

    def prepare_and_persist(
        self, run_key: str = "100-1", token: str = "valid-secret"
    ) -> tuple[dict, int]:
        report = self.run_publisher(
            mode="prepare-publish",
            token=token,
            github_token="github-secret",
            run_key=run_key,
        )
        artifact_id = 7001
        self.state.artifacts.append(
            {
                "id": artifact_id,
                "name": f"{ARTIFACT_PREFIX}{run_key}--intent--{report['multipartSha256'][:12]}",
                "expired": False,
            }
        )
        return report, artifact_id

    def record_persisted_intent_step(self, run_key: str, tag: str = TAG) -> None:
        run_id_text, attempt_text = run_key.split("-", 1)
        run_id = int(run_id_text)
        attempt = int(attempt_text)
        matches = [item for item in self.state.workflow_runs if item.get("id") == run_id]
        if matches:
            matches[0]["run_attempt"] = max(matches[0]["run_attempt"], attempt)
        else:
            self.state.workflow_runs.append(
                {
                    "id": run_id,
                    "run_attempt": attempt,
                    "display_title": f"CurseForge {tag} :: publish",
                }
            )
        self.state.workflow_jobs[(run_id, attempt)] = [
            {
                "steps": [
                    {
                        "name": PERSIST_INTENT_STEP_NAME,
                        "conclusion": "success",
                    }
                ]
            }
        ]

    def publish_from_intent(
        self,
        intent: dict,
        artifact_id: int,
        *,
        token: str = "valid-secret",
        poll_attempts: int = 1,
    ) -> dict:
        return self.run_publisher(
            mode="publish",
            token=token,
            github_token="github-secret",
            run_key=intent["runKey"],
            intent_report=intent,
            intent_artifact_id=artifact_id,
            poll_attempts=poll_attempts,
        )

    def test_dry_run_is_deterministic_and_never_posts_or_uses_cf_token(self) -> None:
        first = self.run_publisher(github_token="github-secret")
        release_authorization = self.state.release_authorization
        asset_authorization = self.state.asset_authorization
        second = self.run_publisher()
        self.assertEqual("AUTOMATION_READY_DRY_RUN", first["status"])
        self.assertEqual(first["metadataSha256"], second["metadataSha256"])
        self.assertEqual(first["multipartSha256"], second["multipartSha256"])
        self.assertEqual(first["multipartSize"], second["multipartSize"])
        self.assertEqual(0, self.state.post_count)
        self.assertEqual("", self.state.game_version_token)
        self.assertEqual("Bearer github-secret", release_authorization)
        self.assertEqual("", asset_authorization)

    def test_dry_run_prepare_and_publish_have_identical_request_hashes(self) -> None:
        dry_run = self.run_publisher()
        intent, artifact_id = self.prepare_and_persist()
        self.state.publish_visible = True
        published = self.publish_from_intent(intent, artifact_id)
        for key in ("metadataSha256", "multipartSha256", "multipartSize"):
            self.assertEqual(dry_run[key], intent[key])
            self.assertEqual(intent[key], published[key])

    def test_missing_token_stops_in_prepare_before_upload(self) -> None:
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="prepare-publish",
                github_token="github-secret",
                run_key="100-1",
            )
        self.assertEqual("BLOCKED_BY_MISSING_CURSEFORGE_API_TOKEN", raised.exception.status)
        self.assertEqual(EXIT_TOKEN_MISSING, raised.exception.exit_code)
        self.assertEqual(0, self.state.post_count)

    def test_rejected_and_forbidden_tokens_are_classified(self) -> None:
        for token, expected in (
            ("rejected-secret", "CURSEFORGE_TOKEN_REJECTED"),
            ("forbidden-secret", "CURSEFORGE_TOKEN_FORBIDDEN"),
        ):
            with self.subTest(token=token):
                with self.assertRaises(PublicationError) as raised:
                    self.run_publisher(
                        mode="prepare-publish",
                        token=token,
                        github_token="github-secret",
                        run_key="100-1",
                    )
                self.assertEqual(expected, raised.exception.status)
                self.assertEqual(EXIT_AUTHORIZATION, raised.exception.exit_code)
                self.assertNotIn(token, str(raised.exception))

    def test_prepare_resolves_only_configured_lookup_names(self) -> None:
        report = self.run_publisher(
            mode="prepare-publish",
            token="valid-secret",
            github_token="github-secret",
            run_key="100-1",
        )
        self.assertEqual("UPLOAD_INTENT_READY", report["status"])
        self.assertEqual({"1.21.1": [3, 33]}, report["resolvedGameVersions"])
        self.assertEqual(0, self.state.post_count)

        self.manifest["curseforge"]["gameVersionLookupNames"] = ["1.21.1", "Client"]
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="prepare-publish",
                token="valid-secret",
                github_token="github-secret",
                run_key="101-1",
            )
        self.assertEqual("CURSEFORGE_GAME_VERSION_MISSING", raised.exception.status)
        self.assertEqual(0, self.state.post_count)

        self.manifest["curseforge"]["gameVersionLookupNames"] = ["1.21.1"]
        self.state.game_versions = [{"id": "not-an-integer", "name": "1.21.1"}]
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="prepare-publish",
                token="valid-secret",
                github_token="github-secret",
                run_key="102-1",
            )
        self.assertEqual("CURSEFORGE_GAME_VERSION_ID_INVALID", raised.exception.status)
        self.assertEqual(0, self.state.post_count)

    def test_transport_timeout_fails_closed(self) -> None:
        client = HttpClient(timeout=0.01, get_attempts=1)
        with mock.patch(
            "publish_curseforge.urllib.request.urlopen",
            side_effect=TimeoutError("simulated timeout"),
        ):
            with self.assertRaises(PublicationError) as raised:
                client.get_json("https://example.invalid/test", label="bounded timeout test")
        self.assertEqual("HTTP_TRANSPORT_FAILED", raised.exception.status)
        self.assertNotIn("simulated timeout", str(raised.exception))

    def test_project_permission_denial_is_classified(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        self.state.upload_status = 403
        with self.assertRaises(PublicationError) as raised:
            self.publish_from_intent(intent, artifact_id)
        self.assertEqual("CURSEFORGE_PROJECT_PERMISSION_DENIED", raised.exception.status)
        self.assertEqual(EXIT_AUTHORIZATION, raised.exception.exit_code)

    def test_identical_duplicate_is_idempotent_success(self) -> None:
        existing_id = 9000001
        self.state.files[existing_id] = self.state.current_file(existing_id)
        self.state.downloads[existing_id] = self.jar_bytes
        report = self.run_publisher(
            mode="prepare-publish",
            token="unused-secret",
            github_token="github-secret",
            run_key="100-1",
        )
        self.assertEqual("ALREADY_PUBLISHED", report["status"])
        self.assertEqual(existing_id, report["fileId"])
        self.assertTrue(report["publicHashMatch"])
        self.assertEqual(self.asset_sha, report["publicReadback"]["sha256"])
        self.assertIs(False, report["postRequired"])
        self.assertEqual(0, self.state.post_count)

    def test_exact_public_file_precedes_stale_history_and_project_aggregation(self) -> None:
        existing_id = 9000001
        self.state.files[existing_id] = self.state.current_file(existing_id)
        self.state.downloads[existing_id] = self.jar_bytes
        self.state.project_relations = self.state.project_relations[-1:]
        self.record_persisted_intent_step("99-1")
        report = self.run_publisher(
            mode="prepare-publish",
            token="unused-secret",
            github_token="github-secret",
            run_key="100-1",
        )
        self.assertEqual("ALREADY_PUBLISHED", report["status"])
        self.assertEqual(existing_id, report["fileId"])
        self.assertEqual(
            "SKIPPED_ACCEPTED_FILE_RESUME",
            report["curseForgeBaseline"]["projectRelationsCheck"],
        )
        self.assertEqual(0, self.state.post_count)

    def test_duplicate_scan_uses_zero_based_page_index_across_all_pages(self) -> None:
        older_id = 8999999
        existing_id = 9000001
        older = self.state.current_file(older_id)
        older["fileName"] = "sample_mod-0.4.1-fixture.jar"
        older["displayName"] = older["fileName"]
        self.state.files[older_id] = older
        self.state.files[existing_id] = self.state.current_file(existing_id)
        self.state.downloads[existing_id] = self.jar_bytes
        self.state.list_page_size = 1
        report = self.run_publisher(mode="publish")
        self.assertEqual("ALREADY_PUBLISHED", report["status"])
        self.assertEqual(existing_id, report["fileId"])
        self.assertEqual([0, 1], self.state.requested_page_indexes)
        self.assertEqual(0, self.state.post_count)

    def test_divergent_duplicate_blocks_publication(self) -> None:
        existing_id = 9000002
        self.state.files[existing_id] = self.state.current_file(existing_id)
        self.state.downloads[existing_id] = make_jar("0.4.2-fixture-divergent")
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(mode="publish")
        self.assertEqual("BLOCKED_BY_REMOTE_ARTIFACT_CONFLICT", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertEqual(0, self.state.post_count)

    def test_project_relation_drift_blocks_before_upload(self) -> None:
        self.state.project_relations = self.state.project_relations[:-1]
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(mode="dry-run")
        self.assertEqual("CURSEFORGE_PROJECT_RELATION_MISMATCH", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertEqual(0, self.state.post_count)

    def test_successful_upload_uses_official_schema_and_full_public_readback(self) -> None:
        secret = "valid-secret-value"
        intent, artifact_id = self.prepare_and_persist(token=secret)
        self.state.publish_visible = True
        report = self.publish_from_intent(intent, artifact_id, token=secret)
        self.assertEqual("PUBLISHED_VERIFIED", report["status"])
        self.assertEqual(NEW_FILE_ID, report["fileId"])
        self.assertTrue(report["publicHashMatch"])
        self.assertEqual(self.asset_sha, report["publicSha256"])
        self.assertEqual(
            sorted(EXPECTED_RELATIONS, key=lambda item: item["projectId"]),
            report["publicReadback"]["relations"],
        )
        self.assertEqual(1, self.state.post_count)
        metadata = parse_metadata(self.state.upload_body, self.state.upload_content_type)
        self.assertEqual(
            ["Client", "Server", "1.21.1", "NeoForge"], metadata["gameVersionNames"]
        )
        self.assertNotIn("gameVersions", metadata)
        self.assertEqual({"projects": UPLOAD_RELATIONS}, metadata["relations"])
        self.assertIs(False, metadata["isMarkedForManualRelease"])
        self.assertNotIn("jei", json.dumps(metadata).lower())
        self.assertNotIn("include", json.dumps(metadata).lower())
        self.assertNotIn(secret, self.state.upload_body.decode("latin-1"))
        self.assertNotIn(secret, json.dumps(report))

    def test_fake_endpoint_rejects_wrong_relations_schema(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        bad_metadata = self.publisher()._metadata("# Test")
        bad_metadata["relations"] = UPLOAD_RELATIONS
        bad_body, content_type = build_multipart(
            bad_metadata, ASSET_NAME, self.jar_bytes, self.asset_sha
        )
        request = urllib.request.Request(
            f"{self.base_url}/api/projects/{PROJECT_ID}/upload-file",
            data=bad_body,
            headers={"Content-Type": content_type, "X-Api-Token": "valid-secret"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=2)
        raised.exception.close()
        self.assertEqual(400, raised.exception.code)
        self.assertEqual(1, self.state.post_count)
        self.assertEqual("UPLOAD_INTENT_READY", intent["status"])
        self.assertGreater(artifact_id, 0)

    def test_missing_or_wrong_current_intent_artifact_blocks_post(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="publish",
                token="valid-secret",
                github_token="github-secret",
                run_key=intent["runKey"],
                intent_report=intent,
            )
        self.assertEqual("INTENT_ARTIFACT_ID_INVALID", raised.exception.status)
        self.assertEqual(0, self.state.post_count)
        self.state.artifacts[0]["name"] = f"{ARTIFACT_PREFIX}{intent['runKey']}--intent--wrong"
        with self.assertRaises(PublicationError) as raised:
            self.publish_from_intent(intent, artifact_id)
        self.assertEqual("DURABLE_INTENT_NOT_VERIFIED", raised.exception.status)
        self.assertEqual(0, self.state.post_count)

    def test_mutated_intent_report_blocks_post(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        altered = dict(intent)
        altered["multipartSize"] += 1
        with self.assertRaises(PublicationError) as raised:
            self.publish_from_intent(altered, artifact_id)
        self.assertEqual("UPLOAD_INTENT_REPORT_MISMATCH", raised.exception.status)
        self.assertEqual(0, self.state.post_count)

    def test_unmatched_prior_intent_blocks_second_post(self) -> None:
        self.state.artifacts.append(
            {
                "id": 7000,
                "name": f"{ARTIFACT_PREFIX}99-1--intent--abcdef123456",
                "expired": False,
            }
        )
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="prepare-publish",
                token="valid-secret",
                github_token="github-secret",
                run_key="100-1",
            )
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertEqual(0, self.state.post_count)

    def test_prior_persisted_state_for_another_tag_does_not_block(self) -> None:
        prior_tag = "v1.1.53-reconstructed"
        run_key = "99-1"
        prior_prefix = state_artifact_prefix(prior_tag)
        self.record_persisted_intent_step(run_key, tag=prior_tag)
        self.state.artifacts.extend(
            [
                {
                    "id": 7000,
                    "name": f"{prior_prefix}{run_key}--intent--abcdef123456",
                    "expired": False,
                },
                {
                    "id": 7001,
                    "name": (
                        f"{prior_prefix}{run_key}--result--"
                        f"UPLOADED_PROCESSING--{NEW_FILE_ID}"
                    ),
                    "expired": False,
                },
            ]
        )

        report = self.run_publisher(
            mode="prepare-publish",
            token="valid-secret",
            github_token="github-secret",
            run_key="100-1",
        )

        self.assertEqual("UPLOAD_INTENT_READY", report["status"])
        self.assertIs(True, report["postRequired"])
        self.assertNotIn("durableStateResume", report)
        self.assertEqual(0, self.state.post_count)

    def test_workflow_history_without_display_title_fails_closed(self) -> None:
        self.state.workflow_runs.append({"id": 99, "run_attempt": 1})

        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="prepare-publish",
                token="valid-secret",
                github_token="github-secret",
                run_key="100-1",
            )

        self.assertEqual("GITHUB_WORKFLOW_HISTORY_INVALID", raised.exception.status)
        self.assertEqual(0, self.state.post_count)

    def test_stale_intent_cannot_be_accepted_as_result(self) -> None:
        run_key = "99-1"
        self.record_persisted_intent_step(run_key)
        self.state.artifacts.extend(
            [
                {
                    "id": 7000,
                    "name": f"{ARTIFACT_PREFIX}{run_key}--intent--abcdef123456",
                    "expired": False,
                },
                {
                    "id": 7001,
                    "name": f"{ARTIFACT_PREFIX}{run_key}--result--UPLOAD_INTENT_READY--0",
                    "expired": False,
                },
            ]
        )
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="prepare-publish",
                token="valid-secret",
                github_token="github-secret",
                run_key="100-1",
            )
        self.assertEqual("GITHUB_STATE_ARTIFACT_INVALID", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertEqual(0, self.state.post_count)

    def test_missing_artifacts_after_persisted_intent_block_second_post(self) -> None:
        self.record_persisted_intent_step("99-1")
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="prepare-publish",
                token="valid-secret",
                github_token="github-secret",
                run_key="100-1",
            )
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertEqual(0, self.state.post_count)

    def test_expired_artifacts_after_persisted_intent_block_second_post(self) -> None:
        run_key = "99-1"
        self.record_persisted_intent_step(run_key)
        self.state.artifacts.extend(
            [
                {
                    "id": 7000,
                    "name": f"{ARTIFACT_PREFIX}{run_key}--intent--abcdef123456",
                    "expired": True,
                },
                {
                    "id": 7001,
                    "name": f"{ARTIFACT_PREFIX}{run_key}--result--PUBLISHED_VERIFIED--{NEW_FILE_ID}",
                    "expired": True,
                },
            ]
        )
        with self.assertRaises(PublicationError) as raised:
            self.run_publisher(
                mode="prepare-publish",
                token="valid-secret",
                github_token="github-secret",
                run_key="100-1",
            )
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertEqual(0, self.state.post_count)

    def test_prior_processing_result_auto_resumes_without_post(self) -> None:
        self.record_persisted_intent_step("99-1")
        self.state.artifacts.extend(
            [
                {
                    "id": 7000,
                    "name": f"{ARTIFACT_PREFIX}99-1--intent--abcdef123456",
                    "expired": False,
                },
                {
                    "id": 7001,
                    "name": f"{ARTIFACT_PREFIX}99-1--result--UPLOADED_PROCESSING--{NEW_FILE_ID}",
                    "expired": False,
                },
            ]
        )
        self.state.publish_visible = True
        self.state.project_relations = self.state.project_relations[-1:]
        report = self.run_publisher(
            mode="prepare-publish",
            token="valid-secret",
            github_token="github-secret",
            run_key="100-1",
        )
        self.assertEqual("RESUMED_PUBLICATION_VERIFIED", report["status"])
        self.assertTrue(report["durableStateResume"])
        self.assertIs(False, report["postRequired"])
        self.assertEqual(
            "SKIPPED_ACCEPTED_FILE_RESUME",
            report["curseForgeBaseline"]["projectRelationsCheck"],
        )
        self.assertEqual(NEW_FILE_ID, report["fileId"])
        self.assertEqual(0, self.state.post_count)

    def test_unexpected_upload_code_failure_is_outcome_unknown(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        with mock.patch.object(Publisher, "_upload", side_effect=RuntimeError("simulated")):
            with self.assertRaises(PublicationError) as raised:
                self.publish_from_intent(intent, artifact_id)
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertNotIn("simulated", str(raised.exception))

    def test_unexpected_public_poll_failure_preserves_file_id_and_blocks(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        with mock.patch.object(
            Publisher, "_poll_public", side_effect=RuntimeError("simulated")
        ):
            with self.assertRaises(PublicationError) as raised:
                self.publish_from_intent(intent, artifact_id)
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertEqual(NEW_FILE_ID, raised.exception.report["fileId"])
        self.assertEqual(1, self.state.post_count)
        self.assertNotIn("simulated", str(raised.exception))

    def test_partial_upload_response_is_outcome_unknown(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        self.state.upload_response = {}
        with self.assertRaises(PublicationError) as raised:
            self.publish_from_intent(intent, artifact_id)
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(EXIT_CONFLICT, raised.exception.exit_code)
        self.assertEqual(1, self.state.post_count)

    def test_malformed_upload_response_is_outcome_unknown(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        self.state.upload_response_mode = "malformed"
        with self.assertRaises(PublicationError) as raised:
            self.publish_from_intent(intent, artifact_id)
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(1, self.state.post_count)

    def test_upload_server_error_is_outcome_unknown_without_retry(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        self.state.upload_status = 500
        with self.assertRaises(PublicationError) as raised:
            self.publish_from_intent(intent, artifact_id)
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(1, self.state.post_count)

    def test_upload_disconnect_is_outcome_unknown_without_retry(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        self.state.upload_response_mode = "disconnect"
        with self.assertRaises(PublicationError) as raised:
            self.publish_from_intent(intent, artifact_id)
        self.assertEqual("UPLOAD_OUTCOME_UNKNOWN", raised.exception.status)
        self.assertEqual(1, self.state.post_count)

    def test_processing_status_preserves_resumable_file_id(self) -> None:
        intent, artifact_id = self.prepare_and_persist()
        with self.assertRaises(PublicationError) as raised:
            self.publish_from_intent(intent, artifact_id, poll_attempts=2)
        self.assertEqual("UPLOADED_PROCESSING", raised.exception.status)
        self.assertEqual(EXIT_PROCESSING, raised.exception.exit_code)
        self.assertEqual(NEW_FILE_ID, raised.exception.report["fileId"])
        self.assertEqual(artifact_id, raised.exception.report["intentArtifactId"])
        self.assertEqual(1, self.state.post_count)

    def test_resume_file_id_polls_without_token_intent_or_second_upload(self) -> None:
        self.state.publish_visible = True
        self.state.project_relations = self.state.project_relations[-1:]
        report = self.run_publisher(mode="publish", resume_file_id=NEW_FILE_ID)
        self.assertEqual("RESUMED_PUBLICATION_VERIFIED", report["status"])
        self.assertEqual(NEW_FILE_ID, report["fileId"])
        self.assertEqual(self.asset_sha, report["publicSha256"])
        self.assertEqual(
            "SKIPPED_ACCEPTED_FILE_RESUME",
            report["curseForgeBaseline"]["projectRelationsCheck"],
        )
        self.assertIs(False, report["postRequired"])
        self.assertEqual(0, self.state.post_count)
        self.assertEqual([], self.state.requested_page_indexes)


if __name__ == "__main__":
    unittest.main()
