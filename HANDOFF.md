# Handoff

## Current state

- Release stage: v1.0 trial-readiness prototype.
- Maintenance completed: 9/10.
- M3 evidence: provenance-labeled reviewer feedback, capture-time redaction, accepted-case replay, deterministic fingerprints, excluded pending feedback and guardrail checks.
- Core flow: validate ticket → redact sensitive data → classify → resolve one current policy → route SLA/handoff or abstain → draft human-reviewed response.
- Synthetic evaluation: 5/5 fixture cases pass.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.
- M4 evidence: seven-case redaction-quality fixture, phone/token patterns, Luhn-gated card detection, clean trial, seven-claim index, external screening and synthetic privacy-feedback regression.
- M5 evidence: optional dependency-free local vector classification hint, side-by-side keyword/local-vector comparison at 5/5 on the same synthetic fixture, CLI exposure and an eight-claim evidence index. The keyword baseline remains authoritative and all privacy, policy and human-handoff gates are unchanged.
- M6 evidence: local-vector hints now expose score margin and a review recommendation for low-confidence, narrow-margin or unknown messages; the hint remains non-authoritative and no automated reply or policy decision changes.
- M7 evidence: a deterministic review-report export summarizes replayed and excluded feedback with bounded next actions while retaining no raw customer messages and applying no policy decisions.
- M8 evidence: a chronological reviewer-history summary exposes status counts while retaining no ticket text and applying no policy decisions.

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

M10 can add bounded queue-aging and closure-state visibility without introducing a paid provider or weakening the deterministic policy, privacy and human-handoff gates. Any provider adapter requires separate evidence and must remain optional.

## M9 evidence

- Sanitized review history is organized into a priority-ordered owner follow-up queue.
- Queue items retain only feedback IDs, status and bounded next actions; replies, policy changes and customer-message retention remain disabled.

## Known limitations

- English keyword rules remain the authoritative gate; local vector mode is a deterministic review hint, not a pretrained semantic model;
- five synthetic policy records, five evaluation cases and three synthetic feedback records;
- feedback replay has no database, authentication, real reviewer identity or workflow approval integration;
- five selected redaction types rather than full DLP or measured production recall;
- deterministic reply templates and in-memory state rather than model-generated conversation or a database;
- no persistence, authentication, ticketing integration, queue or real user study;
- browser and Python implementations are mirrored manually.
