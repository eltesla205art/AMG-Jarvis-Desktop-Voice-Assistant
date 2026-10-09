"""Settings with sensible defaults, optionally overridden by a JSON file.

Copy ``orion_config.example.json`` to ``orion_config.json`` next to
``orion.py`` and change only the keys you care about.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, fields
from pathlib import Path

from . import platform_utils

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_FILE = PROJECT_ROOT / "orion_config.json"
DATA_DIR = Path.home() / "ORION"

SUPPORTED_LANGUAGES = ("en", "fr")


@dataclass
class Config:
    # How O.R.I.O.N. addresses you, e.g. "Andre". Empty = no name.
    user_name: str = ""
    # "auto" detects English or French on every command; "en"/"fr" pins one.
    language: str = "auto"
    # Language used for the greeting and for anything said before you speak.
    default_language: str = "en"
    music_dir: str = field(default_factory=lambda: str(platform_utils.music_dir()))
    notes_file: str = str(DATA_DIR / "notes.txt")
    screenshot_dir: str = field(default_factory=lambda: str(platform_utils.screenshot_dir()))
    # Ask "are you sure?" before shutting down or restarting.
    confirm_power_actions: bool = True
    # Seconds to wait for you to start talking / maximum length of a command.
    listen_timeout: float = 6.0
    phrase_time_limit: float = 12.0
    speech_rate: int = 175
    # Only react to speech that starts with "Hey Orion" (typed commands never need it).
    wake_word: bool = True
    # "auto": offline openWakeWord when installed and the model exists, otherwise
    # spot the phrase in online transcripts. "openwakeword" / "transcript" force one.
    wake_engine: str = "auto"
    # Trained model file (relative to the project folder), a built-in
    # openWakeWord name such as "hey_jarvis", or a list of them
    # (e.g. one model for "Hey Orion" and one for "Dis Orion").
    wake_model: str | list[str] = "models/hey_orion.onnx"
    # Detection score (0-1) needed to wake; raise it if O.R.I.O.N. wakes by mistake.
    wake_threshold: float = 0.5
    # Type commands instead of speaking them (also used when no mic is found).
    text_mode: bool = False

    def validate(self) -> None:
        if self.language not in ("auto", *SUPPORTED_LANGUAGES):
            log.warning("Unknown language %r, using 'auto'.", self.language)
            self.language = "auto"
        if self.wake_engine not in ("auto", "openwakeword", "transcript"):
            log.warning("Unknown wake_engine %r, using 'auto'.", self.wake_engine)
            self.wake_engine = "auto"
        if self.default_language not in SUPPORTED_LANGUAGES:
            self.default_language = "en"
        if self.language != "auto":
            self.default_language = self.language


def load_config(path: Path | None = None) -> Config:
    """Build a Config from defaults plus whatever the JSON file overrides."""
    config = Config()
    path = path or DEFAULT_CONFIG_FILE
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("Could not read %s (%s); using defaults.", path, exc)
            data = {}
        known = {f.name for f in fields(Config)}
        for key, value in data.items():
            if key in known:
                setattr(config, key, value)
            else:
                log.warning("Ignoring unknown setting %r in %s.", key, path)
    config.validate()
    return config
