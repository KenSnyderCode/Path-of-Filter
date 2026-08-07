"""Turns raw poe.ninja overview responses into price-tiered, filterable items.

Two extraction paths, because the two poe.ninja endpoint families shape their
data differently and mean different things:

- Currency items are always shown fully identified on the ground, so each
  currency's own name is directly usable as a filter BaseType, one-to-one.
- Unique items drop *unidentified*, and a PoE2 filter can only match a
  unique's BaseType (e.g. "Shortsword"), never its own name (e.g. "Redbeak") —
  confirmed via GGG's own forums, where exactly this was requested as a
  feature and never implemented. So uniques are grouped by their shared
  BaseType, and priced using the *highest* value among all uniques sharing
  that base type. This means a base type is never under-valued just because
  one of the uniques that can roll on it happens to be junk: erring toward
  showing something loudly is safe, erring toward hiding a chase item is not.
"""

from __future__ import annotations

from collections import defaultdict

from .models import PricedItem, Tier, TierConfig


def extract_currency_items(overview: dict) -> list[PricedItem]:
    core = overview.get("core", {})
    rate_to_exalted = core.get("rates", {}).get("exalted", 1.0)
    # Note: overview["core"]["items"] only holds the 2-3 reference currencies used for the
    # rate conversion (e.g. divine/exalted/chaos); the full id -> display-name lookup for every
    # tradeable currency is the top-level overview["items"] array (confirmed against a live call).
    items_by_id = {item["id"]: item for item in overview.get("items", [])}

    items = []
    for line in overview.get("lines", []):
        item = items_by_id.get(line.get("id"))
        primary_value = line.get("primaryValue")
        if item is None or not item.get("name") or primary_value is None:
            continue
        name = item["name"]
        items.append(
            PricedItem(
                name=name,
                exalted_value=primary_value * rate_to_exalted,
                confidence=line.get("volumePrimaryValue", 0.0) or 0.0,
                contributors=(name,),
            )
        )
    return items


def extract_unique_items(overview: dict) -> list[PricedItem]:
    core = overview.get("core", {})
    rate_to_exalted = core.get("rates", {}).get("exalted", 1.0)

    groups: dict[str, list[tuple[str, float, int]]] = defaultdict(list)
    for line in overview.get("lines", []):
        base_type = line.get("baseType")
        name = line.get("name")
        primary_value = line.get("primaryValue")
        if not base_type or not name or primary_value is None:
            continue
        groups[base_type].append((name, primary_value * rate_to_exalted, line.get("listingCount", 0) or 0))

    items = []
    for base_type, entries in groups.items():
        # Confidence is tied to the listingCount of whichever line set the max price, not the
        # group's total — otherwise a thinly-traded outlier price could "borrow" confidence from
        # unrelated, unconnected uniques that happen to share the same base type.
        top_name, top_value, top_confidence = max(entries, key=lambda entry: entry[1])
        items.append(
            PricedItem(
                name=base_type,
                exalted_value=top_value,
                confidence=float(top_confidence),
                contributors=tuple(sorted(name for name, _, _ in entries)),
            )
        )
    return items


def bucket_into_tiers(items: list[PricedItem], tier_configs: list[TierConfig], min_confidence: float) -> list[Tier]:
    """Sort tier configs highest-cutoff-first and place each item in the first tier it clears."""
    tiers = [Tier(config=tc) for tc in sorted(tier_configs, key=lambda tc: tc.min_exalted, reverse=True)]
    for item in items:
        if item.confidence < min_confidence:
            continue
        for tier in tiers:
            if item.exalted_value >= tier.config.min_exalted:
                tier.items.append(item)
                break
    return tiers
