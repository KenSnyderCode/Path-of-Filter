"""CLI entry point: resolve league -> fetch -> tier -> build -> write dist/.

Usage:
    python -m generator.main [--league LEAGUE_NAME] [--output DIR]

Environment:
    POE2_LEAGUE_OVERRIDE  Same effect as --league; useful for pinning during dev/testing.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .filter_builder import render_filter, render_section, write_output
from .league import resolve_active_league
from .models import TierConfig, TierStyle
from .poe_ninja_client import PoeNinjaClient
from .tiering import bucket_into_tiers, extract_currency_items, extract_unique_items
from .validate import validate_filter_text

_CONFIG_DIR = Path(__file__).resolve().parent / "config"
_DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "dist"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _parse_tier_configs(raw_tiers: list[dict]) -> list[TierConfig]:
    configs = []
    for raw in raw_tiers:
        style_raw = raw.get("style")
        style = TierStyle(**style_raw) if style_raw else None
        configs.append(
            TierConfig(
                name=raw["name"],
                visibility=raw["visibility"],
                min_exalted=float(raw["min_exalted"]),
                style=style,
            )
        )
    return configs


def build_filter(client: PoeNinjaClient, settings: dict, league: str, generated_at: datetime) -> tuple[str, dict]:
    currency_config = _load_yaml(_CONFIG_DIR / "tiers_currency.yaml")
    unique_config = _load_yaml(_CONFIG_DIR / "tiers_uniques.yaml")

    currency_tier_configs = _parse_tier_configs(currency_config["tiers"])
    unique_tier_configs = _parse_tier_configs(unique_config["tiers"])

    sections = []
    stats = {"currency_items": 0, "unique_base_types": 0}

    currency_overview = client.get_exchange_overview(league, settings["currency_type"])
    currency_items = extract_currency_items(currency_overview)
    if not currency_items:
        raise RuntimeError(
            "Currency overview returned no usable priced lines — aborting rather than publishing an empty filter"
        )
    stats["currency_items"] = len(currency_items)
    currency_tiers = bucket_into_tiers(
        currency_items, currency_tier_configs, currency_config.get("min_confidence", 0)
    )
    sections.append(render_section("Currency", "BaseType", currency_tiers))

    for unique_type in settings["unique_types"]:
        overview = client.get_stash_overview(league, unique_type)
        unique_items = extract_unique_items(overview)
        if not unique_items:
            raise RuntimeError(f"Unique overview for '{unique_type}' returned no usable priced lines — aborting")
        stats["unique_base_types"] += len(unique_items)
        tiers = bucket_into_tiers(unique_items, unique_tier_configs, unique_config.get("min_confidence", 0))
        sections.append(
            render_section(f"Uniques - {unique_type}", "BaseType", tiers, extra_conditions=["Rarity == Unique"])
        )

    filter_text = render_filter(league, generated_at, sections)
    return filter_text, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the community PoE2 loot filter from live poe.ninja data")
    parser.add_argument(
        "--league", default=None, help="Override the resolved league name (also via POE2_LEAGUE_OVERRIDE)"
    )
    parser.add_argument(
        "--output", type=Path, default=_DEFAULT_OUTPUT_DIR, help="Output directory for the generated filter + manifest"
    )
    args = parser.parse_args(argv)

    settings = _load_yaml(_CONFIG_DIR / "settings.yaml")
    client = PoeNinjaClient(
        base_url=settings["base_url"],
        user_agent=settings["user_agent"],
        timeout_seconds=settings["timeout_seconds"],
        max_retries=settings["max_retries"],
        retry_backoff_seconds=settings["retry_backoff_seconds"],
    )

    league_override = args.league or os.environ.get("POE2_LEAGUE_OVERRIDE")
    league = resolve_active_league(client, league_override)
    print(f"Resolved league: {league}")

    generated_at = datetime.now(timezone.utc)
    filter_text, stats = build_filter(client, settings, league, generated_at)
    print(f"Currency items priced: {stats['currency_items']}")
    print(f"Unique base types priced: {stats['unique_base_types']}")

    problems = validate_filter_text(filter_text)
    if problems:
        print("Validation FAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    filter_path, manifest_path = write_output(filter_text, league, generated_at, args.output)
    print(f"Wrote {filter_path}")
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
