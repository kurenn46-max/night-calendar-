import unittest
import importlib.util
from pathlib import Path

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
        result = module.diagnose("no tests run", success=True)
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["requires_review"])


if __name__ == "__main__":
    unittest.main()
