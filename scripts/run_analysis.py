#!/usr/bin/env python3
"""
run_analysis.py
----------------
*** ONLY needed for the GitHub Actions + API key path. ***
*** If you're using a Claude Code Routine instead, skip this file entirely -   ***
*** see ROUTINE_PROMPT.md, where Claude does this step in-session using your  ***
*** subscription's included usage, with no ANTHROPIC_API_KEY and no          ***
*** per-token billing.                                                        ***

This script is the one step in the GitHub-Actions version of the pipeline that
calls the Anthropic API directly and is billed per token (separate from any
Claude.ai/Claude Code subscription). Use it if you specifically want a
traditional CI-based setup with metered API billing - e.g. a team scenario
where individual subscription seats don't fit, or you want the pipeline to run
with zero dependency on the Routines research-preview feature.

Everything upstream (extraction, regex parsing, spread math) is deterministic
code so numbers can never be hallucinated either way. This step takes the clean
numeric history.json and asks Claude to produce the NARRATIVE layer: signal
descriptions, borrowing/hedging recommendation, scorecard tone, and explicit gap
flags - the same judgment calls made in our manual runs, applied consistently
every morning.

Requires: ANTHROPIC_API_KEY environment variable (set as a GitHub Actions secret).
This will incur standard per-token API charges on every run.

Usage:
    python scripts/run_analysis.py --history data/consolidated/history.json \
        --out data/consolidated/report_sections.json
"""
import argparse
import json
import os
from pathlib import Path

import anthropic

SYSTEM_PROMPT = """You are a fixed-income/FX analyst producing a daily INR rates and \
FX intelligence briefing for a treasury desk. You are given a JSON time series of \
G-Sec yields, OIS, MMIFOR, T-Bill cutoffs, repo/call rates, and forward premia, all \
sourced from CCIL and RBI WSS.

Rules you must follow exactly:
1. NEVER invent a number. Every figure in your output must trace to a value present \
   in the input JSON, or be a simple, clearly-labeled derived calculation (e.g. a \
   spread = difference of two input values) that you show your work for.
2. If a tenor, horizon (e.g. 6M/9M), or series has no data in the input, say so \
   explicitly in a "gaps" field - do not interpolate or estimate silently.
3. For every section (A: curve slope, B: 10Y trajectory, C: MMIFOR-OIS hedge cost, \
   D: G-Sec-OIS supply premium, E: short-end funding, F: long-end funding if bond \
   data present, G: FX position if FX data present), produce: a one-line signal, a \
   2-4 sentence explanation grounded in the numbers, and a tone (hawkish/dovish/neutral).
4. Produce a top-level "scorecard" with a borrowing/hedging recommendation synthesizing \
   all sections, in the same style as: short end vs long end vs FCY hedged vs supply \
   premium framing.
5. Output ONLY valid JSON matching this shape, nothing else:
{
  "as_of": "YYYY-MM-DD",
  "sections": {
    "A": {"signal": "...", "explanation": "...", "tone": "hawkish|dovish|neutral"},
    "B": {...}, "C": {...}, "D": {...}, "E": {...}, "F": {...}, "G": {...}
  },
  "scorecard": {"recommendation": "...", "tone": "..."},
  "gaps": ["...", "..."]
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="claude-sonnet-5")
    args = ap.parse_args()

    history = json.loads(Path(args.history).read_text())

    # Only send the last ~90 days to keep the prompt small and cheap; trend math
    # over 3M/1Y already happened upstream in the parse step where possible.
    dates = sorted(history.get("ccil", {}).keys())[-90:]
    trimmed = {
        "ccil": {d: history["ccil"][d] for d in dates},
        "wss": history.get("wss", {}),
    }

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model=args.model,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(trimmed)}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        sections = json.loads(text)
    except json.JSONDecodeError:
        print("ERROR: Claude did not return valid JSON. Raw output was:")
        print(text)
        raise

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(sections, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
