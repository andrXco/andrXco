#!/usr/bin/env python3
"""Render an animated contribution calendar GIF from the fetched profile data."""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageColor


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "assets" / "contrib-heatmap.gif"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BACKGROUND, BORDER, MUTED, TEXT, ACCENT = "#0d1117", "#30363d", "#8b949e", "#c9d1d9", "#39d353"
CELL, GAP, PAD, LABEL_W = 11, 4, 28, 33
STEP = CELL + GAP
HEIGHT = 202


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in ("DejaVuSansMono.ttf", "consola.ttf", "C:/Windows/Fonts/consola.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


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


def year_in_bogota() -> int:
    bogota = dt.timezone(dt.timedelta(hours=-5))
    return dt.datetime.now(bogota).year


def render(data: dict[str, object]) -> list[Image.Image]:
    days = list(data["days"])
    columns = grid(days)
    year = year_in_bogota()
    annual_total = sum(int(day.get("count", 0)) for day in days if dt.date.fromisoformat(str(day["date"])).year == year)
    width = PAD * 2 + LABEL_W + len(columns) * STEP
    left, top = PAD + LABEL_W, 59
    regular_font, small_font = font(12), font(10)
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

    images: list[Image.Image] = []
    # A diagonal wave reveals each tile with a brief domino-like tilt.
    frame_count = 141
    for frame_index in range(frame_count):
        sweep_x = left - 140 + (width - left + 280) * frame_index / (frame_count - 1)
        image = Image.new("RGB", (width, HEIGHT), BACKGROUND)
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, width - 1, HEIGHT - 1), radius=14, outline=BORDER)
        draw.text((PAD, 15), f'{data.get("username", "andrXco")}@github: ~/contributions', fill=MUTED, font=regular_font)
        draw.text((width - PAD, 15), "last year", fill=ACCENT, font=regular_font, anchor="ra")
        draw.line((0, 42, width, 42), fill=BORDER)
        for col_idx, month in labels:
            draw.text((left + col_idx * STEP, 46), month, fill=MUTED, font=small_font)
        for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
            draw.text((PAD, top + row * STEP), label, fill=MUTED, font=small_font)
        scale = 3
        cells = Image.new("RGB", (width * scale, HEIGHT * scale), BACKGROUND)
        cell_draw = ImageDraw.Draw(cells)
        for col_idx, column in enumerate(columns):
            for row, day in enumerate(column):
                if not day:
                    continue
                level = max(0, min(4, int(day.get("level", 0))))
                size = CELL
                x, y = left + col_idx * STEP, top + row * STEP
                wave_position = x + CELL / 2 + row * 12
                progress = max(0., min(1., (sweep_x - wave_position + 65) / 110))
                if progress == 0:
                    continue
                eased = 1 - (1 - progress) ** 3
                # Perspective projection of a face rotating around its left edge.
                angle = (1 - eased) * math.radians(78)
                tile_width = CELL * math.cos(angle)
                lift = 2.5 * math.sin(angle)
                distance = abs(wave_position - sweep_x)
                glow = (.5 + .5 * math.cos(math.pi * distance / 85)) ** 2 if distance < 85 else 0.
                base = ImageColor.getrgb(PALETTE[level])
                highlight = (155, 255, 190) if level else (100, 112, 120)
                intensity = glow * (.55 if level else .28)
                shade = .68 + .32 * math.cos(angle)
                lit = tuple((a + (b - a) * intensity) * shade for a, b in zip(base, highlight))
                background = ImageColor.getrgb(BACKGROUND)
                color = tuple(round(a + (b - a) * eased) for a, b in zip(background, lit))
                if progress < .98:
                    corners = [(x, y), (x + tile_width, y + lift), (x + tile_width, y + size - lift), (x, y + size)]
                    points = [(round(px * scale), round(py * scale)) for px, py in corners]
                    shadow = [(px + round(lift * scale), py + round(lift * scale / 2)) for px, py in points]
                    cell_draw.polygon(shadow, fill=BACKGROUND)
                    cell_draw.polygon(points, fill=color)
                    edge = tuple(min(255, round(c * 1.18)) for c in color)
                    cell_draw.line(points[:2], fill=edge, width=scale)
                else:
                    cell_draw.rounded_rectangle((round(x * scale), round(y * scale), round((x + size) * scale) - 1, round((y + size) * scale) - 1), radius=2 * scale, fill=color)
        cells = cells.resize((width, HEIGHT), Image.Resampling.LANCZOS)
        image.paste(cells.crop((left - 12, top - 1, width - PAD, top + 7 * STEP + 6)), (left - 12, top - 1))
        total_label = f"{annual_total:,} contributions in {year}"
        draw.text((PAD, 179), total_label, fill=TEXT, font=regular_font)
        legend_x, legend_y = width - PAD - 128, 177
        draw.text((legend_x, legend_y), "Less", fill=MUTED, font=small_font)
        for index, color in enumerate(PALETTE):
            x = legend_x + 38 + index * 14
            draw.rounded_rectangle((x, legend_y, x + CELL - 1, legend_y + CELL - 1), radius=2, fill=color)
        draw.text((legend_x + 113, legend_y), "More", fill=MUTED, font=small_font)
        images.append(image)
    return images


if __name__ == "__main__":
    data = json.loads(DATA.read_text(encoding="utf-8"))
    frames = render(data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Share a palette across frames to prevent color flicker during the fades.
    samples = Image.new("RGB", (221, 51 * len(frames)))
    for index, frame in enumerate(frames):
        samples.paste(frame.resize((221, 51)), (0, index * 51))
    palette = samples.quantize(colors=256)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:], duration=[30] * (len(frames) - 1) + [4000], loop=0, optimize=True)
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(frames)} frames)")
