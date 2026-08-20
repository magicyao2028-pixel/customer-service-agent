from __future__ import annotations

import re


EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PAYMENT_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
PASSWORD = re.compile(r"\b(password|passcode)\s*(?:is|:|=)\s*\S+", re.IGNORECASE)
PHONE = re.compile(
    r"(?<![\w\d])(?:(?:\+?\d{1,3}[ -])?(?:\(?\d{2,4}\)?[ -]){2,3}\d{3,4}|\+?\d{10,15})(?![\w\d])"
)
ACCESS_TOKEN = re.compile(
    r"\b(?:bearer|access[_ -]?token|api[_ -]?key)\s*(?:is|:|=)?\s*[A-Za-z0-9._~-]{8,}\b",
    re.IGNORECASE,
)


def redact_sensitive_text(value: str) -> tuple[str, list[str]]:
    detected: list[str] = []
    redacted = value
    if EMAIL.search(redacted):
        detected.append("email")
        redacted = EMAIL.sub("[REDACTED_EMAIL]", redacted)
    if ACCESS_TOKEN.search(redacted):
        detected.append("access_token")
        redacted = ACCESS_TOKEN.sub("[REDACTED_ACCESS_TOKEN]", redacted)
    card_found = False

    def replace_card(match: re.Match[str]) -> str:
        nonlocal card_found
        digits = "".join(character for character in match.group(0) if character.isdigit())
        if _passes_luhn(digits):
            card_found = True
            return "[REDACTED_PAYMENT_CARD]"
        return match.group(0)

    redacted = PAYMENT_CARD.sub(replace_card, redacted)
    if card_found:
        detected.append("payment_card")
    if PASSWORD.search(redacted):
        detected.append("password")
        redacted = PASSWORD.sub("[REDACTED_PASSWORD]", redacted)
    if PHONE.search(redacted):
        detected.append("phone")
        redacted = PHONE.sub("[REDACTED_PHONE]", redacted)
    return redacted, detected


def _passes_luhn(digits: str) -> bool:
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, character in enumerate(digits):
        number = int(character)
        if index % 2 == parity:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0
