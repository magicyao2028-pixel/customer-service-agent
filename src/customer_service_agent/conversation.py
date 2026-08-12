from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .agent import CustomerServiceAgent
from .models import SupportTicket
from .privacy import redact_sensitive_text


class ConversationState(str, Enum):
    NEW = "new"
    NEEDS_CLARIFICATION = "needs_clarification"
    READY_FOR_TRIAGE = "ready_for_triage"
    TRIAGED = "triaged"
    ESCALATED = "escalated"
    NO_POLICY = "no_policy"
    POLICY_BLOCKED = "policy_blocked"
    HUMAN_HANDOFF = "human_handoff"


TERMINAL_STATES = {
    ConversationState.TRIAGED,
    ConversationState.ESCALATED,
    ConversationState.NO_POLICY,
    ConversationState.POLICY_BLOCKED,
    ConversationState.HUMAN_HANDOFF,
}


@dataclass
class ConversationSession:
    ticket_id: str
    channel: str
    order_id: str | None
    max_clarification_turns: int
    state: ConversationState = ConversationState.NEW
    clarification_turns: int = 0
    sanitized_messages: list[dict[str, str]] = field(default_factory=list)
    redactions_applied: list[str] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    pending_prompt: str | None = None
    result: dict[str, Any] | None = None
    candidate_result: dict[str, Any] | None = field(default=None, repr=False)

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def to_dict(self) -> dict[str, Any]:
        policy_context = None
        if self.candidate_result:
            policy_context = {
                "classification": self.candidate_result.get("classification"),
                "policy_citation": self.candidate_result.get("policy_citation"),
                "required_evidence": self.candidate_result.get("required_evidence", []),
            }
        return {
            "ticket_id": self.ticket_id,
            "conversation_state": self.state.value,
            "clarification": {
                "turns_used": self.clarification_turns,
                "max_turns": self.max_clarification_turns,
                "pending_prompt": self.pending_prompt,
            },
            "messages": self.sanitized_messages,
            "privacy": {
                "redactions_applied": sorted(set(self.redactions_applied)),
                "original_messages_retained": False,
            },
            "policy_context": policy_context,
            "result": self.result,
            "timeline": self.timeline,
        }


