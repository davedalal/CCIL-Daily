#!/usr/bin/env python3
"""
render_dashboard.py
--------------------
Injects history.json (numbers) + report_sections.json (Claude's narrative) into
the dashboard_template.jsx as a single DATA constant, and writes the final,
ready-to-view .jsx artifact for that day.

Usage:
    python scripts/render_dashboard.py --sections data/consolidated/report_sections.json \
        --template templates/dashboard_template.jsx --out outputs/2026-07-04/dashboard.jsx
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", required=True, help="report_sections.json from run_analysis.py")
    ap.add_argument("--history", default="data/consolidated/history.json")
    ap.add_argument("--template", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    sections = json.loads(Path(args.sections).read_text())
    history_path = Path(args.history)
    history = json.loads(history_path.read_text()) if history_path.exists() else {"ccil": {}, "wss": {}}

    merged = dict(history)
    merged["sections_meta"] = sections

    data_js = "const DATA = " + json.dumps(merged) + ";"

    template = Path(args.template).read_text()
    rendered = template.replace("// __DATA_PLACEHOLDER__", data_js)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
