"""Quick notes appended to a plain text file."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from . import skill

READ_LAST = 3


@skill("take_note",
       en=["take a note", "make a note", "write a note", "write down", "note that",
           "remember that", "save a note", "take note"],
       fr=["prends une note", "prend une note", "note que", "ecris une note", "ecris",
           "souviens toi que", "prendre une note", "nouvelle note"])
def take_note(ctx, req):
    note = req.rest or ctx.ask("note_what")
    if not note:
        ctx.say("note_cancelled")
        return
    path = Path(ctx.config.notes_file).expanduser()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(f"[{dt.datetime.now():%Y-%m-%d %H:%M}] {note}\n")
    except OSError:
        ctx.say("note_failed")
        return
    ctx.ui.log("info", str(path))
    ctx.say("note_saved")


@skill("read_notes",
       en=["read my notes", "read notes", "read the notes", "what are my notes", "show my notes"],
       fr=["lis mes notes", "lire mes notes", "lis les notes", "quelles sont mes notes"])
def read_notes(ctx, req):
    path = Path(ctx.config.notes_file).expanduser()
    try:
        lines = [l.split("] ", 1)[-1] for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError:
        lines = []
    if not lines:
        ctx.say("notes_none")
        return
    ctx.say("notes_reading", notes=". ".join(lines[-READ_LAST:]))
