import unittest
from pathlib import Path

from customer_service_agent import CustomerServiceAgent, load_policies
from customer_service_agent.conversation import ConversationFlow, ConversationState


ROOT = Path(__file__).parents[1]
POLICIES = ROOT / "data" / "support_policies.json"


def flow() -> ConversationFlow:
    return ConversationFlow(CustomerServiceAgent(load_policies(POLICIES)))


class ConversationFlowTests(unittest.TestCase):
    def test_triages_immediately_when_order_id_is_available(self):
        session = flow().start({
            "ticket_id": "C-1",
            "channel": "chat",
            "order_id": "ORDER-100",
            "customer_message": "The parcel arrived damaged and broken.",
        })
        self.assertEqual(session.state, ConversationState.TRIAGED)
        self.assertEqual(session.clarification_turns, 0)
        self.assertEqual(session.result["policy_citation"]["policy_id"], "POL-RET-001")

    def test_clarifies_then_triages_when_order_id_arrives(self):
        agent_flow = flow()
        session = agent_flow.start({
            "ticket_id": "C-2", "channel": "chat", "customer_message": "My parcel is damaged."
        })
        self.assertEqual(session.state, ConversationState.NEEDS_CLARIFICATION)
        agent_flow.reply(session, "Here is the requested reference.", order_id="ORDER-200")
        self.assertEqual(session.state, ConversationState.TRIAGED)
        self.assertEqual(session.clarification_turns, 1)
        self.assertEqual(session.result["human_handoff"]["order_id"], "ORDER-200")

    def test_stops_after_two_unsuccessful_clarification_turns(self):
        agent_flow = flow()
        session = agent_flow.start({
            "ticket_id": "C-3", "channel": "email", "customer_message": "I need a refund."
        })
        agent_flow.reply(session, "I am still looking for it.")
        agent_flow.reply(session, "I cannot find the order ID.")
        self.assertEqual(session.state, ConversationState.HUMAN_HANDOFF)
        self.assertEqual(session.clarification_turns, 2)
        self.assertEqual(session.result["status"], "clarification_exhausted")
        self.assertTrue(session.result["human_handoff"]["required"])

    def test_rejects_reply_after_terminal_state(self):
        agent_flow = flow()
        session = agent_flow.start({
            "ticket_id": "C-4",
            "channel": "chat",
            "order_id": "ORDER-400",
            "customer_message": "The parcel is damaged.",
        })
        with self.assertRaisesRegex(ValueError, "Cannot add"):
            agent_flow.reply(session, "Another message")

    def test_critical_safety_case_bypasses_clarification(self):
        session = flow().start({
            "ticket_id": "C-5", "channel": "chat", "customer_message": "I became sick; this is unsafe."
        })
        self.assertEqual(session.state, ConversationState.ESCALATED)
        self.assertEqual(session.clarification_turns, 0)
        self.assertTrue(session.result["human_handoff"]["required"])

    def test_no_policy_still_abstains_without_clarification(self):
        session = flow().start({
            "ticket_id": "C-6", "channel": "chat", "customer_message": "Where is the office parking?"
        })
        self.assertEqual(session.state, ConversationState.NO_POLICY)
        self.assertEqual(session.result["status"], "no_policy")

    def test_redacts_sensitive_text_across_turns(self):
        agent_flow = flow()
        session = agent_flow.start({
            "ticket_id": "C-7",
            "channel": "chat",
            "customer_message": "Refund person@example.com and password is secret123.",
        })
        agent_flow.reply(session, "Card 4111 1111 1111 1111, but no order ID.")
        rendered = str(session.to_dict())
        self.assertNotIn("person@example.com", rendered)
        self.assertNotIn("secret123", rendered)
        self.assertNotIn("4111", rendered)
        self.assertEqual(
            set(session.to_dict()["privacy"]["redactions_applied"]),
            {"email", "password", "payment_card"},
        )


if __name__ == "__main__":
    unittest.main()
