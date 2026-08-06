import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from customer_service_agent.evaluation import evaluate_cases, write_evaluation


ROOT = Path(__file__).parents[1]
POLICIES = ROOT / "data" / "support_policies.json"
CASES = ROOT / "data" / "evaluation_cases.json"


class CustomerServiceEvaluationTests(unittest.TestCase):
    def test_synthetic_fixture_passes(self):
        report = evaluate_cases(POLICIES, CASES)

        self.assertEqual(report["summary"]["passed_cases"], 5)
        self.assertEqual(report["summary"]["pass_rate"], 1.0)

    def test_writes_reproducible_reports(self):
        report = evaluate_cases(POLICIES, CASES)
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "report.json"
            markdown_path = Path(directory) / "report.md"
            write_evaluation(report, json_path, markdown_path)

            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), report)
            self.assertIn("5/5 cases passed", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
