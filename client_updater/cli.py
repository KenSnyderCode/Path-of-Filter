"""Entry point for the packaged updater tool: install / run / uninstall."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import paths
from .scheduler import register_scheduled_task, unregister_scheduled_task
from .updater import run_update

DEFAULT_MANIFEST_URL = "https://raw.githubusercontent.com/Njardolf/Path-of-Filter/main/dist/manifest.json"
DEFAULT_FILTER_URL = "https://raw.githubusercontent.com/Njardolf/Path-of-Filter/main/dist/community-loot-filter.filter"
DEFAULT_INTERVAL_HOURS = 4


def _configure_logging() -> logging.Logger:
    log_path = paths.get_log_file()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return logging.getLogger("poe2_loot_filter_updater")


def _build_scheduled_command(manifest_url: str, filter_url: str) -> str:
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        return f'"{exe}" run --manifest-url {manifest_url} --filter-url {filter_url}'
    # Dev-mode fallback (not frozen): best-effort, requires the repo root to already be on
    # PYTHONPATH for the scheduled invocation to find the client_updater package.
    exe = Path(sys.executable).resolve()
    return f'"{exe}" -m client_updater.cli run --manifest-url {manifest_url} --filter-url {filter_url}'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Community PoE2 loot filter auto-updater")
    parser.add_argument("action", choices=["install", "run", "uninstall"])
    parser.add_argument("--manifest-url", default=DEFAULT_MANIFEST_URL)
    parser.add_argument("--filter-url", default=DEFAULT_FILTER_URL)
    parser.add_argument("--interval-hours", type=int, default=DEFAULT_INTERVAL_HOURS)
    args = parser.parse_args(argv)

    logger = _configure_logging()

    if args.action == "uninstall":
        unregister_scheduled_task()
        logger.info("Scheduled task removed (filter file left in place)")
        print("Scheduled task removed. Your currently installed filter was left in place.")
        return 0

    try:
        updated = run_update(
            manifest_url=args.manifest_url,
            filter_url=args.filter_url,
            install_path=paths.get_installed_filter_path(),
            state_path=paths.get_state_file(),
            logger=logger,
        )
    except Exception:
        logger.exception("Update failed")
        if args.action == "install":
            raise
        return 1

    if args.action == "install":
        command = _build_scheduled_command(args.manifest_url, args.filter_url)
        register_scheduled_task(command, args.interval_hours)
        print(
            f"Installed. Filter {'updated' if updated else 'already current'}. "
            f"Scheduled to check every {args.interval_hours}h."
        )
    else:
        print(f"Checked for updates. Filter updated: {updated}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
