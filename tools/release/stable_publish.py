#!/usr/bin/env python3
"""Fail-closed stable GitHub mutation adapter and final receipt builder.

This privileged entry point is intentionally separate from stable_autopublish,
which remains a read-only eligibility oracle.  Network clients are injectable
so every mutation and recovery transition can be exercised without touching a
real release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import urllib.parse


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.ci import candidate_evidence, final_release_bundle
from tools.release import publish_curseforge, stable_autopublish


REPOSITORY = stable_autopublish.EXPECTED_REPOSITORY
TAG = stable_autopublish.EXPECTED_TAG
VERSION = stable_autopublish.EXPECTED_VERSION
TITLE = "Immersive BOP Harvest 0.1.1"
EXPECTED_RELATIONS = stable_autopublish.EXPECTED_TARGET_RELATIONS
MAX_TAG_DEREFERENCE = 8
RECEIPT_ARTIFACT_PREFIX = "stable-publication-v0.1.1-"


class MutationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MutationError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=candidate_evidence.unique,
    )
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def write_report(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


class GitHubPublicationAdapter:
    """Structured GitHub REST adapter; injected fakes implement the same methods."""

    def __init__(self, token: str, *, http: publish_curseforge.HttpClient | None = None):
        require(bool(token), "GITHUB_MUTATION_TOKEN_UNAVAILABLE")
        self._token = token
        self._http = http or publish_curseforge.HttpClient()
        self._api = f"https://api.github.com/repos/{REPOSITORY}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_optional(self, path: str) -> dict[str, Any] | None:
        try:
            value = self._http.get_json(
                f"{self._api}/{path}", label="GitHub release state", headers=self._headers()
            )
        except publish_curseforge.HttpStatusError as exc:
            if exc.status_code == 404:
                return None
            raise
        require(isinstance(value, dict), "GITHUB_RESPONSE_INVALID")
        return value

    def get_public_optional(self, path: str) -> dict[str, Any] | None:
        try:
            value = self._http.get_json(
                f"{self._api}/{path}", label="GitHub public release state"
            )
        except publish_curseforge.HttpStatusError as exc:
            if exc.status_code == 404:
                return None
            raise
        require(isinstance(value, dict), "GITHUB_PUBLIC_RESPONSE_INVALID")
        return value

    def get_public_bytes(self, url: str) -> bytes:
        require(url.startswith("https://"), "GITHUB_ASSET_URL_INVALID")
        return self._http._request(  # bounded public readback; no credential follows redirects
            "GET", url, label="GitHub public asset readback", retry_safe=True
        )

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        value = self._http.post_json(
            f"{self._api}/{path}", canonical_json(payload),
            content_type="application/json", label="GitHub release mutation",
            headers=self._headers(),
        )
        require(isinstance(value, dict), "GITHUB_MUTATION_RESPONSE_INVALID")
        return value

    def upload_asset(self, upload_url: str, name: str, raw: bytes) -> dict[str, Any]:
        base = upload_url.split("{", 1)[0]
        url = base + "?name=" + urllib.parse.quote(name, safe="")
        value = self._http.post_json(
            url, raw, content_type="application/java-archive",
            label="GitHub release asset upload", headers=self._headers(),
        )
        require(isinstance(value, dict), "GITHUB_ASSET_RESPONSE_INVALID")
        return value


class StablePublication:
    def __init__(
        self, repo_root: Path, github: Any, source_api: Any,
        curseforge_public: Any | None = None,
    ):
        self.repo_root = repo_root.resolve()
        self.github = github
        self.source_api = source_api
        self.curseforge_public = curseforge_public

    def validate_source_report(self, report: dict[str, Any]) -> dict[str, Any]:
        require(report.get("repository") == REPOSITORY, "SOURCE_REPOSITORY_MISMATCH")
        for field in ("sourceReady", "stableReady", "autoPublishEligible"):
            require(report.get(field) is True, f"SOURCE_{field.upper()}_NOT_TRUE")
        require(report.get("publicationComplete") is False, "SOURCE_REPORT_ALREADY_COMPLETE")
        require(
            report.get("publicationAuthority") == "AUTHORIZED_WHEN_ELIGIBLE",
            "STANDING_POLICY_INVALID",
        )
        require(
            report.get("releasePolicy") == {
                "targets": ["github", "curseforge"],
                "modrinth": "FORBIDDEN_BY_PROJECT_POLICY",
            },
            "RELEASE_POLICY_INVALID",
        )
        source = report.get("authenticatedSource")
        candidate = report.get("candidate")
        contract = report.get("releaseContract")
        require(isinstance(source, dict) and isinstance(candidate, dict)
                and isinstance(contract, dict), "SOURCE_IDENTITY_MISSING")
        require(source.get("sourceCommit") == report.get("workflowRun", {}).get("headSha"),
                "SOURCE_COMMIT_MISMATCH")
        require(candidate.get("version") == VERSION
                and candidate.get("name") == "immersive_bop_harvest-0.1.1.jar",
                "CANDIDATE_IDENTITY_INVALID")
        require(
            set(contract) == {
                "path", "sha256", "notesPath", "notesSha256", "tag",
                "projectId", "projectSlug", "historicalFileRelations",
                "historicalProjectRelations", "targetRelations",
            }
            and contract.get("path") == stable_autopublish.EXPECTED_MANIFEST
            and contract.get("notesPath") == stable_autopublish.EXPECTED_NOTES
            and contract.get("tag") == TAG
            and contract.get("projectId") == 1_609_013
            and contract.get("projectSlug") == "immersive-bop-harvest"
            and contract.get("historicalFileRelations") == 3
            and contract.get("historicalProjectRelations") == 0
            and contract.get("targetRelations") == 5,
            "RELEASE_CONTRACT_INVALID",
        )
        identity = {
            "runId": source.get("runId"),
            "runAttempt": source.get("runAttempt"),
            "sourceCommit": source.get("sourceCommit"),
            "sourceTree": source.get("sourceTree"),
            "artifactId": source.get("artifactId"),
            "archiveSha256": source.get("archiveSha256"),
            "candidateSha256": candidate.get("sha256"),
            "manifestSha256": contract.get("sha256"),
            "notesSha256": contract.get("notesSha256"),
        }
        require(report.get("idempotenceKey") == sha256(canonical_json(identity)),
                "PUBLICATION_KEY_MISMATCH")
        for key in ("runId", "runAttempt", "artifactId"):
            require(type(source.get(key)) is int and source[key] > 0,
                    f"SOURCE_{key.upper()}_INVALID")
        for key in ("sourceCommit", "sourceTree"):
            require(isinstance(source.get(key), str)
                    and re.fullmatch(r"[0-9a-f]{40}", source[key]) is not None,
                    f"SOURCE_{key.upper()}_INVALID")
        for key in ("archiveSha256",):
            require(isinstance(source.get(key), str)
                    and re.fullmatch(r"[0-9a-f]{64}", source[key]) is not None,
                    f"SOURCE_{key.upper()}_INVALID")
        notes_path = self.repo_root / contract.get("notesPath", "")
        manifest_path = self.repo_root / contract.get("path", "")
        require(notes_path.is_file() and manifest_path.is_file(), "RELEASE_INPUT_MISSING")
        notes_raw = notes_path.read_bytes()
        require(sha256(notes_raw) == contract.get("notesSha256"), "RELEASE_NOTES_HASH_MISMATCH")
        require(sha256(manifest_path.read_bytes()) == contract.get("sha256"),
                "RELEASE_MANIFEST_HASH_MISMATCH")
        require(notes_raw.decode("utf-8").splitlines()[0] == f"# {TITLE}",
                "RELEASE_TITLE_CONVENTION_MISMATCH")
        stable_autopublish.verify_checkout(self.repo_root, source["sourceCommit"])
        return {"source": source, "candidate": candidate, "contract": contract,
                "notes": notes_raw.decode("utf-8"), "publicationKey": report["idempotenceKey"]}

    def _current_main(self, source_sha: str) -> None:
        ref = self.github.get_optional("git/ref/heads/main")
        require(isinstance(ref, dict) and ref.get("object", {}).get("type") == "commit"
                and ref["object"].get("sha") == source_sha,
                "CURRENT_MAIN_DRIFT_STOP")

    def _tag_state(self, source_sha: str, *, public: bool = False) -> dict[str, Any]:
        getter = self.github.get_public_optional if public else self.github.get_optional
        ref = getter(f"git/ref/tags/{urllib.parse.quote(TAG, safe='')}")
        if ref is None:
            return {"state": "TAG_ABSENT"}
        obj = ref.get("object")
        require(isinstance(obj, dict), "TAG_AMBIGUOUS_STOP")
        seen: set[str] = set()
        for _ in range(MAX_TAG_DEREFERENCE):
            kind, target = obj.get("type"), obj.get("sha")
            require(isinstance(target, str), "TAG_AMBIGUOUS_STOP")
            if kind == "commit":
                require(target == source_sha, "TAG_DIVERGENT_STOP")
                return {"state": "TAG_EXACT", "resolvedCommit": target}
            require(kind == "tag" and target not in seen, "TAG_AMBIGUOUS_STOP")
            seen.add(target)
            annotated = getter(f"git/tags/{target}")
            require(isinstance(annotated, dict)
                    and isinstance(annotated.get("object"), dict), "TAG_AMBIGUOUS_STOP")
            obj = annotated["object"]
        raise MutationError("TAG_AMBIGUOUS_STOP")

    def _release_state(
        self, source_sha: str, notes: str, candidate: dict[str, Any], *, public: bool = False
    ) -> dict[str, Any]:
        getter = self.github.get_public_optional if public else self.github.get_optional
        release = getter(
            f"releases/tags/{urllib.parse.quote(TAG, safe='')}"
        )
        if release is None:
            return {"releaseState": "RELEASE_ABSENT", "assetState": "ASSET_NOT_APPLICABLE"}
        exact = (
            release.get("tag_name") == TAG
            and release.get("target_commitish") == source_sha
            and release.get("draft") is False
            and release.get("prerelease") is False
            and release.get("name") == TITLE
            and release.get("body") == notes
            and type(release.get("id")) is int and release["id"] > 0
            and isinstance(release.get("html_url"), str)
            and isinstance(release.get("upload_url"), str)
        )
        require(exact, "RELEASE_DIVERGENT_STOP")
        assets = release.get("assets")
        require(isinstance(assets, list)
                and all(isinstance(asset, dict) for asset in assets),
                "ASSET_AMBIGUOUS_STOP")
        base = {
            "releaseState": "RELEASE_EXACT",
            "releaseId": release["id"],
            "releaseUrl": release["html_url"],
            "uploadUrl": release["upload_url"],
        }
        if not assets:
            return {**base, "assetState": "ASSET_ABSENT"}
        require(len(assets) == 1, "ASSET_DIVERGENT_STOP")
        asset = assets[0]
        require(
            asset.get("name") == candidate.get("name")
            and asset.get("size") == candidate.get("size")
            and type(asset.get("id")) is int and asset["id"] > 0
            and isinstance(asset.get("browser_download_url"), str),
            "ASSET_DIVERGENT_STOP",
        )
        digest = asset.get("digest")
        if digest is not None:
            require(str(digest).lower() == "sha256:" + candidate["sha256"],
                    "ASSET_DIVERGENT_STOP")
        raw = self.github.get_public_bytes(asset["browser_download_url"])
        require(len(raw) == candidate["size"] and sha256(raw) == candidate["sha256"],
                "ASSET_DIVERGENT_STOP")
        return {
            **base,
            "assetState": "ASSET_EXACT",
            "assetId": asset["id"],
            "assetName": asset["name"],
            "assetSize": len(raw),
            "assetSha256": sha256(raw),
        }

    def inspect_github(
        self, source_sha: str, notes: str, candidate: dict[str, Any], *, public: bool = False
    ) -> dict[str, Any]:
        tag = self._tag_state(source_sha, public=public)
        release = self._release_state(source_sha, notes, candidate, public=public)
        if release["releaseState"] == "RELEASE_EXACT":
            require(tag["state"] == "TAG_EXACT", "RELEASE_DIVERGENT_STOP")
        return {**tag, **release}

    def _post_then_reconcile(self, operation, inspect, exact, unknown: str) -> dict[str, Any]:
        try:
            operation()
        except Exception:
            state = inspect()
            if exact(state):
                return state
            raise MutationError(unknown) from None
        state = inspect()
        require(exact(state), unknown)
        return state

    def download_candidate(self, source: dict[str, Any], candidate: dict[str, Any]) -> bytes:
        metadata = self.source_api.get(f"actions/artifacts/{source['artifactId']}")
        require(
            metadata.get("id") == source["artifactId"]
            and metadata.get("expired") is False
            and metadata.get("workflow_run", {}).get("id") == source["runId"]
            and metadata.get("workflow_run", {}).get("head_sha") == source["sourceCommit"],
            "CANDIDATE_ARTIFACT_IDENTITY_MISMATCH",
        )
        archive = self.source_api.get(
            f"actions/artifacts/{source['artifactId']}/zip", binary=True
        )
        require(sha256(archive) == source["archiveSha256"], "CANDIDATE_ARCHIVE_HASH_MISMATCH")
        files = candidate_evidence.contents(archive)
        raw = files.get("candidate.jar")
        require(isinstance(raw, bytes), "CANDIDATE_JAR_MISSING")
        identity = candidate_evidence.jar_identity(raw)
        require(
            candidate == {**identity, "name": candidate["name"],
                          "size": len(raw), "sha256": sha256(raw)},
            "CANDIDATE_BYTES_MISMATCH",
        )
        return raw

    def mutate_github(self, source_report: dict[str, Any], candidate_output: Path) -> dict[str, Any]:
        validated = self.validate_source_report(source_report)
        source, candidate, notes = validated["source"], validated["candidate"], validated["notes"]
        raw = self.download_candidate(source, candidate)
        candidate_output.parent.mkdir(parents=True, exist_ok=True)
        temporary = candidate_output.with_suffix(candidate_output.suffix + ".tmp")
        temporary.write_bytes(raw)
        temporary.replace(candidate_output)
        self._current_main(source["sourceCommit"])
        initial = self.inspect_github(source["sourceCommit"], notes, candidate)
        operations: list[str] = []
        state = initial
        if state["state"] == "TAG_ABSENT":
            state = self._post_then_reconcile(
                lambda: self.github.post_json("git/refs", {
                    "ref": f"refs/tags/{TAG}", "sha": source["sourceCommit"]}),
                lambda: self.inspect_github(source["sourceCommit"], notes, candidate),
                lambda value: value.get("state") == "TAG_EXACT",
                "TAG_MUTATION_OUTCOME_UNKNOWN",
            )
            operations.append("CREATE_TAG")
        if state["releaseState"] == "RELEASE_ABSENT":
            state = self._post_then_reconcile(
                lambda: self.github.post_json("releases", {
                    "tag_name": TAG, "target_commitish": source["sourceCommit"],
                    "name": TITLE, "body": notes, "draft": False,
                    "prerelease": False, "generate_release_notes": False}),
                lambda: self.inspect_github(source["sourceCommit"], notes, candidate),
                lambda value: value.get("releaseState") == "RELEASE_EXACT",
                "RELEASE_MUTATION_OUTCOME_UNKNOWN",
            )
            operations.append("CREATE_RELEASE")
        if state["assetState"] == "ASSET_ABSENT":
            upload_url = state["uploadUrl"]
            state = self._post_then_reconcile(
                lambda: self.github.upload_asset(upload_url, candidate["name"], raw),
                lambda: self.inspect_github(source["sourceCommit"], notes, candidate),
                lambda value: value.get("assetState") == "ASSET_EXACT",
                "ASSET_MUTATION_OUTCOME_UNKNOWN",
            )
            operations.append("UPLOAD_ASSET")
        require(state.get("state") == "TAG_EXACT"
                and state.get("releaseState") == "RELEASE_EXACT"
                and state.get("assetState") == "ASSET_EXACT",
                "GITHUB_PUBLICATION_INCOMPLETE")
        return {
            "schemaVersion": 1,
            "status": "GITHUB_PUBLICATION_VERIFIED",
            "publicationKey": validated["publicationKey"],
            "repository": REPOSITORY,
            "qualifiedCommit": source["sourceCommit"],
            "qualifiedTree": source["sourceTree"],
            "tag": TAG,
            "tagState": state["state"],
            "resolvedCommit": state["resolvedCommit"],
            "releaseId": state["releaseId"],
            "releaseUrl": state["releaseUrl"],
            "releaseState": state["releaseState"],
            "assetId": state["assetId"],
            "assetName": state["assetName"],
            "assetSize": state["assetSize"],
            "assetSha256": state["assetSha256"],
            "assetState": state["assetState"],
            "operations": operations,
            "publicationComplete": False,
        }

    def finalize(
        self, source_report: dict[str, Any], github_report: dict[str, Any],
        curseforge_report: dict[str, Any],
    ) -> dict[str, Any]:
        validated = self.validate_source_report(source_report)
        source, candidate, contract, notes = (
            validated["source"], validated["candidate"],
            validated["contract"], validated["notes"],
        )
        fresh = self.inspect_github(source["sourceCommit"], notes, candidate, public=True)
        require(fresh.get("state") == "TAG_EXACT"
                and fresh.get("releaseState") == "RELEASE_EXACT"
                and fresh.get("assetState") == "ASSET_EXACT",
                "GITHUB_FINAL_READBACK_INCOMPLETE")
        for field, expected in {
            "publicationKey": validated["publicationKey"],
            "qualifiedCommit": source["sourceCommit"],
            "qualifiedTree": source["sourceTree"],
            "releaseId": fresh["releaseId"],
            "assetId": fresh["assetId"],
            "assetSha256": candidate["sha256"],
        }.items():
            require(github_report.get(field) == expected, f"GITHUB_REPORT_{field.upper()}_MISMATCH")
        require(curseforge_report.get("status") in {
            "PUBLISHED_VERIFIED", "ALREADY_PUBLISHED", "RESUMED_PUBLICATION_VERIFIED"
        } and curseforge_report.get("verdict") == "PASS"
                and curseforge_report.get("publicHashMatch") is True,
                "CURSEFORGE_PUBLICATION_INCOMPLETE")
        reported_public = curseforge_report.get("publicReadback")
        require(isinstance(reported_public, dict), "CURSEFORGE_PUBLIC_READBACK_MISSING")
        file_id = curseforge_report.get("fileId")
        require(
            type(file_id) is int and file_id > 0
            and reported_public.get("fileId") == file_id,
            "CURSEFORGE_FILE_ID_INVALID",
        )
        require(self.curseforge_public is not None, "CURSEFORGE_FRESH_READBACK_UNAVAILABLE")
        public = self.curseforge_public.readback_public_release(file_id)
        require(isinstance(public, dict), "CURSEFORGE_FRESH_READBACK_INVALID")
        manifest = read_json(self.repo_root / contract["path"])
        expected_game_versions = manifest.get("curseforge", {}).get("gameVersionNames")
        relations = public.get("relations")
        relation_tuples = tuple(sorted(
            (row.get("projectId"), row.get("slug"), row.get("type"))
            for row in relations if isinstance(row, dict)
        )) if isinstance(relations, list) else ()
        normalized_relations = [
            {"projectId": project_id, "slug": slug, "type": relation_type}
            for project_id, slug, relation_type in relation_tuples
        ]
        require(
            public.get("projectId") == contract.get("projectId")
            and public.get("fileName") == candidate["name"]
            and public.get("releaseType") == 1
            and public.get("status") == 4
            and public.get("size") == candidate["size"]
            and public.get("sha256") == candidate["sha256"]
            and isinstance(public.get("gameVersions"), list)
            and set(public["gameVersions"]) == set(expected_game_versions or [])
            and len(public["gameVersions"]) == len(expected_game_versions or [])
            and relation_tuples == tuple(sorted(EXPECTED_RELATIONS)),
            "CURSEFORGE_PUBLIC_READBACK_DIVERGENT",
        )
        require(
            public.get("fileId") == file_id,
            "CURSEFORGE_FILE_ID_INVALID",
        )
        reported_relation_tuples = tuple(sorted(
            (row.get("projectId"), row.get("slug"), row.get("type"))
            for row in reported_public.get("relations", []) if isinstance(row, dict)
        ))
        require(
            {
                "fileId": reported_public.get("fileId"),
                "projectId": reported_public.get("projectId"),
                "fileName": reported_public.get("fileName"),
                "releaseType": reported_public.get("releaseType"),
                "status": reported_public.get("status"),
                "gameVersions": sorted(reported_public.get("gameVersions", [])),
                "relations": reported_relation_tuples,
                "size": reported_public.get("size"),
                "sha256": reported_public.get("sha256"),
            }
            == {
                "fileId": public.get("fileId"),
                "projectId": public.get("projectId"),
                "fileName": public.get("fileName"),
                "releaseType": public.get("releaseType"),
                "status": public.get("status"),
                "gameVersions": sorted(public.get("gameVersions", [])),
                "relations": relation_tuples,
                "size": public.get("size"),
                "sha256": public.get("sha256"),
            },
            "CURSEFORGE_REPORT_FRESH_READBACK_MISMATCH",
        )
        return {
            "schemaVersion": 1,
            "status": "PUBLICATION_COMPLETE",
            "repository": REPOSITORY,
            "qualifiedCommit": source["sourceCommit"],
            "qualifiedTree": source["sourceTree"],
            "sourceRunId": source["runId"],
            "sourceRunAttempt": source["runAttempt"],
            "publicationKey": validated["publicationKey"],
            "candidate": candidate,
            "manifest": {"path": contract["path"], "sha256": contract["sha256"]},
            "releaseNotes": {"path": contract["notesPath"], "sha256": contract["notesSha256"]},
            "github": {
                "tag": TAG, "resolvedCommit": fresh["resolvedCommit"],
                "releaseId": fresh["releaseId"], "releaseUrl": fresh["releaseUrl"],
                "releaseState": "PUBLIC", "assetId": fresh["assetId"],
                "assetName": fresh["assetName"], "assetSize": fresh["assetSize"],
                "assetSha256": fresh["assetSha256"],
            },
            "curseForge": {
                "projectId": contract["projectId"], "fileId": file_id,
                "status": public["status"], "releaseType": public["releaseType"],
                "gameVersions": sorted(public.get("gameVersions", [])),
                "relations": normalized_relations, "publicSha256": public["sha256"],
            },
            "releasePolicy": {
                "targets": ["github", "curseforge"],
                "modrinth": "FORBIDDEN_BY_PROJECT_POLICY",
            },
            "publicationComplete": True,
        }

    def _receipt_artifact_name(self, receipt: dict[str, Any]) -> str:
        key = receipt.get("publicationKey")
        require(isinstance(key, str) and re.fullmatch(r"[0-9a-f]{64}", key) is not None,
                "RECEIPT_PUBLICATION_KEY_INVALID")
        return RECEIPT_ARTIFACT_PREFIX + key

    def _verify_receipt_artifact(
        self, receipt: dict[str, Any], artifact_name: str, artifact_id: int
    ) -> None:
        require(type(artifact_id) is int and artifact_id > 0, "RECEIPT_ARTIFACT_ID_INVALID")
        metadata = self.source_api.get(f"actions/artifacts/{artifact_id}")
        require(
            isinstance(metadata, dict)
            and metadata.get("id") == artifact_id
            and metadata.get("name") == artifact_name
            and metadata.get("expired") is False,
            "RECEIPT_ARTIFACT_IDENTITY_MISMATCH",
        )
        archive = self.source_api.get(f"actions/artifacts/{artifact_id}/zip", binary=True)
        files = candidate_evidence.contents(archive)
        require(len(files) == 1, "RECEIPT_ARTIFACT_CONTENT_INVALID")
        raw = next(iter(files.values()))
        try:
            observed = json.loads(raw.decode("utf-8"), object_pairs_hook=candidate_evidence.unique)
        except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
            raise MutationError("RECEIPT_ARTIFACT_CONTENT_INVALID") from exc
        require(isinstance(observed, dict)
                and canonical_json(observed) == canonical_json(receipt),
                "RECEIPT_ARTIFACT_DIVERGENT_STOP")

    def reconcile_receipt(self, receipt: dict[str, Any]) -> dict[str, Any]:
        artifact_name = self._receipt_artifact_name(receipt)
        encoded = urllib.parse.quote(artifact_name, safe="")
        artifacts: list[dict[str, Any]] = []
        total: int | None = None
        for page in range(1, 11):
            result = self.source_api.get(
                f"actions/artifacts?name={encoded}&per_page=100&page={page}"
            )
            require(isinstance(result, dict) and isinstance(result.get("artifacts"), list)
                    and type(result.get("total_count")) is int
                    and result["total_count"] >= 0,
                    "RECEIPT_ARTIFACT_INDEX_INVALID")
            if total is None:
                total = result["total_count"]
            else:
                require(total == result["total_count"], "RECEIPT_ARTIFACT_INDEX_DRIFTED")
            artifacts.extend(result["artifacts"])
            if len(artifacts) >= total:
                break
        require(total is not None and len(artifacts) >= total,
                "RECEIPT_ARTIFACT_INDEX_INCOMPLETE")
        active_ids: list[int] = []
        for artifact in artifacts:
            require(isinstance(artifact, dict), "RECEIPT_ARTIFACT_INDEX_INVALID")
            if artifact.get("expired") is True:
                continue
            artifact_id = artifact.get("id")
            require(artifact.get("name") == artifact_name
                    and type(artifact_id) is int and artifact_id > 0,
                    "RECEIPT_ARTIFACT_INDEX_INVALID")
            active_ids.append(artifact_id)
        require(len(active_ids) == len(set(active_ids)), "RECEIPT_ARTIFACT_AMBIGUOUS_STOP")
        for artifact_id in sorted(active_ids):
            self._verify_receipt_artifact(receipt, artifact_name, artifact_id)
        return {
            "schemaVersion": 1,
            "status": "RECEIPT_EXACT" if active_ids else "RECEIPT_ABSENT",
            "artifactName": artifact_name,
            "artifactIds": sorted(active_ids),
            "uploadRequired": not active_ids,
        }

    def verify_receipt(
        self, receipt: dict[str, Any], artifact_id: int | None = None
    ) -> dict[str, Any]:
        artifact_name = self._receipt_artifact_name(receipt)
        if artifact_id is None:
            state = self.reconcile_receipt(receipt)
            require(state["status"] == "RECEIPT_EXACT", "RECEIPT_PERSISTENCE_MISSING")
            artifact_ids = state["artifactIds"]
        else:
            self._verify_receipt_artifact(receipt, artifact_name, artifact_id)
            artifact_ids = [artifact_id]
        return {
            "schemaVersion": 1,
            "status": "RECEIPT_PERSISTENCE_VERIFIED",
            "artifactName": artifact_name,
            "artifactIds": artifact_ids,
            "publicationKey": receipt["publicationKey"],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    github = sub.add_parser("github")
    github.add_argument("--source-report", type=Path, required=True)
    github.add_argument("--repo-root", type=Path, default=ROOT)
    github.add_argument("--candidate-output", type=Path, required=True)
    github.add_argument("--github-report", type=Path, required=True)
    final = sub.add_parser("finalize")
    final.add_argument("--source-report", type=Path, required=True)
    final.add_argument("--github-report", type=Path, required=True)
    final.add_argument("--curseforge-report", type=Path, required=True)
    final.add_argument("--repo-root", type=Path, default=ROOT)
    final.add_argument("--receipt", type=Path, required=True)
    final.add_argument("--receipt-state-report", type=Path, required=True)
    verify = sub.add_parser("verify-receipt")
    verify.add_argument("--receipt", type=Path, required=True)
    verify.add_argument("--artifact-id", type=int)
    verify.add_argument("--repo-root", type=Path, default=ROOT)
    verify.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        adapter = GitHubPublicationAdapter(os.environ.get("GITHUB_TOKEN", ""))
        source_api = candidate_evidence.GitHub()
        if args.mode == "github":
            machine = StablePublication(args.repo_root, adapter, source_api)
            source_report = read_json(args.source_report)
            report = machine.mutate_github(source_report, args.candidate_output)
            write_report(args.github_report, report)
        elif args.mode == "finalize":
            source_report = read_json(args.source_report)
            validator = StablePublication(args.repo_root, adapter, source_api)
            validated = validator.validate_source_report(source_report)
            manifest = read_json(args.repo_root / validated["contract"]["path"])
            public_reader = publish_curseforge.Publisher(args.repo_root, manifest)
            machine = StablePublication(
                args.repo_root, adapter, source_api, curseforge_public=public_reader
            )
            report = machine.finalize(
                source_report, read_json(args.github_report),
                read_json(args.curseforge_report),
            )
            write_report(args.receipt, report)
            write_report(args.receipt_state_report, machine.reconcile_receipt(report))
        else:
            machine = StablePublication(args.repo_root, adapter, source_api)
            report = machine.verify_receipt(read_json(args.receipt), args.artifact_id)
            write_report(args.report, report)
        print(json.dumps({
            key: report.get(key) for key in (
                "status", "publicationKey", "qualifiedCommit", "publicationComplete"
            ) if key in report
        }, sort_keys=True))
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError, publish_curseforge.PublicationError) as exc:
        print(json.dumps({"status": "STABLE_PUBLICATION_BLOCKED", "reason": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
