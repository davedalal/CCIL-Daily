#!/usr/bin/env python3
"""
render_markdown.py
--------------------
Writes a plain .md report from report_sections.json. This is the file you click
on directly in GitHub's web UI to read the report - GitHub renders .md inline
(headers, bold, tables) with no download needed, unlike .html or .jsx which
GitHub only shows as raw source code.

Usage:
    python scripts/render_markdown.py --sections data/consolidated/report_sections.json \
        --out outputs/2026-07-04/report.md
"""
import argparse
import json
from pathlib import Path

TONE_EMOJI = {"hawkish": "\U0001F534", "dovish": "\U0001F7E2", "neutral": "\U0001F7E1"}  # red/green/yellow circles

SECTION_TITLES = {
    "A": "A. G-Sec Movement (10Y-1Y)",
    "B": "B. Benchmark Curve (10Y)",
    "C": "C. FX / INR Borrowing (MMIFOR vs OIS)",
    "D": "D. Long-End Funding (G-Sec minus OIS)",
    "E": "E. Short-End Funding",
    "F": "F. Long-Term Funding (Bond Yield Matrix)",
    "G": "G. FX Position",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    sections = json.loads(Path(args.sections).read_text())
    as_of = sections.get("as_of", "unknown date")

    lines = []
    lines.append(f"# INR Rates & FX Daily Intelligence Report")
    lines.append("")
    lines.append(f"**{as_of}** &middot; Automated run &middot; Not investment advice")
    lines.append("")
    lines.append("---")
    lines.append("")

    scorecard = sections.get("scorecard", {})
    lines.append("## Scorecard")
    lines.append("")
    tone_mark = TONE_EMOJI.get(scorecard.get("tone", "neutral"), "")
    lines.append(f"{tone_mark} {scorecard.get('recommendation', '')}")
    lines.append("")

    for key, title in SECTION_TITLES.items():
        sec = sections.get("sections", {}).get(key)
        if not sec:
            continue
        mark = TONE_EMOJI.get(sec.get("tone", "neutral"), "")
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"{mark} **{sec.get('signal', '')}**")
        lines.append("")
        lines.append(sec.get("explanation", ""))
        lines.append("")

    gaps = sections.get("gaps", [])
    if gaps:
        lines.append("## Data Gaps")
        lines.append("")
        for g in gaps:
            lines.append(f"- \u26a0\uFE0F {g}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Internal use only. Not investment advice.*")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
