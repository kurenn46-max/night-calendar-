import unittest
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ci_diagnose", Path(__file__).parent / "ci_diagnose.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DiagnoseTests(unittest.TestCase):
    def test_sdk_failure(self):
        result = module.diagnose('NIGHT_CORE_ERROR: sdkmanager executable not found', stage="sdk")
        self.assertEqual(result["category"], "android-sdk")
        self.assertTrue(result["requires_review"])
        self.assertTrue(result["evidence"])

    def test_kotlin_failure(self):
        log = 'sdkmanager installed\ne: file:///MainActivity.kt: Unresolved reference: x'
        result = module.diagnose(log, stage="build")
        self.assertEqual(result["category"], "kotlin-compile")
        self.assertNotIn('sdkmanager installed', result['evidence'])

    def test_unknown_stays_failed(self):
        result = module.diagnose("Runner received shutdown signal", stage="build")
        self.assertEqual(result["category"], "unknown")
        self.assertEqual(result["status"], "failed")

    def test_artifact_upload_failure(self):
        result = module.diagnose('', stage="apk-upload")
        self.assertEqual(result['category'], 'artifact-upload')

    def test_failure_of_sdk_when_no_text_does_not_generate_repair_evidence(self):
        result = module.diagnose('sdkmanager installed before failure', stage='sdk')
        self.assertEqual(result['category'], 'android-sdk')
        self.assertEqual(result['evidence'], [])

    def test_success_requires_explicit_signal(self):
        result = module.diagnose("no tests run", success=True)
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["requires_review"])


if __name__ == "__main__":
    unittest.main()
