from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .agent import CustomerServiceAgent
from .conversation import ConversationFlow, ConversationState
from .models import load_policies


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded support conversation from JSON.")
    parser.add_argument("conversation", type=Path, help="JSON with ticket and optional replies")
    parser.add_argument("--policies", type=Path, default=Path("data/support_policies.json"))
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def run_transcript(payload: dict[str, Any], policies: Path) -> dict[str, Any]:
    ticket = payload.get("ticket")
    replies = payload.get("replies", [])
    if not isinstance(ticket, dict) or not isinstance(replies, list):
        raise ValueError("conversation must contain a ticket object and a replies list")

    flow = ConversationFlow(CustomerServiceAgent(load_policies(policies)))
    session = flow.start(ticket)
    for reply in replies:
        if session.state != ConversationState.NEEDS_CLARIFICATION:
            break
        if not isinstance(reply, dict):
            raise ValueError("each reply must be an object")
        flow.reply(session, str(reply.get("message", "")), str(reply.get("order_id", "")).strip() or None)
    return session.to_dict()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.conversation.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("conversation file must contain a JSON object")
    result = run_transcript(payload, args.policies)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Conversation result written to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
