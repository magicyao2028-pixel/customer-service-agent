from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .agent import CustomerServiceAgent
from .models import load_policies, load_ticket


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage one support ticket with cited local policies.")
    parser.add_argument("ticket", type=Path, help="Support-ticket JSON")
    parser.add_argument("--policies", type=Path, default=Path("data/support_policies.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--analysis-date", default=date.today().isoformat())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = CustomerServiceAgent(
        load_policies(args.policies), analysis_date=args.analysis_date
    ).handle(load_ticket(args.ticket))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Triage result written to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
