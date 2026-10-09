"""Shut down or restart the computer — always after a spoken confirmation
unless ``confirm_power_actions`` is turned off in the config."""

from __future__ import annotations

from ..platform_utils import power_action
from . import skill


def _power(ctx, action: str, confirm_key: str, done_key: str) -> None:
    if ctx.config.confirm_power_actions and not ctx.confirm(confirm_key):
        ctx.say("power_cancelled")
        return
    ctx.say(done_key)
    if power_action(action):
        ctx.stop()
    else:
        ctx.say("power_failed")


@skill("shutdown",
       en=["shut down", "shutdown", "power off", "turn off the computer", "switch off the computer"],
       fr=["eteins l ordinateur", "eteindre l ordinateur", "eteins le pc", "extinction", "arrete l ordinateur"])
def shutdown(ctx, req):
    _power(ctx, "shutdown", "confirm_shutdown", "shutting_down")


@skill("restart",
       en=["restart", "reboot", "restart the computer"],
       fr=["redemarre", "redemarrer", "redemarrage", "redemarre l ordinateur"])
def restart(ctx, req):
    _power(ctx, "restart", "confirm_restart", "restarting")
