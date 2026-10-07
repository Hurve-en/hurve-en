#!/usr/bin/env python3
"""Convert source-prepped.png into a monochrome, self-typing ASCII SVG.

Reveal technique: every text row is covered by a background-coloured rectangle
whose left edge slides right (x grows, width shrinks), uncovering the text.
This only animates plain <rect> x/width, which every browser supports.

Usage: python scripts/make_ascii_svg.py [--invert] [--cols 100]
"""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space = blank
CW, LH, FONT = 5.0, 9.0, 8.4  # char cell width/height and font size (px)
PAD = 14
FG, BG, BORDER = "#c9d1d9", "#0d1117", "#30363d"
ROW_STAGGER, ROW_DUR = 0.06, 0.5  # seconds


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "source-prepped.png"))
    ap.add_argument("--out", default=str(ROOT / "ascii-portrait.svg"))
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--invert", action="store_true", help="dark pixels -> sparse glyphs")
    args = ap.parse_args()

    img = Image.open(args.src).convert("L")
    w, h = img.size
    cols = args.cols
    rows = max(1, round(cols * (h / w) * (CW / LH)))
    g = np.asarray(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32)

    t = g / 255.0 if args.invert else (255.0 - g) / 255.0
    idx = np.rint(t * (len(RAMP) - 1)).astype(int)
    lines = ["".join(RAMP[i] for i in row) for row in idx]

    text_w, text_h = cols * CW, rows * LH
    total_w, total_h = text_w + 2 * PAD, text_h + 2 * PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w:g} {total_h:g}" '
        f'width="{total_w:g}" height="{total_h:g}" role="img" aria-label="ASCII portrait">',
        f'<rect width="{total_w:g}" height="{total_h:g}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<g transform="translate({PAD},{PAD})" fill="{FG}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FONT}">',
    ]
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = i * LH
        begin = i * ROW_STAGGER
        end = begin + ROW_DUR
        # 1) the text, always present
        parts.append(
            f'<text x="0" y="{y + LH - 2:g}" textLength="{text_w:g}" lengthAdjust="spacing" '
            f'xml:space="preserve" style="white-space:pre">{escape(line)}</text>'
        )
        # 2) the cover: fully covers the row at first, then its left edge slides right
        parts.append(
            f'<rect x="0" y="{y:g}" width="{text_w:g}" height="{LH:g}" fill="{BG}">'
            f'<animate attributeName="x" from="0" to="{text_w:g}" dur="{ROW_DUR}s" begin="{begin:.2f}s" fill="freeze"/>'
            f'<animate attributeName="width" from="{text_w:g}" to="0" dur="{ROW_DUR}s" begin="{begin:.2f}s" fill="freeze"/>'
            f"</rect>"
        )
        # 3) the block cursor riding the reveal edge, gone when the row is done
        parts.append(
            f'<rect x="0" y="{y:g}" width="{CW:g}" height="{LH - 1:g}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="0" to="{text_w - CW:g}" dur="{ROW_DUR}s" begin="{begin:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.2f}s" fill="freeze"/></rect>'
        )
    parts += ["</g>", "</svg>"]

    Path(args.out).write_text("\n".join(parts), encoding="utf-8")
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "portrait_meta.json").write_text(
        json.dumps({"width": total_w, "height": total_h}), encoding="utf-8"
    )
    print(f"wrote {args.out} ({cols}x{rows} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
