import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("nightcore_repair", Path(__file__).parent / "nightcore_repair.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = '''name: Android APK
steps:
      - name: Install Android SDK
        run: |
            test -x "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" || { echo "NIGHT_CORE_ERROR: sdkmanager missing"; exit 1; }
            yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses > /dev/null || true
            "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "platforms;android-35" "build-tools;35.0.0"
'''


class RepairTests(unittest.TestCase):
    def test_known_sdk_failure_produces_narrow_fix(self):
        amended, rule = module.plan_repair({"status": "failed", "category": "android-sdk", "evidence": ["sdkmanager: executable not found"]}, BASE)
        self.assertEqual(rule, "sdkmanager-path-fallback")
        self.assertIn('command -v sdkmanager', amended)
        self.assertIn('platforms;android-35', amended)

    def test_repeated_failure_does_not_patch_twice(self):
        evidence = {"status": "failed", "category": "android-sdk", "evidence": ["sdkmanager: not found"]}
        patched, _ = module.plan_repair(evidence, BASE)
        again, rule = module.plan_repair(evidence, patched)
        self.assertIsNone(again)
        self.assertEqual(rule, "precondition-mismatch")

    def test_non_sdk_failure_is_never_autopatched(self):
        amended, reason = module.plan_repair({"status": "failed", "category": "kotlin-compile", "evidence": ["Unresolved reference"]}, BASE)
        self.assertIsNone(amended)
        self.assertEqual(reason, "no-verified-playbook")

    def test_forged_category_cannot_patch(self):
        amended, reason = module.plan_repair({"status": "failed", "category": "android-sdk; rm -rf /", "evidence": ["sdkmanager"]}, BASE)
        self.assertIsNone(amended)
        self.assertEqual(reason, "invalid-category")

    def test_passed_build_not_changed(self):
        amended, reason = module.plan_repair({"status": "passed", "category": "android-sdk", "evidence": ["sdkmanager"]}, BASE)
        self.assertIsNone(amended)
        self.assertEqual(reason, "not-failed")

    def test_missing_evidence_stops_patch(self):
        amended, reason = module.plan_repair({"status": "failed", "category": "android-sdk", "evidence": []}, BASE)
        self.assertIsNone(amended)
        self.assertEqual(reason, "insufficient-evidence")


if __name__ == '__main__':
    unittest.main()
