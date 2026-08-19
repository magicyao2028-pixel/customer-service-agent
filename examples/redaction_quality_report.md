# Redaction Quality Fixture

- Result: **7/7 cases passed**
- Source: synthetic public fixture

| Case | Expected | Detected | Original retained | Result |
| --- | --- | --- | --- | --- |
| RED-EMAIL-001 | email | email | no | PASS |
| RED-CARD-002 | payment_card | payment_card | no | PASS |
| RED-PASSWORD-003 | password | password | no | PASS |
| RED-PHONE-004 | phone | phone | no | PASS |
| RED-TOKEN-005 | access_token | access_token | no | PASS |
| RED-COMBINED-006 | email, phone | email, phone | no | PASS |
| RED-SAFE-007 | none | none | no | PASS |

## Boundary

- Reports contain case IDs and detection labels, never original message text or sensitive values.
- This exact-pattern fixture is regression evidence, not recall, precision or full DLP coverage.
