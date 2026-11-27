import unittest
import importlib.util
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile

spec = importlib.util.spec_from_file_location("ci_diagnose", Path(__file__).parent / "ci_diagnose.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DiagnoseTests(unittest.TestCase):
    def test_sdk_failure(self):
        result = module.diagnose("sdkmanager: command not found")
        self.assertEqual(result["category"], "android-sdk")
        self.assertTrue(result["requires_review"])

    def test_kotlin_failure(self):
        result = module.diagnose("e: file:///MainActivity.kt: Unresolved reference: x")
        self.assertEqual(result["category"], "kotlin-compile")

    def test_unknown_stays_failed(self):
        result = module.diagnose("Runner received shutdown signal")
        self.assertEqual(result["category"], "unknown")
        self.assertEqual(result["status"], "failed")

    def test_success_requires_explicit_signal(self):
        result = module.diagnose("BUILD SUCCESSFUL", success=True)
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["requires_review"])

    def test_empty_log_stays_failed_despite_success_signal(self):
        self.assertEqual(module.diagnose(" \n", success=True)["status"], "failed")

    def test_emulator_failure_classes_are_classified_separately(self):
        for line, category in (
            ("KVM unavailable on this runner", "android-emulator-host"),
            ("adb: device offline", "android-adb-transport"),
            ("NIGHT CALENDAR QA: install failed (exit 1)", "android-apk-install"),
            ("INSTRUMENTATION_RESULT: calendar_smoke=failed synthetic-event-display", "android-ui-smoke"),
        ):
            with self.subTest(category=category):
                result = module.diagnose(line)
                self.assertEqual(result["category"], category)
                self.assertEqual(result["status"], "failed")
                self.assertTrue(result["requires_review"])

    def test_cli_preserves_utf8_evidence_under_ascii_locale(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "input.log"
            output = Path(directory) / "result.json"
            log.write_text("e: file:///MainActivity.kt: Unresolved reference: 祝日\n", encoding="utf-8")
            subprocess.run([sys.executable, spec.origin, "--log", str(log), "--out", str(output)], check=True,
                           env={**os.environ, "LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"},
                           capture_output=True)
            self.assertIn("祝日", json.loads(output.read_text(encoding="utf-8"))["evidence"][0])


if __name__ == "__main__":
    unittest.main()
