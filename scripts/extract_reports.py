#!/usr/bin/env python3
"""
extract_reports.py
-------------------
CCIL / Arete / WSS files are uploaded with a .pdf extension but are often actually
ZIP archives (containing numbered .txt + .jpeg page files and a manifest.json) or,
less often, genuine PDFs. This script inspects magic bytes for every file in the
inbox, extracts ZIP-disguised files, and copies real PDFs through for the pdf-reading
fallback path.

Usage:
    python scripts/extract_reports.py --inbox inbox --out data/raw_extract
"""
import argparse
import json
import shutil
import zipfile
from pathlib import Path


def sniff(path: Path) -> str:
    with open(path, "rb") as f:
        head = f.read(8)
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if head.startswith(b"%PDF"):
        return "pdf"
    return "unknown"


def classify_name(name: str) -> str:
    n = name.lower()
    if "ccil" in n:
        return "ccil"
    if "wss" in n:
        return "wss"
    if "fixed_income" in n or "fixd_income" in n or "arete" in n:
        return "arete"
    return "other"


def extract_one(path: Path, out_root: Path):
    kind = classify_name(path.name)
    filetype = sniff(path)
    dest = out_root / kind / path.stem
    dest.mkdir(parents=True, exist_ok=True)

    if filetype == "zip":
        with zipfile.ZipFile(path) as zf:
            zf.extractall(dest)
    elif filetype == "pdf":
        # Genuine PDF - copy through; downstream parser can pdftotext -layout it.
        shutil.copy(path, dest / path.name)
    else:
        print(f"WARNING: {path.name} is neither a ZIP nor a PDF by magic bytes - skipping")
        return None

    return {"source_file": path.name, "kind": kind, "filetype": filetype, "extracted_to": str(dest)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    inbox = Path(args.inbox)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    manifest = []
    for path in sorted(inbox.iterdir()):
        if path.name.startswith("."):
            continue
        if path.is_dir():
            continue
        result = extract_one(path, out_root)
        if result:
            manifest.append(result)

    if not manifest:
        print("No extractable files found in inbox/ - nothing to do this run.")

    with open(out_root / "extract_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Extracted {len(manifest)} file(s). Manifest written to {out_root / 'extract_manifest.json'}")


if __name__ == "__main__":
    main()
