#!/usr/bin/env python3
"""NIGHT CORE: classify CI failures without transmitting private project data.

Reads local CI log only and produces a small JSON diagnostic report.
This does not call an AI model or auto-apply changes.
"""
import argparse
import json
import re
from pathlib import Path

RULES = (
    ("android-sdk", r"sdkmanager|SDK location not found|Failed to find Platform SDK|licenses? not accepted"),
    ("gradle-dependencies", r"Could not resolve|Could not find .*gradle|Plugin .* was not found"),
    ("kotlin-compile", r"Compilation error|:compile.*Kotlin FAILED|e: file://|Unresolved reference"),
    ("android-resources", r"Android resource linking failed|:process.*Resources FAILED|AAPT: error"),
    ("unit-tests", r"There were failing tests|:test.*UnitTest FAILED|AssertionError"),
    ("artifact-upload", r"no files were found|upload-artifact.*failed"),
)


def diagnose(log: str, success: bool = False) -> dict:
    if success:
        return {"status": "passed", "category": "none", "evidence": [], "requires_review": False}
    lines = log.splitlines()
    for category, pattern in RULES:
        matches = [line.strip()[:300] for line in lines if re.search(pattern, line, re.IGNORECASE)]
        if matches:
            return {"status": "failed", "category": category, "evidence": matches[:5], "requires_review": True}
    return {"status": "failed", "category": "unknown", "evidence": [x.strip()[:300] for x in lines[-5:]], "requires_review": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--success", action="store_true")
    args = parser.parse_args()
    log_path = Path(args.log)
    report = diagnose(log_path.read_text(errors="replace") if log_path.exists() else "", args.success)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NIGHT CORE CI: {report['status']} ({report['category']})")


if __name__ == "__main__":
    main()
