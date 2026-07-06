#!/usr/bin/env python3
"""
render_pdf.py
--------------
Builds the print-ready PDF from report_sections.json (Claude's narrative) +
history.json (numbers). This is a working skeleton with the cream/navy palette
and gap-flag styling from the manual workflow - port the fuller per-section
chart/table layout from the manually-built PDF (INR_Daily_Report_03Jul2026.pdf's
build_pdf.py) into this file once you're happy with the template.

Usage:
    python scripts/render_pdf.py --sections data/consolidated/report_sections.json \
        --out outputs/2026-07-04/report.pdf
"""
import argparse
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

NAVY = colors.HexColor("#1a2744")
CREAM = colors.HexColor("#faf6ee")
GREY = colors.HexColor("#6b6455")
TONE_HEX = {"hawkish": "#a13d3d", "dovish": "#2e7d4f", "neutral": "#c1892f"}

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY, spaceAfter=8))
styles.add(ParagraphStyle(name="ReportSub", fontName="Helvetica", fontSize=8.5, textColor=GREY, spaceAfter=10))
styles.add(ParagraphStyle(name="SectionHead", fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, spaceBefore=14, spaceAfter=6))
styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=9.5, textColor=NAVY, leading=13, spaceAfter=6))
styles.add(ParagraphStyle(name="Gap", fontName="Helvetica-Oblique", fontSize=8, textColor=colors.HexColor("#c1892f"), leading=11, spaceBefore=4, spaceAfter=4))


def signal_html(section):
    c = TONE_HEX.get(section.get("tone", "neutral"), TONE_HEX["neutral"])
    return f'<font color="{c}"><b>[{section.get("signal","")}]</b></font>'


def add_page_decor(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(2)
    canvas.line(15 * mm, A4[1] - 12 * mm, A4[0] - 15 * mm, A4[1] - 12 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawRightString(A4[0] - 15 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    sections = json.loads(Path(args.sections).read_text())
    as_of = sections.get("as_of", "unknown date")

    story = []
    story.append(Paragraph("INR Rates &amp; FX Daily Intelligence Report", styles["ReportTitle"]))
    story.append(Paragraph(f"{as_of} &middot; Automated run &middot; Not investment advice", styles["ReportSub"]))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=8))

    scorecard = sections.get("scorecard", {})
    story.append(Paragraph("Scorecard", styles["SectionHead"]))
    story.append(Paragraph(scorecard.get("recommendation", ""), styles["Body"]))

    section_titles = {
        "A": "A. G-Sec Movement (10Y-1Y)", "B": "B. Benchmark Curve (10Y)",
        "C": "C. FX / INR Borrowing (MMIFOR vs OIS)", "D": "D. Long-End Funding (G-Sec minus OIS)",
        "E": "E. Short-End Funding", "F": "F. Long-Term Funding (Bond Yield Matrix)", "G": "G. FX Position",
    }
    for key, title in section_titles.items():
        sec = sections.get("sections", {}).get(key)
        if not sec:
            continue
        story.append(Paragraph(title, styles["SectionHead"]))
        story.append(Paragraph(f"{signal_html(sec)} {sec.get('explanation','')}", styles["Body"]))

    gaps = sections.get("gaps", [])
    if gaps:
        story.append(Paragraph("Data Gaps", styles["SectionHead"]))
        for g in gaps:
            story.append(Paragraph(f"\u26a0 {g}", styles["Gap"]))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, topMargin=18 * mm, bottomMargin=16 * mm,
                             leftMargin=15 * mm, rightMargin=15 * mm)
    doc.build(story, onFirstPage=add_page_decor, onLaterPages=add_page_decor)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
