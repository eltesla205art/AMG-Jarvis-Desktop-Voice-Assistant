"""Time and date."""

from __future__ import annotations

import datetime as dt

from ..i18n import MONTHS, WEEKDAYS
from . import skill


def format_time(now: dt.datetime, lang: str) -> str:
    if lang == "fr":
        return f"{now.hour} h {now.minute:02d}" if now.minute else f"{now.hour} heures"
    hour12 = now.hour % 12 or 12
    suffix = "AM" if now.hour < 12 else "PM"
    return f"{hour12}:{now.minute:02d} {suffix}"


def format_date(now: dt.datetime, lang: str) -> str:
    weekday = WEEKDAYS[lang][now.weekday()]
    month = MONTHS[lang][now.month - 1]
    if lang == "fr":
        day = "1er" if now.day == 1 else str(now.day)
        return f"{weekday} {day} {month} {now.year}"
    return f"{weekday}, {month} {now.day}, {now.year}"


@skill("time",
       en=["time", "what time", "the time", "current time"],
       fr=["heure", "quelle heure", "l heure"])
def tell_time(ctx, req):
    ctx.say("time", time=format_time(dt.datetime.now(), ctx.lang))


@skill("date",
       en=["date", "the date", "what day", "today s date", "day is it"],
       fr=["date", "quel jour", "quelle date", "la date", "on est quel jour"])
def tell_date(ctx, req):
    ctx.say("date", date=format_date(dt.datetime.now(), ctx.lang))
