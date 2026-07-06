#!/usr/bin/env python3
"""
parse_ccil.py
-------------
Pulls the specific rows we care about out of the extracted CCIL text pages.

CCIL's page layout has shifted before (6 pages -> 8 pages, table numbering moved)
so this parser matches on ROW LABELS + the CCIL "Change Over (Basis Points)" column
pattern rather than hardcoded page/table numbers - it's more robust to layout
changes, but re-check it against the printed report whenever CCIL revises their
template (compare a fresh manual run's numbers against this script's output).

Usage:
    python scripts/parse_ccil.py --extract data/raw_extract --out data/raw
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

# Row label -> output key. Add rows here as needed.
GSEC_ROWS = {
    "1-Year": "1Y", "2-Year": "2Y", "5-Year": "5Y", "10-Year": "10Y",
    "15-Year": "15Y", "20-Year": "20Y", "30-Year": "30Y", "10Y Benchmark": "10Y_Bench",
}
OIS_MMIFOR_ROWS = {"1 Year": "1Y", "2 Years": "2Y", "3 Years": "3Y", "5 Years": "5Y"}

# Matches: "<label> <current> <1D> <1W> <1M> <3M> <1Y>"  (all numbers may be signed decimals)
NUM = r"(-?\d+\.?\d*)"
ROW_RE_TMPL = r"{label}\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM

# GOTCHA (found during testing against the real 03-Jul-2026 report): CCIL prints the
# OIS table (Table 3: MIBOR-OIS) and the MMIFOR table (Table 4) as ONE combined block
# where each row has BOTH tables' 6 change-over columns concatenated on a single text
# line: "<label> <6 OIS numbers> <6 MMIFOR numbers-or-dashes>". A naive per-table regex
# using the same row labels for both tables will silently match the OIS columns twice.
# We therefore parse OIS and MMIFOR together from one 12-value (or 6-value-then-dashes,
# for 1Y where MMIFOR was discontinued in 2023) row match.
NUM_OR_DASH = r"(-?\d+\.?\d*|-)"
COMBINED_ROW_RE_TMPL = (r"{label}\s+" + (NUM + r"\s+") * 6 +
                        (NUM_OR_DASH + r"\s+") * 5 + NUM_OR_DASH)


def parse_ois_mmifor(text: str):
    ois_out, mmifor_out = {}, {}
    for label, key in OIS_MMIFOR_ROWS.items():
        pattern = COMBINED_ROW_RE_TMPL.format(label=re.escape(label))
        m = re.search(pattern, text)
        if not m:
            ois_out[key] = None
            mmifor_out[key] = None
            continue
        vals = m.groups()
        oc, o1d, o1w, o1m, o3m, o1y = (float(x) for x in vals[:6])
        ois_out[key] = {"current": oc, "1D": o1d, "1W": o1w, "1M": o1m, "3M": o3m, "1Y": o1y}
        mmifor_vals = vals[6:]
        if mmifor_vals[0] == "-":
            mmifor_out[key] = None  # discontinued tenor (e.g. 1Y MMIFOR since Jul-2023)
        else:
            mc, m1d, m1w, m1m, m3m, m1y = (float(x) for x in mmifor_vals)
            mmifor_out[key] = {"current": mc, "1D": m1d, "1W": m1w, "1M": m1m, "3M": m3m, "1Y": m1y}
    return ois_out, mmifor_out


def parse_rows(text: str, row_map: dict) -> dict:
    out = {}
    for label, key in row_map.items():
        pattern = ROW_RE_TMPL.format(label=re.escape(label))
        m = re.search(pattern, text)
        if m:
            current, d1, w1, m1, m3, y1 = (float(x) for x in m.groups())
            out[key] = {"current": current, "1D": d1, "1W": w1, "1M": m1, "3M": m3, "1Y": y1}
        else:
            out[key] = None  # flag missing rather than silently omit
    return out


def find_date(all_text: str) -> str:
    m = re.search(r"Date:\s*(\d{2}-[A-Za-z]{3}-\d{4})", all_text)
    if m:
        return datetime.strptime(m.group(1), "%d-%b-%Y").strftime("%Y-%m-%d")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", required=True, help="data/raw_extract root")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ccil_dirs = sorted(Path(args.extract, "ccil").glob("*"))
    if not ccil_dirs:
        print("No CCIL extract found this run - skipping (will use last available in history.json).")
        return

    latest_dir = ccil_dirs[-1]  # assumes filename sort ~ date sort; adjust if needed
    all_text = ""
    for txt_file in sorted(latest_dir.glob("*.txt"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0):
        all_text += txt_file.read_text(errors="ignore") + "\n"

    report_date = find_date(all_text) or datetime.utcnow().strftime("%Y-%m-%d")

    ois, mmifor = parse_ois_mmifor(all_text)

    result = {
        "report_date": report_date,
        "source": "CCIL Daily Analytics",
        "source_dir": str(latest_dir),
        "gsec": parse_rows(all_text, GSEC_ROWS),
        "ois": ois,
        "mmifor": mmifor,
    }

    missing = [k for section in ("gsec", "ois", "mmifor") for k, v in result[section].items()
               if v is None and not (section == "mmifor" and k == "1Y")]  # 1Y MMIFOR is expected-missing
    if missing:
        print(f"WARNING: could not find rows {missing} - CCIL report format may have changed. "
              f"Check {latest_dir} manually and update ROW label maps in this script.")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"ccil_{report_date}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
