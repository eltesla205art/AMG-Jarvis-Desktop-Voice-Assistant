"""Text helpers for matching spoken commands."""

from __future__ import annotations

import re
import unicodedata

WAKE_WORDS = ("hey orion", "ok orion", "okay orion", "dis orion", "orion")


def normalize(text: str) -> str:
    """Lowercase, drop accents and punctuation — without changing the length.

    Keeping one output character per input character means a regex match on
    the normalized text points at the same span in the original text, so we
    can extract e.g. the body of a note with its accents intact.
    """
    out = []
    for ch in text:
        low = ch.lower()[:1] or ch
        base = unicodedata.normalize("NFD", low)[0]
        out.append(base if base.isalnum() or base == "." else " ")
    return "".join(out)


def phrase_pattern(phrase: str) -> re.Pattern[str]:
    """Compile a trigger phrase into a whole-word, whitespace-tolerant regex."""
    words = normalize(phrase).split()
    return re.compile(r"(?<!\w)" + r"\s+".join(map(re.escape, words)) + r"(?!\w)")


def strip_wake_word(text: str) -> str:
    norm = normalize(text)
    for wake in WAKE_WORDS:
        m = phrase_pattern(wake).match(norm.lstrip())
        if m:
            offset = len(norm) - len(norm.lstrip())
            return text[offset + m.end():].strip(" ,")
    return text


def strip_words(text: str, words: tuple[str, ...]) -> str:
    """Remove filler words (``for``, ``about``, ``sur``...) from both ends."""
    tokens = text.split()
    norm = [normalize(t).strip() for t in tokens]
    while tokens and norm[0] in words:
        tokens.pop(0)
        norm.pop(0)
    while tokens and norm[-1] in words:
        tokens.pop()
        norm.pop()
    return " ".join(tokens).strip(" ,.;:!?\"'")


def has_any_word(text: str, words: set[str]) -> bool:
    norm = normalize(text)
    return any(phrase_pattern(w).search(norm) for w in words)
