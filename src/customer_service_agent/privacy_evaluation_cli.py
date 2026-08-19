from __future__ import annotations

import argparse
from pathlib import Path

from .privacy_evaluation import evaluate_redaction_cases, write_redaction_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic redaction-quality fixture.")
    parser.add_argument("fixture", type=Path, nargs="?", default=Path("data/redaction_quality_cases.json"))
    parser.add_argument("--json-output", type=Path, default=Path("examples/redaction_quality_report.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("examples/redaction_quality_report.md"))
    args = parser.parse_args()
    report = evaluate_redaction_cases(args.fixture)
    write_redaction_report(report, args.json_output, args.markdown_output)
    print(f"Redaction fixture: {report['summary']['passed']}/{report['summary']['total']} passed")


if __name__ == "__main__":
    main()
