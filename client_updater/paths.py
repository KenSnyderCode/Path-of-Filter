"""Locates the PoE2 filter folder and this tool's own local state/log files."""

from __future__ import annotations

import os
from pathlib import Path

INSTALLED_FILTER_NAME = "CommunityAutoFilter.filter"


def get_poe2_filter_dir() -> Path:
    return Path(os.environ["USERPROFILE"]) / "Documents" / "My Games" / "Path of Exile 2"


def get_installed_filter_path() -> Path:
    return get_poe2_filter_dir() / INSTALLED_FILTER_NAME


def get_local_state_dir() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "CommunityLootFilter"


def get_state_file() -> Path:
    return get_local_state_dir() / "state.json"


def get_log_file() -> Path:
    return get_local_state_dir() / "updater.log"