class ConversationFlow:
    """Adds explicit, bounded conversation state around deterministic triage."""

    def __init__(self, agent: CustomerServiceAgent, max_clarification_turns: int = 2) -> None:
        if max_clarification_turns not in {1, 2}:
            raise ValueError("max_clarification_turns must be 1 or 2")
        self.agent = agent
        self.max_clarification_turns = max_clarification_turns

    def start(self, ticket: SupportTicket | dict[str, Any]) -> ConversationSession:
        item = ticket if isinstance(ticket, SupportTicket) else SupportTicket.from_mapping(ticket)
        sanitized, redactions = redact_sensitive_text(item.customer_message)
        session = ConversationSession(
            ticket_id=item.ticket_id,
            channel=item.channel,
            order_id=item.order_id,
            max_clarification_turns=self.max_clarification_turns,
            sanitized_messages=[{"role": "customer", "content": sanitized}],
            redactions_applied=redactions,
        )
        self._transition(session, ConversationState.READY_FOR_TRIAGE, "initial message validated")
        self._evaluate(session)
        return session

    def reply(
        self,
        session: ConversationSession,
        message: str,
        order_id: str | None = None,
    ) -> ConversationSession:
        if session.state != ConversationState.NEEDS_CLARIFICATION:
            raise ValueError(f"Cannot add a clarification reply while state is '{session.state.value}'")
        if not message.strip():
            raise ValueError("clarification message must not be blank")

        sanitized, redactions = redact_sensitive_text(message.strip())
        session.sanitized_messages.append({"role": "customer", "content": sanitized})
        session.redactions_applied.extend(redactions)
        session.clarification_turns += 1
        if order_id and order_id.strip():
            session.order_id = order_id.strip()

        if session.order_id:
            session.pending_prompt = None
            self._transition(session, ConversationState.READY_FOR_TRIAGE, "required order ID supplied")
            self._evaluate(session)
        elif session.clarification_turns >= session.max_clarification_turns:
            self._handoff_after_limit(session)
        else:
            self._transition(
                session,
                ConversationState.NEEDS_CLARIFICATION,
                "order ID still missing; one bounded clarification remains",
            )
        return session

    def _evaluate(self, session: ConversationSession) -> None:
        ticket = SupportTicket(
            ticket_id=session.ticket_id,
            channel=session.channel,
            customer_message="\n".join(item["content"] for item in session.sanitized_messages),
            order_id=session.order_id,
        )
        candidate = self.agent.handle(ticket)
        session.candidate_result = candidate
        self._merge_privacy(session, candidate)

        if candidate["status"] == "escalated":
            self._finish(session, candidate, ConversationState.ESCALATED, "urgent case bypassed clarification")
        elif candidate["status"] == "no_policy":
            self._finish(session, candidate, ConversationState.NO_POLICY, "no approved policy matched")
        elif candidate["status"] in {"policy_conflict", "policy_stale"}:
            self._finish(
                session,
                candidate,
                ConversationState.POLICY_BLOCKED,
                "policy version resolution requires human review",
            )
        elif self._requires_order_id(candidate) and not session.order_id:
            session.pending_prompt = (
                "Please provide the order ID so a support reviewer can verify the policy evidence. "
                "Do not send payment-card details or passwords."
            )
            self._transition(session, ConversationState.NEEDS_CLARIFICATION, "matched policy requires an order ID")
        else:
            self._finish(session, candidate, ConversationState.TRIAGED, "required structured evidence available")

    @staticmethod
    def _requires_order_id(candidate: dict[str, Any]) -> bool:
        return any("order number" in item.casefold() for item in candidate.get("required_evidence", []))

    @staticmethod
    def _merge_privacy(session: ConversationSession, result: dict[str, Any]) -> None:
        existing = result.get("privacy", {}).get("redactions_applied", [])
        result["privacy"] = {
            "redactions_applied": sorted(set(session.redactions_applied + existing)),
            "original_message_retained": False,
        }

    def _finish(
        self,
        session: ConversationSession,
        result: dict[str, Any],
        state: ConversationState,
        reason: str,
    ) -> None:
        session.pending_prompt = None
        session.result = result
        self._transition(session, state, reason)

    def _handoff_after_limit(self, session: ConversationSession) -> None:
        candidate = session.candidate_result or {}
        session.pending_prompt = None
        session.result = {
            "ticket_id": session.ticket_id,
            "status": "clarification_exhausted",
            "classification": candidate.get("classification"),
            "policy_citation": candidate.get("policy_citation"),
            "required_evidence": candidate.get("required_evidence", []),
            "response_draft": (
                "The required order ID was not available within the clarification limit. "
                "A human support reviewer must continue the case."
            ),
            "human_handoff": {
                "required": True,
                "owner": candidate.get("human_handoff", {}).get("owner", "Support Lead"),
                "reason": "clarification limit reached with required evidence missing",
                "customer_reply_requires_approval": True,
            },
            "privacy": {
                "redactions_applied": sorted(set(session.redactions_applied)),
                "original_message_retained": False,
            },
            "limitations": ["The workflow stopped after the configured clarification limit."],
        }
        self._transition(
            session,
            ConversationState.HUMAN_HANDOFF,
            "clarification limit reached; automation stopped",
        )

    @staticmethod
    def _transition(session: ConversationSession, target: ConversationState, reason: str) -> None:
        source = session.state
        session.state = target
        session.timeline.append({
            "from": source.value,
            "to": target.value,
            "reason": reason,
            "clarification_turn": session.clarification_turns,
        })
