"""Static safeguards for manual signing and disposable-key CI rehearsal."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/signed-candidate.yml").read_text(encoding="utf-8")
SCRIPT = (ROOT / "scripts/sign_release_candidate.sh").read_text(encoding="utf-8")
RELEASE_SMOKE = (ROOT / "scripts/release_emulator_smoke.sh").read_text(encoding="utf-8")


class CandidateGatePolicyTests(unittest.TestCase):
    def test_release_never_happens_from_this_workflow(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", WORKFLOW)
        self.assertNotIn("gh release create", WORKFLOW + SCRIPT)
        self.assertNotIn("releases: write", WORKFLOW)
        self.assertNotIn("permissions:\n  contents: write", WORKFLOW)

    def test_real_signing_must_run_only_from_reviewed_main(self):
        self.assertIn(
            "if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'",
            WORKFLOW,
        )
        # Pull-request runs must never read a production signing environment.
        signing = WORKFLOW.split("  sign_candidate:", 1)[1].split("  signing_rehearsal:", 1)[0]
        self.assertIn("environment: release-candidate", signing)
        self.assertIn("needs: policy", signing)
        self.assertNotIn("contents: write", signing)

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

    def test_signed_release_is_installed_and_relaunched_on_emulator(self):
        rehearsal = WORKFLOW.split("  signing_rehearsal:", 1)[1]
        self.assertIn("reactivecircus/android-emulator-runner@v2", rehearsal)
        self.assertIn("api-level: 36", rehearsal)
        self.assertIn("script: bash scripts/release_emulator_smoke.sh", rehearsal)
        self.assertIn('export EXPECTED_CERT_SHA256="$trusted_fingerprint"', rehearsal)
        self.assertIn("Delete ephemeral signed APK", rehearsal)
        self.assertIn("rm -rf signed-candidate", rehearsal)
        self.assertIn('adb -e install -r "$apk"', RELEASE_SMOKE)
        self.assertIn("adb -e shell am start -W", RELEASE_SMOKE)
        self.assertIn('adb -e shell am force-stop "$package"', RELEASE_SMOKE)
        self.assertIn("端末内だけでカレンダーの読み込み状態を診断", RELEASE_SMOKE)
        self.assertNotIn("secrets.", rehearsal)
        self.assertNotIn("upload-artifact", rehearsal)

    def test_android16_emulator_can_use_safe_cpu_fallback(self):
        rehearsal = WORKFLOW.split("  signing_rehearsal:", 1)[1]
        self.assertIn("api-level: 36", rehearsal)
        self.assertIn("disable-linux-hw-accel: auto", rehearsal)
        self.assertIn('if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then', rehearsal)
        self.assertIn('echo "ANDROID_I_WANT_MY_TCG=yes" >> "$GITHUB_ENV"', rehearsal)
        self.assertIn("emulator-boot-timeout: 900", rehearsal)
        self.assertIn("script: bash scripts/release_emulator_smoke.sh", rehearsal)
        self.assertNotIn("secrets.", rehearsal)

    def test_no_release_candidate_artifact_on_failed_signing(self):
        self.assertIn("if-no-files-found: error", WORKFLOW)
        self.assertIn("needs: policy", WORKFLOW)
        self.assertIn("retention-days: 14", WORKFLOW)
        self.assertIn("if [ \"$success\" -ne 1 ]; then", SCRIPT)


if __name__ == "__main__":
    unittest.main()
