# Security and Governance

- Public tickets and policies are synthetic.
- The workflow makes no network request and needs no API key.
- Selected email, Luhn-valid payment-card, password, phone and access-token patterns are redacted before classification and output.
- The original message is not included in the result.
- No response, refund, compensation or external action is executed.
- Safety incidents and unsupported requests require human handoff.
- The v1.2 Python conversation flow re-triages each processed sanitized clarification reply before order-ID and turn-limit decisions. Supported escalation therefore takes priority over missing evidence, including on the last permitted turn. This is a keyword-based offline routing check, not complete incident detection or an external notification.
- Stale policies, category conflicts and unresolved current versions are blocked rather than guessed.
- The analysis date and version-selection evidence are included in the output for review.

The redactor is not a complete data-loss-prevention system. A production service would need comprehensive data classification, authenticated users, role-based policy access, encryption, retention and deletion controls, tamper-evident audit logs, incident response and independent security testing.

The v0.5 quality report never includes fixture messages or sensitive values. It contains only synthetic case IDs, expected/detected labels and pass status; this remains exact-pattern regression evidence rather than measured production recall.
