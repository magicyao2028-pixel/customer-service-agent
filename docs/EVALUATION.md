# Evaluation Plan

## Current synthetic fixture

The five public cases cover:

- damaged product → routine triage under `POL-RET-001`;
- delivery delay → routine triage under `POL-DEL-002`;
- safety incident → critical duty-manager handoff under `POL-SAFE-003`;
- refund request → routine triage under `POL-REF-004`;
- unsupported parking question → no-policy abstention and support-lead handoff.

The fixture checks status, category, handoff and policy ID. A 5/5 result is regression evidence for engineered public examples, not production accuracy.

## Reviewer-feedback replay

v0.4 adds a separate feedback batch with explicit provenance, reviewer alias, disposition, rationale and recorded date. Only `accepted_for_replay` records execute. Pending or rejected suggestions remain visible but cannot edit policy or Agent behavior. Ticket text is redacted before it becomes a replay record, and the report retains only the sanitized case fingerprint, redaction categories, expected behavior, actual behavior and checks.

Every accepted replay verifies status, category, handoff, policy citation, original-message non-retention, customer-reply approval and policy-block handoff. The public batch is wholly synthetic: its 2/2 result demonstrates deterministic guardrail preservation, not real feedback quality or production performance.

## Future validation

A controlled private evaluation should measure classification accuracy by category, critical-case recall, false escalation, policy-citation correctness, redaction recall, handoff completeness and human edit rate. Production claims require a reviewed private policy set and representative, privacy-approved tickets.
