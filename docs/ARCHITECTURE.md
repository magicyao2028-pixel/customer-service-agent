# System Architecture

## v0.4 design goals

- zero paid runtime dependency;
- privacy filtering before policy matching;
- policy-grounded responses with visible citations;
- deterministic policy-version resolution using effective, review-due and supersession metadata;
- safe blocking when policy categories conflict, all versions are stale or multiple current versions remain;
- explicit abstention and human handoff;
- explicit in-memory states with no more than two clarification turns;
- synthetic public evidence only.
- provenance-labeled feedback that cannot alter policy automatically;
- deterministic replay after capture-time redaction and explicit acceptance.

## Logical architecture

```mermaid
flowchart TB
    subgraph Interface
      CLI[Python CLI]
      WEB[Static browser prototype]
    end
    subgraph Agent
      V[Ticket validator]
      P[Privacy redactor]
      C[Issue classifier]
      R[Policy version resolver]
      H[Handoff router]
      F[Feedback validator and redactor]
      RP[Accepted-case replay]
    end
    subgraph Data
      T[Ticket JSON]
      K[Approved policy JSON]
      FB[Reviewer feedback JSON]
      O[Triage result JSON]
    end
    T --> CLI --> V --> P --> C --> R --> H --> O
    K --> R
    FB --> F --> RP --> V
    T --> WEB
    K --> WEB
```

## Component responsibilities

| Component | Responsibility |
| --- | --- |
| `models.py` | Validate ticket and policy structures. |
| `privacy.py` | Redact selected email, payment-card and password patterns. |
| `agent.py` | Orchestrate classification, policy evidence, SLA and handoff. |
| `policy_resolution.py` | Select one current unsuperseded version or return a reviewable block reason. |
| `conversation.py` | Track transitions, sanitize every turn and stop clarification after two replies. |
| `evaluation.py` | Run deterministic behavior fixtures and write reports. |
| `feedback.py` | Validate feedback provenance/disposition, redact tickets, replay accepted cases and check guardrails. |
| `cli.py` | Provide local ticket input and JSON output. |
| `site/` | Demonstrate supported, escalated and unsupported states without a server. |

## Future production architecture

A later service may add authenticated ticket storage, role-based policy access, persistent conversations, queues, ticketing connectors, audit events, quality monitoring and an optional grounded model adapter. None is implemented in v0.4.
