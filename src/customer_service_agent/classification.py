from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .models import SupportPolicy


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "i", "in", "is", "it", "of", "on", "or", "the", "to", "what", "with"}


def _features(value: str) -> list[str]:
    features: list[str] = []
    for token in TOKEN_PATTERN.findall(value.casefold()):
        if token in STOP_WORDS:
            continue
        features.append(f"t:{token}")
        if len(token) >= 3:
            features.extend(f"c:{token[index:index + 3]}" for index in range(len(token) - 2))
    return features


class LocalLanguageClassificationAdapter:
    """Dependency-free local vector classifier used only as a reviewable hint."""

    def __init__(self, policies: Iterable[SupportPolicy], dimension: int = 256) -> None:
        self.policies = tuple(policies)
        if not self.policies:
            raise ValueError("At least one policy is required")
        if dimension < 32:
            raise ValueError("dimension must be at least 32")
        self.dimension = dimension

    def _encode(self, value: str) -> list[float]:
        vector = [0.0] * self.dimension
        for feature, count in Counter(_features(value)).items():
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            vector[index] += (1.0 if digest[4] & 1 else -1.0) * count
        return vector

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(item * item for item in left))
        right_norm = math.sqrt(sum(item * item for item in right))
        if not left_norm or not right_norm:
            return 0.0
        return max(0.0, numerator / (left_norm * right_norm))

    def predict(self, message: str) -> dict[str, object]:
        query_features = set(_features(message))
        query_vector = self._encode(message)
        scores: list[tuple[str, float, int]] = []
        for policy in self.policies:
            keywords = " ".join(policy.keywords)
            keyword_features = set(_features(keywords))
            overlap = len(query_features.intersection(keyword_features))
            score = self._cosine(query_vector, self._encode(keywords)) if overlap else 0.0
            scores.append((policy.category, score, overlap))
        by_category: dict[str, tuple[float, int]] = {}
        for category, score, overlap in scores:
            current = by_category.get(category, (0.0, 0))
            by_category[category] = (max(current[0], score), max(current[1], overlap))
        ranked = sorted(by_category.items(), key=lambda item: (-item[1][0], -item[1][1], item[0]))
        if not ranked or ranked[0][1][0] <= 0:
            return {"category": "unknown", "confidence": "none", "scores": []}
        top_category, (top_score, top_overlap) = ranked[0]
        confidence = "high" if top_score >= 0.55 and top_overlap >= 2 else "medium" if top_score >= 0.25 else "low"
        return {
            "category": top_category,
            "confidence": confidence,
            "score": round(top_score, 4),
            "matched_feature_count": top_overlap,
            "scores": [
                {"category": category, "score": round(score, 4), "matched_feature_count": overlap}
                for category, (score, overlap) in ranked
            ],
        }
