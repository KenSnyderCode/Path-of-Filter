"""Registers/removes a Windows Task Scheduler entry that re-runs the updater periodically.

Uses a plain recurring HOURLY trigger. Deliberately omits /RU and /RP (run-as-user and its
password), which makes the task default to "only run when the creating user is logged on" —
avoids ever needing to store the user's Windows credentials, at the cost of not updating while
they're logged out. Confirmed live: /SC ONLOGON does NOT accept /RI or /DU (schtasks rejects it
outright — "not applicable for the scheduled types: ONSTART, ONLOGON, ONIDLE, ONEVENT"), so a
logon-triggered repeating task isn't an option; HOURLY is the correct trigger type for this.
"""

from __future__ import annotations

import subprocess

TASK_NAME = "PoE2CommunityLootFilterUpdater"


def register_scheduled_task(command: str, interval_hours: int) -> None:
    args = [
        "schtasks",
        "/Create",
        "/TN",
        TASK_NAME,
        "/TR",
        command,
        "/SC",
        "HOURLY",
        "/MO",
        str(interval_hours),
        "/F",
    ]
    subprocess.run(args, check=True, capture_output=True, text=True)


def unregister_scheduled_task() -> None:
    subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True, text=True)


def is_task_registered() -> bool:
    result = subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME], capture_output=True, text=True)
    return result.returncode == 0
