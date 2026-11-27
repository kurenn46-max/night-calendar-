"""Fail-closed verification before publishing an owner-signed NIGHT CALENDAR APK.

This file never signs an APK and has no GitHub write operations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ARTIFACT_NAME = "night-calendar-signed-candidate"
APK_NAME = "NIGHT_CALENDAR_candidate.apk"
PACKAGE = "com.nightcalendar"
SIGNING_JOB = "Sign candidate APK but do not publish"


def demand(condition, reason):
    if not condition:
        raise ValueError(reason)


def verify_origin(run, workflow, jobs, artifacts, ci, *, run_id, repo, sha):
    """Accept only a successful, same-SHA, main-only manual signed run."""
    demand(re.fullmatch(r"[a-f0-9]{40}", sha) is not None, "invalid target SHA")
    demand(repo == "kurenn46-max/night-calendar-", "wrong release repository")
    demand(run.get("id") == run_id, "wrong candidate run ID")
    demand(run.get("repository", {}).get("full_name") == repo, "wrong source repository")
    demand(run.get("workflow_id") == workflow.get("id"), "wrong signing workflow")
    demand(workflow.get("path") == ".github/workflows/signed-candidate.yml", "wrong signing workflow path")
    demand(run.get("event") == "workflow_dispatch", "candidate was not manually requested")
    demand(run.get("head_branch") == "main" and run.get("head_sha") == sha, "candidate not from current main SHA")
    demand(run.get("status") == "completed" and run.get("conclusion") == "success", "signed candidate run did not pass")
    done = [job for job in jobs.get("jobs", []) if job.get("name") == SIGNING_JOB and job.get("conclusion") == "success"]
    demand(len(done) == 1, "production signer job not proven successful")
    eligible = [a for a in artifacts.get("artifacts", []) if a.get("name") == ARTIFACT_NAME]
    demand(len(eligible) == 1 and eligible[0].get("expired") is False, "unique live signed APK artifact missing")
    source = eligible[0].get("workflow_run") or {}
    demand(source.get("id") == run_id and source.get("head_sha") == sha, "artifact provenance does not match candidate")
    green = [w for w in ci.get("workflow_runs", []) if w.get("head_sha") == sha
             and w.get("event") == "push" and w.get("status") == "completed"
             and w.get("conclusion") == "success" and w.get("head_branch") == "main"]
    demand(bool(green), "main Android CI has not passed at candidate SHA")
    return eligible[0]["id"]


def verify_apk(directory, expected_digest, expected_tag, aapt, apksigner):
    """Cross-check the downloaded APK, signed certificate presence, package and version."""
    demand(re.fullmatch(r"[a-f0-9]{64}", expected_digest) is not None, "invalid expected APK SHA-256")
    demand(re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", expected_tag) is not None, "invalid release version")
    apk = directory / APK_NAME
    digest_file = directory / "SHA256SUMS.txt"
    demand(apk.is_file() and digest_file.is_file(), "signed candidate files missing")
    line = digest_file.read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"([a-f0-9]{64})  " + re.escape(APK_NAME), line)
    demand(match is not None, "malformed or ambiguous SHA256SUMS")
    actual = hashlib.sha256(apk.read_bytes()).hexdigest()
    demand(actual == match.group(1) == expected_digest, "candidate APK hash mismatch")
    subprocess.run([apksigner, "verify", "--verbose", "--min-sdk-version", "26", str(apk)], check=True,
                   capture_output=True, text=True, timeout=30)
    certificate = subprocess.run([apksigner, "verify", "--print-certs", str(apk)], check=True,
                                 capture_output=True, text=True, timeout=30).stdout
    demand(re.search(r"Signer #1 certificate SHA-256 digest: [a-fA-F0-9]{64}", certificate) is not None,
           "missing Android signing certificate")
    badging = subprocess.run([aapt, "dump", "badging", str(apk)], check=True,
                             capture_output=True, text=True, timeout=30).stdout
    package = re.search(r"^package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging, re.M)
    demand(package is not None and package.group(1) == PACKAGE, "wrong Android package")
    demand(package.group(2).isdigit() and int(package.group(2)) >= 1, "invalid versionCode")
    demand("v" + package.group(3) == expected_tag, "release tag does not match APK version")
    return actual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-json", type=Path)
    parser.add_argument("--workflow-json", type=Path)
    parser.add_argument("--jobs-json", type=Path)
    parser.add_argument("--artifacts-json", type=Path)
    parser.add_argument("--ci-json", type=Path)
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--apk-dir", type=Path)
    parser.add_argument("--expected-digest")
    parser.add_argument("--tag")
    parser.add_argument("--aapt")
    parser.add_argument("--apksigner")
    args = parser.parse_args()
    try:
        if args.apk_dir:
            demand(all((args.expected_digest, args.tag, args.aapt, args.apksigner)),
                   "APK validation options required")
            verify_apk(args.apk_dir, args.expected_digest, args.tag, args.aapt, args.apksigner)
        else:
            demand(all((args.run_json, args.workflow_json, args.jobs_json,
                        args.artifacts_json, args.ci_json, args.run_id)),
                   "GitHub provenance options required")
            files = (args.run_json, args.workflow_json, args.jobs_json, args.artifacts_json, args.ci_json)
            data = [json.loads(file.read_text(encoding="utf-8")) for file in files]
            artifact_id = verify_origin(*data, run_id=args.run_id, repo=args.repository, sha=args.head_sha)
            print("Signed candidate provenance accepted; artifact ID:", artifact_id)
    except (ValueError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print("RELEASE BLOCKED:", exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
