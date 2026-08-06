# Security and Governance

- Public tickets and policies are synthetic.
- The workflow makes no network request and needs no API key.
- Selected email, payment-card and password patterns are redacted before classification and output.
- The original message is not included in the result.
- No response, refund, compensation or external action is executed.
- Safety incidents and unsupported requests require human handoff.

The redactor is not a complete data-loss-prevention system. A production service would need comprehensive data classification, authenticated users, role-based policy access, encryption, retention and deletion controls, tamper-evident audit logs, incident response and independent security testing.
