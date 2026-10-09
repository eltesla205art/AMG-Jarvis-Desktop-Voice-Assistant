"""Play music from the local music folder with the system's default player."""

from __future__ import annotations

import random
from pathlib import Path

from ..platform_utils import open_path
from ..text import normalize, strip_words
from . import skill

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".opus"}
FILLER = ("some", "a", "the", "song", "track", "by", "called", "named", "music", "please",
          "de", "la", "le", "les", "du", "un", "une", "morceau", "chanson", "musique", "s", "il", "te", "plait")


def find_songs(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*")
                  if p.suffix.lower() in AUDIO_EXTENSIONS and p.is_file())


def pick_song(songs: list[Path], query: str, root: Path | None = None) -> Path | None:
    """Random song, or a random one whose path contains every word of ``query``
    (so artist/album folder names count too)."""
    if not query:
        return random.choice(songs) if songs else None
    words = normalize(query).split()

    def label(song: Path) -> str:
        rel = song.relative_to(root) if root and song.is_relative_to(root) else Path(song.name)
        return normalize(str(rel.with_suffix("")))

    matches = [s for s in songs if all(w in label(s) for w in words)]
    return random.choice(matches) if matches else None


@skill("music",
       en=["play music", "play some music", "play a song", "play song", "play the song", "play my music"],
       fr=["joue de la musique", "mets de la musique", "joue la chanson", "joue une chanson",
           "lance la musique", "mets la chanson", "musique"])
def play_music(ctx, req):
    folder = Path(ctx.config.music_dir).expanduser()
    if not folder.is_dir():
        ctx.say("music_no_dir", path=folder)
        return
    songs = find_songs(folder)
    if not songs:
        ctx.say("music_none")
        return
    query = strip_words(req.rest, FILLER)
    song = pick_song(songs, query, folder)
    if not song:
        ctx.say("music_no_match", query=query)
        return
    if open_path(song):
        ctx.say("music_playing", song=song.stem)
    else:
        ctx.say("music_open_failed")
