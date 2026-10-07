#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53x7 heatmap SVG.

Boxes slide in diagonally once on load (CSS keyframes, fill-mode both) and then
freeze; no looping. Output: contrib-heatmap.svg
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
W, CELL, GAP = 860, 12, 3
PITCH = CELL + GAP
LEFT, TOP = 40, 44
BG, BORDER, DIM = "#0d1117", "#30363d", "#8b949e"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for(d: dict, top: int) -> int:
    lv = d["level"]
    return 5 if lv == 4 and top > 0 and d["count"] >= 0.8 * top else lv


def main() -> int:
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    days, stats = data["days"], data["stats"]
    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)  # back up to Sunday
    top = max(d["count"] for d in days)
    weeks = (date.fromisoformat(days[-1]["date"]) - start).days // 7 + 1

    grid_w = weeks * PITCH - GAP
    x0 = max(LEFT, (W - grid_w) // 2)
    height = TOP + 7 * PITCH + 56

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" role="img" aria-label="Contribution heatmap">',
        "<style>.d{opacity:0;animation:s .5s ease-out both}"
        "@keyframes s{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}}"
        f"text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:10px;fill:{DIM}}}</style>",
        f'<rect width="{W}" height="{height}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
    ]

    # day labels (Mon/Wed/Fri)
    for r, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{x0 - 8}" y="{TOP + r * PITCH + CELL - 2}" text-anchor="end">{label}</text>')

    # month labels
    last_col = -10
    for d in days:
        dt = date.fromisoformat(d["date"])
        col = (dt - start).days // 7
        if dt.day <= 7 and dt.weekday() == 0 or (d is days[0]):
            if col - last_col >= 3:
                out.append(f'<text x="{x0 + col * PITCH}" y="{TOP - 10}">{MONTHS[dt.month - 1]}</text>')
                last_col = col

    for d in days:
        dt = date.fromisoformat(d["date"])
        idx = (dt - start).days
        col, row = idx // 7, idx % 7
        delay = (col + row) * 0.012
        out.append(
            f'<rect class="d" style="animation-delay:{delay:.3f}s" x="{x0 + col * PITCH}" y="{TOP + row * PITCH}" '
            f'width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[level_for(d, top)]}"/>'
        )

    # footer: stats + legend
    fy = TOP + 7 * PITCH + 24
    out.append(f'<text x="{x0}" y="{fy}" style="font-size:12px">{stats["total"]:,} contributions in the last year'
               f' · current streak {stats["current_streak"]}d · longest {stats["longest_streak"]}d</text>')
    lx = x0 + grid_w - (len(PALETTE) * (CELL + 4) + 70)
    out.append(f'<text x="{lx}" y="{fy}">Less</text>')
    for i, col in enumerate(PALETTE):
        out.append(f'<rect x="{lx + 30 + i * (CELL + 4)}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="3" fill="{col}"/>')
    out.append(f'<text x="{lx + 30 + len(PALETTE) * (CELL + 4) + 4}" y="{fy}">More</text>')
    out.append("</svg>")

    (ROOT / "contrib-heatmap.svg").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote contrib-heatmap.svg ({weeks} weeks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
