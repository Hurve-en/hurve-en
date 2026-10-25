#!/usr/bin/env python3
"""Convert source-prepped.png into a framed, self-typing ASCII portrait SVG.

Output is an 840x880 terminal window (title bar, portrait, whoami footer), the
same canvas as stats.svg, so the two line up when shown side by side.

Reveal technique: every text row is covered by a background-coloured rectangle
whose left edge slides right, uncovering the text. Only plain <rect> x/width are
animated, which every browser supports (an earlier clipPath version did not
work in Safari).

Usage: python scripts/make_ascii_svg.py [--invert] [--cols 110]
"""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space = blank
CW, LH, FONT = 5.0, 9.0, 8.4  # char cell width/height and font size of the raw art
W, H = 840, 880
BAR_TOP, FOOT_H, PAD = 44, 52, 28
FG, BG, BORDER, DIM = "#c9d1d9", "#0d1117", "#30363d", "#8b949e"
ROW_STAGGER, ROW_DUR = 0.06, 0.5  # seconds
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "source-prepped.png"))
    ap.add_argument("--out", default=str(ROOT / "ascii-portrait.svg"))
    ap.add_argument("--cols", type=int, default=110)
    ap.add_argument("--invert", action="store_true", help="dark pixels -> sparse glyphs")
    args = ap.parse_args()

    profile = json.loads((ROOT / "profile.json").read_text())
    handle = profile.get("handle") or profile["username"]
    name = profile.get("name") or handle

    img = Image.open(args.src).convert("L")
    w, h = img.size
    cols = args.cols
    rows = max(1, round(cols * (h / w) * (CW / LH)))
    g = np.asarray(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32)

    t = g / 255.0 if args.invert else (255.0 - g) / 255.0
    idx = np.rint(t * (len(RAMP) - 1)).astype(int)
    lines = ["".join(RAMP[i] for i in row) for row in idx]

    text_w, text_h = cols * CW, rows * LH
    avail_w = W - 2 * PAD
    avail_h = H - BAR_TOP - FOOT_H - 2 * PAD
    s = min(avail_w / text_w, avail_h / text_h)
    tx = (W - text_w * s) / 2
    ty = BAR_TOP + PAD + (avail_h - text_h * s) / 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="ASCII portrait">',
        f'<rect width="{W}" height="{H}" rx="16" fill="{BG}" stroke="{BORDER}" stroke-width="2"/>',
        f'<path d="M0 {BAR_TOP}H{W}" stroke="{BORDER}" stroke-width="2"/>',
        f'<path d="M0 {H - FOOT_H}H{W}" stroke="{BORDER}" stroke-width="2"/>',
        '<circle cx="26" cy="22" r="6" fill="#ff5f56"/><circle cx="46" cy="22" r="6" fill="#ffbd2e"/><circle cx="66" cy="22" r="6" fill="#27c93f"/>',
        f'<text x="{W/2}" y="28" text-anchor="middle" fill="{DIM}" font-size="15" font-family="{MONO}">{escape(handle)}@github: ~$ ./portrait.sh</text>',
        f'<text x="{PAD}" y="{H - 19}" font-size="16" font-family="{MONO}" fill="{DIM}">{escape(handle)}@github:~$ whoami '
        f'<tspan fill="#e6edf3" font-weight="700">{escape(name)}</tspan></text>',
        f'<g transform="translate({tx:.2f},{ty:.2f}) scale({s:.4f})" fill="{FG}" font-family="{MONO}" font-size="{FONT}">',
    ]
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = i * LH
        begin = i * ROW_STAGGER
        end = begin + ROW_DUR
        parts.append(
            f'<text x="0" y="{y + LH - 2:g}" textLength="{text_w:g}" lengthAdjust="spacing" '
            f'xml:space="preserve" style="white-space:pre">{escape(line)}</text>'
        )
        parts.append(
            f'<rect x="0" y="{y:g}" width="{text_w:g}" height="{LH:g}" fill="{BG}">'
            f'<animate attributeName="x" from="0" to="{text_w:g}" dur="{ROW_DUR}s" begin="{begin:.2f}s" fill="freeze"/>'
            f'<animate attributeName="width" from="{text_w:g}" to="0" dur="{ROW_DUR}s" begin="{begin:.2f}s" fill="freeze"/>'
            f"</rect>"
        )
        parts.append(
            f'<rect x="0" y="{y:g}" width="{CW:g}" height="{LH - 1:g}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="0" to="{text_w - CW:g}" dur="{ROW_DUR}s" begin="{begin:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.2f}s" fill="freeze"/></rect>'
        )
    parts += ["</g>", "</svg>"]

    Path(args.out).write_text("\n".join(parts), encoding="utf-8")
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "portrait_meta.json").write_text(json.dumps({"width": W, "height": H}), encoding="utf-8")
    print(f"wrote {args.out} ({cols}x{rows} chars, scale {s:.2f}x, canvas {W}x{H})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
