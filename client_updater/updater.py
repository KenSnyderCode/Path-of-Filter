"""Fetch-compare-download-replace logic: keeps the local filter file in sync with the repo."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

import requests


def fetch_manifest(manifest_url: str, timeout_seconds: float = 15.0) -> dict:
    response = requests.get(manifest_url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.json()


def download_filter(filter_url: str, timeout_seconds: float = 30.0) -> bytes:
    response = requests.get(filter_url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.content


def load_local_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def save_local_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def run_update(
    manifest_url: str,
    filter_url: str,
    install_path: Path,
    state_path: Path,
    logger: logging.Logger,
) -> bool:
    """Fetch the manifest, and if the filter changed (or isn't installed yet), install it.

    Returns True if the local filter file was written, False if it was already current.
    """
    manifest = fetch_manifest(manifest_url)
    remote_sha256 = manifest["sha256"]

    state = load_local_state(state_path)
    if state.get("sha256") == remote_sha256 and install_path.exists():
        logger.info(
            "Already up to date (league=%s, version=%s)", manifest.get("league"), manifest.get("version")
        )
        return False

    content = download_filter(filter_url)
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if actual_sha256 != remote_sha256:
        raise RuntimeError(
            f"Downloaded filter sha256 {actual_sha256} does not match manifest {remote_sha256} — aborting install"
        )

    install_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = install_path.with_name(install_path.name + ".tmp")
    temp_path.write_bytes(content)
    os.replace(temp_path, install_path)  # atomic on the same volume

    state.update(
        {
            "sha256": remote_sha256,
            "version": manifest.get("version"),
            "league": manifest.get("league"),
            "generatedAtUtc": manifest.get("generatedAtUtc"),
        }
    )
    save_local_state(state_path, state)

    logger.info("Installed updated filter (league=%s, version=%s)", manifest.get("league"), manifest.get("version"))
    return True
