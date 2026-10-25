#!/usr/bin/env python3
"""Render about.json as about.svg: six info tiles + a "learning" list.

Same 840x880 terminal-window canvas as the ASCII portrait, so the two line up
side by side in the README. All content lives in about.json; this panel is
static (it does not need the daily refresh).
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
W, H = 840, 880
BG, BORDER, TILE_BG = "#0d1117", "#30363d", "#161b22"
DIM, FG, ACCENT = "#8b949e", "#e6edf3", "#3fb950"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def main() -> int:
    cfg = json.loads((ROOT / "about.json").read_text(encoding="utf-8"))
    profile = json.loads((ROOT / "profile.json").read_text())
    handle = profile.get("handle") or profile["username"]
    tiles, lst = cfg["tiles"], cfg["list"]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="About">',
        "<style>.t{animation:f .5s ease-out both}"
        "@keyframes f{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
        f".m{{font-family:{MONO}}}</style>",
        f'<rect width="{W}" height="{H}" rx="16" fill="{BG}" stroke="{BORDER}" stroke-width="2"/>',
        f'<path d="M0 44H{W}" stroke="{BORDER}" stroke-width="2"/>',
        '<circle cx="26" cy="22" r="6" fill="#ff5f56"/><circle cx="46" cy="22" r="6" fill="#ffbd2e"/><circle cx="66" cy="22" r="6" fill="#27c93f"/>',
        f'<text class="m" x="{W/2}" y="28" text-anchor="middle" fill="{DIM}" font-size="15">{escape(handle)}@github: ~$ ./{escape(cfg.get("title", "about.sh"))}</text>',
    ]

    tw, th, gap, x_left, y_top = 384, 150, 16, 28, 68
    for i, t in enumerate(tiles):
        col, row = i % 2, i // 2
        tx, ty = x_left + col * (tw + gap), y_top + row * (th + gap)
        big, unit = t["big"], t.get("unit", "")
        # shrink long values so they never run out of the tile
        size = int(min(64, 336 / (0.62 * (len(big) + (len(unit) * 0.45 if unit else 0)))))
        unit_part = (f'<tspan font-size="28" fill="{DIM}" dx="12" font-weight="400">{escape(unit)}</tspan>' if unit else "")
        out.append(
            f'<g class="t" style="animation-delay:{0.08 * i:.2f}s">'
            f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="10" fill="{TILE_BG}" stroke="{BORDER}" stroke-width="2"/>'
            f'<text class="m" x="{tx + 24}" y="{ty + 40}" fill="{DIM}" font-size="20">{escape(t["label"])}</text>'
            f'<text x="{tx + 24}" y="{ty + 104}" fill="{ACCENT if i == 0 else FG}" font-size="{size}" font-weight="700" font-family="{SANS}">{escape(big)}{unit_part}</text>'
            f'<text class="m" x="{tx + 24}" y="{ty + 134}" fill="{DIM}" font-size="20">{escape(t.get("sub", ""))}</text></g>'
        )

    # wide "learning" tile fills the rest of the window
    rows_used = (len(tiles) + 1) // 2
    cy = y_top + rows_used * (th + gap)
    cw, ch = 784, H - 28 - cy
    items = lst["items"]
    out.append(
        f'<g class="t" style="animation-delay:{0.08 * len(tiles):.2f}s">'
        f'<rect x="{x_left}" y="{cy}" width="{cw}" height="{ch}" rx="10" fill="{TILE_BG}" stroke="{BORDER}" stroke-width="2"/>'
        f'<text class="m" x="{x_left + 24}" y="{cy + 40}" fill="{DIM}" font-size="20">{escape(lst["label"])}</text></g>'
    )
    step = min(48, (ch - 80) / max(len(items), 1))
    for i, item in enumerate(items):
        y = cy + 92 + i * step
        out.append(
            f'<g class="t" style="animation-delay:{0.08 * len(tiles) + 0.15 * (i + 1):.2f}s">'
            f'<text class="m" x="{x_left + 24}" y="{y:.0f}" fill="{ACCENT}" font-size="26">▸</text>'
            f'<text class="m" x="{x_left + 58}" y="{y:.0f}" fill="{FG}" font-size="26">{escape(item)}</text></g>'
        )
    out.append("</svg>")

    (ROOT / "about.svg").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote about.svg ({len(tiles)} tiles, {len(items)} learning items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
