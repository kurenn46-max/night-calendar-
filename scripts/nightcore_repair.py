#!/usr/bin/env python3
"""Safe deterministic NIGHT CORE repair proposals for known CI failures.

No LLM, shell execution, or remote calls. Edits only a fixed workflow snippet
on a review branch. Unknown failures remain unresolved for human/AI review.
"""
import argparse
import json
from pathlib import Path

KNOWN_CATEGORIES = {
    "android-sdk", "gradle-dependencies", "kotlin-compile",
    "android-resources", "unit-tests", "artifact-upload", "unknown",
}

OLD_SDK = '''            test -x "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" || { echo "NIGHT_CORE_ERROR: sdkmanager missing"; exit 1; }
            yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses > /dev/null || true
            "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "platforms;android-35" "build-tools;35.0.0"'''
NEW_SDK = '''            SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
            if [ ! -x "$SDKMANAGER" ]; then
              SDKMANAGER="$(command -v sdkmanager || true)"
            fi
            if [ -z "$SDKMANAGER" ] || [ ! -x "$SDKMANAGER" ]; then
              echo "NIGHT_CORE_ERROR: sdkmanager executable not found"
              exit 1
            fi
            yes | "$SDKMANAGER" --licenses > /dev/null || true
            "$SDKMANAGER" "platforms;android-35" "build-tools;35.0.0"'''


def plan_repair(diagnosis: dict, workflow: str) -> tuple[str | None, str]:
    """Return (patched workflow or None, machine-readable reason)."""
    if diagnosis.get("status") != "failed":
        return None, "not-failed"
    category = diagnosis.get("category")
    if category not in KNOWN_CATEGORIES:
        return None, "invalid-category"
    if category != "android-sdk":
        return None, "no-verified-playbook"
    if diagnosis.get("stage") != "sdk":
        return None, "wrong-failing-stage"
    evidence = diagnosis.get("evidence", [])
    if not isinstance(evidence, list) or not any(
        isinstance(line, str) and "sdkmanager" in line.lower() for line in evidence
    ):
        return None, "insufficient-evidence"
    if workflow.count(OLD_SDK) != 1:
        return None, "precondition-mismatch"
    return workflow.replace(OLD_SDK, NEW_SDK, 1), "sdkmanager-path-fallback"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnosis", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    diagnosis_path = Path(args.diagnosis)
    diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8")) if diagnosis_path.exists() else {
        "status": "failed", "category": "unknown", "evidence": []
    }
    workflow_path = Path(args.workflow)
    original = workflow_path.read_text(encoding="utf-8")
    replacement, rule = plan_repair(diagnosis, original)
    if replacement is not None:
        workflow_path.write_text(replacement, encoding="utf-8")
    result = {"proposed": replacement is not None, "rule": rule,
              "category": diagnosis.get("category") if diagnosis.get("category") in KNOWN_CATEGORIES else "unknown"}
    Path(args.result).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NIGHT CORE: {rule}; proposed={result['proposed']}")


if __name__ == "__main__":
    main()
