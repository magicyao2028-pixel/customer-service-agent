"""Synthetic conversation regressions; no customer reply or platform write."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent import CustomerServiceAgent
from .conversation import ConversationFlow
from .models import load_policies


def conversation_receipt_passed(receipt: dict[str, Any], turns: int) -> bool:
    expected = {
        "schema_version": "1.0", "triage_evaluation_count": turns + 1,
        "clarification_retriage_count": turns, "reply_retriage_performed": True,
        "clarification_limit_enforced": True, "customer_reply_requires_approval": True,
        "customer_reply_sent": False, "external_actions_executed": 0,
        "original_messages_retained": False,
    }
    return (isinstance(receipt, dict) and set(receipt) == set(expected)
            and all(type(receipt[key]) is type(value) and receipt[key] == value for key, value in expected.items()))


def conversation_report_passed(report: dict[str, Any], expected_cases: list[dict[str, Any]]) -> bool:
    if (report.get("source_data") != "synthetic"
            or report.get("raw_customer_messages_retained") is not False
            or report.get("customer_replies_sent") is not False
            or type(report.get("external_actions_executed")) is not int
            or report["external_actions_executed"] != 0):
        return False
    cases = report.get("cases")
    if (not isinstance(cases, list) or len(cases) != len(expected_cases)
            or type(report.get("total_cases")) is not int or report["total_cases"] != len(cases)
            or type(report.get("passed_cases")) is not int or report["passed_cases"] != len(cases)):
        return False
    indexed = {case["case_id"]: case for case in cases}
    if len(indexed) != len(cases) or set(indexed) != {case["case_id"] for case in expected_cases}:
        return False
    return all(
        indexed[case["case_id"]]["passed"] is True
        and indexed[case["case_id"]]["observed_state"] == case["expected_state"]
        and indexed[case["case_id"]]["observed_status"] == case["expected_status"]
        and indexed[case["case_id"]]["policy_id"] == case["expected_policy_id"]
        and conversation_receipt_passed(indexed[case["case_id"]]["receipt"], case["expected_turns"])
        for case in expected_cases
    )


def evaluate_conversation_guardrails(policies_path: Path, cases_path: Path) -> dict[str, Any]:
    fixture = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = fixture.get("cases")
    if fixture.get("source_data") != "synthetic" or not isinstance(cases, list) or not cases:
        raise ValueError("conversation regressions require explicit synthetic cases")
    policies = load_policies(policies_path)
    results = []
    seen = set()
    for case in cases:
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen:
            raise ValueError("conversation case IDs must be non-blank and unique")
        seen.add(case_id)
        flow = ConversationFlow(CustomerServiceAgent(policies, analysis_date=fixture["analysis_date"]))
        session = flow.start(case["ticket"])
        for reply in case["replies"]:
            flow.reply(session, reply["message"], reply.get("order_id"))
        output = session.to_dict()
        receipt = output["conversation_guardrail_receipt"]
        receipt_passed = conversation_receipt_passed(receipt, case["expected_turns"])
        result = output["result"] or {}
        passed = (receipt_passed and output["conversation_state"] == case["expected_state"]
                  and result.get("status") == case["expected_status"]
                  and (result.get("policy_citation") or {}).get("policy_id") == case["expected_policy_id"]
                  and session.clarification_turns == case["expected_turns"]
                  and result.get("human_handoff", {}).get("required") is True
                  and result.get("human_handoff", {}).get("customer_reply_requires_approval") is True
                  and output["privacy"]["original_messages_retained"] is False
                  and result.get("privacy", {}).get("original_message_retained") is False)
        results.append({"case_id": case_id, "passed": passed, "observed_state": output["conversation_state"],
                        "observed_status": result.get("status"), "policy_id": (result.get("policy_citation") or {}).get("policy_id"),
                        "receipt": receipt})
    return {"source_data": "synthetic", "total_cases": len(results),
            "passed_cases": sum(item["passed"] for item in results), "cases": results,
            "raw_customer_messages_retained": False, "customer_replies_sent": False,
            "external_actions_executed": 0}
