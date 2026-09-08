from __future__ import annotations

from datetime import date
from typing import Any


_OPEN_STATUSES = {"needs_revision", "excluded", "pending"}
_CLOSED_STATUSES = {"passed"}


def summarize_owner_queue_aging(
    owner_queue: dict[str, Any], history: dict[str, Any], *, as_of_date: str, stale_after_days: int = 14
) -> dict[str, Any]:
    """Expose sanitized queue age and closure state without sending or applying work."""
    if stale_after_days < 1:
        raise ValueError("stale_after_days must be at least 1")
    try:
        as_of = date.fromisoformat(as_of_date)
    except ValueError as exc:
        raise ValueError("as_of_date must be ISO format") from exc
    if not isinstance(owner_queue, dict) or owner_queue.get("decisions_applied") is not False or owner_queue.get("raw_customer_messages_retained") is not False:
        raise ValueError("owner queue must remain sanitized and non-writing")
    queue_items = owner_queue.get("items")
    history_entries = history.get("entries") if isinstance(history, dict) else None
    if not isinstance(queue_items, list) or not queue_items or not isinstance(history_entries, list) or not history_entries:
        raise ValueError("owner queue and review history entries are required")
    dates: dict[str, date] = {}
    for entry in history_entries:
        if not isinstance(entry, dict):
            raise ValueError("review history entries must be objects")
        feedback_id = str(entry.get("feedback_id", "")).strip()
        if not feedback_id or feedback_id in dates:
            raise ValueError("review history feedback IDs must be unique")
        try:
            dates[feedback_id] = date.fromisoformat(str(entry.get("recorded_on", "")))
        except ValueError as exc:
            raise ValueError("review history recorded_on must be ISO format") from exc

    items: list[dict[str, Any]] = []
    seen_queue_ids: set[str] = set()
    for queue_item in queue_items:
        if not isinstance(queue_item, dict):
            raise ValueError("owner queue items must be objects")
        feedback_id = str(queue_item.get("feedback_id", "")).strip()
        status = str(queue_item.get("status", "")).strip()
        if not feedback_id or feedback_id in seen_queue_ids:
            raise ValueError("owner queue feedback IDs must be unique")
        seen_queue_ids.add(feedback_id)
        if feedback_id not in dates or status not in _OPEN_STATUSES | _CLOSED_STATUSES:
            raise ValueError("owner queue item is not linked to valid review history")
        age_days = (as_of - dates[feedback_id]).days
        if age_days < 0:
            raise ValueError("review history cannot be future-dated")
        closure_state = "closed" if status in _CLOSED_STATUSES else "open"
        items.append({
            "feedback_id": feedback_id,
            "status": status,
            "closure_state": closure_state,
            "age_days": age_days,
            "stale": closure_state == "open" and age_days >= stale_after_days,
        })
    items.sort(key=lambda item: (-item["age_days"], item["feedback_id"]))
    return {
        "schema_version": "1.0",
        "as_of_date": as_of.isoformat(),
        "stale_after_days": stale_after_days,
        "item_count": len(items),
        "open_count": sum(item["closure_state"] == "open" for item in items),
        "closed_count": sum(item["closure_state"] == "closed" for item in items),
        "stale_count": sum(item["stale"] for item in items),
        "items": items,
        "decisions_applied": False,
        "replies_sent": 0,
        "raw_customer_messages_retained": False,
        "authority_boundary": "Queue aging exposes sanitized follow-up state only; it does not close tickets, change policy or send replies.",
    }


__all__ = ["summarize_owner_queue_aging"]
