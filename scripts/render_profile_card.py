#!/usr/bin/env python3
"""Render the profile terminal card from data/profile.json.

No third-party packages are required.  Change the JSON, run this script, and
commit the regenerated SVG.
"""
from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "profile.json"
OUTPUT = ROOT / "assets" / "profile-card.svg"

WIDTH = 900
HEIGHT = 590
PAD = 34
MONO = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(x: int, y: int, value: object, *, size: int = 14, fill: str = "#c9d1d9", weight: int = 400) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
        f'font-weight="{weight}">{esc(value)}</text>'
    )


def section(x: int, y: int, title: str, values: list[str], width: int) -> tuple[list[str], int]:
    lines = [text(x, y, title.upper(), size=11, fill="#58a6ff", weight=700)]
    y += 23
    for value in values:
        lines.append(text(x, y, "› " + value, size=13, fill="#e6edf3"))
        y += 21
    return lines, y + 8


def render(profile: dict[str, object]) -> str:
    name = str(profile["name"])
    handle = str(profile["handle"])
    headline = str(profile["headline"])
    focus = list(profile["focus"])
    languages = " · ".join(profile["languages"])
    technologies = " · ".join(profile["technologies"])
    currently = list(profile["currently"])

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{esc(name)} profile" font-family="{MONO}">',
        "<style>@keyframes enter{from{opacity:0;transform:translateY(-5px)}to{opacity:1;transform:translateY(0)}}.line{opacity:0;animation:enter .45s ease-out forwards}</style>",
        "<defs><linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\"><stop stop-color=\"#0d1117\"/><stop offset=\"1\" stop-color=\"#070b10\"/></linearGradient><filter id=\"glow\"><feGaussianBlur stdDeviation=\"5\" result=\"b\"/><feMerge><feMergeNode in=\"b\"/><feMergeNode in=\"SourceGraphic\"/></feMerge></filter></defs>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="14" fill="none" stroke="#30363d"/>',
        '<line x1="0" y1="44" x2="900" y2="44" stroke="#30363d"/>',
        '<circle cx="34" cy="22" r="6" fill="#ff5f56"/><circle cx="54" cy="22" r="6" fill="#ffbd2e"/><circle cx="74" cy="22" r="6" fill="#27c93f"/>',
        f'<text x="450" y="27" text-anchor="middle" font-size="12" fill="#8b949e">{esc(handle)}@github: ~/profile</text>',
        '<g class="line" style="animation-delay:.05s">',
        '<text x="58" y="123" font-size="28" font-weight="700" fill="#39d353" filter="url(#glow)">      _    ____</text>',
        '<text x="58" y="157" font-size="28" font-weight="700" fill="#39d353">     / \\  / ___|</text>',
        '<text x="58" y="191" font-size="28" font-weight="700" fill="#39d353">    / _ \\| |</text>',
        '<text x="58" y="225" font-size="28" font-weight="700" fill="#39d353">   / ___ \\ |___</text>',
        '<text x="58" y="259" font-size="28" font-weight="700" fill="#39d353">  /_/   \\_\\____|</text>',
        f'<text x="68" y="300" font-size="13" fill="#8b949e">{esc(profile["location"])}</text>',
        '</g>',
        '<line x1="342" y1="76" x2="342" y2="552" stroke="#30363d"/>',
        '<g class="line" style="animation-delay:.14s">',
        f'<text x="382" y="109" font-size="26" font-weight="700" fill="#f0f6fc">{esc(name)}</text>',
        f'<text x="382" y="136" font-size="14" fill="#8b949e">{esc(headline)}</text>',
        '</g>',
    ]

    left, _ = section(58, 357, "focus", focus, 240)
    parts.append('<g class="line" style="animation-delay:.22s">' + "".join(left) + "</g>")
    right_y = 180
    parts.append('<g class="line" style="animation-delay:.36s">')
    parts.append(text(382, right_y, "LANGUAGES", size=11, fill="#58a6ff", weight=700))
    parts.append(text(382, right_y + 23, languages, size=13, fill="#e6edf3"))
    parts.append(text(382, right_y + 58, "TECHNOLOGIES", size=11, fill="#58a6ff", weight=700))
    parts.append(text(382, right_y + 81, technologies, size=13, fill="#e6edf3"))
    parts.append('</g>')
    current_y = right_y + 121
    current_lines, _ = section(382, current_y, "currently", currently, 470)
    parts.append('<g class="line" style="animation-delay:.44s">' + "".join(current_lines) + "</g>")
    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(profile), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
