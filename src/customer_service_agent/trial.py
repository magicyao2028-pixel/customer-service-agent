from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .evaluation import evaluate_cases
from .feedback import replay_feedback
from .review_export import build_review_report_export
from .review_history import summarize_review_history
from .privacy_evaluation import evaluate_redaction_cases
from .owner_queue import build_owner_followup_queue
from .queue_aging import summarize_owner_queue_aging
from .conversation_guardrails import evaluate_conversation_guardrails, conversation_report_passed


COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def validate_evidence_index(root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("Evidence index must contain claims")
    root = root.resolve()
    seen: set[str] = set()
    checked = []
    for claim in claims:
        if not isinstance(claim, dict) or not str(claim.get("claim_id", "")).strip() or not str(claim.get("statement", "")).strip():
            raise ValueError("Every evidence claim needs claim_id and statement")
        claim_id = claim["claim_id"]
        if claim_id in seen:
            raise ValueError(f"Duplicate evidence claim_id: {claim_id}")
        seen.add(claim_id)
        artifacts = claim.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError(f"{claim_id} must link artifacts")
        paths = []
        for artifact in artifacts:
            relative = str(artifact.get("path", "")) if isinstance(artifact, dict) else ""
            target = (root / relative).resolve()
            if not isinstance(artifact, dict) or not str(artifact.get("kind", "")).strip() or not relative or not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Missing, unsafe or untyped evidence path: {relative}")
            paths.append(relative)
        checked.append({"claim_id": claim_id, "artifact_paths": paths, "passed": True})
    return checked


def validate_external_intake(payload: dict[str, Any]) -> list[dict[str, Any]]:
    date.fromisoformat(str(payload.get("reviewed_on", "")))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("External intake must contain candidates")
    checks = []
    for item in candidates:
        required = {"repository", "version", "commit", "license", "decision", "code_adopted", "reason"}
        if not isinstance(item, dict) or required.difference(item):
            raise ValueError("External candidate metadata is incomplete")
        if not str(item["repository"]).startswith("https://github.com/") or not COMMIT_PATTERN.fullmatch(str(item["commit"])):
            raise ValueError("External repository or full commit SHA is invalid")
        if item["decision"] not in {"adopted", "rejected"} or not isinstance(item["code_adopted"], bool) or (item["decision"] == "adopted") != item["code_adopted"]:
            raise ValueError("External decision is invalid or inconsistent")
        checks.append({"repository": item["repository"], "decision": item["decision"], "passed": True})
    return checks


def validate_feedback(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    required = {"feedback_id", "source_type", "recorded_on", "classification", "decision", "summary", "acceptance_test", "implementation", "release_result"}
    if required.difference(payload) or any(not str(payload[key]).strip() for key in required):
        raise ValueError("Feedback record is incomplete")
    date.fromisoformat(str(payload["recorded_on"]))
    if payload["source_type"] not in {"real", "synthetic"} or payload["classification"] not in {"defect", "requirement", "usability", "performance", "safety", "documentation"}:
        raise ValueError("Feedback source_type or classification is unsupported")
    if payload["decision"] != "accepted":
        raise ValueError("Trial feedback case must be accepted")
    for key in ("acceptance_test", "implementation"):
        target = (root.resolve() / str(payload[key])).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError(f"Feedback {key} path is missing or unsafe")
    return {"feedback_id": payload["feedback_id"], "source_type": payload["source_type"], "passed": True}


def run_trial(root: Path) -> dict[str, Any]:
    root = root.resolve()
    privacy = evaluate_redaction_cases(root / "data/redaction_quality_cases.json")
    behavior = evaluate_cases(root / "data/support_policies.json", root / "data/evaluation_cases.json")
    feedback_replay = replay_feedback(root / "data/support_policies.json", root / "data/reviewer_feedback.json")
    review_export = build_review_report_export(feedback_replay)
    review_history = summarize_review_history(
        review_export,
        json.loads((root / "data/review_history.json").read_text(encoding="utf-8")),
    )
    owner_queue = build_owner_followup_queue(review_export, review_history)
    queue_aging = summarize_owner_queue_aging(owner_queue, review_history, as_of_date="2026-09-08")
    conversations = evaluate_conversation_guardrails(root / "data/support_policies.json", root / "data/conversation_guardrail_cases.json")
    conversation_checks = conversation_report_passed(conversations, load_json_object(root / "data/conversation_guardrail_cases.json")["cases"])
    evidence = validate_evidence_index(root, load_json_object(root / "evidence/evidence_index.json"))
    external = validate_external_intake(load_json_object(root / "evidence/external_intake.json"))
    feedback = validate_feedback(root, load_json_object(root / "evidence/feedback_case.json"))
    core_passed = (
        privacy["summary"]["failed"] == 0
        and behavior["summary"]["passed_cases"] == 5
        and behavior["mode_comparison"]["local_vector"]["passed_cases"] == 5
        and feedback_replay["summary"]["passed"] == 2
        and review_export["record_count"] == 3
        and review_export["decisions_applied"] is False
        and review_export["raw_customer_messages_retained"] is False
        and review_history["entry_count"] == 3
        and review_history["decisions_applied"] is False
        and review_history["raw_customer_messages_retained"] is False
        and owner_queue["item_count"] == 3
        and owner_queue["decisions_applied"] is False
        and owner_queue["raw_customer_messages_retained"] is False
        and type(owner_queue["external_actions_executed"]) is int and owner_queue["external_actions_executed"] == 0
        and type(review_export["external_actions_executed"]) is int and review_export["external_actions_executed"] == 0
        and type(review_history["external_actions_executed"]) is int and review_history["external_actions_executed"] == 0
        and queue_aging["open_count"] == 1
        and queue_aging["closed_count"] == 2
        and queue_aging["stale_count"] == 1
        and queue_aging["decisions_applied"] is False
        and queue_aging["raw_customer_messages_retained"] is False
        and type(queue_aging["replies_sent"]) is int and queue_aging["replies_sent"] == 0
        and all(item["applied"] is False for item in owner_queue["items"])
        and all(item["applied"] is False for item in review_history["entries"])
        and conversation_checks
        and conversations["total_cases"] == 4 and conversations["passed_cases"] == 4
        and all(case["passed"] is True for case in conversations["cases"])
        and conversations["raw_customer_messages_retained"] is False
        and conversations["customer_replies_sent"] is False
        and type(conversations["external_actions_executed"]) is int and conversations["external_actions_executed"] == 0
    )
    return {
        "schema_version": "1.0", "trial_id": "TRIAL-SERVICE-001", "source_data": "synthetic",
        "overall_passed": core_passed and feedback["passed"] and all(item["passed"] for item in evidence + external),
        "core_flow": {"passed": core_passed, "redaction_cases": privacy["summary"], "behavior_cases_passed": behavior["summary"]["passed_cases"], "local_vector_behavior_cases_passed": behavior["mode_comparison"]["local_vector"]["passed_cases"], "feedback_replay_passed": feedback_replay["summary"]["passed"], "external_actions_executed": sum((review_export["external_actions_executed"], review_history["external_actions_executed"], owner_queue["external_actions_executed"], queue_aging["replies_sent"], conversations["external_actions_executed"]))},
        "feedback_regression": feedback, "feedback_review_export": review_export, "review_history": review_history, "owner_followup_queue": owner_queue, "owner_queue_aging": queue_aging, "external_intake": external, "evidence_index": evidence,
        "conversation_guardrails": conversations,
        "boundaries": load_json_object(root / "evidence/evidence_index.json")["boundaries"],
    }


def write_trial_report(root: Path, json_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = run_trial(root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text("\n".join([
        "# Customer Service Trial Readiness", "", "> Synthetic offline verification; no ticketing write or customer reply is executed.", "",
        f"- Overall: **{'PASS' if report['overall_passed'] else 'FAIL'}**",
        f"- Redaction cases: {report['core_flow']['redaction_cases']['passed']}/{report['core_flow']['redaction_cases']['total']}",
        f"- Behavior cases: {report['core_flow']['behavior_cases_passed']}/5",
        f"- Local-vector behavior cases: {report['core_flow']['local_vector_behavior_cases_passed']}/5",
        f"- Feedback replay: {report['core_flow']['feedback_replay_passed']}/2",
        f"- Clarification-retriage guardrails: {report['conversation_guardrails']['passed_cases']}/{report['conversation_guardrails']['total_cases']} (no replies sent)",
        f"- Owner queue aging: {report['owner_queue_aging']['open_count']} open, {report['owner_queue_aging']['closed_count']} closed, {report['owner_queue_aging']['stale_count']} stale", "", "## Pilot boundary", "",
        *[f"- {item}" for item in report["boundaries"]], "",
    ]), encoding="utf-8")
    return report
