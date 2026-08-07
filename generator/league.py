"""Resolves the active PoE2 challenge league so it never needs to be hardcoded."""

from __future__ import annotations

from .poe_ninja_client import PoeNinjaClient

_EXCLUDED_EXACT = {"standard", "hardcore"}


def resolve_active_league(client: PoeNinjaClient, override: str | None = None) -> str:
    """Return the current challenge league name.

    poe.ninja lists leagues with the active softcore challenge league first,
    followed by its hardcore counterpart, then the permanent Standard/Hardcore
    leagues. We pick the first entry that isn't one of the permanent leagues
    or their hardcore variant, so this keeps working automatically across
    league launches without a code change.
    """
    if override:
        return override

    leagues = client.get_leagues()
    for entry in leagues:
        name = entry.get("name", "").strip()
        lowered = name.lower()
        if lowered in _EXCLUDED_EXACT or lowered.startswith("hc "):
            continue
        if name:
            return name

    raise ValueError(f"Could not resolve an active challenge league from poe.ninja response: {leagues!r}")
