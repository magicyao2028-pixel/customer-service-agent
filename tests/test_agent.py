import json
import unittest
from pathlib import Path

from customer_service_agent import CustomerServiceAgent, SupportPolicy, SupportTicket, load_policies


ROOT = Path(__file__).parents[1]
POLICIES = ROOT / "data" / "support_policies.json"


def agent() -> CustomerServiceAgent:
    return CustomerServiceAgent(load_policies(POLICIES), analysis_date="2026-08-12")


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
        self.assertEqual(result["policy_resolution"]["status"], "selected")
        self.assertIn(
            {"policy_id": "POL-RET-000", "reason": "superseded"},
            result["policy_resolution"]["excluded_policies"],
        )
        self.assertEqual(result["policy_citation"]["supersedes_policy_ids"], ["POL-RET-000"])
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

    def test_policy_ids_are_unique_and_categories_can_have_versions(self):
        policies = load_policies(POLICIES)
        self.assertEqual(len({item.policy_id for item in policies}), len(policies))
        self.assertLess(len({item.category for item in policies}), len(policies))

    def test_stale_policy_abstains_with_current_date_evidence(self):
        result = CustomerServiceAgent(
            load_policies(POLICIES), analysis_date="2028-01-01"
        ).handle({"ticket_id": "T-7", "channel": "chat", "customer_message": "Refund please"})

        self.assertEqual(result["status"], "policy_stale")
        self.assertIsNone(result["policy_citation"])
        self.assertTrue(result["human_handoff"]["required"])
        self.assertEqual(result["policy_resolution"]["excluded_policies"][0]["reason"], "review_overdue")

    def test_equal_category_matches_abstain_as_policy_conflict(self):
        result = agent().handle({
            "ticket_id": "T-8",
            "channel": "chat",
            "customer_message": "The parcel is damaged and I also need a refund.",
        })

        self.assertEqual(result["status"], "policy_conflict")
        self.assertEqual(result["classification"]["category"], "multiple")
        self.assertIsNone(result["policy_citation"])

    def test_unresolved_same_category_versions_abstain(self):
        policies = load_policies(POLICIES)
        source = next(item for item in policies if item.policy_id == "POL-DEL-002")
        extra = SupportPolicy.from_mapping({
            **source.__dict__,
            "policy_id": "POL-DEL-ALT",
            "title": "Alternative Delivery Rule",
            "keywords": list(source.keywords),
            "escalation_keywords": list(source.escalation_keywords),
            "required_evidence": list(source.required_evidence),
            "resolution_steps": list(source.resolution_steps),
            "supersedes_policy_ids": [],
        })
        result = CustomerServiceAgent(
            [*policies, extra], analysis_date="2026-08-12"
        ).handle({"ticket_id": "T-9", "channel": "chat", "customer_message": "tracking not arrived"})

        self.assertEqual(result["status"], "policy_conflict")
        self.assertIn("multiple current policies", result["policy_resolution"]["reason"])

    def test_rejects_unknown_supersession_and_cycles(self):
        payload = json.loads(POLICIES.read_text(encoding="utf-8"))
        payload[1]["supersedes_policy_ids"] = ["POL-MISSING"]
        with self.assertRaisesRegex(ValueError, "supersedes unknown policies"):
            from tempfile import TemporaryDirectory
            with TemporaryDirectory() as directory:
                path = Path(directory) / "policies.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                load_policies(path)

        payload = json.loads(POLICIES.read_text(encoding="utf-8"))
        payload[0]["supersedes_policy_ids"] = ["POL-RET-001"]
        with self.assertRaisesRegex(ValueError, "must not contain a cycle"):
            from tempfile import TemporaryDirectory
            with TemporaryDirectory() as directory:
                path = Path(directory) / "policies.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                load_policies(path)


if __name__ == "__main__":
    unittest.main()
