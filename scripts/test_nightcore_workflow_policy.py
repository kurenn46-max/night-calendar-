"""NIGHT CORE policy checks for the privileged failure-triage workflow.

These are source-level safety invariants, not proof of production authorization.
"""
import unittest
from pathlib import Path


WORKFLOW = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "nightcore-recovery.yml").read_text(encoding="utf-8")


class RecoveryWorkflowPolicyTests(unittest.TestCase):
    def test_only_main_push_failures_are_eligible(self):
        self.assertIn("github.event.workflow_run.conclusion == 'failure'", WORKFLOW)
        self.assertIn("github.event.workflow_run.event == 'push'", WORKFLOW)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", WORKFLOW)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", WORKFLOW)

    def test_workflow_uses_trusted_main_checkout(self):
        self.assertIn("ref: main", WORKFLOW)
        self.assertNotIn("pull_request_target:", WORKFLOW)
        self.assertNotIn("ref: ${{ github.event.workflow_run.head_sha }}", WORKFLOW)

    def test_privileges_are_bounded(self):
        self.assertIn("  actions: read", WORKFLOW)
        self.assertNotIn("  actions: write", WORKFLOW)
        self.assertIn("  pull-requests: write", WORKFLOW)
        self.assertIn("  contents: write", WORKFLOW)

    def test_review_gate_and_retry_guard_remain(self):
        self.assertIn("nightcore/sdk-fallback-", WORKFLOW)
        self.assertIn("Repair branch already exists", WORKFLOW)
        self.assertIn("gh pr create", WORKFLOW)
        self.assertNotIn("gh pr merge", WORKFLOW)
        self.assertNotIn("gh api repos/", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
