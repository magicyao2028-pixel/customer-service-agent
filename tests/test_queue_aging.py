import unittest

from customer_service_agent.queue_aging import summarize_owner_queue_aging


class QueueAgingTests(unittest.TestCase):
    def setUp(self):
        self.queue = {
            "decisions_applied": False, "raw_customer_messages_retained": False,
            "items": [{"feedback_id": "F-1", "status": "passed"}, {"feedback_id": "F-2", "status": "excluded"}],
        }
        self.history = {"entries": [
            {"feedback_id": "F-1", "recorded_on": "2026-08-10"},
            {"feedback_id": "F-2", "recorded_on": "2026-08-11"},
        ]}

    def test_exposes_closure_and_stale_counts(self):
        result = summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08")
        self.assertEqual((result["open_count"], result["closed_count"], result["stale_count"]), (1, 1, 1))
        self.assertEqual(result["replies_sent"], 0)

    def test_recent_open_item_is_not_stale(self):
        self.history["entries"][1]["recorded_on"] = "2026-09-01"
        result = summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08")
        self.assertEqual(result["stale_count"], 0)

    def test_rejects_invalid_threshold(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08", stale_after_days=0)

    def test_rejects_writing_queue(self):
        self.queue["decisions_applied"] = True
        with self.assertRaisesRegex(ValueError, "non-writing"):
            summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08")

    def test_rejects_unknown_feedback(self):
        self.queue["items"][0]["feedback_id"] = "F-X"
        with self.assertRaisesRegex(ValueError, "linked"):
            summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08")

    def test_rejects_duplicate_history_ids(self):
        self.history["entries"][1]["feedback_id"] = "F-1"
        with self.assertRaisesRegex(ValueError, "unique"):
            summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08")

    def test_rejects_duplicate_queue_ids(self):
        self.queue["items"][1]["feedback_id"] = "F-1"
        with self.assertRaisesRegex(ValueError, "unique"):
            summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08")

    def test_rejects_future_history(self):
        self.history["entries"][0]["recorded_on"] = "2026-09-09"
        with self.assertRaisesRegex(ValueError, "future-dated"):
            summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08")

    def test_rejects_unknown_status(self):
        self.queue["items"][0]["status"] = "auto_closed"
        with self.assertRaisesRegex(ValueError, "valid review history"):
            summarize_owner_queue_aging(self.queue, self.history, as_of_date="2026-09-08")


if __name__ == "__main__":
    unittest.main()
