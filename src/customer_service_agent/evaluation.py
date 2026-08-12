from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent import CustomerServiceAgent
from .models import SupportTicket, load_policies


def evaluate_cases(policy_path: Path, case_path: Path) -> dict[str, Any]:
    try:
        cases = json.loads(case_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid evaluation JSON: {exc.msg}") from exc
    if not isinstance(cases, list) or not cases:
        raise ValueError("Evaluation cases must be a non-empty list")
    agent = CustomerServiceAgent(load_policies(policy_path), analysis_date="2026-08-12")
    results = []
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("case_id", "")).strip()
        if not case_id or case_id in seen:
            raise ValueError("Evaluation case IDs must be present and unique")
        seen.add(case_id)
        output = agent.handle(SupportTicket.from_mapping(case["ticket"]))
        checks = {
            "status": output["status"] == case["expected_status"],
            "category": output["classification"]["category"] == case["expected_category"],
            "handoff": output["human_handoff"]["required"] == case["expected_handoff"],
            "policy": (output["policy_citation"] or {}).get("policy_id") == case.get("expected_policy_id"),
        }
        results.append({
            "case_id": case_id,
            "passed": all(checks.values()),
            "checks": checks,
            "actual": {
                "status": output["status"],
                "category": output["classification"]["category"],
                "handoff": output["human_handoff"]["required"],
                "policy_id": (output["policy_citation"] or {}).get("policy_id"),
            },
        })
    return {
        "evaluation_version": "0.3",
        "method": "synthetic deterministic behavior checks; no production accuracy claim",
        "summary": {
            "total_cases": len(results),
            "passed_cases": sum(item["passed"] for item in results),
            "pass_rate": round(sum(item["passed"] for item in results) / len(results), 3),
        },
        "cases": results,
    }


def write_evaluation(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Customer Service Agent Evaluation",
        "",
        f"- Method: {report['method']}",
        f"- Result: **{report['summary']['passed_cases']}/{report['summary']['total_cases']} cases passed**",
        "",
        "| Case | Result | Status | Category | Handoff | Policy |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["cases"]:
        actual = item["actual"]
        rows.append(
            f"| {item['case_id']} | {'PASS' if item['passed'] else 'FAIL'} | {actual['status']} | "
            f"{actual['category']} | {actual['handoff']} | {actual['policy_id'] or 'none'} |"
        )
    rows.extend([
        "",
        "## Interpretation boundary",
        "",
        "These fixtures prove reproducible behavior for synthetic cases. They do not estimate production classification accuracy, service quality or customer outcomes.",
    ])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
