"""Shape assertions against real, recorded poe.ninja fixtures — catches the API changing under us."""

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_leagues_shape():
    leagues = _load("leagues.json")
    assert isinstance(leagues, list)
    assert leagues
    assert all("id" in entry and "name" in entry for entry in leagues)


def test_currency_overview_shape():
    overview = _load("exchange_overview_currency.json")
    assert set(overview.keys()) >= {"core", "items", "lines"}
    assert "rates" in overview["core"]
    assert "exalted" in overview["core"]["rates"]
    assert overview["items"], "top-level items array must be non-empty (it's the id->name lookup)"
    assert all("id" in item and "name" in item for item in overview["items"])
    assert overview["lines"]
    assert all("id" in line and "primaryValue" in line for line in overview["lines"])


def test_unique_overview_shape():
    overview = _load("stash_overview_uniqueweapons.json")
    assert set(overview.keys()) >= {"core", "lines"}
    assert overview["lines"]
    sample = overview["lines"][0]
    for field in ("name", "baseType", "primaryValue", "listingCount"):
        assert field in sample
