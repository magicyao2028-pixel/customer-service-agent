# Product Requirements Document

## 1. Document control

| Field | Value |
| --- | --- |
| Product | Customer Service Agent |
| Version | 0.4 |
| Status | Product-validation MVP |
| Primary user | Support lead or customer-operations specialist in a small or medium-sized business |
| Public data policy | Synthetic tickets and policies only |

## 2. Problem statement

Support requests arrive through several channels with inconsistent classification, evidence collection and escalation. A useful AI application must not invent policy, expose sensitive data or delay urgent cases.

## 3. Product hypothesis

If each ticket passes through one transparent privacy, policy and handoff workflow, a support lead can review more consistent case packets and identify critical exceptions earlier.

This hypothesis has not been validated with real support users. v0.4 verifies deterministic workflow and governed synthetic-feedback replay only.

### v0.3 maintenance scope

- validate effective, review-due and supersession metadata;
- select one current unsuperseded policy version on a reproducible analysis date;
- block the workflow when categories tie, all relevant versions are stale or multiple versions remain current;
- expose selected, candidate and excluded policy IDs for human review.

### v0.4 maintenance scope

- capture feedback with provenance, reviewer alias, disposition and rationale;
- redact accepted feedback tickets before replay and avoid retaining original text in the normalized record;
- replay only explicitly accepted cases under a fixed analysis date;
- verify status, category, policy, handoff, reply approval, privacy and policy-block boundaries;
- retain pending and rejected suggestions without changing policy or Agent behavior.

## 4. v0.1 scope

### In scope

1. Validate one chat, email or marketplace ticket.
2. Redact common email, payment-card and password patterns.
3. Classify four synthetic issue categories using explicit rules.
4. Attach one approved policy, evidence list, owner and SLA.
5. Escalate safety incidents and configured trigger phrases.
6. Abstain when no approved policy matches.
7. Produce a response draft and handoff packet for human approval.
8. Preserve a five-step execution trace.

### Out of scope

- autonomous customer replies or refunds;
- semantic classification or generative conversation;
- real tickets, personal data or private company policy;
- ticketing-system integration, accounts, queues or persistence;
- medical, legal or compensation decisions;
- measured customer or handling-time outcomes.

## 5. Functional requirements

| ID | Requirement | Priority | Acceptance criterion |
| --- | --- | --- | --- |
| FR-01 | Validate ticket | Must | Unsupported channels and blank fields fail clearly. |
| FR-02 | Redact sensitive text | Must | Selected email, card and password values do not appear downstream. |
| FR-03 | Classify issue | Must | Known synthetic cases map to the expected category. |
| FR-04 | Cite policy | Must | Supported responses include policy ID, title and update date. |
| FR-05 | Escalate critical case | Must | Safety incidents route to the duty manager within 15 minutes. |
| FR-06 | Abstain | Must | Unsupported requests receive no fabricated policy citation. |
| FR-07 | Require approval | Must | Every customer-facing draft states that human approval is required. |
| FR-08 | Export JSON | Should | CLI writes one structured triage result. |
| FR-09 | Bound clarification | Must | Missing order ID triggers no more than two clarification replies. |
| FR-10 | Preserve urgent routing | Must | Critical and unsupported cases do not wait in the routine clarification loop. |
| FR-11 | Resolve current policy | Must | A supported response cites one effective, in-review, unsuperseded policy. |
| FR-12 | Block ambiguity | Must | Category ties, stale policies and unresolved versions abstain and require a support lead. |
| FR-13 | Expose resolution evidence | Must | Output includes analysis date, candidate IDs and excluded-version reasons. |
| FR-14 | Govern feedback | Must | Unknown provenance, duplicate IDs and incomplete accepted records fail validation. |
| FR-15 | Replay safely | Must | Only accepted feedback executes after redaction under the current reviewed policy set. |
| FR-16 | Preserve guardrails | Must | Replay cannot bypass policy blocking, human handoff or reply approval. |
| FR-17 | Separate evidence from change | Must | Pending or rejected feedback remains excluded and cannot mutate policy automatically. |

## 6. Release gate

The public v0.4 must pass all deterministic tests and both accepted replay cases, preserve privacy, abstention, bounded clarification, urgent routing, policy blocking and human approval, use only synthetic data and clearly state that feedback does not change policy automatically.
