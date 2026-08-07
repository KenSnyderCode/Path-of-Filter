import json
from pathlib import Path

from generator.models import TierConfig, TierStyle
from generator.tiering import bucket_into_tiers, extract_currency_items, extract_unique_items

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_extract_currency_items_joins_id_to_display_name():
    overview = _load("exchange_overview_currency.json")
    items = extract_currency_items(overview)

    names = {item.name for item in items}
    assert "Exalted Orb" in names
    assert "Divine Orb" in names
    # every priced line must resolve to a real display name, never a bare id like "vaal-orb"
    assert all(" " in item.name or item.name[0].isupper() for item in items)


def test_extract_currency_items_exalted_orb_is_near_one():
    overview = _load("exchange_overview_currency.json")
    items = {item.name: item for item in extract_currency_items(overview)}
    assert 0.9 < items["Exalted Orb"].exalted_value < 1.1


def test_extract_unique_items_groups_by_base_type_and_takes_max_value():
    overview = {
        "core": {"rates": {"exalted": 100.0}, "primary": "divine"},
        "lines": [
            {"name": "Junk Belt", "baseType": "Leather Belt", "primaryValue": 0.1, "listingCount": 50},
            {"name": "Headhunter", "baseType": "Leather Belt", "primaryValue": 20.0, "listingCount": 30},
        ],
    }
    items = extract_unique_items(overview)
    assert len(items) == 1
    belt = items[0]
    assert belt.name == "Leather Belt"
    assert belt.exalted_value == 2000.0  # driven by Headhunter's price, not Junk Belt's
    assert belt.confidence == 30.0  # confidence follows the line that set the max, not the sum
    assert belt.contributors == ("Headhunter", "Junk Belt")


def test_bucket_into_tiers_respects_min_confidence():
    overview = {
        "core": {"rates": {"exalted": 1.0}, "primary": "divine"},
        "lines": [
            {"name": "Thin Sample", "baseType": "Shortsword", "primaryValue": 9999.0, "listingCount": 2},
        ],
    }
    items = extract_unique_items(overview)
    tiers = bucket_into_tiers(
        items,
        [TierConfig(name="Mythic", visibility="show", min_exalted=1000.0, style=TierStyle())],
        min_confidence=10,
    )
    assert all(not tier.items for tier in tiers), "a low-confidence outlier price must not populate any tier"


def test_bucket_into_tiers_places_item_in_highest_qualifying_tier():
    from generator.models import PricedItem

    configs = [
        TierConfig(name="Low", visibility="show", min_exalted=0.0),
        TierConfig(name="Mid", visibility="show", min_exalted=10.0),
        TierConfig(name="High", visibility="show", min_exalted=100.0),
    ]
    items = [PricedItem(name="X", exalted_value=50.0, confidence=999.0, contributors=("X",))]
    tiers = {tier.config.name: tier for tier in bucket_into_tiers(items, configs, min_confidence=0)}

    assert tiers["Mid"].items == items
    assert tiers["Low"].items == []
    assert tiers["High"].items == []
