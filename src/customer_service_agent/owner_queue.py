from __future__ import annotations

from typing import Any


_PRIORITY = {"needs_revision": "critical", "excluded": "high", "pending": "high", "passed": "normal"}
_ACTION = {
    "needs_revision": "investigate_failed_checks",
    "excluded": "await_explicit_acceptance",
    "pending": "await_review_decision",
    "passed": "retain_regression_coverage",
}


def build_owner_followup_queue(review_export: dict[str, Any], history: dict[str, Any]) -> dict[str, Any]:
    """Build a bounded owner queue from sanitized review history only."""
    if not isinstance(review_export, dict) or review_export.get("decisions_applied") is not False or review_export.get("raw_customer_messages_retained") is not False:
        raise ValueError("Review export must remain non-writing and sanitized")
    entries = history.get("entries") if isinstance(history, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ValueError("Review history entries are required")
    allowed = {str(item.get("feedback_id")) for item in review_export.get("records", [])}
    if not allowed:
        raise ValueError("Review export records are required")
    queue = []
    for entry in entries:
        feedback_id = str(entry.get("feedback_id", "")).strip()
        status = entry.get("status")
        if feedback_id not in allowed or status not in _PRIORITY:
            raise ValueError("Owner queue entry is not linked to the review export")
        queue.append({
            "feedback_id": feedback_id,
            "status": status,
            "priority": _PRIORITY[status],
            "next_action": _ACTION[status],
            "applied": False,
        })
    order = {"critical": 0, "high": 1, "normal": 2}
    queue.sort(key=lambda item: (order[item["priority"]], item["feedback_id"]))
    return {
        "schema_version": "1.0",
        "items": queue,
        "item_count": len(queue),
        "decisions_applied": False,
        "external_actions_executed": 0,
        "raw_customer_messages_retained": False,
        "authority_boundary": "This owner queue organizes sanitized follow-up only; it does not change policy, send replies or approve automated decisions.",
    }
