#!/usr/bin/env python3
"""
render_html.py
---------------
Writes a single, self-contained .html file from report_sections.json - no
external dependencies, no CDN, no build step, so it opens correctly in a
browser even offline, indefinitely, regardless of what's available at the time
you open it. All CSS is inline.

Note: GitHub does NOT execute/render .html files inline in its web UI - clicking
this file on github.com shows raw source, same as any code file. To actually see
it rendered, download it and open it locally (double-click, or "Open with
browser"), or set up GitHub Pages for this repo if you want a stable URL that
renders it directly. The report.md file (render_markdown.py) is what renders
inline on github.com without any extra step.

Usage:
    python scripts/render_html.py --sections data/consolidated/report_sections.json \
        --out outputs/2026-07-04/report.html
"""
import argparse
import json
from pathlib import Path

TONE_COLOR = {"hawkish": "#a13d3d", "dovish": "#2e7d4f", "neutral": "#c1892f"}

SECTION_TITLES = {
    "A": "A. G-Sec Movement (10Y\u22121Y)",
    "B": "B. Benchmark Curve (10Y)",
    "C": "C. FX / INR Borrowing (MMIFOR vs OIS)",
    "D": "D. Long-End Funding (G-Sec minus OIS)",
    "E": "E. Short-End Funding",
    "F": "F. Long-Term Funding (Bond Yield Matrix)",
    "G": "G. FX Position",
}

CSS = """
:root { --navy:#1a2744; --cream:#faf6ee; --grey:#6b6455; --line:#d8d0bc; }
* { box-sizing: border-box; }
body {
  background: var(--cream); color: var(--navy);
  font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  max-width: 860px; margin: 0 auto; padding: 32px 24px 64px;
  line-height: 1.55;
}
h1 { font-size: 26px; margin-bottom: 2px; }
.meta { color: var(--grey); font-size: 13px; margin-bottom: 18px; }
hr { border: none; border-top: 2px solid var(--navy); margin: 18px 0 28px; }
.card {
  background: #fff; border: 1px solid var(--line); border-radius: 8px;
  padding: 18px 20px; margin-bottom: 18px;
}
.section-title { font-weight: 700; font-size: 16px; margin-bottom: 8px; }
.badge {
  display: inline-block; font-weight: 700; font-size: 12px; letter-spacing: .02em;
  padding: 3px 10px; border-radius: 4px; margin-bottom: 8px;
}
.gaps { background: #fbf1de; border: 1px solid #c1892f55; border-radius: 6px; padding: 14px 18px; }
.gaps li { margin-bottom: 6px; font-size: 13px; }
footer { color: var(--grey); font-size: 11px; text-align: center; margin-top: 40px; }
"""


def badge(section: dict) -> str:
    tone = section.get("tone", "neutral")
    color = TONE_COLOR.get(tone, TONE_COLOR["neutral"])
    signal = section.get("signal", "")
    return (f'<span class="badge" style="background:{color}22;color:{color};'
            f'border:1px solid {color}55">{signal}</span>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    sections = json.loads(Path(args.sections).read_text())
    as_of = sections.get("as_of", "unknown date")
    scorecard = sections.get("scorecard", {})

    parts = []
    parts.append(f"<h1>INR Rates &amp; FX Daily Intelligence Report</h1>")
    parts.append(f'<div class="meta">{as_of} &middot; Automated run &middot; Not investment advice</div>')
    parts.append("<hr>")

    parts.append('<div class="card">')
    parts.append('<div class="section-title">Scorecard</div>')
    parts.append(f"<p>{scorecard.get('recommendation', '')}</p>")
    parts.append("</div>")

    for key, title in SECTION_TITLES.items():
        sec = sections.get("sections", {}).get(key)
        if not sec:
            continue
        parts.append('<div class="card">')
        parts.append(f'<div class="section-title">{title}</div>')
        parts.append(badge(sec))
        parts.append(f"<p>{sec.get('explanation', '')}</p>")
        parts.append("</div>")

    gaps = sections.get("gaps", [])
    if gaps:
        parts.append('<div class="gaps"><b>\u26a0 Data Gaps</b><ul>')
        for g in gaps:
            parts.append(f"<li>{g}</li>")
        parts.append("</ul></div>")

    parts.append('<footer>Internal use only &middot; Not investment advice</footer>')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>INR Rates &amp; FX Daily Intelligence Report - {as_of}</title>
<style>{CSS}</style>
</head>
<body>
{"".join(parts)}
</body>
</html>
"""

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
