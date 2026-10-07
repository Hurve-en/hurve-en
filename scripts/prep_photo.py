#!/usr/bin/env python3
"""Prep a photo for ASCII conversion.

1. (optional) remove the background with rembg
2. crop tightly around the subject whenever the image has a transparent cutout
3. boost local contrast with CLAHE so flat lighting gets real highlights/shadows
4. composite onto a plain background (white by default, black with --bg black)

Pairing: white bg -> use make_ascii_svg.py normally.
         black bg -> use make_ascii_svg.py --invert (face reads bright on the dark card).

Usage: python scripts/prep_photo.py source-photo.png [--no-rembg] [--clip 3.0] [--bg black]
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--out", default=str(ROOT / "source-prepped.png"))
    ap.add_argument("--no-rembg", action="store_true", help="skip background removal")
    ap.add_argument("--clip", type=float, default=3.0, help="CLAHE clip limit")
    ap.add_argument("--bg", choices=["white", "black"], default="white", help="background to composite onto")
    args = ap.parse_args()

    img = Image.open(args.photo).convert("RGBA")
    if not args.no_rembg:
        try:
            from rembg import remove

            img = remove(img)
        except ImportError:
            print("rembg not installed; continuing without background removal.", file=sys.stderr)

    arr = np.array(img)
    alpha = arr[:, :, 3].astype(np.float32) / 255.0

    # Crop tightly around the subject if there is a real transparent area
    # (from rembg OR from a cutout you made yourself, e.g. macOS Remove Background).
    if (alpha < 0.5).mean() > 0.01:
        ys, xs = np.where(alpha > 0.5)
        if len(xs):
            m = int(0.04 * max(arr.shape[:2]))
            y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, arr.shape[0])
            x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, arr.shape[1])
            arr, alpha = arr[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=args.clip, tileGridSize=(8, 8)).apply(gray)

    bg = 0.0 if args.bg == "black" else 255.0
    out = gray.astype(np.float32) * alpha + bg * (1.0 - alpha)
    Image.fromarray(out.clip(0, 255).astype(np.uint8), "L").save(args.out)
    print(f"wrote {args.out} (background: {args.bg})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
