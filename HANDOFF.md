# Handoff

## Current state

- Release stage: v0.3 product-validation prototype.
- Maintenance completed: 2/10.
- M2 evidence: effective/review dates, explicit supersession chains, conflict and stale-policy abstention, and a `POLICY_BLOCKED` terminal state.
- Core flow: validate ticket → redact sensitive data → classify → resolve one current policy → route SLA/handoff or abstain → draft human-reviewed response.
- Synthetic evaluation: 5/5 fixture cases pass.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m customer_service_agent.cli data/sample_ticket.json --analysis-date 2026-08-12 --output output/triage_result.json
PYTHONPATH=src python -m customer_service_agent.conversation_cli data/sample_conversation.json --analysis-date 2026-08-12 --output output/conversation_result.json
PYTHONPATH=src python -m customer_service_agent.evaluation_cli
```

## Next maintenance round

M3 should add structured reviewer-feedback capture and evaluation replay. It must preserve policy-version resolution, bounded clarification, privacy redaction, abstention and human approval.

## Known limitations

- English keyword rules only;
- five synthetic policy records across four categories and five evaluation cases;
- selected redaction patterns rather than full DLP;
- deterministic reply templates and in-memory state rather than model-generated conversation or a database;
- no persistence, authentication, ticketing integration, queue or real user study;
- browser and Python implementations are mirrored manually.
