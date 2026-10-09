"""Skill registry: every voice command O.R.I.O.N. understands.

Adding a command is one function in any module of this package::

    from orion.skills import skill

    @skill("weather", en=["weather", "forecast"], fr=["météo"])
    def weather(ctx, req):
        ctx.say_text("It's sunny!")

Modules in this folder are imported automatically. When several trigger
phrases match, the longest one wins, so "open youtube" can coexist with
"search youtube for ...".
"""

from __future__ import annotations

import importlib
import pkgutil
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from ..text import phrase_pattern

if TYPE_CHECKING:
    from ..assistant import Assistant

    Handler = Callable[[Assistant, "Request"], None]


@dataclass
class Skill:
    name: str
    handler: "Handler"
    triggers: dict[str, list[re.Pattern[str]]]


@dataclass
class Request:
    """A recognised command, handed to the skill that matched it."""

    raw: str           # what the user said, as transcribed
    lang: str          # language the command was given in ("en"/"fr")
    match: re.Match[str]  # where the trigger phrase was found

    @property
    def rest(self) -> str:
        """Everything said after the trigger, e.g. the song in "play music Daft Punk"."""
        return self.raw[self.match.end():].strip(" ,.;:!?\"'")

    @property
    def before(self) -> str:
        """Everything said before the trigger."""
        return self.raw[:self.match.start()].strip(" ,.;:!?\"'")


@dataclass
class Match:
    skill: Skill
    lang: str
    match: re.Match[str]

    @property
    def score(self) -> int:
        return len(self.match.group(0))


REGISTRY: list[Skill] = []


def skill(name: str, *, en: list[str], fr: list[str]):
    """Decorator registering ``handler(ctx, req)`` for the given trigger phrases."""
    def register(handler: "Handler") -> "Handler":
        REGISTRY.append(Skill(name, handler, {
            "en": [phrase_pattern(p) for p in en],
            "fr": [phrase_pattern(p) for p in fr],
        }))
        return handler
    return register


def find_skill(norm_text: str, prefer: str = "en") -> Match | None:
    """Return the best match for already-normalized text, or None."""
    best: Match | None = None
    for sk in REGISTRY:
        for lang, patterns in sk.triggers.items():
            for pattern in patterns:
                m = pattern.search(norm_text)
                if not m:
                    continue
                cand = Match(sk, lang, m)
                if (best is None or cand.score > best.score
                        or (cand.score == best.score and lang == prefer != best.lang)):
                    best = cand
    return best


def load_all() -> None:
    """Import every module in this package so their @skill decorators run."""
    for info in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{info.name}")
