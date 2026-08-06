from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .models import SupportPolicy, SupportTicket
from .privacy import redact_sensitive_text


@dataclass
class AgentTrace:
    steps: list[dict[str, str]] = field(default_factory=list)

    def record(self, tool: str, purpose: str, status: str = "completed") -> None:
        self.steps.append({"tool": tool, "purpose": purpose, "status": status})


class CustomerServiceAgent:
    """Runs deterministic support triage with cited policies and human handoff."""

    def __init__(self, policies: Iterable[SupportPolicy]) -> None:
        self.policies = list(policies)
        if not self.policies:
            raise ValueError("At least one support policy is required")

    def handle(self, ticket: SupportTicket | dict[str, Any]) -> dict[str, Any]:
        item = ticket if isinstance(ticket, SupportTicket) else SupportTicket.from_mapping(ticket)
        trace = AgentTrace()
        trace.record("validate_ticket", "Validate ticket identity, channel and message.")

        sanitized_message, redactions = redact_sensitive_text(item.customer_message)
        trace.record(
            "redact_sensitive_data",
            "Remove email, payment-card and password text before policy matching.",
            "redacted" if redactions else "completed",
        )

        policy, matched_keywords = self._match_policy(sanitized_message)
        trace.record("classify_issue", "Match the sanitized ticket to explicit policy keywords.")
        if policy is None:
            trace.record("evidence_gate", "Stop automation because no approved policy supports a response.", "no_policy")
            return self._unsupported(item, sanitized_message, redactions, trace.steps)

        lowered = sanitized_message.casefold()
        escalation_hits = [term for term in policy.escalation_keywords if term.casefold() in lowered]
        requires_handoff = policy.priority == "critical" or bool(escalation_hits)
        priority = "critical" if policy.priority == "critical" else "high" if escalation_hits else policy.priority
        trace.record("retrieve_policy", "Attach the approved policy, evidence requirements and service deadline.")
        trace.record(
            "route_handoff",
            "Route critical or explicitly escalated cases to an authorized human owner.",
            "escalated" if requires_handoff else "queued",
        )

        confidence = "high" if len(matched_keywords) >= 2 else "medium"
        status = "escalated" if requires_handoff else "triaged"
        response = self._response_draft(policy, requires_handoff)
        return {
            "ticket_id": item.ticket_id,
            "status": status,
            "sanitized_message": sanitized_message,
            "privacy": {"redactions_applied": redactions, "original_message_retained": False},
            "classification": {
                "category": policy.category,
                "confidence": confidence,
                "matched_keywords": matched_keywords,
            },
            "priority": priority,
            "sla_minutes": policy.sla_minutes,
            "policy_citation": {
                "policy_id": policy.policy_id,
                "title": policy.title,
                "updated_at": policy.updated_at,
            },
            "required_evidence": list(policy.required_evidence),
            "next_steps": list(policy.resolution_steps),
            "response_draft": response,
            "human_handoff": {
                "required": requires_handoff,
                "owner": policy.owner,
                "reason": "critical policy" if policy.priority == "critical" else ", ".join(escalation_hits) or "routine queue",
                "order_id": item.order_id,
                "customer_reply_requires_approval": True,
            },
            "trace": trace.steps,
            "limitations": [
                "Classification uses explicit English keyword rules, not semantic understanding.",
                "The response draft is policy-grounded but still requires an authorized human before sending.",
                "The public workflow uses synthetic policies and does not connect to a ticketing platform.",
            ],
        }

    def _match_policy(self, message: str) -> tuple[SupportPolicy | None, list[str]]:
        lowered = message.casefold()
        ranked: list[tuple[int, str, SupportPolicy, list[str]]] = []
        for policy in self.policies:
            matched = [term for term in policy.keywords if term.casefold() in lowered]
            if matched:
                ranked.append((len(matched), policy.policy_id, policy, matched))
        if not ranked:
            return None, []
        _, _, policy, matched = sorted(ranked, key=lambda item: (-item[0], item[1]))[0]
        return policy, matched

    @staticmethod
    def _response_draft(policy: SupportPolicy, requires_handoff: bool) -> str:
        evidence = ", ".join(policy.required_evidence)
        if requires_handoff:
            return (
                f"Thank you for reporting this. I have prepared the case for {policy.owner} under "
                f"{policy.policy_id}. Please provide {evidence}. A human reviewer will confirm the next action."
            )
        return (
            f"Thank you for contacting support. Under {policy.policy_id}, please provide {evidence}. "
            "A support reviewer will verify the information before confirming any resolution."
        )

    @staticmethod
    def _unsupported(
        ticket: SupportTicket,
        sanitized_message: str,
        redactions: list[str],
        trace: list[dict[str, str]],
    ) -> dict[str, Any]:
        return {
            "ticket_id": ticket.ticket_id,
            "status": "no_policy",
            "sanitized_message": sanitized_message,
            "privacy": {"redactions_applied": redactions, "original_message_retained": False},
            "classification": {"category": "unknown", "confidence": "none", "matched_keywords": []},
            "priority": "needs_review",
            "sla_minutes": None,
            "policy_citation": None,
            "required_evidence": [],
            "next_steps": ["Assign the case to a support lead for policy selection or clarification."],
            "response_draft": "I do not have an approved policy for this request. A human support lead must review it before a reply is sent.",
            "human_handoff": {
                "required": True,
                "owner": "Support Lead",
                "reason": "no approved policy matched",
                "order_id": ticket.order_id,
                "customer_reply_requires_approval": True,
            },
            "trace": trace,
            "limitations": ["No approved policy supported an automated draft; the workflow abstained."],
        }
