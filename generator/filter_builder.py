"""Renders tiered items into valid PoE2 .filter text, and writes the generator's output."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from .models import Tier


def _quote_join(names: list[str]) -> str:
    return " ".join(f'"{name}"' for name in names)


def _rgba_line(action: str, rgba: list[int]) -> str:
    return f"    {action} {' '.join(str(c) for c in rgba)}"


def render_tier_block(tier: Tier, condition_field: str, extra_conditions: list[str] | None = None) -> str:
    """Render one Show/Hide block for a tier, or "" if the tier has no items."""
    if not tier.items:
        return ""

    names = sorted({item.name for item in tier.items})
    style = tier.config.style

    lines = [f"# {tier.config.name} ({len(names)} {condition_field.lower()}s)"]
    lines.append("Show" if tier.config.visibility == "show" else "Hide")
    for condition in extra_conditions or []:
        lines.append(f"    {condition}")
    lines.append(f"    {condition_field} == {_quote_join(names)}")

    if style is not None:
        if style.font_size is not None:
            lines.append(f"    SetFontSize {style.font_size}")
        if style.text_color is not None:
            lines.append(_rgba_line("SetTextColor", style.text_color))
        if style.border_color is not None:
            lines.append(_rgba_line("SetBorderColor", style.border_color))
        if style.background_color is not None:
            lines.append(_rgba_line("SetBackgroundColor", style.background_color))
        if style.sound_id is not None:
            lines.append(f"    PlayAlertSound {style.sound_id} {style.sound_volume or 300}")
        if style.minimap_icon:
            lines.append(f"    MinimapIcon {style.minimap_icon}")
        if style.play_effect:
            lines.append(f"    PlayEffect {style.play_effect}")

    return "\n".join(lines)


def render_section(title: str, condition_field: str, tiers: list[Tier], extra_conditions: list[str] | None = None) -> str:
    lines = [f"# ===== {title} =====", ""]
    for tier in tiers:
        block = render_tier_block(tier, condition_field, extra_conditions)
        if block:
            lines.append(block)
            lines.append("")
    return "\n".join(lines)


def render_filter(league: str, generated_at: datetime, sections: list[str]) -> str:
    header = [
        "# Community PoE2 Auto-Loot-Filter",
        "# Automatically generated daily from live poe.ninja market data.",
        "# This is an independent, community-run project — not affiliated with",
        "# GGG, poe.ninja, NeverSink, or FilterBlade.",
        f"# League: {league}",
        f"# Generated: {generated_at.isoformat()}",
        "#",
        "# Categories not covered by this filter (weapons, armour, gems, waystones, etc.)",
        "# intentionally fall through to the game's default visibility — this filter never",
        "# emits a blanket Hide rule.",
        "",
    ]
    return "\n".join(header) + "\n" + "\n".join(sections)


def write_output(filter_text: str, league: str, generated_at: datetime, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    filter_path = output_dir / "community-loot-filter.filter"
    filter_path.write_text(filter_text, encoding="utf-8", newline="\n")

    digest = hashlib.sha256(filter_text.encode("utf-8")).hexdigest()
    manifest = {
        "version": digest[:12],
        "generatedAtUtc": generated_at.isoformat(),
        "league": league,
        "sha256": digest,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    return filter_path, manifest_path
