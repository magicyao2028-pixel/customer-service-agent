import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from customer_service_agent.trial import load_json_object, run_trial, validate_external_intake, validate_feedback, write_trial_report


ROOT = Path(__file__).parents[1]


class TrialTests(unittest.TestCase):
    def test_complete_trial_passes(self):
        report = run_trial(ROOT)
        self.assertTrue(report["overall_passed"])
        self.assertEqual(report["core_flow"]["redaction_cases"]["passed"], 7)
        self.assertEqual(report["core_flow"]["external_actions_executed"], 0)

    def test_external_intake_requires_full_sha_and_consistent_decision(self):
        payload = load_json_object(ROOT / "evidence/external_intake.json")
        payload["candidates"][0]["commit"] = "abc"
        with self.assertRaisesRegex(ValueError, "full commit SHA"):
            validate_external_intake(payload)

    def test_feedback_rejects_unknown_source_and_nonaccepted_decision(self):
        payload = load_json_object(ROOT / "evidence/feedback_case.json")
        payload["decision"] = "pending"
        with self.assertRaisesRegex(ValueError, "accepted"):
            validate_feedback(ROOT, payload)

    def test_trial_report_is_reproducible(self):
        with TemporaryDirectory() as directory:
            json_path, md_path = Path(directory) / "trial.json", Path(directory) / "trial.md"
            first = write_trial_report(ROOT, json_path, md_path)
            first_bytes = (json_path.read_bytes(), md_path.read_bytes())
            second = write_trial_report(ROOT, json_path, md_path)
            self.assertEqual(first, second)
            self.assertEqual(first_bytes, (json_path.read_bytes(), md_path.read_bytes()))
            self.assertTrue(json.loads(json_path.read_text())["overall_passed"])


if __name__ == "__main__":
    unittest.main()
