# Handoff

## Current state

- Release stage: v0.5 trial-readiness prototype.
- Maintenance completed: 4/10.
- M3 evidence: provenance-labeled reviewer feedback, capture-time redaction, accepted-case replay, deterministic fingerprints, excluded pending feedback and guardrail checks.
- Core flow: validate ticket → redact sensitive data → classify → resolve one current policy → route SLA/handoff or abstain → draft human-reviewed response.
- Synthetic evaluation: 5/5 fixture cases pass.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.
- M4 evidence: seven-case redaction-quality fixture, phone/token patterns, Luhn-gated card detection, clean trial, seven-claim index, external screening and synthetic privacy-feedback regression.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m customer_service_agent.cli data/sample_ticket.json --analysis-date 2026-08-12 --output output/triage_result.json
PYTHONPATH=src python -m customer_service_agent.conversation_cli data/sample_conversation.json --analysis-date 2026-08-12 --output output/conversation_result.json
PYTHONPATH=src python -m customer_service_agent.evaluation_cli
PYTHONPATH=src python -m customer_service_agent.feedback_cli data/support_policies.json data/reviewer_feedback.json --json-output examples/feedback_replay_report.json --markdown-output examples/feedback_replay_report.md
PYTHONPATH=src python -m customer_service_agent.privacy_evaluation_cli
PYTHONPATH=src python -m customer_service_agent.trial_cli
```

## Next maintenance round

M5 should add an optional local language-classification adapter behind the existing privacy, policy and human-handoff gates. The deterministic baseline must remain available.

## Known limitations

- English keyword rules only;
- five synthetic policy records, five evaluation cases and three synthetic feedback records;
- feedback replay has no database, authentication, real reviewer identity or workflow approval integration;
- five selected redaction types rather than full DLP or measured production recall;
- deterministic reply templates and in-memory state rather than model-generated conversation or a database;
- no persistence, authentication, ticketing integration, queue or real user study;
- browser and Python implementations are mirrored manually.
