#!/usr/bin/env python3
"""Classify failing NIGHT CALENDAR CI stages; never infer success from logs."""
import argparse
import json
import re
from pathlib import Path

RULES = (
    ("kotlin-compile", r"Compilation error|:compile.*Kotlin FAILED|e: file://|Unresolved reference"),
    ("android-resources", r"Android resource linking failed|:process.*Resources FAILED|AAPT: error"),
    ("unit-tests", r"There were failing tests|:test.*UnitTest FAILED|AssertionError"),
    ("gradle-dependencies", r"Could not resolve|Could not find .*gradle|Plugin .* was not found"),
)
STAGES = ("sdk", "gradle-setup", "diagnostic-tests", "build", "apk-upload")


def diagnose(log: str, success: bool = False, stage: str = "build") -> dict:
    if success:
        return {"status": "passed", "category": "none", "stage": "complete", "evidence": [], "requires_review": False}
    if stage not in STAGES:
        return {"status": "failed", "category": "unknown", "stage": "unknown", "evidence": [], "requires_review": True}
    category = {"sdk": "android-sdk", "gradle-setup": "gradle-dependencies",
                "diagnostic-tests": "diagnostic-tests", "apk-upload": "artifact-upload"}.get(stage, "unknown")
    lines = log.splitlines()
    if stage == "sdk":
        # Require a genuine error marker: an earlier successful sdkmanager invocation
        # must never be mistaken for the cause of a later build failure.
        matches = [x.strip()[:240] for x in lines if re.search(r"NIGHT_CORE_ERROR: sdkmanager|sdkmanager.*(missing|not found|command not found)", x, re.I)]
    elif stage == "build":
        matches = []
        for kind, pattern in RULES:
            matching = [x.strip()[:240] for x in lines if re.search(pattern, x, re.I)]
            if matching:
                category, matches = kind, matching
                break
    else:
        matches = []
    return {"status": "failed", "category": category, "stage": stage,
            "evidence": matches[:3], "requires_review": True}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--stage", choices=STAGES, default="build")
    p.add_argument("--success", action="store_true")
    args = p.parse_args()
    log_path = Path(args.log)
    log = log_path.read_text(errors="replace") if log_path.exists() else ""
    report = diagnose(log, args.success, args.stage)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NIGHT CORE CI: {report['status']} ({report['category']}, stage={report['stage']})")


if __name__ == "__main__":
    main()
