# Claude Code Routine — daily INR pipeline (subscription usage, no API key)

Paste this as the Routine's prompt. It replaces `scripts/run_analysis.py` for this
path — a Routine IS a full Claude Code session, so Claude can write the narrative
analysis directly, in-session, using your Pro/Max/Team/Enterprise subscription's
included usage. No `ANTHROPIC_API_KEY` needed, no per-token billing.

(If you'd rather run this via GitHub Actions with a metered API key instead — e.g.
for a team where individual subscription seats don't fit — use `run_analysis.py`
and `.github/workflows/daily-run.yml` instead, and skip this file. The two paths
are alternatives, not both-at-once.)

---

## Routine prompt (copy everything below this line)

Run the daily INR rates & FX intelligence pipeline in this repo:

1. Run `python scripts/fetch_ccil.py --out inbox` — best-effort automated CCIL
   download. If it fails (bot detection, template change), don't treat that as
   fatal — just continue; the pipeline should still run against whatever files
   are already sitting in `inbox/` from a manual drop.
2. Run `python scripts/extract_reports.py --inbox inbox --out data/raw_extract`.
3. Run `python scripts/parse_ccil.py --extract data/raw_extract --out data/raw`
   and `python scripts/parse_wss.py --extract data/raw_extract --out data/raw`.
   If either prints a WARNING about missing fields, open the relevant extracted
   `.txt` page yourself, figure out whether CCIL/RBI changed their report
   template, and either fix the regex in that script or note the specific gap
   explicitly in the final report — do not guess at a number.
4. Run `python scripts/build_dataset.py --raw data/raw --history data/consolidated/history.json`.
5. Read `data/consolidated/history.json`. Using ONLY the numbers in that file
   (plus simple, clearly-labeled derived calculations you show your work for —
   e.g. a spread is just the difference of two values already in the file),
   write `data/consolidated/report_sections.json` yourself, in this JSON shape:

   ```json
   {
     "as_of": "YYYY-MM-DD",
     "sections": {
       "A": {"signal": "...", "explanation": "...", "tone": "hawkish|dovish|neutral"},
       "B": {...}, "C": {...}, "D": {...}, "E": {...}, "F": {...}, "G": {...}
     },
     "scorecard": {"recommendation": "...", "tone": "..."},
     "gaps": ["...", "..."]
   }
   ```

   Section meanings: A = 10Y-1Y G-Sec curve slope, B = 10Y benchmark trajectory,
   C = MMIFOR vs OIS (FCY hedging cost), D = G-Sec minus OIS (supply premium),
   E = short-end funding (T-Bills, WACR vs repo, CD/CP), F = long-term funding
   (bond yield matrix, if bond data is present), G = FX position (if forward
   premia / USD data is present). Only include a section if the underlying data
   for it actually exists in history.json for this run - skip it rather than
   invent one, and note the omission in "gaps".

   Rules, non-negotiable:
   - Never invent a number. Every figure must trace to history.json or be a
     simple derived calculation you show.
   - If a tenor, horizon (e.g. 6M/9M), or series has no data, say so explicitly
     in "gaps" - do not interpolate or estimate silently.
   - The "scorecard.recommendation" should synthesize all sections into a
     short-end vs long-end vs FCY-hedged vs supply-premium borrowing/hedging
     view, in plain prose, 3-5 sentences.

6. Run `python scripts/render_dashboard.py --sections data/consolidated/report_sections.json --template templates/dashboard_template.jsx --out outputs/<today's date>/dashboard.jsx`.
7. Run `python scripts/render_pdf.py --sections data/consolidated/report_sections.json --out outputs/<today's date>/report.pdf`.
8. Commit `outputs/<today's date>/` and `data/consolidated/` with message
   `Daily run: <today's date>`, and push.

If any step fails in a way that isn't graceful (not the CCIL-fetch best-effort
case above), stop and report exactly what failed rather than committing a
partial or guessed report.
