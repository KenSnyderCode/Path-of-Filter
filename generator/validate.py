"""Lightweight sanity checks on generated filter text before it's committed.

There's no official offline PoE2 filter validator, so this is a conservative
best-effort check — it can't guarantee the game will accept the file, but it
catches the classes of mistake a generator bug is likely to produce (unbalanced
quotes, out-of-range action values, an empty or truncated file).
"""

from __future__ import annotations

import re

_MIN_BLOCK_COUNT = 1
_FONT_SIZE_RANGE = (18, 45)
_RGBA_COMPONENT_RANGE = (0, 255)


def validate_filter_text(text: str) -> list[str]:
    problems = []

    if not text.strip():
        problems.append("filter text is empty")
        return problems

    if text.count('"') % 2 != 0:
        problems.append("odd number of double-quote characters (unbalanced quoting)")

    show_hide_count = len(re.findall(r"^(Show|Hide)\s*$", text, flags=re.MULTILINE))
    if show_hide_count < _MIN_BLOCK_COUNT:
        problems.append(f"expected at least {_MIN_BLOCK_COUNT} Show/Hide block, found {show_hide_count}")

    for match in re.finditer(r"^\s*SetFontSize\s+(-?\d+)", text, flags=re.MULTILINE):
        size = int(match.group(1))
        if not (_FONT_SIZE_RANGE[0] <= size <= _FONT_SIZE_RANGE[1]):
            problems.append(f"SetFontSize {size} outside valid range {_FONT_SIZE_RANGE}")

    for match in re.finditer(
        r"^\s*(SetTextColor|SetBorderColor|SetBackgroundColor)\s+([\d\s]+)$", text, flags=re.MULTILINE
    ):
        action, values_str = match.groups()
        values = [int(v) for v in values_str.split()]
        if not (3 <= len(values) <= 4):
            problems.append(f"{action} has {len(values)} components, expected 3 (RGB) or 4 (RGBA)")
        elif any(not (_RGBA_COMPONENT_RANGE[0] <= v <= _RGBA_COMPONENT_RANGE[1]) for v in values):
            problems.append(f"{action} {values} has a component outside {_RGBA_COMPONENT_RANGE}")

    return problems
