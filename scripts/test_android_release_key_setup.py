"""Source-level checks for the owner-operated, Android-only key setup script.
This CI suite never runs keytool, authenticates to GitHub or creates a real key.
"""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts/android_release_key_setup.sh"
SCRIPT = SCRIPT_PATH.read_text(encoding="utf-8")


class AndroidReleaseKeySetupTests(unittest.TestCase):
    def test_bash_syntax_only(self):
        subprocess.run(["bash", "-n", str(SCRIPT_PATH)], check=True, capture_output=True)

    def test_keystore_stays_in_termux_private_storage(self):
        self.assertIn('umask 077', SCRIPT)
        self.assertIn('private_dir="$HOME/.local/share/night-calendar-signing"', SCRIPT)
        self.assertIn('chmod 700 "$private_dir"', SCRIPT)
        self.assertIn('chmod 600 "$keystore"', SCRIPT)
        self.assertNotIn("termux-setup-storage", SCRIPT)
        self.assertNotIn("/sdcard/", SCRIPT)

    def test_never_overwrite_an_existing_release_key(self):
        self.assertIn('if [ -e "$keystore" ]; then', SCRIPT)
        self.assertIn('if [ "$choice" != "REUSE" ]; then', SCRIPT)
        self.assertIn("keytool -list", SCRIPT)
        self.assertIn("keytool -genkeypair", SCRIPT)
        self.assertIn("keytool -exportcert", SCRIPT)

    def test_password_not_passed_as_process_argument(self):
        self.assertIn('IFS= read -r -s -p', SCRIPT)
        self.assertIn('-storepass:env NIGHT_SIGN_PASS', SCRIPT)
        self.assertIn('-keypass:env NIGHT_SIGN_PASS', SCRIPT)
        self.assertIn('set +x', SCRIPT)
        self.assertIn("trap 'unset NIGHT_SIGN_PASS' EXIT", SCRIPT)
        self.assertNotIn('-storepass "$NIGHT_SIGN_PASS"', SCRIPT)
        self.assertNotIn('-keypass "$NIGHT_SIGN_PASS"', SCRIPT)
        self.assertNotIn('echo "$NIGHT_SIGN_PASS"', SCRIPT)

    def test_all_secrets_go_only_to_expected_environment(self):
        self.assertIn('repo="kurenn46-max/night-calendar-"', SCRIPT)
        self.assertIn('environment="release-candidate"', SCRIPT)
        for name in (
            "NIGHT_CALENDAR_KEYSTORE_B64",
            "NIGHT_CALENDAR_KEYSTORE_PASSWORD",
            "NIGHT_CALENDAR_KEY_ALIAS",
            "NIGHT_CALENDAR_KEY_PASSWORD",
            "NIGHT_CALENDAR_EXPECTED_CERT_SHA256",
        ):
            self.assertIn('gh secret set ' + name, SCRIPT)
        secret_calls = [line for line in SCRIPT.splitlines() if " | gh secret set " in line]
        self.assertEqual(len(secret_calls), 5)
        self.assertTrue(all('-R "$repo" -e "$environment"' in line for line in secret_calls))
        self.assertIn('fingerprint_compact', SCRIPT)

    def test_main_only_environment_policy_precedes_secret_upload(self):
        self.assertIn(
            '"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}',
            SCRIPT,
        )
        self.assertIn("-f name=main -f type=branch", SCRIPT)
        self.assertIn('approved_branches" != "main"', SCRIPT)
        self.assertIn("Existing environment protection rules must never be overwritten", SCRIPT)
        self.assertLess(SCRIPT.index("Checking GitHub release environment"),
                        SCRIPT.index("gh secret set NIGHT_CALENDAR_KEYSTORE_B64"))

    def test_no_automatic_build_or_release(self):
        self.assertNotIn("gh workflow run", SCRIPT)
        self.assertNotIn("gh release create", SCRIPT)
        self.assertNotIn("gradle ", SCRIPT)
        self.assertNotIn("git push", SCRIPT)
        self.assertIn("OFF-DEVICE backups", SCRIPT)


if __name__ == "__main__":
    unittest.main()
