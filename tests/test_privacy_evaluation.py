import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from customer_service_agent.privacy import redact_sensitive_text
from customer_service_agent.privacy_evaluation import evaluate_redaction_cases, write_redaction_report


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "data/redaction_quality_cases.json"


class PrivacyEvaluationTests(unittest.TestCase):
    def test_fixture_passes_without_retaining_original_values(self):
        report = evaluate_redaction_cases(FIXTURE)
        self.assertEqual(report["summary"]["passed"], 7)
        self.assertTrue(all(not item["original_sensitive_values_retained"] for item in report["cases"]))

    def test_phone_and_access_token_are_redacted(self):
        text, detected = redact_sensitive_text("Call +86 138 0013 8000; bearer demo_token_12345")
        self.assertEqual(detected, ["phone", "access_token"])
        self.assertNotIn("138 0013 8000", text)
        self.assertNotIn("demo_token_12345", text)

    def test_safe_order_identifier_is_not_redacted(self):
        text, detected = redact_sensitive_text("Order ORDER-2026-004 needs a delivery update")
        self.assertEqual(text, "Order ORDER-2026-004 needs a delivery update")
        self.assertEqual(detected, [])

    def test_report_is_deterministic_and_contains_no_raw_messages(self):
        report = evaluate_redaction_cases(FIXTURE)
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "report.json"
            md_path = Path(directory) / "report.md"
            write_redaction_report(report, json_path, md_path)
            first = (json_path.read_bytes(), md_path.read_bytes())
            write_redaction_report(report, json_path, md_path)
            self.assertEqual(first, (json_path.read_bytes(), md_path.read_bytes()))
            serialized = json.dumps(report)
            self.assertNotIn("reviewer@example.test", serialized)
            self.assertNotIn("demo_token_12345", serialized)


if __name__ == "__main__":
    unittest.main()
