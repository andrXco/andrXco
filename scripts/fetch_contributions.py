#!/usr/bin/env python3
"""Fetch the public contribution calendar for the configured GitHub profile.

The GitHub endpoint is public and needs no token.  We retain only date and
intensity—the README deliberately does not show contribution statistics.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "contributions.json"
USERNAME = os.getenv("GH_PROFILE_USER", "andrXco")
URL = f"https://github.com/users/{USERNAME}/contributions"


def attr(tag: str, name: str) -> str | None:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', tag)
    return html.unescape(match.group(1)) if match else None


def fetch_days() -> list[dict[str, object]]:
    request = urllib.request.Request(URL, headers={"User-Agent": "andrXco-profile-readme"})
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")

    days: list[dict[str, object]] = []
    for tag in re.findall(r"<(?:td|rect)\b[^>]*\bdata-date=\"[^\"]+\"[^>]*>", page):
        date = attr(tag, "data-date")
        if not date:
            continue
        level = attr(tag, "data-level")
        days.append({"date": date, "level": int(level) if level and level.isdigit() else 0})
    unique = {str(day["date"]): day for day in days}
    result = [unique[key] for key in sorted(unique)]
    if not result:
        raise RuntimeError("GitHub returned no contribution-calendar cells")
    return result


if __name__ == "__main__":
    days = fetch_days()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"username": USERNAME, "generated_at": dt.datetime.now(dt.UTC).isoformat(), "days": days}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} with {len(days)} days")
