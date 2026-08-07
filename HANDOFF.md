# Handoff

## Current state

- Release stage: v0.2 product-validation prototype.
- Maintenance completed: 1/10.
- M1 evidence: explicit state timeline, at most two clarification replies, urgent bypass and clarification-exhausted human handoff.
- Core flow: validate ticket → redact sensitive data → classify → retrieve approved policy → route SLA/handoff → draft human-reviewed response.
- Synthetic evaluation: 5/5 fixture cases pass.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m customer_service_agent.cli data/sample_ticket.json --output output/triage_result.json
PYTHONPATH=src python -m customer_service_agent.conversation_cli data/sample_conversation.json --output output/conversation_result.json
PYTHONPATH=src python -m customer_service_agent.evaluation_cli
```

## Next maintenance round

M2 should add policy-conflict, freshness and supersession handling. It must preserve the two-turn clarification limit, no-policy abstention, privacy redaction and human approval.

## Known limitations

- English keyword rules only;
- four synthetic policies and five evaluation cases;
- selected redaction patterns rather than full DLP;
- deterministic reply templates and in-memory state rather than model-generated conversation or a database;
- no persistence, authentication, ticketing integration, queue or real user study;
- browser and Python implementations are mirrored manually.
