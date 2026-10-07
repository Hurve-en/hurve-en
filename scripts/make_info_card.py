#!/usr/bin/env python3
"""Build a neofetch-style info card SVG from profile.json.

Lines fade/slide in on a short stagger, then freeze. Set STATIC=1 for a frozen
frame (handy for local previews).
"""
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
W = 490
DISPLAY_PORTRAIT_W = 370  # must match the <img width> used in README.md
LINE_H, TOP, PAD_X = 26, 78, 22
CHAR_W = 8.4  # approx monospace advance at font-size 14
KEY_W = 12  # key column width in chars
MAX_VALUE_CHARS = int((W - 2 * PAD_X) / CHAR_W) - KEY_W - 1

COLORS = {"bg": "#0d1117", "border": "#30363d", "fg": "#c9d1d9", "dim": "#8b949e",
          "key": "#58a6ff", "accent": "#3fb950"}


def main() -> int:
    cfg = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
    title = cfg["card"]["title"]
    rows = cfg["card"]["rows"]
    static = os.environ.get("STATIC") == "1"

    for k, v in rows:
        if len(v) > MAX_VALUE_CHARS:
            print(f"warning: value for '{k}' is {len(v)} chars (max ~{MAX_VALUE_CHARS}); it will overflow the card")

    needed = TOP + (len(rows) + 1) * LINE_H + 24
    height = needed
    meta = ROOT / "data" / "portrait_meta.json"
    if meta.exists():  # match the rendered height of the portrait next to it
        m = json.loads(meta.read_text())
        height = max(needed, round(m["height"] * DISPLAY_PORTRAIT_W / m["width"]))

    c = COLORS
    anim = "" if static else (
        ".l{opacity:0;animation:in .5s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
    )
    static_css = ".l{opacity:1}" if static else ""

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" role="img" aria-label="Profile info card">',
        f"<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:14px}}{anim}{static_css}</style>",
        f'<rect width="{W}" height="{height}" rx="12" fill="{c["bg"]}" stroke="{c["border"]}"/>',
        f'<path d="M0 34H{W}" stroke="{c["border"]}"/>',
        '<circle cx="20" cy="17" r="5" fill="#ff5f56"/><circle cx="38" cy="17" r="5" fill="#ffbd2e"/><circle cx="56" cy="17" r="5" fill="#27c93f"/>',
        f'<text x="{W/2}" y="22" text-anchor="middle" fill="{c["dim"]}" style="font-size:12px">neofetch</text>',
    ]

    lines = []  # (svg-fragment) printed with stagger
    lines.append(f'<text x="{PAD_X}" y="{TOP-20}" fill="{c["accent"]}">$ neofetch</text>')
    lines.append(f'<text x="{PAD_X}" y="{TOP+2}" fill="{c["accent"]}" style="font-weight:700">{escape(title)}</text>')
    for i, (k, v) in enumerate(rows):
        y = TOP + (i + 1) * LINE_H + 4
        lines.append(
            f'<text x="{PAD_X}" y="{y}" xml:space="preserve">'
            f'<tspan fill="{c["key"]}" style="font-weight:700">{escape(k.ljust(KEY_W))}</tspan>'
            f'<tspan fill="{c["fg"]}">{escape(v)}</tspan></text>'
        )

    for n, frag in enumerate(lines):
        out.append(frag.replace("<text ", f'<text class="l" style="animation-delay:{0.18 * n:.2f}s" ', 1)
                   if "style=" not in frag.split(">", 1)[0]
                   else frag.replace('style="', f'class="l" style="animation-delay:{0.18 * n:.2f}s;', 1))

    # colour swatches, like real neofetch
    sw_y = TOP + (len(rows) + 1) * LINE_H + 22
    swatches = ["#f85149", "#d29922", "#3fb950", "#58a6ff", "#bc8cff", "#39c5cf"]
    sw = "".join(f'<rect x="{PAD_X + i * 22}" y="{sw_y}" width="18" height="12" rx="2" fill="{s}"/>'
                 for i, s in enumerate(swatches))
    out.append(f'<g class="l" style="animation-delay:{0.18 * len(lines):.2f}s">{sw}</g>')
    out.append("</svg>")

    (ROOT / "info-card.svg").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote info-card.svg ({W}x{height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
