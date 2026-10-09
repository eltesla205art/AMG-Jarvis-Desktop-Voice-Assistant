"""Open websites and run Google / YouTube searches."""

from __future__ import annotations

import re
from urllib.parse import quote_plus

from ..platform_utils import open_url
from ..text import normalize, strip_words
from . import skill

# Spoken name -> URL. Anything else is guessed as <name>.com.
KNOWN_SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "wikipedia": "https://www.wikipedia.org",
    "wikipedia en francais": "https://fr.wikipedia.org",
    "github": "https://github.com",
    "stack overflow": "https://stackoverflow.com",
    "stackoverflow": "https://stackoverflow.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "spotify": "https://open.spotify.com",
    "google maps": "https://maps.google.com",
    "maps": "https://maps.google.com",
    "claude": "https://claude.ai",
}

OPEN_VERBS = ("open", "go", "to", "launch", "navigate", "ouvre", "ouvrir", "va", "aller", "sur", "lance")
FILLER = ("the", "website", "site", "web", "page", "please", "for", "me", "up",
          "le", "la", "les", "l", "site", "internet", "s", "il", "te", "plait", "vous", "plaît")
SEARCH_FILLER = ("for", "about", "on", "the", "web", "internet", "google", "youtube",
                 "sur", "pour", "de", "des", "du", "le", "la", "les", "a", "propos")


def resolve_site(spoken: str) -> tuple[str, str] | None:
    """Turn "github", "github dot com" or "lemonde.fr" into (label, url)."""
    name = strip_words(spoken, FILLER)
    if not name:
        return None
    key = " ".join(normalize(name).split())
    if key in KNOWN_SITES:
        return name, KNOWN_SITES[key]
    # "example dot com" / "exemple point fr" -> example.com
    domain = re.sub(r"\s+(dot|point)\s+", ".", key)
    if "." not in domain:
        domain = domain.replace(" ", "") + ".com"
    domain = domain.replace(" ", "")
    if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", domain):
        return None
    return domain, f"https://{domain}"


# Popular sites get their own triggers so "open google" beats the shorter
# "google"-style triggers of the search skills.
_POPULAR = ("youtube", "google", "wikipedia", "gmail", "github")


@skill("open_website",
       en=["open", "go to", "launch", "open website", "navigate to", *(f"open {s}" for s in _POPULAR)],
       fr=["ouvre", "ouvrir", "va sur", "lance", "aller sur", *(f"ouvre {s}" for s in _POPULAR)])
def open_website(ctx, req):
    # Drop the verb but keep a site name that is part of the trigger.
    target = strip_words(req.raw[req.match.start():], OPEN_VERBS) or ctx.ask("which_site")
    site = resolve_site(target) if target else None
    if not site:
        ctx.say("not_understood")
        return
    label, url = site
    if open_url(url):
        ctx.say("opening", site=label)
    else:
        ctx.say("browser_failed")


@skill("google_search",
       en=["search for", "search google for", "google search", "search the web for", "look up", "google for"],
       fr=["cherche", "recherche", "cherche sur google", "recherche sur google"])
def google_search(ctx, req):
    query = strip_words(req.rest, SEARCH_FILLER) or ctx.ask("what_search")
    if not query:
        return
    if open_url(f"https://www.google.com/search?q={quote_plus(query)}"):
        ctx.say("searching_google", query=query)
    else:
        ctx.say("browser_failed")


@skill("youtube_search",
       en=["search youtube for", "youtube search", "on youtube", "play on youtube"],
       fr=["cherche sur youtube", "sur youtube", "recherche sur youtube"])
def youtube_search(ctx, req):
    # "play daft punk on youtube": the query comes before the trigger.
    query = strip_words(req.rest or req.before, SEARCH_FILLER + ("play", "joue", "mets", "watch",
                                                              "search", "cherche", "recherche"))
    url = (f"https://www.youtube.com/results?search_query={quote_plus(query)}"
           if query else KNOWN_SITES["youtube"])
    if not open_url(url):
        ctx.say("browser_failed")
    elif query:
        ctx.say("searching_youtube", query=query)
    else:
        ctx.say("opening", site="YouTube")
