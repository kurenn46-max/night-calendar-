"""Offline, no-secrets verification tests for production publication policy."""
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from verify_release_candidate import verify_apk, verify_origin, APK_NAME, SIGNING_JOB, ARTIFACT_NAME


REPO = "kurenn46-max/night-calendar-"
SHA = "a" * 40
RUN_ID = 12345678


def fixtures():
    run = {"id": RUN_ID, "repository": {"full_name": REPO}, "workflow_id": 42,
           "event": "workflow_dispatch", "head_branch": "main", "head_sha": SHA,
           "status": "completed", "conclusion": "success"}
    workflow = {"id": 42, "path": ".github/workflows/signed-candidate.yml"}
    jobs = {"jobs": [{"name": SIGNING_JOB, "conclusion": "success"}]}
    artifacts = {"artifacts": [{"id": 9, "name": ARTIFACT_NAME, "expired": False,
                               "workflow_run": {"id": RUN_ID, "head_sha": SHA}}]}
    ci = {"workflow_runs": [{"head_sha": SHA, "event": "push", "status": "completed",
                             "conclusion": "success", "head_branch": "main"}]}
    return [run, workflow, jobs, artifacts, ci]


def check(data):
    return verify_origin(*data, run_id=RUN_ID, repo=REPO, sha=SHA)


class PublicationOriginTests(unittest.TestCase):
    def test_exact_valid_run(self):
        self.assertEqual(check(fixtures()), 9)

    def test_unknown_or_wrong_workflow_fails(self):
        data = fixtures()
        data[0]["workflow_id"] = 44
        with self.assertRaisesRegex(ValueError, "workflow"):
            check(data)

    def test_wrong_event_fails(self):
        data = fixtures()
        data[0]["event"] = "pull_request"
        with self.assertRaisesRegex(ValueError, "manually"):
            check(data)

    def test_head_sha_tamper_fails(self):
        data = fixtures()
        data[0]["head_sha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "main SHA"):
            check(data)

    def test_unfinished_sign_job_fails(self):
        data = fixtures()
        data[2]["jobs"][0]["conclusion"] = "skipped"
        with self.assertRaisesRegex(ValueError, "signer job"):
            check(data)

    def test_forged_artifact_link_fails(self):
        data = fixtures()
        data[3]["artifacts"][0]["workflow_run"]["id"] = 123
        with self.assertRaisesRegex(ValueError, "provenance"):
            check(data)

    def test_expired_or_duplicate_artifact_fails(self):
        data = fixtures()
        data[3]["artifacts"][0]["expired"] = True
        with self.assertRaisesRegex(ValueError, "artifact"):
            check(data)
        data = fixtures()
        data[3]["artifacts"].append(copy.deepcopy(data[3]["artifacts"][0]))
        with self.assertRaisesRegex(ValueError, "artifact"):
            check(data)

    def test_main_ci_must_match_sha(self):
        data = fixtures()
        data[4]["workflow_runs"][0]["head_sha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "CI"):
            check(data)

    def test_candidate_run_must_have_succeeded(self):
        data = fixtures()
        data[0]["conclusion"] = "failure"
        with self.assertRaisesRegex(ValueError, "did not pass"):
            check(data)


class PublicationApkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        (self.path / APK_NAME).write_bytes(b"valid-signed-test-fixture")
        self.digest = hashlib.sha256((self.path / APK_NAME).read_bytes()).hexdigest()
        (self.path / "SHA256SUMS.txt").write_text(f"{self.digest}  {APK_NAME}\n")
        self.signer = subprocess.CompletedProcess(
            [], 0, stdout="Signer #1 certificate SHA-256 digest: " + ("b" * 64))
        self.badging = subprocess.CompletedProcess(
            [], 0, stdout="package: name='com.nightcalendar' versionCode='1' versionName='0.1.0'\n")

    def validate(self, digest=None, tag="v0.1.0"):
        def process(cmd, **kwargs):
            if "dump" in cmd:
                return self.badging
            if "--print-certs" in cmd:
                return self.signer
            return subprocess.CompletedProcess([], 0, stdout="Verified")
        with patch("verify_release_candidate.subprocess.run", side_effect=process) as run:
            outcome = verify_apk(self.path, digest or self.digest, tag, "aapt", "apksigner")
            self.assertEqual(run.call_count, 3)
            return outcome

    def test_signed_candidate_verifies(self):
        self.assertEqual(self.validate(), self.digest)

    def test_wrong_owner_entered_sha_rejected(self):
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.validate(digest="0" * 64)

    def test_checksum_tampering_rejected(self):
        (self.path / "SHA256SUMS.txt").write_text(self.digest + " *" + APK_NAME)
        with self.assertRaisesRegex(ValueError, "SHA256SUMS"):
            self.validate()

    def test_wrong_version_rejected(self):
        with self.assertRaisesRegex(ValueError, "tag"):
            self.validate(tag="v2.0.0")

    def test_wrong_package_rejected(self):
        self.badging.stdout = "package: name='com.bad' versionCode='1' versionName='0.1.0'"
        with self.assertRaisesRegex(ValueError, "package"):
            self.validate()

    def test_absent_certificate_rejected(self):
        self.signer.stdout = "no signing cert"
        with self.assertRaisesRegex(ValueError, "certificate"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
