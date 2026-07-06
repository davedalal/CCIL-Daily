#!/usr/bin/env python3
"""
parse_wss.py
------------
Pulls T-Bill cutoffs, repo/call rates, and forward premia off the RBI Weekly
Statistical Supplement "Ratios and Rates" table. WSS is a weekly-lag publication
(this week's PDF reports last Friday's data) - report_date below is the WSS
*publish* date; the actual data column used is the rightmost (latest) week.

Usage:
    python scripts/parse_wss.py --extract data/raw_extract --out data/raw
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

NUM = r"(-?\d+\.?\d*|\.\.)"
# GOTCHA (found during testing against the real 03-Jul-2026 report): WSS rows have
# SIX weekly columns, not five (1-year-ago + 5 recent weeks), and cells for weeks
# where a particular instrument wasn't auctioned show ".." instead of a number
# (e.g. 182D/364D T-Bills on a week with no auction). A pure-digit regex expecting
# exactly 5 numeric columns will silently mis-align and grab the wrong week as
# "latest". We match 6 tokens (number or ".."), and always take the last (6th,
# rightmost = most recent week) column as latest_value.
ROW_PATTERNS = {
    "call": r"Call Money Rate \(Weighted Average\)\s+" + (NUM + r"\s+") * 5 + NUM,
    "tb91": r"91-Day Treasury Bill \(Primary\) Yield\s+" + (NUM + r"\s+") * 5 + NUM,
    "tb182": r"182-Day Treasury Bill \(Primary\) Yield\s+" + (NUM + r"\s+") * 5 + NUM,
    "tb364": r"364-Day Treasury Bill \(Primary\) Yield\s+" + (NUM + r"\s+") * 5 + NUM,
    "g10par": r"10-Year G-Sec Par Yield \(FBIL\)\s+" + (NUM + r"\s+") * 5 + NUM,
    "repo": r"Policy Repo Rate\s+" + (NUM + r"\s+") * 5 + NUM,
}
FWD_PATTERNS = {
    "fp1m": r"1-month\s+" + (NUM + r"\s+") * 5 + NUM,
    "fp3m": r"3-month\s+" + (NUM + r"\s+") * 5 + NUM,
    "fp6m": r"6-month\s+" + (NUM + r"\s+") * 5 + NUM,
}


def latest_value(text: str, pattern: str):
    m = re.search(pattern, text)
    if not m:
        return None
    last = m.groups()[-1]  # rightmost column = most recent week
    return None if last == ".." else float(last)


def find_publish_date(all_text: str) -> str:
    m = re.search(r"(\w+ \d{1,2}, \d{4})", all_text)
    if m:
        try:
            return datetime.strptime(m.group(1), "%B %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    wss_dirs = sorted(Path(args.extract, "wss").glob("*"))
    if not wss_dirs:
        print("No WSS extract found this run - skipping.")
        return

    latest_dir = wss_dirs[-1]
    all_text = ""
    for txt_file in sorted(latest_dir.glob("*.txt"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0):
        all_text += txt_file.read_text(errors="ignore") + "\n"

    publish_date = find_publish_date(all_text) or datetime.utcnow().strftime("%Y-%m-%d")

    rates = {k: latest_value(all_text, p) for k, p in ROW_PATTERNS.items()}
    fwd = {k: latest_value(all_text, p) for k, p in FWD_PATTERNS.items()}

    missing = [k for k, v in {**rates, **fwd}.items() if v is None]
    if missing:
        print(f"WARNING: could not find WSS fields {missing} - check {latest_dir} manually, "
              f"WSS layout may have shifted.")

    result = {
        "publish_date": publish_date,
        "source": "RBI Weekly Statistical Supplement",
        "source_dir": str(latest_dir),
        "rates": rates,
        "forward_premia": fwd,
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"wss_{publish_date}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
