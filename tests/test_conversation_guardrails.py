import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from customer_service_agent import CustomerServiceAgent, load_policies
from customer_service_agent.conversation import ConversationFlow, ConversationState, ConversationSession
from customer_service_agent.conversation_cli import run_transcript
from customer_service_agent.conversation_guardrails import evaluate_conversation_guardrails
from customer_service_agent.trial import run_trial

ROOT = Path(__file__).parents[1]
POLICIES = ROOT / "data/support_policies.json"
FIXTURE = ROOT / "data/conversation_guardrail_cases.json"


class ClarificationGuardrailTests(unittest.TestCase):
    def flow(self):
        return ConversationFlow(CustomerServiceAgent(load_policies(POLICIES), analysis_date="2026-08-12"))

    def start(self, flow):
        return flow.start({"ticket_id": "SYN-P3-001", "channel": "chat", "customer_message": "I need a refund."})

    def test_critical_reply_without_order_id_is_immediately_escalated(self):
        flow = self.flow()
        session = self.start(flow)
        flow.reply(session, "I have an injury and this is unsafe; it is a safety concern.")
        self.assertEqual(session.state, ConversationState.ESCALATED)
        self.assertIsNone(session.order_id)
        self.assertIsNone(session.pending_prompt)
        self.assertEqual(session.result["policy_citation"]["policy_id"], "POL-SAFE-003")
        self.assertEqual(session.result["human_handoff"]["owner"], "Duty Manager")
        self.assertIs(session.result["human_handoff"]["customer_reply_requires_approval"], True)
        self.assertEqual(session.to_dict()["conversation_guardrail_receipt"], {
            "schema_version": "1.0", "triage_evaluation_count": 2, "clarification_retriage_count": 1,
            "reply_retriage_performed": True, "clarification_limit_enforced": True,
            "customer_reply_requires_approval": True, "customer_reply_sent": False,
            "external_actions_executed": 0, "original_messages_retained": False,
        })

    def test_safety_on_last_allowed_turn_precedes_clarification_exhaustion(self):
        flow = self.flow()
        session = self.start(flow)
        flow.reply(session, "I am still looking.")
        flow.reply(session, "I have an injury and this is unsafe; it is a safety concern.")
        self.assertEqual(session.result["status"], "escalated")
        self.assertEqual(session.clarification_turns, 2)
        self.assertEqual(session.triage_evaluation_count, 3)

    def test_same_policy_escalation_signal_is_not_delayed_by_order_id(self):
        flow = self.flow()
        session = self.start(flow)
        flow.reply(session, "This refund involves fraud and legal action.")
        self.assertEqual(session.state, ConversationState.ESCALATED)
        self.assertEqual(session.result["policy_citation"]["policy_id"], "POL-REF-004")

    def test_regular_clarification_remains_bounded_and_terminal_reply_is_atomic(self):
        flow = self.flow()
        session = self.start(flow)
        flow.reply(session, "I am still looking.")
        self.assertEqual(session.state, ConversationState.NEEDS_CLARIFICATION)
        flow.reply(session, "I cannot find the reference.")
        self.assertEqual(session.result["status"], "clarification_exhausted")
        before = copy.deepcopy(session.to_dict())
        with self.assertRaises(ValueError):
            flow.reply(session, "I have an injury and this is unsafe.")
        self.assertEqual(session.to_dict(), before)

    def test_one_turn_limit_still_permits_safety_escalation_first(self):
        flow = ConversationFlow(self.flow().agent, max_clarification_turns=1)
        session = self.start(flow)
        flow.reply(session, "I have an injury and this is unsafe; it is a safety concern.")
        self.assertEqual(session.state, ConversationState.ESCALATED)
        self.assertEqual(session.clarification_turns, 1)

    def test_transcript_route_and_redaction_preserve_guardrails(self):
        case = json.loads(FIXTURE.read_text())["cases"][0]
        before = copy.deepcopy(case)
        output = run_transcript(case, POLICIES, analysis_date="2026-08-12")
        self.assertEqual(output["conversation_state"], "escalated")
        self.assertNotIn("person@example.com", json.dumps(output))
        self.assertIn("email", output["privacy"]["redactions_applied"])
        self.assertEqual(case, before)

    def test_four_synthetic_cases_pass_without_retaining_messages_in_report(self):
        report = evaluate_conversation_guardrails(POLICIES, FIXTURE)
        self.assertEqual(report["passed_cases"], 4)
        rendered = json.dumps(report)
        self.assertNotIn('"customer_message":', rendered)
        self.assertNotIn("person@example.com", rendered)
        self.assertNotIn("I need a refund.", rendered)
        self.assertIs(report["customer_replies_sent"], False)
        self.assertIs(report["raw_customer_messages_retained"], False)
        self.assertEqual(report["external_actions_executed"], 0)

    def test_every_returned_receipt_field_is_bound_into_trial_even_if_case_pass_is_true(self):
        report = evaluate_conversation_guardrails(POLICIES, FIXTURE)
        for key, value in report["cases"][0]["receipt"].items():
            bad = copy.deepcopy(report)
            bad["cases"][0]["receipt"][key] = not value if type(value) is bool else "tampered"
            with patch("customer_service_agent.trial.evaluate_conversation_guardrails", return_value=bad):
                altered = run_trial(ROOT)
            self.assertFalse(altered["overall_passed"], key)
            self.assertEqual(altered["conversation_guardrails"], bad)
        bad = copy.deepcopy(report)
        bad["cases"][0]["receipt"]["external_actions_executed"] = False
        with patch("customer_service_agent.trial.evaluate_conversation_guardrails", return_value=bad):
            self.assertFalse(run_trial(ROOT)["overall_passed"])
        for key, value in report["cases"][0]["receipt"].items():
            if type(value) is bool:
                bad = copy.deepcopy(report)
                bad["cases"][0]["receipt"][key] = int(value)
                with patch("customer_service_agent.trial.evaluate_conversation_guardrails", return_value=bad):
                    self.assertFalse(run_trial(ROOT)["overall_passed"], key)

    def test_trial_rejects_retriage_regression_in_actual_session_outputs(self):
        original = ConversationSession.to_dict
        def missing_retriage(session):
            output = original(session)
            output["conversation_guardrail_receipt"]["clarification_retriage_count"] = 0
            return output
        with patch.object(ConversationSession, "to_dict", missing_retriage):
            self.assertFalse(run_trial(ROOT)["overall_passed"])

    def test_all_returned_no_send_privacy_and_application_fields_are_trial_gates(self):
        report = run_trial(ROOT)
        targets = [
            ("build_review_report_export", "feedback_review_export", ("decisions_applied", "raw_customer_messages_retained"), ("external_actions_executed",)),
            ("summarize_review_history", "review_history", ("decisions_applied", "raw_customer_messages_retained"), ("external_actions_executed",)),
            ("build_owner_followup_queue", "owner_followup_queue", ("decisions_applied", "raw_customer_messages_retained"), ("external_actions_executed",)),
            ("summarize_owner_queue_aging", "owner_queue_aging", ("decisions_applied", "raw_customer_messages_retained"), ("replies_sent",)),
            ("evaluate_conversation_guardrails", "conversation_guardrails", ("raw_customer_messages_retained", "customer_replies_sent"), ("external_actions_executed",)),
        ]
        for function, key, false_fields, zero_fields in targets:
            for field in false_fields + zero_fields:
                bad = copy.deepcopy(report[key])
                bad[field] = True if field in false_fields else 1
                with patch("customer_service_agent.trial." + function, return_value=bad):
                    try:
                        altered = run_trial(ROOT)
                    except ValueError:
                        continue  # Downstream fail-closed validation also denies Trial PASS.
                self.assertFalse(altered["overall_passed"], (key, field))
