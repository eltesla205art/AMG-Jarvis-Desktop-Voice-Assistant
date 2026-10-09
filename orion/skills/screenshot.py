"""Screenshots, saved with a timestamped filename."""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

from . import skill

log = logging.getLogger(__name__)


def capture(path: Path) -> bool:
    """Save a screenshot of all monitors. Tries mss first, then Pillow."""
    try:
        import mss
        import mss.tools
        factory = getattr(mss, "MSS", None) or mss.mss  # mss >= 10.2 renamed the class
        with factory() as sct:
            shot = sct.grab(sct.monitors[0])  # monitor 0 = every screen combined
            mss.tools.to_png(shot.rgb, shot.size, output=str(path))
        return True
    except Exception as exc:  # e.g. Wayland, where mss can't read the screen
        log.info("mss screenshot failed (%s), trying Pillow.", exc)
    try:
        from PIL import ImageGrab
        ImageGrab.grab(all_screens=True).save(path)
        return True
    except Exception as exc:
        log.warning("Screenshot failed: %s", exc)
        return False


@skill("screenshot",
       en=["screenshot", "screen shot", "capture the screen", "capture my screen"],
       fr=["capture d ecran", "capture ecran", "capture l ecran", "fais une capture"])
def take_screenshot(ctx, req):
    folder = Path(ctx.config.screenshot_dir).expanduser()
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        folder = Path.home()
    path = folder / f"screenshot_{dt.datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    if capture(path):
        ctx.ui.log("info", str(path))
        ctx.say("screenshot_saved", folder=folder.name)
    else:
        ctx.say("screenshot_failed")
