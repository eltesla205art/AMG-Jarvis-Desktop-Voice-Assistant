"""Text helpers for matching spoken commands."""

from __future__ import annotations

import re
import unicodedata

# The wake phrase is a greeting followed by the name ("Hey Orion", "Dis Orion"),
# or the name alone at the very start ("Orion, what time is it?").
# Recognizers sometimes mishear the name, so a few close spellings count too.
WAKE_GREETINGS = ("hey", "hi", "hello", "ok", "okay", "dis", "salut", "he", "eh", "allo", "bonjour")
WAKE_NAMES = ("orion", "orien", "orian", "oreon", "o ryan", "o rion", "oh ryan")


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


def _alternation(phrases: tuple[str, ...]) -> str:
    return "|".join(r"\s+".join(map(re.escape, p.split())) for p in phrases)


_NAME = rf"(?:{_alternation(WAKE_NAMES)})(?!\w)"
_WAKE_RE = re.compile(
    rf"(?<!\w)(?:{_alternation(WAKE_GREETINGS)})\s+{_NAME}"  # "hey orion" anywhere
    rf"|^\s*{_NAME}"                                         # "orion ..." at the start
)


def find_wake_word(text: str) -> int | None:
    """Index in ``text`` just after the wake phrase, or None if it isn't there."""
    m = _WAKE_RE.search(normalize(text))
    return m.end() if m else None


def strip_wake_word(text: str) -> str:
    """Drop the wake phrase (and anything before it): "Hey Orion, play music" -> "play music"."""
    end = find_wake_word(text)
    return text if end is None else text[end:].strip(" ,.!?")


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
