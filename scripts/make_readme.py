#!/usr/bin/env python3
"""Generate README.md and the link-button SVGs from profile.json + links.json.

README.md is a generated file: edit profile.json / links.json / stack.json and
re-run this script instead of editing the README by hand.

Link buttons are local SVGs (links/*.svg) rather than shields.io images, so they
cannot break when an outside service is down. Entries in links.json with an
empty "url" are skipped.
"""
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parent.parent
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
CHAR_W, H = 9.4, 40  # 13px mono bold + letter-spacing


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "link"


def button_svg(label: str, value: str, color: str) -> str:
    l, v = label.upper(), value.upper()
    lw = len(l) * CHAR_W + 36
    vw = len(v) * CHAR_W + 36
    w = lw + vw
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{H}" viewBox="0 0 {w:g} {H}" role="img" aria-label="{escape(label)}: {escape(value)}">'
        f'<clipPath id="r"><rect width="{w:g}" height="{H}" rx="5"/></clipPath>'
        f'<g clip-path="url(#r)">'
        f'<rect width="{lw:g}" height="{H}" fill="#3b4048"/><rect x="{lw:g}" width="{vw:g}" height="{H}" fill="{color}"/></g>'
        f'<g font-family="{MONO}" font-size="13" font-weight="700" letter-spacing="1.4" text-anchor="middle" fill="#ffffff">'
        f'<text x="{lw / 2:g}" y="25" fill="#e6edf3">{escape(l)}</text>'
        f'<text x="{lw + vw / 2:g}" y="25">{escape(v)}</text></g></svg>'
    )


def main() -> int:
    profile = json.loads((ROOT / "profile.json").read_text())
    links_cfg = json.loads((ROOT / "links.json").read_text())
    h = profile.get("handle") or profile["username"]

    (ROOT / "links").mkdir(exist_ok=True)
    anchors, skipped = [], []
    for item in links_cfg["links"]:
        if not item.get("url"):
            skipped.append(item["label"])
            continue
        f = f"links/{slug(item['label'])}.svg"
        (ROOT / f).write_text(button_svg(item["label"], item["value"], item.get("color", "#1f6feb")), encoding="utf-8")
        anchors.append(
            f'<a href={quoteattr(item["url"])}><img src="./{f}" height="{H}" alt={quoteattr(item["label"] + ": " + item["value"])} /></a>'
        )

    tagline = escape(links_cfg.get("tagline", ""))
    links_html = "\n".join(anchors)
    readme = f"""<div align="center">

<h3><code>{h}@github ~ $ ./contributions.sh</code></h3>
<img src="./contrib-heatmap.svg" width="860" alt="Contribution graph, refreshed daily" />

<br><br>

<h3><code>{h}@github ~ $ whoami</code></h3>
<table>
<tr>
<td valign="top"><img src="./ascii-portrait.svg" width="420" alt="ASCII portrait" /></td>
<td valign="top"><img src="./about.svg" width="420" alt="About me" /></td>
</tr>
</table>

<br><br>

<h3><code>{h}@github ~ $ cat stack.txt</code></h3>
<img src="./stack-strip.svg" width="860" alt="Tech stack" />

<br><br>

<h3><code>{h}@github ~ $ ./links.sh</code></h3>
<p><b>{tagline}</b></p>
{links_html}

</div>
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"wrote README.md ({len(anchors)} link buttons)")
    if skipped:
        print("skipped (no url yet): " + ", ".join(skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
