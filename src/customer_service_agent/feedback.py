from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .agent import CustomerServiceAgent
from .models import SupportTicket, load_policies
from .privacy import redact_sensitive_text


ALLOWED_PROVENANCE = {"synthetic_public_fixture"}
ALLOWED_DISPOSITIONS = {"accepted_for_replay", "pending", "rejected"}
EXPECTED_FIELDS = {"status", "category", "handoff", "policy_id"}


def load_feedback(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid feedback JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Feedback file must contain an object")
    batch_id = str(payload.get("batch_id", "")).strip()
    analysis_date = str(payload.get("analysis_date", "")).strip()
    records = payload.get("records")
    if not batch_id or not analysis_date or not isinstance(records, list) or not records:
        raise ValueError("Feedback requires batch_id, analysis_date and a non-empty records list")

    normalized = []
    seen: set[str] = set()
    for raw in records:
        if not isinstance(raw, dict):
            raise ValueError("Every feedback record must be an object")
        feedback_id = str(raw.get("feedback_id", "")).strip()
        if not feedback_id or feedback_id in seen:
            raise ValueError("Feedback IDs must be present and unique")
        seen.add(feedback_id)
        provenance = str(raw.get("provenance", "")).strip()
        disposition = str(raw.get("disposition", "")).strip()
        if provenance not in ALLOWED_PROVENANCE:
            raise ValueError(f"Unsupported feedback provenance: {provenance}")
        if disposition not in ALLOWED_DISPOSITIONS:
            raise ValueError(f"Unsupported feedback disposition: {disposition}")
        reviewer_alias = str(raw.get("reviewer_alias", "")).strip()
        issue_type = str(raw.get("issue_type", "")).strip()
        rationale = str(raw.get("rationale", "")).strip()
        recorded_at = str(raw.get("recorded_at", "")).strip()
        if not all((reviewer_alias, issue_type, rationale, recorded_at)):
            raise ValueError("Feedback reviewer, issue type, rationale and recorded_at must not be blank")
        try:
            date.fromisoformat(recorded_at)
        except ValueError as exc:
            raise ValueError("Feedback recorded_at must use YYYY-MM-DD") from exc

        ticket = raw.get("ticket")
        expected = raw.get("expected")
        if disposition == "accepted_for_replay" and not isinstance(ticket, dict):
            raise ValueError("Accepted feedback requires a ticket")
        if disposition == "accepted_for_replay" and (
            not isinstance(expected, dict) or set(expected) != EXPECTED_FIELDS
        ):
            raise ValueError("Accepted feedback must define status, category, handoff and policy_id")
        if disposition == "accepted_for_replay":
            _validate_expected(expected)

        sanitized_ticket = None
        redactions: list[str] = []
        if isinstance(ticket, dict):
            sanitized_message, redactions = redact_sensitive_text(str(ticket.get("customer_message", "")))
            sanitized_ticket = SupportTicket.from_mapping({**ticket, "customer_message": sanitized_message})
        normalized.append({
            "feedback_id": feedback_id,
            "provenance": provenance,
            "reviewer_alias": reviewer_alias,
            "recorded_at": recorded_at,
            "issue_type": issue_type,
            "disposition": disposition,
            "rationale": rationale,
            "ticket": sanitized_ticket,
            "expected": expected,
            "privacy": {"redactions_applied": redactions, "original_message_retained": False},
        })
    return {"batch_id": batch_id, "analysis_date": analysis_date, "records": normalized}


def replay_feedback(policy_path: Path, feedback_path: Path) -> dict[str, Any]:
    batch = load_feedback(feedback_path)
    agent = CustomerServiceAgent(load_policies(policy_path), analysis_date=batch["analysis_date"])
    replayed = []
    excluded = []
    for record in batch["records"]:
        if record["disposition"] != "accepted_for_replay":
            excluded.append({
                "feedback_id": record["feedback_id"],
                "disposition": record["disposition"],
                "reason": "feedback does not alter policy or enter replay until explicitly accepted",
            })
            continue
        ticket = record["ticket"]
        assert isinstance(ticket, SupportTicket)
        output = agent.handle(ticket)
        expected = record["expected"]
        actual = {
            "status": output["status"],
            "category": output["classification"]["category"],
            "handoff": output["human_handoff"]["required"],
            "policy_id": (output["policy_citation"] or {}).get("policy_id"),
        }
        checks = {name: actual[name] == expected[name] for name in EXPECTED_FIELDS}
        checks.update({
            "original_message_not_retained": output["privacy"]["original_message_retained"] is False,
            "customer_reply_requires_approval": output["human_handoff"]["customer_reply_requires_approval"] is True,
            "blocked_policy_requires_handoff": _blocked_policy_guard(output),
        })
        ticket_payload = {
            "ticket_id": ticket.ticket_id,
            "channel": ticket.channel,
            "customer_message": ticket.customer_message,
            "order_id": ticket.order_id,
        }
        fingerprint = hashlib.sha256(
            json.dumps(ticket_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        replayed.append({
            "feedback_id": record["feedback_id"],
            "provenance": record["provenance"],
            "reviewer_alias": record["reviewer_alias"],
            "issue_type": record["issue_type"],
            "sanitized_ticket_fingerprint": fingerprint,
            "privacy": record["privacy"],
            "expected": expected,
            "actual": actual,
            "checks": dict(sorted(checks.items())),
            "passed": all(checks.values()),
        })
    return {
        "replay_version": "0.4",
        "batch_id": batch["batch_id"],
        "analysis_date": batch["analysis_date"],
        "method": "deterministic replay of explicitly accepted reviewer feedback; no model judge",
        "summary": {
            "total_feedback": len(batch["records"]),
            "replayed": len(replayed),
            "passed": sum(item["passed"] for item in replayed),
            "failed": sum(not item["passed"] for item in replayed),
            "excluded": len(excluded),
        },
        "replayed": replayed,
        "excluded": excluded,
        "governance": [
            "Feedback is evidence for review and replay; it does not edit policy or production behavior automatically.",
            "Only accepted_for_replay records execute; pending and rejected records remain excluded.",
            "Public records are synthetic and do not represent real customer feedback.",
        ],
    }


def write_feedback_replay(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Reviewer Feedback Replay",
        "",
        f"- Batch: `{report['batch_id']}`",
        f"- Analysis date: `{report['analysis_date']}`",
        f"- Method: {report['method']}",
        f"- Result: **{report['summary']['passed']}/{report['summary']['replayed']} replay cases passed**",
        "",
        "| Feedback | Provenance | Issue | Result | Status | Handoff | Policy |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["replayed"]:
        actual = item["actual"]
        rows.append(
            f"| {item['feedback_id']} | {item['provenance']} | {item['issue_type']} | "
            f"{'PASS' if item['passed'] else 'FAIL'} | {actual['status']} | {actual['handoff']} | "
            f"{actual['policy_id'] or 'none'} |"
        )
    rows.extend(["", "## Excluded feedback", ""])
    rows.extend(
        f"- `{item['feedback_id']}` ({item['disposition']}): {item['reason']}"
        for item in report["excluded"]
    )
    rows.extend(["", "## Governance boundary", ""])
    rows.extend(f"- {item}" for item in report["governance"])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _blocked_policy_guard(output: dict[str, Any]) -> bool:
    if output["status"] not in {"no_policy", "policy_conflict", "policy_stale"}:
        return True
    return output["policy_citation"] is None and output["human_handoff"]["required"] is True


def _validate_expected(expected: dict[str, Any]) -> None:
    if not isinstance(expected["status"], str) or not expected["status"].strip():
        raise ValueError("expected.status must be a non-empty string")
    if not isinstance(expected["category"], str) or not expected["category"].strip():
        raise ValueError("expected.category must be a non-empty string")
    if not isinstance(expected["handoff"], bool):
        raise ValueError("expected.handoff must be a boolean")
    policy_id = expected["policy_id"]
    if policy_id is not None and (not isinstance(policy_id, str) or not policy_id.strip()):
        raise ValueError("expected.policy_id must be null or a non-empty string")
