#!/usr/bin/env python3
"""Scrape the public contribution calendar (no token, no GraphQL).

GitHub serves https://github.com/users/<username>/contributions as an HTML
fragment. This is an undocumented endpoint: if GitHub changes the markup, the
parser finds zero days and this script exits non-zero so CI fails loudly
instead of committing an empty graph.

Usage: python scripts/fetch_contributions.py [username]
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
COUNT_RE = re.compile(r"^(No|\d[\d,]*)\s+contributions?", re.I)


def parse_calendar(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.find_all("td", attrs={"data-date": True}):
        text = tips.get(td.get("id"), "")
        m = COUNT_RE.match(text)
        count = 0 if (not m or m.group(1).lower() == "no") else int(m.group(1).replace(",", ""))
        days.append({"date": td["data-date"], "count": count, "level": int(td.get("data-level", 0))})
    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    counts = {d["date"]: d["count"] for d in days}
    total = sum(counts.values())

    longest = run = 0
    prev = None
    for d in days:
        dt = date.fromisoformat(d["date"])
        if d["count"] > 0:
            run = run + 1 if prev and (dt - prev).days == 1 else 1
            longest = max(longest, run)
            prev = dt
        else:
            run, prev = 0, None

    # current streak: today being empty (so far) must not break it
    cur = 0
    cursor = date.fromisoformat(days[-1]["date"])
    if counts.get(cursor.isoformat(), 0) == 0:
        cursor -= timedelta(days=1)
    while counts.get(cursor.isoformat(), 0) > 0:
        cur += 1
        cursor -= timedelta(days=1)

    best = max(days, key=lambda d: d["count"])
    months: dict[str, int] = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    return {"total": total, "current_streak": cur, "longest_streak": longest,
            "best_day": {"date": best["date"], "count": best["count"]}, "monthly": months}


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else json.loads((ROOT / "profile.json").read_text())["username"]
    if username.startswith("YOUR_"):
        print("Set your GitHub username in profile.json (or pass it as an argument).", file=sys.stderr)
        return 2

    resp = requests.get(
        f"https://github.com/users/{username}/contributions",
        headers={"User-Agent": "profile-readme-bot (+https://github.com/" + username + ")"},
        timeout=30,
    )
    resp.raise_for_status()
    days = parse_calendar(resp.text)
    if len(days) < 300:
        print(f"Parsed only {len(days)} days; GitHub's markup probably changed. Refusing to write.", file=sys.stderr)
        return 1

    out = {"username": username, "days": days, "stats": compute_stats(days)}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "contributions.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote data/contributions.json: {len(days)} days, {out['stats']['total']} contributions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
