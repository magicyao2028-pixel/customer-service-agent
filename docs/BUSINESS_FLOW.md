# Business Workflow

```mermaid
flowchart TB
    I[Incoming ticket] --> V{Valid channel and message?}
    V -->|No| X[Return clear validation error]
    V -->|Yes| P[Redact selected sensitive text]
    P --> C[Classify with explicit rules]
    C --> K{One current policy resolved?}
    K -->|No: missing, stale or conflict| A[Assign support lead and abstain]
    K -->|Yes| R[Attach policy version, evidence and SLA]
    R --> E{Critical or escalation trigger?}
    E -->|Yes| H[Priority human handoff]
    E -->|No| Q[Routine support queue]
    H --> D[Human reviews reply draft]
    Q --> D
```

## Role boundaries

| Role | Responsibility |
| --- | --- |
| Customer Service Agent workflow | Sanitizes, classifies, retrieves policy and prepares the packet. |
| Support specialist | Verifies evidence, edits the draft and owns the customer interaction. |
| Duty manager | Reviews safety, fraud or explicit escalation cases. |
| Policy owner | Maintains policy content, categories, evidence and SLAs. |
| Authorized business owner | Approves refunds, compensation and other high-impact actions. |

The workflow never sends a reply, promises a refund or makes a medical conclusion.

Policy owners must provide effective dates, review deadlines and explicit supersession links. A policy conflict is treated as a governance exception, not as permission for the Agent to guess.
