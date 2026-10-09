"""Terminal front-end. The HUD in ``gui.py`` implements the same methods."""

from __future__ import annotations

from . import DISPLAY_NAME

BANNER = r"""
   ___    ____    ___   ___    _   _
  / _ \  |  _ \  |_ _| / _ \  | \ | |
 | | | | | |_) |  | | | | | | |  \| |
 | |_| |_|  _ < _ | |_| |_| |_| |\  |_
  \___/(_)_| \_(_)___(_)___/(_)_| \_(_)

        A I   V O I C E   A S S I S T A N T
     Powered by AMG · Ascension Media Group
"""


class ConsoleUI:
    def __init__(self) -> None:
        self._last_typed: str | None = None

    def start(self) -> None:
        print(BANNER)

    def status(self, text: str, state: str = "idle") -> None:
        """Show what O.R.I.O.N. is doing; ``state`` is listening/thinking/speaking/idle."""
        if state in ("listening", "thinking"):
            print(f"  … {text}", flush=True)

    def log(self, who: str, text: str) -> None:
        if who == "user" and text == self._last_typed:
            return  # already visible after the "You>" prompt
        label = {"orion": DISPLAY_NAME, "user": "You", "info": "  ↳", "error": "  !"}.get(who, who)
        print(f"{label}: {text}" if who in ("orion", "user") else f"{label} {text}", flush=True)

    def read_text(self, prompt: str = "You> ") -> str | None:
        """Blocking keyboard input; None when the input stream is closed."""
        try:
            self._last_typed = input(prompt).strip()
            return self._last_typed
        except EOFError:
            return None

    def poll_text(self) -> str | None:
        """Typed command waiting while in voice mode (terminal can't do both)."""
        return None

    @property
    def closed(self) -> bool:
        return False
