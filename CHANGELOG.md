# Changelog

## 0.4.0 - 2026-08-15

- added structured reviewer feedback with provenance, attribution alias, disposition and rationale validation;
- redacted accepted feedback tickets before normalized replay and added deterministic sanitized-ticket fingerprints;
- replayed only explicitly accepted records under a fixed policy-analysis date;
- verified status, category, policy, handoff, privacy, reply approval and policy-block boundaries;
- preserved a pending automation request without allowing feedback to mutate policy or behavior;
- added two reproducible replay reports and seven regression tests.
- tightened accepted-case type validation and ISO feedback-date validation after independent review.

## 0.3.0 - 2026-08-12

- added effective, review-due and supersession metadata to validated policies;
- added deterministic current-policy resolution with superseded-version evidence;
- added safe abstention and human handoff for category conflicts, unresolved versions and stale policies;
- added an explicit `POLICY_BLOCKED` conversation state for policy-governance failures;
- added a reproducible analysis date, policy-resolution documentation and four regression tests.

## 0.2.0 - 2026-08-07

- added explicit conversation states and auditable state-transition timelines;
- added a missing-order-ID clarification flow capped at two customer replies;
- added automatic human handoff when the clarification limit is exhausted;
- preserved immediate escalation for critical cases and abstention for unmatched policy;
- redacted sensitive data on every turn and added a transcript CLI plus seven tests.

## 0.1.0 - 2026-08-06

- added validated synthetic support tickets and four approved policies;
- added sensitive-data redaction, deterministic classification and policy citations;
- added critical and keyword-triggered human handoff with explicit SLAs;
- added no-policy abstention and human-approved response drafts;
- added a nine-test suite and reproducible five-case evaluation report;
- added product documentation, ten-round maintenance plan and static browser prototype.
