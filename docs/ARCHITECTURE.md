# System Architecture

## v0.2 design goals

- zero paid runtime dependency;
- privacy filtering before policy matching;
- policy-grounded responses with visible citations;
- explicit abstention and human handoff;
- explicit in-memory states with no more than two clarification turns;
- synthetic public evidence only.

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
      R[Policy retriever]
      H[Handoff router]
    end
    subgraph Data
      T[Ticket JSON]
      K[Approved policy JSON]
      O[Triage result JSON]
    end
    T --> CLI --> V --> P --> C --> R --> H --> O
    K --> R
    T --> WEB
    K --> WEB
```

## Component responsibilities

| Component | Responsibility |
| --- | --- |
| `models.py` | Validate ticket and policy structures. |
| `privacy.py` | Redact selected email, payment-card and password patterns. |
| `agent.py` | Orchestrate classification, policy evidence, SLA and handoff. |
| `conversation.py` | Track transitions, sanitize every turn and stop clarification after two replies. |
| `evaluation.py` | Run deterministic behavior fixtures and write reports. |
| `cli.py` | Provide local ticket input and JSON output. |
| `site/` | Demonstrate supported, escalated and unsupported states without a server. |

## Future production architecture

A later service may add authenticated ticket storage, role-based policy access, persistent conversations, queues, ticketing connectors, audit events, quality monitoring and an optional grounded model adapter. None is implemented in v0.2.
