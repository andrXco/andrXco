#!/usr/bin/env python3
"""Render a clean, animated contribution calendar SVG with an annual total."""
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "assets" / "contrib-heatmap.svg"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
CELL, GAP, PAD, LABEL_W = 11, 4, 28, 33
STEP = CELL + GAP


def fallback() -> dict[str, object]:
    today = dt.date.today()
    start = today - dt.timedelta(days=364)
    return {"username": "andrXco", "days": [{"date": (start + dt.timedelta(days=offset)).isoformat(), "level": 0} for offset in range(365)]}


def grid(days: list[dict[str, object]]) -> list[list[dict[str, object] | None]]:
    first = dt.date.fromisoformat(str(days[0]["date"]))
    column: list[dict[str, object] | None] = [None] * ((first.weekday() + 1) % 7)
    columns: list[list[dict[str, object] | None]] = []
    for day in days:
        date = dt.date.fromisoformat(str(day["date"]))
        weekday = (date.weekday() + 1) % 7
        while len(column) < weekday:
            column.append(None)
        column.append(day)
        if len(column) == 7:
            columns.append(column)
            column = []
    if column:
        columns.append(column + [None] * (7 - len(column)))
    return columns


def render(data: dict[str, object]) -> str:
    days = list(data["days"])
    columns = grid(days)
    art_width = len(columns) * STEP
    width = PAD * 2 + LABEL_W + art_width
    height = 202
    top, left = 60, PAD + LABEL_W
    labels: list[tuple[int, str]] = []
    seen: set[tuple[int, int]] = set()
    for col_idx, column in enumerate(columns):
        for day in column:
            if not day:
                continue
            date = dt.date.fromisoformat(str(day["date"]))
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                seen.add(key)
                labels.append((col_idx, date.strftime("%b")))
            break
    user = html.escape(str(data.get("username", "andrXco")))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contribution calendar" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>'
        '@keyframes reveal{0%{opacity:0;transform:translateY(-3px) scaleX(.15);filter:brightness(1)}55%{opacity:1;filter:brightness(1.65)}100%{opacity:1;transform:none;filter:brightness(1)}}'
        f'@keyframes grid-sweep{{from{{transform:translateX(0)}}to{{transform:translateX({width + 150}px)}}}}'
        '@media(prefers-reduced-motion:no-preference){'
        '.cell{transform-box:fill-box;transform-origin:left center;animation:reveal 1s cubic-bezier(.22,1,.36,1) backwards}'
        '.grid-reflection{animation:grid-sweep 5.5s linear 4.5s infinite}}'
        '</style>',
        '<defs>'
        '<linearGradient id="grid-reflection-gradient">'
        '<stop offset="0" stop-color="#e6edf3" stop-opacity="0"/>'
        '<stop offset=".52" stop-color="#e6edf3" stop-opacity=".36"/>'
        '<stop offset="1" stop-color="#e6edf3" stop-opacity="0"/>'
        '</linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="14" fill="#0d1117"/><rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="none" stroke="#30363d"/>',
        f'<text x="{PAD}" y="27" fill="#8b949e" font-size="12">{user}@github: ~/contributions</text>',
        f'<text x="{width - PAD}" y="27" text-anchor="end" fill="#39d353" font-size="12">last year</text>',
        f'<line x1="0" y1="42" x2="{width}" y2="42" stroke="#30363d"/>',
    ]
    for col_idx, month in labels:
        parts.append(f'<text x="{left + col_idx * STEP}" y="55" fill="#8b949e" font-size="10">{month}</text>')
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(f'<text x="{PAD}" y="{top + row * STEP + 9}" fill="#8b949e" font-size="9">{label}</text>')
    cell_shapes = []
    parts.append('<g id="calendar-cells">')
    for col_idx, column in enumerate(columns):
        for row, day in enumerate(column):
            if not day:
                continue
            level = max(0, min(4, int(day.get("level", 0))))
            date = html.escape(str(day["date"]))
            x, y = left + col_idx * STEP, top + row * STEP
            delay = 0.05 + (col_idx * 0.055) + (row * 0.055)
            shape = f'x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2"'
            cell_shapes.append(f'<rect {shape}/>')
            parts.append(f'<rect class="cell" {shape} fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s"><title>{date}</title></rect>')
    parts.append('</g><defs><clipPath id="grid-silhouette" clipPathUnits="userSpaceOnUse">')
    parts.extend(cell_shapes)
    parts.append(
        '</clipPath></defs><g clip-path="url(#grid-silhouette)" aria-hidden="true" pointer-events="none">'
        '<g class="grid-reflection"><rect x="-125" y="50" width="125" height="120" '
        'transform="skewX(-20)" fill="url(#grid-reflection-gradient)"/></g></g>'
    )
    year = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))).year
    annual_total = sum(int(day["count"]) for day in days if dt.date.fromisoformat(str(day["date"])).year == year)
    parts.append(f'<text x="{PAD}" y="184" fill="#c9d1d9" font-size="12">{annual_total:,} contributions in {year}</text>')
    legend_y = 175
    legend_x = width - PAD - 128
    parts.append(f'<text x="{legend_x}" y="{legend_y + 9}" text-anchor="end" fill="#8b949e" font-size="10">Less</text>')
    for index, color in enumerate(PALETTE):
        parts.append(f'<rect x="{legend_x + 9 + index * 14}" y="{legend_y}" width="11" height="11" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 84}" y="{legend_y + 9}" fill="#8b949e" font-size="10">More</text>')
    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    data = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else fallback()
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(render(data), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
