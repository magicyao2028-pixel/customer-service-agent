# Policy Resolution

## Decision contract

The resolver receives the sanitized ticket text, validated synthetic policy records and an explicit analysis date. It returns exactly one of four statuses:

| Status | Meaning | Automated draft |
| --- | --- | --- |
| `selected` | One current unsuperseded policy remains. | Allowed, but human approval is still required. |
| `no_policy` | No policy keyword matches the request. | Blocked. |
| `policy_stale` | Matching policies exist, but none is within its effective and review window. | Blocked. |
| `policy_conflict` | Best categories tie or more than one current version remains. | Blocked. |

## Resolution order

1. Match explicit keywords against the already-redacted message.
2. Compare the best keyword score by category; tied categories block selection.
3. Exclude records that are not yet effective or whose review deadline has passed.
4. Exclude a current record when another current record explicitly supersedes it.
5. Select only when exactly one current unsuperseded record remains.

The result exposes the analysis date, matched terms, candidate policy IDs and every excluded policy with a reason. Supersession links must reference an existing policy in the same category and cannot form a cycle.

## Deliberate limitations

- Dates are day-level ISO values and do not model time zones or publication timestamps.
- Keyword matching is deterministic, not semantic.
- There is no policy-authoring approval workflow or persistent audit database.
- Review deadlines are treated as hard blocks in this prototype; a production policy owner may define a different controlled fallback.
