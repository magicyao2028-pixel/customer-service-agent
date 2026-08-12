from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterable

from .models import SupportPolicy, SupportTicket
from .privacy import redact_sensitive_text
from .policy_resolution import PolicyResolution, resolve_policy


@dataclass
class AgentTrace:
    steps: list[dict[str, str]] = field(default_factory=list)

    def record(self, tool: str, purpose: str, status: str = "completed") -> None:
        self.steps.append({"tool": tool, "purpose": purpose, "status": status})


class CustomerServiceAgent:
    """Runs deterministic support triage with cited policies and human handoff."""

    def __init__(self, policies: Iterable[SupportPolicy], analysis_date: str | None = None) -> None:
        self.policies = list(policies)
        if not self.policies:
            raise ValueError("At least one support policy is required")
        self.analysis_date = analysis_date or date.today().isoformat()
        try:
            date.fromisoformat(self.analysis_date)
        except ValueError as exc:
            raise ValueError("analysis_date must use YYYY-MM-DD") from exc

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

        resolution = resolve_policy(self.policies, sanitized_message, self.analysis_date)
        policy = resolution.policy
        matched_keywords = list(resolution.matched_keywords)
        trace.record("classify_issue", "Match the sanitized ticket to explicit policy keywords.")
        if policy is None:
            trace.record(
                "resolve_policy_version",
                "Check policy effective dates, review windows, conflicts and supersession links.",
                resolution.status,
            )
            trace.record(
                "evidence_gate",
                "Stop automation because no single current policy supports a response.",
                resolution.status,
            )
            return self._unsupported(item, sanitized_message, redactions, trace.steps, resolution)

        lowered = sanitized_message.casefold()
        escalation_hits = [term for term in policy.escalation_keywords if term.casefold() in lowered]
        requires_handoff = policy.priority == "critical" or bool(escalation_hits)
        priority = "critical" if policy.priority == "critical" else "high" if escalation_hits else policy.priority
        trace.record(
            "resolve_policy_version",
            "Select one current unsuperseded policy and expose excluded versions.",
        )
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
            "policy_resolution": resolution.to_dict(self.analysis_date),
            "priority": priority,
            "sla_minutes": policy.sla_minutes,
            "policy_citation": {
                "policy_id": policy.policy_id,
                "title": policy.title,
                "updated_at": policy.updated_at,
                "effective_from": policy.effective_from,
                "review_due_at": policy.review_due_at,
                "supersedes_policy_ids": list(policy.supersedes_policy_ids),
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

    def _unsupported(
        self,
        ticket: SupportTicket,
        sanitized_message: str,
        redactions: list[str],
        trace: list[dict[str, str]],
        resolution: PolicyResolution,
    ) -> dict[str, Any]:
        return {
            "ticket_id": ticket.ticket_id,
            "status": resolution.status,
            "sanitized_message": sanitized_message,
            "privacy": {"redactions_applied": redactions, "original_message_retained": False},
            "classification": {
                "category": resolution.category,
                "confidence": "none",
                "matched_keywords": list(resolution.matched_keywords),
            },
            "policy_resolution": resolution.to_dict(self.analysis_date),
            "priority": "needs_review",
            "sla_minutes": None,
            "policy_citation": None,
            "required_evidence": [],
            "next_steps": ["Assign the case to a support lead for current-policy selection or clarification."],
            "response_draft": "I do not have one unambiguous current policy for this request. A human support lead must review it before a reply is sent.",
            "human_handoff": {
                "required": True,
                "owner": "Support Lead",
                "reason": resolution.reason,
                "order_id": ticket.order_id,
                "customer_reply_requires_approval": True,
            },
            "trace": trace,
            "limitations": ["No single current policy supported an automated draft; the workflow abstained."],
        }
