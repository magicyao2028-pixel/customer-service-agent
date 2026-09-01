from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any


def summarize_review_history(review_export: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize a public-safe owner queue without retaining ticket content or applying decisions."""
    if not isinstance(history, list) or not history:
        raise ValueError("review history must be a non-empty list")
    records = review_export.get("records")
    if not isinstance(records, list):
        raise ValueError("review export records are required")
    allowed = {str(item.get("feedback_id")) for item in records}
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    previous: date | None = None
    for item in history:
        if not isinstance(item, dict):
            raise ValueError("review history records must be objects")
        feedback_id = item.get("feedback_id")
        if not isinstance(feedback_id, str) or feedback_id not in allowed or feedback_id in seen:
            raise ValueError("review history feedback_id must be unique and reference the export")
        status = item.get("status")
        if status not in {"passed", "needs_revision", "excluded", "pending"}:
            raise ValueError("review history status is unsupported")
        recorded_on = item.get("recorded_on")
        try:
            parsed = date.fromisoformat(str(recorded_on))
        except ValueError as exc:
            raise ValueError("review history recorded_on must be ISO-8601") from exc
        if previous and parsed < previous:
            raise ValueError("review history must be chronological")
        if not isinstance(item.get("applied"), bool) or item["applied"]:
            raise ValueError("review history applied must remain false")
        seen.add(feedback_id)
        previous = parsed
        normalized.append({"feedback_id": feedback_id, "status": status, "recorded_on": str(recorded_on), "applied": False})
    return {
        "history_version": "0.9",
        "entry_count": len(normalized),
        "status_counts": dict(sorted(Counter(item["status"] for item in normalized).items())),
        "latest_recorded_on": normalized[-1]["recorded_on"],
        "entries": normalized,
        "decisions_applied": False,
        "raw_customer_messages_retained": False,
        "external_actions_executed": 0,
        "boundary": "History is descriptive reviewer evidence only; it does not change policy, send replies or retain ticket text.",
    }


__all__ = ["summarize_review_history"]
