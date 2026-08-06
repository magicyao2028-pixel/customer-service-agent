from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUPPORTED_CHANNELS = {"chat", "email", "marketplace"}


@dataclass(frozen=True)
class SupportTicket:
    ticket_id: str
    channel: str
    customer_message: str
    order_id: str | None = None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "SupportTicket":
        ticket_id = str(value.get("ticket_id", "")).strip()
        channel = str(value.get("channel", "")).strip().lower()
        message = str(value.get("customer_message", "")).strip()
        order_id = str(value.get("order_id", "")).strip() or None
        if not ticket_id or not message:
            raise ValueError("ticket_id and customer_message must not be blank")
        if channel not in SUPPORTED_CHANNELS:
            raise ValueError(f"channel must be one of: {', '.join(sorted(SUPPORTED_CHANNELS))}")
        return cls(ticket_id, channel, message, order_id)


@dataclass(frozen=True)
class SupportPolicy:
    policy_id: str
    category: str
    title: str
    updated_at: str
    priority: str
    sla_minutes: int
    owner: str
    keywords: tuple[str, ...]
    escalation_keywords: tuple[str, ...]
    required_evidence: tuple[str, ...]
    resolution_steps: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "SupportPolicy":
        required = {
            "policy_id", "category", "title", "updated_at", "priority", "sla_minutes",
            "owner", "keywords", "escalation_keywords", "required_evidence", "resolution_steps",
        }
        missing = sorted(required.difference(value))
        if missing:
            raise ValueError(f"Missing policy fields: {', '.join(missing)}")
        priority = str(value["priority"]).strip().lower()
        if priority not in {"low", "medium", "high", "critical"}:
            raise ValueError("policy priority must be low, medium, high or critical")
        sla_minutes = int(value["sla_minutes"])
        if sla_minutes < 1:
            raise ValueError("sla_minutes must be at least 1")
        policy = cls(
            policy_id=str(value["policy_id"]).strip(),
            category=str(value["category"]).strip(),
            title=str(value["title"]).strip(),
            updated_at=str(value["updated_at"]).strip(),
            priority=priority,
            sla_minutes=sla_minutes,
            owner=str(value["owner"]).strip(),
            keywords=_strings(value["keywords"], "keywords"),
            escalation_keywords=_strings(value["escalation_keywords"], "escalation_keywords", allow_empty=True),
            required_evidence=_strings(value["required_evidence"], "required_evidence"),
            resolution_steps=_strings(value["resolution_steps"], "resolution_steps"),
        )
        if not all((policy.policy_id, policy.category, policy.title, policy.updated_at, policy.owner)):
            raise ValueError("Policy text fields must not be blank")
        return policy


def load_ticket(path: Path) -> SupportTicket:
    payload = _load_object(path, "ticket")
    return SupportTicket.from_mapping(payload)


def load_policies(path: Path) -> list[SupportPolicy]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid policy JSON: {exc.msg}") from exc
    if not isinstance(payload, list) or not payload:
        raise ValueError("Policy file must contain a non-empty list")
    policies = [SupportPolicy.from_mapping(item) for item in payload]
    ids = [item.policy_id for item in policies]
    categories = [item.category for item in policies]
    if len(ids) != len(set(ids)) or len(categories) != len(set(categories)):
        raise ValueError("Policy IDs and categories must be unique")
    return policies


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid {label} JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label.title()} file must contain a JSON object")
    return payload


def _strings(value: Any, field: str, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    cleaned = tuple(item.strip() for item in value if item.strip())
    if not cleaned and not allow_empty:
        raise ValueError(f"{field} must not be empty")
    return cleaned
