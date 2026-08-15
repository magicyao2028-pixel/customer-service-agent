from __future__ import annotations

import argparse
import json
from pathlib import Path

from .feedback import replay_feedback, write_feedback_replay


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay explicitly accepted reviewer feedback.")
    parser.add_argument("policies", type=Path)
    parser.add_argument("feedback", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    report = replay_feedback(args.policies, args.feedback)
    if args.json_output or args.markdown_output:
        json_path = args.json_output or Path("examples/feedback_replay_report.json")
        markdown_path = args.markdown_output or Path("examples/feedback_replay_report.md")
        write_feedback_replay(report, json_path, markdown_path)
        print(f"Feedback replay written to {json_path} and {markdown_path}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
