"""Small OS-specific helpers so the rest of the code stays platform-neutral."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def _xdg_user_dir(kind: str) -> Path | None:
    """Ask Linux for a localised user folder (e.g. ~/Musique on French systems)."""
    if not IS_LINUX or not shutil.which("xdg-user-dir"):
        return None
    try:
        out = subprocess.run(["xdg-user-dir", kind], capture_output=True,
                             text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    path = Path(out) if out else None
    # xdg-user-dir falls back to $HOME when the folder is not configured.
    return path if path and path != Path.home() else None


def music_dir() -> Path:
    return _xdg_user_dir("MUSIC") or Path.home() / "Music"


def screenshot_dir() -> Path:
    pictures = _xdg_user_dir("PICTURES") or Path.home() / "Pictures"
    return pictures / "ORION"


def open_url(url: str) -> bool:
    return webbrowser.open(url, new=2)


def open_path(path: Path) -> bool:
    """Open a file with the default application (music player, editor...)."""
    try:
        if IS_WINDOWS:
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            opener = "open" if IS_MAC else "xdg-open"
            subprocess.Popen([opener, str(path)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


POWER_COMMANDS = {
    "shutdown": {
        "win32": [["shutdown", "/s", "/t", "5"]],
        "darwin": [["osascript", "-e", 'tell application "System Events" to shut down']],
        "linux": [["systemctl", "poweroff"], ["shutdown", "-h", "now"]],
    },
    "restart": {
        "win32": [["shutdown", "/r", "/t", "5"]],
        "darwin": [["osascript", "-e", 'tell application "System Events" to restart']],
        "linux": [["systemctl", "reboot"], ["shutdown", "-r", "now"]],
    },
}


def power_action(action: str) -> bool:
    """Shut down or restart the machine. Returns False if every attempt failed."""
    key = "linux" if IS_LINUX else sys.platform
    for cmd in POWER_COMMANDS[action].get(key, []):
        if not shutil.which(cmd[0]):
            continue
        try:
            if subprocess.run(cmd, capture_output=True, timeout=20).returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False
