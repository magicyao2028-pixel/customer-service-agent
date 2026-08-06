# Evaluation Plan

## Current synthetic fixture

The five public cases cover:

- damaged product → routine triage under `POL-RET-001`;
- delivery delay → routine triage under `POL-DEL-002`;
- safety incident → critical duty-manager handoff under `POL-SAFE-003`;
- refund request → routine triage under `POL-REF-004`;
- unsupported parking question → no-policy abstention and support-lead handoff.

The fixture checks status, category, handoff and policy ID. A 5/5 result is regression evidence for engineered public examples, not production accuracy.

## Future validation

A controlled private evaluation should measure classification accuracy by category, critical-case recall, false escalation, policy-citation correctness, redaction recall, handoff completeness and human edit rate. Production claims require a reviewed private policy set and representative, privacy-approved tickets.
