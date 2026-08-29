from __future__ import annotations

from typing import Any


def build_review_report_export(replay_report: dict[str, Any]) -> dict[str, Any]:
    """Summarize replay outcomes for a human queue without retaining ticket text."""
    summary = replay_report.get("summary")
    if not isinstance(summary, dict) or not isinstance(replay_report.get("replayed"), list) or not isinstance(replay_report.get("excluded"), list):
        raise ValueError("Replay report is incomplete")
    records: list[dict[str, Any]] = []
    for item in replay_report["replayed"]:
        if not isinstance(item, dict) or not str(item.get("feedback_id", "")).strip():
            raise ValueError("Replayed feedback must contain feedback_id")
        checks = item.get("checks")
        if not isinstance(checks, dict):
            raise ValueError("Replayed feedback must contain checks")
        failed_checks = sorted(name for name, passed in checks.items() if passed is not True)
        records.append(
            {
                "feedback_id": item["feedback_id"],
                "record_type": "replayed",
                "issue_type": item.get("issue_type"),
                "reviewer_alias": item.get("reviewer_alias"),
                "status": "passed" if item.get("passed") is True else "needs_revision",
                "failed_checks": failed_checks,
                "recommended_action": "retain_regression_coverage" if not failed_checks else "investigate_failed_checks",
                "sanitized_ticket_fingerprint": item.get("sanitized_ticket_fingerprint"),
            }
        )
    for item in replay_report["excluded"]:
        if not isinstance(item, dict) or not str(item.get("feedback_id", "")).strip():
            raise ValueError("Excluded feedback must contain feedback_id")
        records.append(
            {
                "feedback_id": item["feedback_id"],
                "record_type": "excluded",
                "issue_type": None,
                "reviewer_alias": None,
                "status": "excluded",
                "failed_checks": [],
                "recommended_action": "await_explicit_acceptance",
                "exclusion_reason": item.get("reason", ""),
            }
        )
    records.sort(key=lambda row: row["feedback_id"])
    return {
        "schema_version": "1.0",
        "review_export_version": "0.7",
        "batch_id": replay_report.get("batch_id"),
        "analysis_date": replay_report.get("analysis_date"),
        "records": records,
        "record_count": len(records),
        "decisions_applied": False,
        "external_actions_executed": 0,
        "raw_customer_messages_retained": False,
        "authority_boundary": "This export organizes human follow-up only; it does not change policy, send replies or approve automated decisions.",
    }
