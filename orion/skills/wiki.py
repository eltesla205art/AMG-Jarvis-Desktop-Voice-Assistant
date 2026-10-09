"""Wikipedia lookups, read back as a short spoken summary.

Uses the public MediaWiki API directly (no extra dependency): one request
searches for the best page and returns its plain-text introduction.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request

from .. import __version__
from ..text import strip_words
from . import skill

API = "https://{lang}.wikipedia.org/w/api.php"
# Wikimedia asks API clients to identify themselves.
USER_AGENT = f"ORION-Voice-Assistant/{__version__} (desktop voice assistant)"
FILLER = ("search", "wikipedia", "on", "for", "about", "the", "me", "tell", "who", "what", "is", "was",
          "sur", "cherche", "recherche", "de", "du", "des", "a", "propos", "moi", "qui", "est",
          "le", "la", "les", "l")


class WikipediaUnavailable(Exception):
    pass


def first_sentences(text: str, count: int = 2) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:count])


def fetch_summary(query: str, lang: str, sentences: int = 2, timeout: float = 8.0) -> str | None:
    """Return a short summary of the best-matching article, or None if not found."""
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "generator": "search", "gsrsearch": query, "gsrlimit": "1",
        "prop": "extracts", "exintro": "1", "explaintext": "1", "redirects": "1",
    }
    url = API.format(lang=lang) + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise WikipediaUnavailable(str(exc)) from exc
    return parse_summary(data, sentences)


def parse_summary(data: dict, sentences: int = 2) -> str | None:
    pages = data.get("query", {}).get("pages", [])
    for page in pages:
        extract = (page.get("extract") or "").strip()
        if extract:
            return first_sentences(extract, sentences)
    return None


@skill("wikipedia",
       en=["wikipedia", "who is", "who was", "what is", "tell me about", "search wikipedia for"],
       fr=["wikipedia", "qui est", "qui etait", "c est quoi", "qu est ce que", "parle moi de",
           "cherche sur wikipedia"])
def wikipedia(ctx, req):
    query = strip_words(req.rest or req.before, FILLER) or ctx.ask("wiki_what")
    if not query:
        return
    ctx.say("wiki_searching", query=query)
    try:
        summary = fetch_summary(query, ctx.lang)
    except WikipediaUnavailable:
        ctx.say("wiki_offline")
        return
    if summary:
        ctx.say("according_wiki", summary=summary)
    else:
        ctx.say("wiki_none", query=query)
