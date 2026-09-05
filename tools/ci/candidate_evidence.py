"""Produce and verify CI-owned evidence. Local files never authenticate a run."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import threading
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPOSITORY = "emmanueltremblay9-stack/Immersive-BOP_Harvest"
WORKFLOW = ".github/workflows/build.yml"
ARTIFACT_PREFIX = "candidate-evidence-"
LIMIT = 64 * 1024 * 1024
REQUIRED_STEPS = {
    "Clean Gradle outputs before collecting evidence",
    "Test publisher safety first", "Validate specification and deterministic resources",
    "Check authoritative manifest ledger", "Lint GitHub Actions workflows", "Gradle check and build",
    "Supply exact isolated runtime dependencies without Prism", "Required GameTests and datagen",
    "Collect candidate evidence", "Retain candidate evidence",
}
WINDOWS_STEPS = {"Test publisher safety first", "Test source consumers and strict stable evidence"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def read_json(raw: bytes):
    return json.loads(raw, object_pairs_hook=unique)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def jar_identity(raw: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(raw)) as jar:
        name = "META-INF/neoforge.mods.toml"
        require(jar.namelist().count(name) == 1 and jar.getinfo(name).file_size <= 65536, "Ambiguous JAR metadata")
        metadata = tomllib.loads(jar.read(name).decode("utf-8"))
    mods = [m for m in metadata["mods"] if m.get("modId") == "immersive_bop_harvest"]
    require(len(mods) == 1 and isinstance(mods[0].get("version"), str), "Wrong candidate mod identity")
    require(metadata.get("license") == "All Rights Reserved", "Wrong candidate license")
    return {"modId": mods[0]["modId"], "version": mods[0]["version"], "license": metadata["license"]}


def contents(archive: bytes) -> dict[str, bytes]:
    require(len(archive) <= LIMIT, "Archive exceeds limit")
    output = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        require(len(z.infolist()) <= 100 and sum(i.file_size for i in z.infolist()) <= LIMIT, "Expanded archive exceeds limit")
        for item in z.infolist():
            name = item.filename
            require(item.orig_filename == name and name not in output and not item.is_dir() and "\\" not in name and ":" not in name
                    and not PurePosixPath(name).is_absolute() and all(p not in {"", ".", ".."} for p in name.split("/")), "Unsafe or duplicate ZIP entry")
            require((item.external_attr >> 16) & 0o170000 != 0o120000, "Symlinked ZIP entry")
            output[name] = z.read(item)
    return output


def report_capabilities(files: dict[str, bytes], *, specs: dict | None = None) -> dict:
    """Derive limited capabilities from captured outputs, never submitted PASS lists."""
    runtime = files["runtime.log"].decode("utf-8")
    matches = re.findall(r"All (\d+) required tests passed", runtime)
    require(len(matches) == 1 and int(matches[0]) >= 3 and "BUILD SUCCESSFUL" in runtime, "No complete GameTest evidence")
    require("BUILD SUCCESSFUL" in files["gradle-build.log"].decode("utf-8"), "No build evidence")
    require("BUILD SUCCESSFUL" in files["datagen-repeat.log"].decode("utf-8"), "No repeated datagen evidence")
    dependencies = read_json(files["runtime-dependencies.json"])
    require(dependencies.get("status") == "PASS" and len(dependencies.get("dependencies", [])) == 5, "Missing locked dependency proof")
    result = {"sourceBuild": True, "developmentGameTests": int(matches[0]), "repeatedDatagen": True,
              "packagedRuntime": False, "client": False, "multiplayer": False, "saveReload": False}
    if "qualification-gametests.json" in files:
        require(specs is not None, "Qualification requires the exact source specification")
        from tools.ci.qualification_report import validate
        qualified = validate(files["qualification-gametests.json"], specs, jar_identity(files["candidate.jar"])["version"])
        require(int(matches[0]) == qualified["cases"] + 3, "GameTest log/report count mismatch")
        result["scopedCompatibility"] = qualified
    return result


def check_dependency_receipt(raw: bytes, lock: bytes) -> None:
    keys = ["modId", "version", "projectId", "fileId", "filename", "size", "sha256"]
    expected = [{key: row[key] for key in keys} for row in read_json(lock)["dependencies"]]
    actual = read_json(raw)["dependencies"]
    require(len(expected) == 5 and actual == expected, "Dependency receipt differs from exact source lock")


def collect() -> None:
    require(os.environ.get("GITHUB_ACTIONS") == "true", "Collection requires CI context; not local attestation")
    require(os.environ["GITHUB_REPOSITORY"] == REPOSITORY, "Wrong repository")
    commit = git("rev-parse", "HEAD")
    version = dict(line.split("=", 1) for line in (ROOT / "gradle.properties").read_text().splitlines() if "=" in line)["mod_version"]
    name = f"immersive_bop_harvest-{version}.jar"
    jar = (ROOT / "build/libs" / name).read_bytes()
    identity = jar_identity(jar)
    require(identity["version"] == version, "JAR/source version mismatch")
    files = {"candidate.jar": jar}
    for filename in ("runtime.log", "gradle-build.log", "datagen-repeat.log", "runtime-dependencies.json", "qualification-gametests.json"):
        files[filename] = (ROOT / "build/ci-evidence" / filename).read_bytes()
    from tools.ci.qualification_report import load_specs
    capabilities = report_capabilities(files, specs=load_specs(ROOT))
    check_dependency_receipt(files["runtime-dependencies.json"], (ROOT / "tools/ci/runtime-dependencies.lock.json").read_bytes())
    receipt = {"schemaVersion": 1, "repository": REPOSITORY, "workflowPath": WORKFLOW,
               "workflowRef": os.environ["GITHUB_WORKFLOW_REF"], "workflowSha": os.environ["GITHUB_WORKFLOW_SHA"],
               "runId": int(os.environ["GITHUB_RUN_ID"]), "runAttempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
               "event": os.environ["GITHUB_EVENT_NAME"], "sourceCommit": commit, "sourceTree": git("rev-parse", "HEAD^{tree}"),
               "dependencyLockSha256": sha((ROOT / "tools/ci/runtime-dependencies.lock.json").read_bytes()),
               "candidate": {**identity, "name": name, "size": len(jar), "sha256": sha(jar)},
               "executionMode": "development-classpath", "capabilities": capabilities,
               "files": {name: {"size": len(raw), "sha256": sha(raw)} for name, raw in files.items()}}
    output = ROOT / "build/candidate-evidence"
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


class GitHub:
    """Only GETs through the existing authenticated gh session; no token reads."""
    def get(self, path: str, *, binary: bool = False):
        command = ["gh", "api", "--method", "GET", f"repos/{REPOSITORY}/{path}"]
        if binary:
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
                timer = threading.Timer(90, process.kill)
                timer.start()
                try:
                    raw = process.stdout.read(LIMIT + 1)
                    require(len(raw) <= LIMIT, "Downloaded archive exceeds limit")
                    require(process.wait(timeout=5) == 0, "GitHub artifact download failed")
                    return raw
                finally:
                    timer.cancel()
                    if process.poll() is None:
                        process.kill()
                    process.wait()
        result = subprocess.run(command,
                                capture_output=True, timeout=90)
        require(result.returncode == 0, "GitHub readback failed; credentials/API access unavailable")
        return read_json(result.stdout)


def verify(run_id: int, attempt: int, expected_commit: str, *, api: GitHub | None = None) -> dict:
    require(type(run_id) is int and run_id > 0 and type(attempt) is int and attempt > 0, "Invalid run identity")
    require(re.fullmatch(r"[0-9a-f]{40}", expected_commit) is not None, "Expected commit must be supplied independently")
    api = api or GitHub()
    run = api.get(f"actions/runs/{run_id}/attempts/{attempt}")
    require(run.get("id") == run_id and run.get("run_attempt") == attempt and run.get("head_sha") == expected_commit,
            "Run/attempt/source identity mismatch")
    require(run.get("repository", {}).get("full_name") == REPOSITORY and run.get("path") == WORKFLOW,
            "Unexpected repository/workflow")
    require(run.get("event") == "push" and run.get("head_branch") == "main", "Only canonical main push qualifies execution provenance")
    require(run.get("status") == "completed" and run.get("conclusion") == "success", "Run is not successful")
    jobs = api.get(f"actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100")
    require(jobs.get("total_count") == len(jobs.get("jobs", [])) and len(jobs["jobs"]) == 2, "Incomplete or unexpected job inventory")
    by_name = {job["name"]: job for job in jobs["jobs"]}
    require(set(by_name) == {"Gradle validation", "Windows manifest regressions"}, "Wrong job identity")
    require(all(j["conclusion"] == "success" for j in by_name.values()), "Required job failed")
    for job, required in {"Gradle validation": REQUIRED_STEPS, "Windows manifest regressions": WINDOWS_STEPS}.items():
        passed = {s["name"] for s in by_name[job]["steps"] if s["conclusion"] == "success"}
        require(required <= passed, f"Required {job} steps missing or skipped")
    commit = api.get(f"git/commits/{expected_commit}")
    artifacts = api.get(f"actions/runs/{run_id}/artifacts?per_page=100")
    require(artifacts.get("total_count") == len(artifacts.get("artifacts", [])), "Incomplete artifact inventory")
    name = f"{ARTIFACT_PREFIX}{run_id}-{attempt}"
    matches = [a for a in artifacts["artifacts"] if a.get("name") == name]
    require(len(matches) == 1 and matches[0].get("expired") is False, "Missing, duplicate or expired candidate artifact")
    artifact = matches[0]
    require(type(artifact.get("size_in_bytes")) is int and 0 < artifact["size_in_bytes"] <= LIMIT,
            "Service artifact size missing or exceeds limit")
    require(artifact.get("workflow_run", {}).get("id") == run_id and artifact["workflow_run"].get("head_sha") == expected_commit,
            "Artifact belongs to another run/source")
    archive = api.get(f"actions/artifacts/{artifact['id']}/zip", binary=True)
    require(artifact.get("digest") == "sha256:" + sha(archive), "Service digest missing or artifact altered")
    files = contents(archive)
    receipt = read_json(files.pop("receipt.json"))
    require(type(receipt.get("schemaVersion")) is int and receipt["schemaVersion"] == 1, "Wrong evidence schema")
    for key, expected in {"repository": REPOSITORY, "workflowPath": WORKFLOW, "runId": run_id, "runAttempt": attempt,
                          "event": "push", "sourceCommit": expected_commit, "sourceTree": commit["tree"]["sha"],
                          "workflowSha": expected_commit, "workflowRef": f"{REPOSITORY}/{WORKFLOW}@refs/heads/main",
                          "executionMode": "development-classpath"}.items():
        require(type(receipt.get(key)) is type(expected) and receipt[key] == expected, f"Receipt {key} not bound to service state")
    require(set(receipt["files"]) == set(files), "Receipt inventory mismatch")
    for name, raw in files.items():
        require(receipt["files"][name] == {"size": len(raw), "sha256": sha(raw)}, "Evidence bytes mismatch")
    import base64
    lock = api.get(f"contents/tools/ci/runtime-dependencies.lock.json?ref={expected_commit}")
    lock_raw = base64.b64decode(lock["content"])
    require(receipt["dependencyLockSha256"] == sha(lock_raw), "Dependency lock mismatch")
    check_dependency_receipt(files["runtime-dependencies.json"], lock_raw)
    candidate = receipt["candidate"]
    raw = files["candidate.jar"]
    require(candidate == {**jar_identity(raw), "name": f"immersive_bop_harvest-{jar_identity(raw)['version']}.jar", "size": len(raw), "sha256": sha(raw)}, "Candidate raw/TOML identity mismatch")
    specs = None
    if "qualification-gametests.json" in files:
        from tools.ci.qualification_report import SPEC_FILES
        specs = {}
        for name in SPEC_FILES:
            source = api.get(f"contents/spec/{name}.json?ref={expected_commit}")
            specs[name] = read_json(base64.b64decode(source["content"]))
    capabilities = report_capabilities(files, specs=specs)
    require(receipt["capabilities"] == capabilities, "Unsupported capability claim")
    return {"authenticatedExecution": True, "stableReady": False, "status": "AUTHENTICATED_DEVELOPMENT_EXECUTION",
            "runId": run_id, "runAttempt": attempt, "sourceCommit": expected_commit, "sourceTree": receipt["sourceTree"],
            "artifactId": artifact["id"], "archiveSha256": sha(archive), "candidate": candidate, "capabilities": capabilities,
            "remaining": ["packaged-runtime", "client", "multiplayer", "save-reload", "full-acceptance", "final-stable-version"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("collect")
    check = modes.add_parser("verify")
    check.add_argument("--run-id", type=int, required=True)
    check.add_argument("--attempt", type=int, required=True)
    check.add_argument("--expected-commit", required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "collect":
            collect()
        else:
            print(json.dumps(verify(args.run_id, args.attempt, args.expected_commit), indent=2))
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        print(json.dumps({"authenticatedExecution": False, "stableReady": False, "status": "BLOCKED_PROVENANCE_READBACK", "reason": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
