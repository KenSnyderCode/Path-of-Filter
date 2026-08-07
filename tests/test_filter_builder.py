from datetime import datetime, timezone

from generator.filter_builder import render_filter, render_section, render_tier_block
from generator.models import PricedItem, Tier, TierConfig, TierStyle
from generator.validate import validate_filter_text


def _tier(name="Mythic", visibility="show", items=None, style=None):
    return Tier(
        config=TierConfig(name=name, visibility=visibility, min_exalted=100.0, style=style),
        items=items or [],
    )


def test_render_tier_block_empty_tier_returns_empty_string():
    assert render_tier_block(_tier(items=[]), "BaseType") == ""


def test_render_tier_block_show_includes_conditions_and_style():
    style = TierStyle(font_size=40, text_color=[255, 255, 255], sound_id=6, sound_volume=300)
    item = PricedItem(name="Divine Orb", exalted_value=368.0, confidence=100.0, contributors=("Divine Orb",))
    block = render_tier_block(_tier(items=[item], style=style), "BaseType")

    assert "Show" in block
    assert 'BaseType == "Divine Orb"' in block
    assert "SetFontSize 40" in block
    assert "SetTextColor 255 255 255" in block
    assert "PlayAlertSound 6 300" in block


def test_render_tier_block_hide_has_no_style_requirement():
    item = PricedItem(name="Scroll of Wisdom", exalted_value=0.01, confidence=100.0, contributors=("Scroll of Wisdom",))
    block = render_tier_block(_tier(name="Chaff", visibility="hide", items=[item]), "BaseType")
    assert block.startswith("# Chaff")
    assert "\nHide\n" in block


def test_render_tier_block_extra_conditions_scope_uniques_to_rarity():
    item = PricedItem(name="Shortsword", exalted_value=50.0, confidence=100.0, contributors=("Redbeak",))
    block = render_tier_block(_tier(items=[item]), "BaseType", extra_conditions=["Rarity == Unique"])
    assert "Rarity == Unique" in block


def test_render_filter_never_emits_a_blanket_hide():
    item = PricedItem(name="Chaos Orb", exalted_value=48.0, confidence=100.0, contributors=("Chaos Orb",))
    section = render_section("Currency", "BaseType", [_tier(items=[item])])
    text = render_filter("Runes of Aldur", datetime(2026, 8, 6, tzinfo=timezone.utc), [section])

    # a bare "Hide" with no condition beneath it would blank out an entire category —
    # every Hide block this generator emits must be scoped to specific BaseType names.
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "Hide":
            assert i + 1 < len(lines)
            assert lines[i + 1].strip(), "a bare Hide block with no condition would blank out an entire category"


def test_generated_filter_passes_validation():
    item = PricedItem(name="Divine Orb", exalted_value=368.0, confidence=100.0, contributors=("Divine Orb",))
    style = TierStyle(font_size=40, text_color=[255, 255, 255, 200], sound_id=6, sound_volume=300)
    section = render_section("Currency", "BaseType", [_tier(items=[item], style=style)])
    text = render_filter("Runes of Aldur", datetime(2026, 8, 6, tzinfo=timezone.utc), [section])

    assert validate_filter_text(text) == []
