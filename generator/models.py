"""Data structures shared across the generator pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PricedItem:
    """A single filterable entity (a currency, or a shared unique base type) with a normalized value.

    For currency, `name` is the exact currency BaseType (e.g. "Chaos Orb") and
    `contributors` is just the currency's own name. For uniques, `name` is the
    shared item BaseType (e.g. "Shortsword") and `contributors` lists every
    unique item name that maps to it, since PoE2 uniques drop unidentified and
    a filter can only ever match on BaseType, never the unique's own name.
    """

    name: str
    exalted_value: float
    confidence: float
    contributors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TierStyle:
    font_size: int | None = None
    text_color: list[int] | None = None
    border_color: list[int] | None = None
    background_color: list[int] | None = None
    sound_id: int | None = None
    sound_volume: int | None = None
    minimap_icon: str | None = None
    play_effect: str | None = None


@dataclass(frozen=True)
class TierConfig:
    name: str
    visibility: str  # "show" or "hide"
    min_exalted: float
    style: TierStyle | None = None


@dataclass
class Tier:
    config: TierConfig
    items: list[PricedItem] = field(default_factory=list)
