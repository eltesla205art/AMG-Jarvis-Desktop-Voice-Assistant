#!/usr/bin/env python3
"""O.R.I.O.N. — AI Voice Assistant. Powered by AMG · Ascension Media Group.

Run:  python orion.py              (HUD window, voice + typed commands)
      python orion.py --console    (terminal only)
      python orion.py --text       (type commands instead of speaking)
      python orion.py --lang fr    (French only; default: auto EN/FR)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from orion.assistant import Assistant
from orion.config import load_config
from orion.ui import ConsoleUI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="O.R.I.O.N. bilingual desktop voice assistant")
    parser.add_argument("--console", action="store_true", help="run in the terminal, no window")
    parser.add_argument("--text", action="store_true", help="type commands instead of speaking")
    parser.add_argument("--lang", choices=["auto", "en", "fr"], help="language (default: auto)")
    parser.add_argument("--config", help="path to a JSON config file")
    parser.add_argument("--debug", action="store_true", help="verbose logging")
    return parser.parse_args()


def make_hud():
    """The HUD window, or None if Tk or a display is not available."""
    try:
        from orion.gui import HudUI
        return HudUI()
    except Exception as exc:  # ImportError (no tkinter) or TclError (no display)
        logging.getLogger("orion").warning("HUD unavailable (%s); using the terminal.", exc)
        return None


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO if args.debug else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    config = load_config(Path(args.config) if args.config else None)
    if args.lang:
        config.language = args.lang
    if args.text:
        config.text_mode = True
    config.validate()

    hud = None if args.console else make_hud()
    assistant = Assistant(config, hud or ConsoleUI())
    try:
        if hud:
            hud.run(assistant.run)
        else:
            assistant.run()
    except KeyboardInterrupt:
        print("\nO.R.I.O.N. offline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
