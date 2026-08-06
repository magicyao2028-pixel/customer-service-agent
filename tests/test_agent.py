import unittest
from pathlib import Path

from customer_service_agent import CustomerServiceAgent, SupportTicket, load_policies


ROOT = Path(__file__).parents[1]
POLICIES = ROOT / "data" / "support_policies.json"


def agent() -> CustomerServiceAgent:
    return CustomerServiceAgent(load_policies(POLICIES))


class CustomerServiceAgentTests(unittest.TestCase):
    def test_triages_damaged_product_with_policy_citation(self):
        result = agent().handle({
            "ticket_id": "T-1",
            "channel": "chat",
            "order_id": "ORDER-1",
            "customer_message": "The package is damaged and broken. I have photo evidence.",
        })

        self.assertEqual(result["status"], "triaged")
        self.assertEqual(result["classification"]["category"], "damaged_product")
        self.assertEqual(result["policy_citation"]["policy_id"], "POL-RET-001")
        self.assertFalse(result["human_handoff"]["required"])

    def test_escalates_safety_incident_to_duty_manager(self):
        result = agent().handle({
            "ticket_id": "T-2",
            "channel": "email",
            "customer_message": "I became sick and the product seems unsafe.",
        })

        self.assertEqual(result["status"], "escalated")
        self.assertEqual(result["priority"], "critical")
        self.assertEqual(result["sla_minutes"], 15)
        self.assertEqual(result["human_handoff"]["owner"], "Duty Manager")
        self.assertNotIn("medical conclusion", result["response_draft"].lower())

    def test_abstains_when_no_policy_matches(self):
        result = agent().handle({
            "ticket_id": "T-3",
            "channel": "chat",
            "customer_message": "Where is the office parking entrance?",
        })

        self.assertEqual(result["status"], "no_policy")
        self.assertIsNone(result["policy_citation"])
        self.assertTrue(result["human_handoff"]["required"])

    def test_redacts_email_card_and_password_before_output(self):
        message = "Refund me at person@example.com. Card 4111 1111 1111 1111 and password is secret123."
        result = agent().handle({"ticket_id": "T-4", "channel": "chat", "customer_message": message})

        self.assertEqual(set(result["privacy"]["redactions_applied"]), {"email", "payment_card", "password"})
        self.assertNotIn("person@example.com", result["sanitized_message"])
        self.assertNotIn("4111", result["sanitized_message"])
        self.assertNotIn("secret123", result["sanitized_message"])
        self.assertFalse(result["privacy"]["original_message_retained"])

    def test_explicit_escalation_keyword_requires_handoff(self):
        result = agent().handle({
            "ticket_id": "T-5",
            "channel": "marketplace",
            "customer_message": "The delivery delay affects an event deadline and tracking is unchanged.",
        })

        self.assertEqual(result["status"], "escalated")
        self.assertEqual(result["priority"], "high")
        self.assertTrue(result["human_handoff"]["required"])

    def test_rejects_unsupported_channel(self):
        with self.assertRaisesRegex(ValueError, "channel must be one of"):
            SupportTicket.from_mapping({"ticket_id": "T-6", "channel": "phone", "customer_message": "Refund"})

    def test_policy_ids_and_categories_are_unique(self):
        policies = load_policies(POLICIES)
        self.assertEqual(len({item.policy_id for item in policies}), len(policies))
        self.assertEqual(len({item.category for item in policies}), len(policies))


if __name__ == "__main__":
    unittest.main()
