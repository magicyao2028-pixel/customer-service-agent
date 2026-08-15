import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from customer_service_agent.feedback import load_feedback, replay_feedback, write_feedback_replay


ROOT = Path(__file__).parents[1]
POLICIES = ROOT / "data" / "support_policies.json"
FEEDBACK = ROOT / "data" / "reviewer_feedback.json"


class ReviewerFeedbackReplayTests(unittest.TestCase):
    def test_replays_only_explicitly_accepted_feedback(self):
        report = replay_feedback(POLICIES, FEEDBACK)
        self.assertEqual(report["summary"], {"total_feedback": 3, "replayed": 2, "passed": 2, "failed": 0, "excluded": 1})
        self.assertEqual(report["excluded"][0]["feedback_id"], "FB-AUTOMATION-003")

    def test_capture_redacts_feedback_ticket_and_does_not_retain_original(self):
        batch = load_feedback(FEEDBACK)
        record = batch["records"][0]
        self.assertNotIn("reviewer@example.test", record["ticket"].customer_message)
        self.assertEqual(record["privacy"]["redactions_applied"], ["email"])
        self.assertFalse(record["privacy"]["original_message_retained"])

    def test_safety_replay_preserves_escalation_and_approval(self):
        report = replay_feedback(POLICIES, FEEDBACK)
        safety = next(item for item in report["replayed"] if item["feedback_id"] == "FB-SAFE-001")
        self.assertTrue(safety["checks"]["customer_reply_requires_approval"])
        self.assertEqual(safety["actual"]["status"], "escalated")
        self.assertTrue(safety["actual"]["handoff"])

    def test_policy_conflict_replay_stays_blocked_and_uncited(self):
        report = replay_feedback(POLICIES, FEEDBACK)
        conflict = next(item for item in report["replayed"] if item["feedback_id"] == "FB-CONFLICT-002")
        self.assertEqual(conflict["actual"]["status"], "policy_conflict")
        self.assertIsNone(conflict["actual"]["policy_id"])
        self.assertTrue(conflict["checks"]["blocked_policy_requires_handoff"])

    def test_rejects_duplicate_ids_and_unreviewed_provenance(self):
        payload = json.loads(FEEDBACK.read_text(encoding="utf-8"))
        payload["records"].append(copy.deepcopy(payload["records"][0]))
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "present and unique"):
                load_feedback(path)

        payload = json.loads(FEEDBACK.read_text(encoding="utf-8"))
        payload["records"][0]["provenance"] = "anonymous_web_comment"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported feedback provenance"):
                load_feedback(path)

    def test_accepted_feedback_requires_complete_expectation(self):
        payload = json.loads(FEEDBACK.read_text(encoding="utf-8"))
        del payload["records"][0]["expected"]["handoff"]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must define"):
                load_feedback(path)

    def test_writes_deterministic_replay_evidence(self):
        report = replay_feedback(POLICIES, FEEDBACK)
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "replay.json"
            markdown_path = Path(directory) / "replay.md"
            write_feedback_replay(report, json_path, markdown_path)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), report)
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("2/2 replay cases passed", markdown)
            self.assertIn("does not alter policy", markdown)


if __name__ == "__main__":
    unittest.main()
