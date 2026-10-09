"""Jokes, in English (via pyjokes when installed) and French."""

from __future__ import annotations

import random

from . import skill

JOKES = {
    "en": [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "I told my computer I needed a break, and it said: no problem, I'll go to sleep.",
        "Why did the astronaut break up with the moon? It needed space.",
        "How does the solar system hold up its pants? With an asteroid belt.",
        "Why don't scientists trust atoms? Because they make up everything.",
    ],
    "fr": [
        "Pourquoi les plongeurs plongent-ils toujours en arrière ? Parce que sinon, ils tombent dans le bateau.",
        "Qu'est-ce qu'un crocodile qui surveille la pharmacie ? Un Lacoste garde.",
        "Pourquoi les programmeurs confondent Halloween et Noël ? Parce que oct 31 égale dec 25.",
        "Que dit une imprimante dans l'eau ? J'ai papier.",
        "Pourquoi les poissons détestent l'ordinateur ? Parce qu'ils ont peur du Net.",
        "Quel est le comble pour un électricien ? De ne pas être au courant.",
    ],
}


def get_joke(lang: str) -> str:
    if lang == "en" and random.random() < 0.6:
        try:
            import pyjokes
            return pyjokes.get_joke(language="en", category="neutral")
        except Exception:  # optional dependency; fall back to built-ins
            pass
    return random.choice(JOKES.get(lang, JOKES["en"]))


@skill("joke",
       en=["joke", "tell me a joke", "make me laugh", "something funny"],
       fr=["blague", "raconte une blague", "raconte moi une blague", "fais moi rire"])
def tell_joke(ctx, req):
    ctx.say_text(get_joke(ctx.lang))
