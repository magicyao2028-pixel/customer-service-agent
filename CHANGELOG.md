# Changelog

## 0.9.0 - 2026-09-01

- Added chronological reviewer-history visibility over replay/export records.
- Preserved no-ticket-text retention and no-policy-application boundaries.

## 0.8.0 - 2026-08-29

- added a deterministic replay-review export for passed, failed and excluded feedback;
- retained sanitized fingerprints only and explicitly excluded raw customer messages;
- added bounded next actions, trial evidence and regression coverage without policy or reply execution.

## 0.7.0 - 2026-08-26

- added deterministic score-margin and review-recommendation fields to the optional local-vector hint;
- marked unknown, low-confidence and narrow-margin hints for human review without changing policy resolution;
- added regression evidence while retaining privacy, handoff and no-send boundaries.

## 0.6.0 - 2026-08-24

- added an optional dependency-free local vector classification hint with explicit `keyword` and `local_vector` modes;
- kept privacy redaction, policy resolution, abstention and human handoff authoritative over the hint;
- added side-by-side evaluation reporting for both modes on the five-case synthetic fixture (5/5 each);
- exposed the mode through the service and evaluation CLIs and added regression coverage;
- expanded the evidence index to eight claims while retaining zero-cost, synthetic-data and no-production-accuracy boundaries.

## 0.5.0 - 2026-08-20

- added phone and access-token redaction while requiring Luhn validation before card classification;
- added a seven-case synthetic redaction-quality fixture whose reports retain no source messages or sensitive values;
- added a clean trial command, seven-claim evidence index and exact external-component screening;
- linked a clearly synthetic privacy requirement to implementation and deterministic regression evidence;
- retained explicit selected-pattern, non-DLP and human-review boundaries.

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
