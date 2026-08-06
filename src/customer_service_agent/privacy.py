from __future__ import annotations

import re


EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PAYMENT_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
PASSWORD = re.compile(r"\b(password|passcode)\s*(?:is|:|=)\s*\S+", re.IGNORECASE)


def redact_sensitive_text(value: str) -> tuple[str, list[str]]:
    detected: list[str] = []
    redacted = value
    if EMAIL.search(redacted):
        detected.append("email")
        redacted = EMAIL.sub("[REDACTED_EMAIL]", redacted)
    if PAYMENT_CARD.search(redacted):
        detected.append("payment_card")
        redacted = PAYMENT_CARD.sub("[REDACTED_PAYMENT_CARD]", redacted)
    if PASSWORD.search(redacted):
        detected.append("password")
        redacted = PASSWORD.sub("[REDACTED_PASSWORD]", redacted)
    return redacted, detected
