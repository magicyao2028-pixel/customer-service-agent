# Handoff

## Current state

- Release stage: v0.1 product-validation prototype.
- Maintenance completed: 0/10.
- Core flow: validate ticket → redact sensitive data → classify → retrieve approved policy → route SLA/handoff → draft human-reviewed response.
- Synthetic evaluation: 5/5 fixture cases pass.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m customer_service_agent.cli data/sample_ticket.json --output output/triage_result.json
PYTHONPATH=src python -m customer_service_agent.evaluation_cli
```

## Next maintenance round

M1 should add explicit multi-turn conversation state and a bounded clarification loop. It must preserve no-policy abstention, privacy redaction and human approval.

## Known limitations

- English keyword rules only;
- four synthetic policies and five evaluation cases;
- selected redaction patterns rather than full DLP;
- deterministic reply templates rather than model-generated conversation;
- no persistence, authentication, ticketing integration, queue or real user study;
- browser and Python implementations are mirrored manually.
