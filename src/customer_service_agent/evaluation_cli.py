from __future__ import annotations

import argparse
from pathlib import Path

from .evaluation import evaluate_cases, write_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic customer-service behavior fixture.")
    parser.add_argument("--policies", type=Path, default=Path("data/support_policies.json"))
    parser.add_argument("--cases", type=Path, default=Path("data/evaluation_cases.json"))
    parser.add_argument("--json-output", type=Path, default=Path("reports/evaluation_report.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/evaluation_report.md"))
    args = parser.parse_args()
    report = evaluate_cases(args.policies, args.cases)
    write_evaluation(report, args.json_output, args.markdown_output)
    print(f"Evaluation complete: {report['summary']['passed_cases']}/{report['summary']['total_cases']} cases passed")


if __name__ == "__main__":
    main()
