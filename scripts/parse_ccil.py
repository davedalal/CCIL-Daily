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
import subprocess
from datetime import datetime
from pathlib import Path

# Row label -> output key. Add rows here as needed.
GSEC_ROWS = {
    "1-Year": "1Y", "2-Year": "2Y", "5-Year": "5Y", "10-Year": "10Y",
    "15-Year": "15Y", "20-Year": "20Y", "30-Year": "30Y", "10Y Benchmark": "10Y_Bench",
}
OIS_MMIFOR_ROWS = {"1 Year": "1Y", "2 Years": "2Y", "3 Years": "3Y", "5 Years": "5Y"}

# Matches: "<label> <current> <1D> <1W> <1M> <3M> <1Y>"  (all numbers may be signed decimals)
# NB: separator is same-line whitespace only (no \n). A \s+ separator would also match
# across a line break, and since GSEC_ROWS labels can appear with only a bare label on
# their own line (see PAIR_ROW_RE_TMPL below), that would let a label match the WRONG
# row's numbers on the following line instead of correctly falling through to None.
NUM = r"(-?\d+\.?\d*)"
SEP = r"[ \t]+"
ROW_RE_TMPL = r"{label}" + SEP + NUM + SEP + NUM + SEP + NUM + SEP + NUM + SEP + NUM + SEP + NUM

# GOTCHA (found during testing against the real 03-Jul-2026 report): CCIL prints the
# OIS table (Table 3: MIBOR-OIS) and the MMIFOR table (Table 4) as ONE combined block
# where each row has BOTH tables' 6 change-over columns concatenated on a single text
# line: "<label> <6 OIS numbers> <6 MMIFOR numbers-or-dashes>". A naive per-table regex
# using the same row labels for both tables will silently match the OIS columns twice.
# We therefore parse OIS and MMIFOR together from one 12-value (or 6-value-then-dashes,
# for 1Y where MMIFOR was discontinued in 2023) row match.
NUM_OR_DASH = r"(-?\d+\.?\d*|-)"
COMBINED_ROW_RE_TMPL = (r"{label}" + SEP + (NUM + SEP) * 6 +
                        (NUM_OR_DASH + SEP) * 5 + NUM_OR_DASH)


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


# GOTCHA (found 06-Jul-2026 report): when Table 1's chart column squeezes the table,
# pdftotext -layout can no longer fit "<label> <6 numbers>" on one line. Instead it
# prints two row labels back-to-back, then the same two rows' values GROUPED BY
# COLUMN (both current values, then both 1-Day values, then both 1-Week values, ...).
# i.e. for labels [A, B]: current_A, current_B, 1D_A, 1D_B, 1W_A, 1W_B, 1M_A, 1M_B,
# 3M_A, 3M_B, 1Y_A, 1Y_B - one number per line. GSEC_ROWS happens to list its 8 tenors
# in exactly the pairs CCIL renders together (1Y/2Y, 5Y/10Y, 15Y/20Y, 30Y/10Y Bench),
# so we parse two labels + 12 solo numbers at a time.
PAIR_ROW_RE_TMPL = (
    r"{label_a}\s*\n{label_b}\s*\n"
    + r"".join(rf"\s*{NUM}\s*\n" for _ in range(11))
    + rf"\s*{NUM}"  # last value's line may have trailing footnote text after it
)


def parse_rows_paired(text: str, row_map: dict) -> dict:
    labels = list(row_map.items())
    out = {}
    for i in range(0, len(labels), 2):
        (label_a, key_a), (label_b, key_b) = labels[i], labels[i + 1]
        pattern = PAIR_ROW_RE_TMPL.format(label_a=re.escape(label_a), label_b=re.escape(label_b))
        m = re.search(pattern, text)
        if not m:
            out[key_a] = None
            out[key_b] = None
            continue
        vals = [float(x) for x in m.groups()]
        current_a, current_b, d1_a, d1_b, w1_a, w1_b, m1_a, m1_b, m3_a, m3_b, y1_a, y1_b = vals
        out[key_a] = {"current": current_a, "1D": d1_a, "1W": w1_a, "1M": m1_a, "3M": m3_a, "1Y": y1_a}
        out[key_b] = {"current": current_b, "1D": d1_b, "1W": w1_b, "1M": m1_b, "3M": m3_b, "1Y": y1_b}
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
    txt_files = sorted(latest_dir.glob("*.txt"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0)
    all_text = ""
    for txt_file in txt_files:
        all_text += txt_file.read_text(errors="ignore") + "\n"

    if not txt_files:
        # Genuine (non-ZIP) PDF case: extract_reports.py just copies the raw PDF
        # through, so there are no pre-rendered .txt pages - run pdftotext ourselves.
        pdf_files = sorted(latest_dir.glob("*.pdf"))
        for pdf_file in pdf_files:
            proc = subprocess.run(["pdftotext", "-layout", str(pdf_file), "-"],
                                   capture_output=True, text=True)
            if proc.returncode == 0:
                all_text += proc.stdout + "\n"
            else:
                print(f"WARNING: pdftotext failed on {pdf_file}: {proc.stderr.strip()}")

    report_date = find_date(all_text) or datetime.utcnow().strftime("%Y-%m-%d")

    ois, mmifor = parse_ois_mmifor(all_text)

    gsec = parse_rows(all_text, GSEC_ROWS)
    missing_gsec = [key for key, val in gsec.items() if val is None]
    if missing_gsec:
        # Fall back to the paired-column layout (see parse_rows_paired docstring)
        # for whichever tenors the single-line regex couldn't find.
        gsec_paired = parse_rows_paired(all_text, GSEC_ROWS)
        for key in missing_gsec:
            if gsec_paired.get(key) is not None:
                gsec[key] = gsec_paired[key]

    result = {
        "report_date": report_date,
        "source": "CCIL Daily Analytics",
        "source_dir": str(latest_dir),
        "gsec": gsec,
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
