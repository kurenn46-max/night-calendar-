"""Static safeguards for manual signing and disposable-key CI rehearsal."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/signed-candidate.yml").read_text(encoding="utf-8")
SCRIPT = (ROOT / "scripts/sign_release_candidate.sh").read_text(encoding="utf-8")


class CandidateGatePolicyTests(unittest.TestCase):
    def test_release_never_happens_from_this_workflow(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", WORKFLOW)
        self.assertNotIn("gh release create", WORKFLOW + SCRIPT)
        self.assertNotIn("releases: write", WORKFLOW)
        self.assertNotIn("permissions:\n  contents: write", WORKFLOW)

    def test_manual_signing_requires_secrets_and_environment(self):
        for name in ("KEYSTORE_B64", "KEYSTORE_PASSWORD", "KEY_ALIAS", "KEY_PASSWORD",
                     "EXPECTED_CERT_SHA256"):
            self.assertIn("secrets.NIGHT_CALENDAR_" + name, WORKFLOW)
            self.assertIn(name, SCRIPT)
        self.assertIn("environment: release-candidate", WORKFLOW)
        self.assertIn("persist-credentials: false", WORKFLOW)
        self.assertIn('if [ -z "${!name:-}" ]; then', SCRIPT)

    def test_shared_signer_verifies_signature_fingerprint_and_identity(self):
        self.assertIn("bash scripts/sign_release_candidate.sh", WORKFLOW)
        self.assertIn('"$tools_dir/apksigner" sign', SCRIPT)
        self.assertIn('"$tools_dir/apksigner" verify --verbose', SCRIPT)
        self.assertIn('Signing certificate fingerprint mismatch', SCRIPT)
        self.assertIn('"$package" != "com.nightcalendar"', SCRIPT)
        self.assertIn("sha256sum NIGHT_CALENDAR_candidate.apk", SCRIPT)
        self.assertIn("if [ \"${#actual}\" -ne 64 ]", SCRIPT)
        self.assertIn("rm -f \"$output\"", SCRIPT)

    def test_signing_key_is_ephemeral_and_never_committed(self):
        self.assertIn('mktemp -d "$RUNNER_TEMP/', SCRIPT)
        self.assertIn("chmod 600", SCRIPT)
        self.assertIn('trap cleanup EXIT', SCRIPT)
        self.assertNotIn("git add", WORKFLOW + SCRIPT)
        self.assertNotIn("git push", WORKFLOW + SCRIPT)

    def test_rehearsal_uses_no_secrets_and_disposable_key(self):
        rehearsal = WORKFLOW.split("  signing_rehearsal:", 1)[1]
        self.assertIn("if: github.event_name == 'pull_request'", rehearsal)
        self.assertIn("ci-only-throwaway", rehearsal)
        self.assertIn("keytool -genkeypair", rehearsal)
        self.assertIn("bash scripts/sign_release_candidate.sh", rehearsal)
        self.assertIn("sha256sum -c SHA256SUMS.txt", rehearsal)
        self.assertIn("The signer accepted a mismatched certificate", rehearsal)
        self.assertIn("test ! -f signed-candidate/NIGHT_CALENDAR_candidate.apk", rehearsal)
        self.assertNotIn("secrets.", rehearsal)
        self.assertNotIn("upload-artifact", rehearsal)

    def test_no_release_candidate_artifact_on_failed_signing(self):
        self.assertIn("if-no-files-found: error", WORKFLOW)
        self.assertIn("needs: policy", WORKFLOW)
        self.assertIn("retention-days: 14", WORKFLOW)
        self.assertIn("if [ \"$success\" -ne 1 ]; then", SCRIPT)


if __name__ == "__main__":
    unittest.main()
