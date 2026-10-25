#!/usr/bin/env python3
"""Build stack-strip.svg: grouped tech pills, generated from stack.json.

Pure SVG, no external icon services (those render on someone else's server and
can break). Pills fade in once on a short stagger, then freeze.
Width is 860 so it lines up with the heatmap above it in the README.
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
W = 860
PAD_X = 28
LABEL_W = 150
CHAR_W = 7.4  # approx monospace advance at 12px
PILL_H, PILL_GAP, ROW_GAP = 26, 10, 14
TOP = 56
BG, BORDER, DIM, FG = "#0d1117", "#30363d", "#8b949e", "#c9d1d9"


def pill_width(text: str) -> float:
    return len(text) * CHAR_W + 22


def main() -> int:
    cfg = json.loads((ROOT / "stack.json").read_text(encoding="utf-8"))
    groups = cfg["groups"]
    right = W - PAD_X
    start_x = PAD_X + LABEL_W

    # lay out rows, wrapping a group's pills onto extra lines if it would overflow
    rows = []  # (label|None, color, [(text, x, w)])
    for g in groups:
        x, line = start_x, []
        first = True
        for item in g["items"]:
            w = pill_width(item)
            if line and x + w > right:
                rows.append((g["label"] if first else None, g["color"], line))
                first, x, line = False, start_x, []
            line.append((item, x, w))
            x += w + PILL_GAP
        rows.append((g["label"] if first else None, g["color"], line))

    height = TOP + len(rows) * (PILL_H + ROW_GAP) + 10
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" role="img" aria-label="Tech stack">',
        "<style>.p{opacity:0;animation:in .45s ease-out both}"
        "@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        "text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}</style>",
        f'<rect width="{W}" height="{height}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M0 34H{W}" stroke="{BORDER}"/>',
        '<circle cx="20" cy="17" r="5" fill="#ff5f56"/><circle cx="38" cy="17" r="5" fill="#ffbd2e"/><circle cx="56" cy="17" r="5" fill="#27c93f"/>',
        f'<text x="{W/2}" y="22" text-anchor="middle" fill="{DIM}" font-size="12">{escape(cfg.get("title", "stack"))}</text>',
    ]

    n = 0
    for r, (label, color, pills) in enumerate(rows):
        y = TOP + r * (PILL_H + ROW_GAP)
        if label:
            out.append(
                f'<text class="p" style="animation-delay:{0.07 * n:.2f}s" x="{PAD_X}" y="{y + 17}" '
                f'fill="{DIM}" font-size="12">{escape(label)}</text>'
            )
        for text, x, w in pills:
            out.append(
                f'<g class="p" style="animation-delay:{0.07 * n:.2f}s">'
                f'<rect x="{x:g}" y="{y}" width="{w:g}" height="{PILL_H}" rx="13" fill="{color}" fill-opacity="0.12" stroke="{color}" stroke-opacity="0.55"/>'
                f'<text x="{x + w / 2:g}" y="{y + 17}" text-anchor="middle" fill="{FG}" font-size="12">{escape(text)}</text></g>'
            )
            n += 1
    out.append("</svg>")

    (ROOT / "stack-strip.svg").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote stack-strip.svg ({W}x{height}, {n} pills, {len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
