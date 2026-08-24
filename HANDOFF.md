# Handoff

## Current state

- Release stage: v0.6 trial-readiness prototype.
- Maintenance completed: 5/10.
- M3 evidence: provenance-labeled reviewer feedback, capture-time redaction, accepted-case replay, deterministic fingerprints, excluded pending feedback and guardrail checks.
- Core flow: validate ticket → redact sensitive data → classify → resolve one current policy → route SLA/handoff or abstain → draft human-reviewed response.
- Synthetic evaluation: 5/5 fixture cases pass.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.
- M4 evidence: seven-case redaction-quality fixture, phone/token patterns, Luhn-gated card detection, clean trial, seven-claim index, external screening and synthetic privacy-feedback regression.
- M5 evidence: optional dependency-free local vector classification hint, side-by-side keyword/local-vector comparison at 5/5 on the same synthetic fixture, CLI exposure and an eight-claim evidence index. The keyword baseline remains authoritative and all privacy, policy and human-handoff gates are unchanged.

## Verification command

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m customer_service_agent.cli data/sample_ticket.json --analysis-date 2026-08-12 --output output/triage_result.json
PYTHONPATH=src python -m customer_service_agent.conversation_cli data/sample_conversation.json --analysis-date 2026-08-12 --output output/conversation_result.json
PYTHONPATH=src python -m customer_service_agent.evaluation_cli
PYTHONPATH=src python -m customer_service_agent.feedback_cli data/support_policies.json data/reviewer_feedback.json --json-output examples/feedback_replay_report.json --markdown-output examples/feedback_replay_report.md
PYTHONPATH=src python -m customer_service_agent.privacy_evaluation_cli
PYTHONPATH=src python -m customer_service_agent.trial_cli
PYTHONPATH=src python -m customer_service_agent.evaluation_cli --classification-mode local_vector
```

## Next maintenance round

M6 should evaluate one bounded improvement to the local classification hint or its review report without introducing a paid provider or weakening the deterministic policy, privacy and human-handoff gates. Any provider adapter requires separate evidence and must remain optional.

## Known limitations

- English keyword rules remain the authoritative gate; local vector mode is a deterministic review hint, not a pretrained semantic model;
- five synthetic policy records, five evaluation cases and three synthetic feedback records;
- feedback replay has no database, authentication, real reviewer identity or workflow approval integration;
- five selected redaction types rather than full DLP or measured production recall;
- deterministic reply templates and in-memory state rather than model-generated conversation or a database;
- no persistence, authentication, ticketing integration, queue or real user study;
- browser and Python implementations are mirrored manually.
