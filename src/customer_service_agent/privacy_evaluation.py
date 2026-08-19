from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .privacy import redact_sensitive_text


SUPPORTED_TYPES = {"email", "payment_card", "password", "phone", "access_token"}


def evaluate_redaction_cases(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError("Redaction fixture must contain cases")
    seen: set[str] = set()
    results = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Every redaction case must be an object")
        case_id = str(case.get("case_id", "")).strip()
        message = case.get("message")
        expected = case.get("expected_types")
        sensitive_values = case.get("sensitive_values")
        if not case_id or case_id in seen:
            raise ValueError("Redaction case IDs must be present and unique")
        seen.add(case_id)
        if not isinstance(message, str) or not isinstance(expected, list) or not isinstance(sensitive_values, list):
            raise ValueError("Redaction message, expected_types and sensitive_values have invalid types")
        if not all(isinstance(item, str) and item for item in expected + sensitive_values):
            raise ValueError("Expected types and sensitive values must be non-blank strings")
        if set(expected).difference(SUPPORTED_TYPES):
            raise ValueError("Fixture references an unsupported detection type")
        redacted, detected = redact_sensitive_text(message)
        originals_removed = all(value not in redacted for value in sensitive_values)
        passed = sorted(detected) == sorted(expected) and originals_removed
        results.append({
            "case_id": case_id,
            "expected_types": sorted(expected),
            "detected_types": sorted(detected),
            "original_sensitive_values_retained": not originals_removed,
            "passed": passed,
        })
    return {
        "evaluation_version": "0.5",
        "source_data": "synthetic",
        "summary": {
            "total": len(results),
            "passed": sum(item["passed"] for item in results),
            "failed": sum(not item["passed"] for item in results),
            "supported_detection_types": sorted(SUPPORTED_TYPES),
        },
        "cases": results,
        "boundaries": [
            "Reports contain case IDs and detection labels, never original message text or sensitive values.",
            "This exact-pattern fixture is regression evidence, not recall, precision or full DLP coverage.",
        ],
    }


def write_redaction_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Redaction Quality Fixture", "",
        f"- Result: **{report['summary']['passed']}/{report['summary']['total']} cases passed**",
        "- Source: synthetic public fixture", "",
        "| Case | Expected | Detected | Original retained | Result |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["cases"]:
        rows.append(
            f"| {item['case_id']} | {', '.join(item['expected_types']) or 'none'} | "
            f"{', '.join(item['detected_types']) or 'none'} | "
            f"{'yes' if item['original_sensitive_values_retained'] else 'no'} | "
            f"{'PASS' if item['passed'] else 'FAIL'} |"
        )
    rows.extend(["", "## Boundary", "", *[f"- {item}" for item in report["boundaries"]]])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
