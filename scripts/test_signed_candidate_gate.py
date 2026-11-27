"""Source-level safeguards for manual signed-candidate workflow (no real keys)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/signed-candidate.yml").read_text(encoding="utf-8")


class CandidateGatePolicyTests(unittest.TestCase):
    def test_never_auto_publishes(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", WORKFLOW)
        self.assertNotIn("gh release create", WORKFLOW)
        self.assertNotIn("releases: write", WORKFLOW)
        self.assertNotIn("permissions:\n  contents: write", WORKFLOW)

    def test_no_stored_keys_in_repository(self):
        self.assertIn("secrets.NIGHT_CALENDAR_KEYSTORE_B64", WORKFLOW)
        self.assertIn("secrets.NIGHT_CALENDAR_KEYSTORE_PASSWORD", WORKFLOW)
        self.assertIn("secrets.NIGHT_CALENDAR_KEY_ALIAS", WORKFLOW)
        self.assertIn("secrets.NIGHT_CALENDAR_KEY_PASSWORD", WORKFLOW)
        self.assertIn("secrets.NIGHT_CALENDAR_EXPECTED_CERT_SHA256", WORKFLOW)
        self.assertIn('keystore="$RUNNER_TEMP/night-calendar-signing/release.keystore"', WORKFLOW)
        self.assertIn("chmod 600", WORKFLOW)
        self.assertNotIn("git add", WORKFLOW)

    def test_signature_and_identity_are_verified_before_artifact(self):
        self.assertIn('"$tools_dir/apksigner" sign', WORKFLOW)
        self.assertIn('"$tools_dir/apksigner" verify', WORKFLOW)
        self.assertIn("Signing certificate fingerprint mismatch", WORKFLOW)
        self.assertIn("com.nightcalendar", WORKFLOW)
        self.assertIn("Store verified candidate without publishing a release", WORKFLOW)

    def test_workflow_uses_readonly_token_and_manual_gate(self):
        self.assertIn("  contents: read", WORKFLOW)
        self.assertIn("environment: release-candidate", WORKFLOW)
        self.assertIn("persist-credentials: false", WORKFLOW)
        self.assertIn("if-no-files-found: error", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
