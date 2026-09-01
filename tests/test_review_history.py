import unittest

from customer_service_agent.review_history import summarize_review_history


class ReviewHistoryTests(unittest.TestCase):
    def test_summary_is_chronological_and_non_executing(self):
        result = summarize_review_history(
            {"records": [{"feedback_id": "A"}, {"feedback_id": "B"}]},
            [
                {"feedback_id": "A", "status": "passed", "recorded_on": "2026-08-14", "applied": False},
                {"feedback_id": "B", "status": "excluded", "recorded_on": "2026-08-15", "applied": False},
            ],
        )
        self.assertEqual(result["entry_count"], 2)
        self.assertTrue(result["decisions_applied"] is False)
        self.assertFalse(result["raw_customer_messages_retained"])

    def test_rejects_applied_and_unknown_records(self):
        with self.assertRaisesRegex(ValueError, "applied"):
            summarize_review_history({"records": [{"feedback_id": "A"}]}, [{"feedback_id": "A", "status": "passed", "recorded_on": "2026-08-14", "applied": True}])
        with self.assertRaisesRegex(ValueError, "reference"):
            summarize_review_history({"records": [{"feedback_id": "A"}]}, [{"feedback_id": "B", "status": "passed", "recorded_on": "2026-08-14", "applied": False}])


if __name__ == "__main__":
    unittest.main()
