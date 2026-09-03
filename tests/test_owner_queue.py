import unittest

from customer_service_agent.owner_queue import build_owner_followup_queue


class OwnerQueueTests(unittest.TestCase):
    def setUp(self):
        self.export = {"records": [{"feedback_id": "F-1"}, {"feedback_id": "F-2"}], "decisions_applied": False, "raw_customer_messages_retained": False}
        self.history = {"entries": [{"feedback_id": "F-1", "status": "passed"}, {"feedback_id": "F-2", "status": "needs_revision"}]}

    def test_prioritizes_sanitized_followup(self):
        result = build_owner_followup_queue(self.export, self.history)
        self.assertEqual([item["priority"] for item in result["items"]], ["critical", "normal"])
        self.assertFalse(result["decisions_applied"])

    def test_unknown_feedback_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "linked"):
            build_owner_followup_queue(self.export, {"entries": [{"feedback_id": "F-X", "status": "passed"}]})

    def test_applied_export_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-writing"):
            build_owner_followup_queue({**self.export, "decisions_applied": True}, self.history)


if __name__ == "__main__":
    unittest.main()
