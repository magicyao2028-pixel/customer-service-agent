from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .models import SupportPolicy


@dataclass(frozen=True)
class PolicyResolution:
    status: str
    policy: SupportPolicy | None
    matched_keywords: tuple[str, ...]
    category: str
    candidate_policy_ids: tuple[str, ...]
    excluded_policies: tuple[dict[str, str], ...]
    reason: str

    def to_dict(self, analysis_date: str) -> dict[str, object]:
        return {
            "analysis_date": analysis_date,
            "status": self.status,
            "category": self.category,
            "selected_policy_id": self.policy.policy_id if self.policy else None,
            "candidate_policy_ids": list(self.candidate_policy_ids),
            "excluded_policies": list(self.excluded_policies),
            "reason": self.reason,
        }


def resolve_policy(
    policies: Iterable[SupportPolicy], message: str, analysis_date: str
) -> PolicyResolution:
    on_date = _analysis_date(analysis_date)
    lowered = message.casefold()
    matches: list[tuple[SupportPolicy, tuple[str, ...]]] = []
    for policy in policies:
        terms = tuple(term for term in policy.keywords if term.casefold() in lowered)
        if terms:
            matches.append((policy, terms))
    if not matches:
        return PolicyResolution(
            "no_policy", None, (), "unknown", (), (), "no policy keyword matched"
        )

    category_scores: dict[str, int] = {}
    for policy, terms in matches:
        category_scores[policy.category] = max(category_scores.get(policy.category, 0), len(terms))
    best_score = max(category_scores.values())
    best_categories = sorted(
        category for category, score in category_scores.items() if score == best_score
    )
    if len(best_categories) > 1:
        candidates = tuple(sorted(policy.policy_id for policy, _ in matches if policy.category in best_categories))
        return PolicyResolution(
            "policy_conflict",
            None,
            (),
            "multiple",
            candidates,
            (),
            "equally supported policy categories require human selection",
        )

    category = best_categories[0]
    category_policies = [policy for policy in policies if policy.category == category]
    matched_by_id = {policy.policy_id: terms for policy, terms in matches}
    excluded: list[dict[str, str]] = []
    active: list[SupportPolicy] = []
    for policy in category_policies:
        if on_date < date.fromisoformat(policy.effective_from):
            excluded.append({"policy_id": policy.policy_id, "reason": "not_yet_effective"})
        elif on_date > date.fromisoformat(policy.review_due_at):
            excluded.append({"policy_id": policy.policy_id, "reason": "review_overdue"})
        else:
            active.append(policy)

    if not active:
        return PolicyResolution(
            "policy_stale",
            None,
            (),
            category,
            tuple(sorted(policy.policy_id for policy in category_policies)),
            tuple(sorted(excluded, key=lambda item: item["policy_id"])),
            "no current policy version is within its effective review window",
        )

    superseded = {policy_id for policy in active for policy_id in policy.supersedes_policy_ids}
    current = [policy for policy in active if policy.policy_id not in superseded]
    for policy in active:
        if policy.policy_id in superseded:
            excluded.append({"policy_id": policy.policy_id, "reason": "superseded"})

    if len(current) != 1:
        return PolicyResolution(
            "policy_conflict",
            None,
            (),
            category,
            tuple(sorted(policy.policy_id for policy in current)),
            tuple(sorted(excluded, key=lambda item: item["policy_id"])),
            "multiple current policies remain without a supersession decision",
        )

    selected = current[0]
    selected_terms = matched_by_id.get(selected.policy_id, ())
    if not selected_terms:
        selected_terms = max(
            (terms for policy_id, terms in matched_by_id.items() if any(
                item.policy_id == policy_id and item.category == category for item in category_policies
            )),
            key=len,
        )
    return PolicyResolution(
        "selected",
        selected,
        selected_terms,
        category,
        tuple(sorted(policy.policy_id for policy in category_policies)),
        tuple(sorted(excluded, key=lambda item: item["policy_id"])),
        "one current unsuperseded policy selected",
    )


def _analysis_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("analysis_date must use YYYY-MM-DD") from exc
