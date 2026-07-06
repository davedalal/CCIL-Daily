#!/usr/bin/env python3
"""
build_dataset.py
-----------------
Merges today's ccil_*.json / wss_*.json into a single rolling history.json,
keyed by date. This is what unlocks proper 3M/6M/9M/1Y trend charts over time
without re-parsing old PDFs - every day's run just appends one more entry.

Usage:
    python scripts/build_dataset.py --raw data/raw --history data/consolidated/history.json
"""
import argparse
import json
from pathlib import Path


def load_history(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"ccil": {}, "wss": {}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--history", required=True)
    args = ap.parse_args()

    raw_dir = Path(args.raw)
    history_path = Path(args.history)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history = load_history(history_path)

    for f in raw_dir.glob("ccil_*.json"):
        data = json.loads(f.read_text())
        history["ccil"][data["report_date"]] = data

    for f in raw_dir.glob("wss_*.json"):
        data = json.loads(f.read_text())
        history["wss"][data["publish_date"]] = data

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2, sort_keys=True)

    print(f"History now has {len(history['ccil'])} CCIL day(s) and {len(history['wss'])} WSS week(s).")
    print(f"Written to {history_path}")


if __name__ == "__main__":
    main()
