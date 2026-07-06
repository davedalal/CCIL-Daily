# INR Daily Rates & FX Intelligence — Automation

Automates everything **after** you download the raw CCIL / RBI WSS / Arete files.
Two ways to run the pipeline; pick one:

| | Path A: Claude Code Routine | Path B: GitHub Actions |
|---|---|---|
| **Billing** | Your existing Pro/Max/Team/Enterprise subscription — no extra cost | Metered Anthropic API tokens (billed per run) |
| **Setup** | Paste `ROUTINE_PROMPT.md` into a Routine at claude.ai/code/routines | Push repo + add `ANTHROPIC_API_KEY` secret |
| **Analysis step** | Claude writes `report_sections.json` itself, in-session | `run_analysis.py` calls the API |
| **Automated CCIL fetch** | **Doesn't work** — confirmed the sandbox has no general internet egress (see below) | Best-effort — has full outbound internet, subject to bot-detection risk (see below) |
| **File drop needed** | All 3 files (CCIL, WSS, Arete) manually into `inbox/` | WSS + Arete manually; CCIL attempted automatically |
| **Status** | Research preview — behavior may change | Stable, standard CI |
| **Best for** | Individual use, avoiding token cost | Teams, or wanting full unattended fetch a real chance of working |

Both paths run the exact same deterministic scripts (`extract_reports.py`,
`parse_ccil.py`, `parse_wss.py`, `build_dataset.py`, `render_markdown.py`,
`render_html.py`, `render_pdf.py`) — the only difference is *who* writes the
narrative analysis, *how that step gets billed*, and *whether CCIL's download
can be automated at all*. Use one or the other, not both at once.

```
you download all 3 files manually (Routine path)
   or WSS/Arete manually, CCIL attempted automatically (GitHub Actions path)
        │
        ▼
   drop into inbox/, push
        │
        ▼
┌── Claude Code Routine — or GitHub Actions, whichever path you set up ──┐
│  1. fetch_ccil.py       -> GitHub Actions only; skipped entirely on    │
│                            the Routine path (sandboxed, no egress)     │
│  2. extract_reports.py  -> unzips the disguised-as-PDF files           │
│  3. parse_ccil.py /                                                    │
│     parse_wss.py        -> regex-pulls tables into data/raw/*.json     │
│  4. build_dataset.py    -> merges into data/consolidated/history.json  │
│  5. ANALYSIS: Claude writes report_sections.json directly in-session   │
│     (or run_analysis.py -> API call, metered, GitHub Actions path only)│
│  6. render_markdown.py  -> report.md   (renders inline on github.com)  │
│  7. render_html.py      -> report.html (self-contained, open in a browser)│
│  8. render_pdf.py       -> reportlab + matplotlib -> report.pdf        │
│  9. commit + push outputs back to the repo                             │
└──────────────────────────────────────────────────────────────────────────┘
```

## Path A: Claude Code Routine (no extra token cost)

1. Push this repo to GitHub (see Setup below) — no `ANTHROPIC_API_KEY` needed for
   this path.
2. Go to claude.ai/code/routines → create a new Routine.
3. **Repository:** this repo. **Trigger:** Scheduled, weekday mornings, set after
   you've already dropped all 3 files into `inbox/` and pushed — see the network
   restriction below for why that's non-negotiable on this path.
4. **Prompt:** open `ROUTINE_PROMPT.md` in this repo and paste its contents
   (everything under "Routine prompt" at the bottom of that file) into the
   Routine's prompt field.
5. Test with **"Run now"** before trusting the schedule.
6. Check whether the Routine can push straight to `main` or only to a
   `claude/`-prefixed branch by default for this repo — if it's branch-restricted,
   either enable unrestricted pushes for this repo or plan to merge a PR each
   morning.

That's it — no secret to add, no per-run bill. This is a research-preview
feature, so run it alongside spot-checks for the first couple of weeks.

**Confirmed by testing a real run: Routines have no general internet egress.**
The first live run tried `fetch_ccil.py` and failed with a proxy-level error
(`ERR_TUNNEL_CONNECTION_FAILED`). To isolate whether that was CCIL-specific
(bot detection, changed page) or a total block, we tested `curl` against a
completely unrelated, generic domain from inside the Routine — it got the exact
same kind of failure (a 403 policy denial from the environment's egress proxy).
That rules out CCIL's site as the cause: **the Routine sandbox can't reach any
external website**, likely by design (an allowlist that includes GitHub, since
that's core to how Routines work, and blocks everything else). `ROUTINE_PROMPT.md`
reflects this — it doesn't attempt `fetch_ccil.py` at all, and all three files
need to be manually in `inbox/` before the Routine runs.

## Path B: GitHub Actions (metered API billing)

1. Push this repo to GitHub.
2. **Add a secret**: repo → Settings → Secrets and variables → Actions → New
   repository secret → name `ANTHROPIC_API_KEY`, value = your API key from
   console.anthropic.com. Never commit the key itself.
3. The workflow at `.github/workflows/daily-run.yml` runs on push to `inbox/**`,
   on a schedule, or manually via "Run workflow" in the Actions tab.
4. Every run that reaches the analysis step calls the Anthropic API and is
   billed per token — check console.anthropic.com's usage page if you want to
   track what this costs you.
5. This is the only path where `fetch_ccil.py` has a chance of working at all,
   since GitHub Actions runners have full outbound internet (unlike a Routine's
   sandbox) — though still subject to the bot-detection caveat below, unproven
   from GitHub's actual IP ranges specifically.

## Setup common to both paths

1. `pip install -r requirements.txt` locally if you want to test scripts before
   relying on either path.
2. `playwright install chromium` if you want to test `fetch_ccil.py` locally —
   note this only makes sense to test for the GitHub Actions path; it will never
   work inside a Routine, confirmed above.
3. Adjust `parse_ccil.py` / `parse_wss.py` regexes if CCIL/RBI change their
   report format again (CCIL's report went from 6 pages to 8 between two of our
   manual runs — these parsers are the thing most likely to need occasional
   maintenance, regardless of which path runs them).

## Daily flow

**Routine path:** download all 3 files yourself, drop into `inbox/`, push —
every morning, before the Routine's scheduled run time.

```bash
mv ~/Downloads/CCIL_DAILY_ANALYSIS_*.pdf inr-daily-intel/inbox/
mv ~/Downloads/WSS*.pdf inr-daily-intel/inbox/
mv ~/Downloads/Daily_Fixed_Income_Report_*.pdf inr-daily-intel/inbox/   # when a new one exists
cd inr-daily-intel
git add inbox/ && git commit -m "data: $(date +%F)" && git push
```

**GitHub Actions path:** same, but you can skip the CCIL line — `fetch_ccil.py`
attempts it automatically as part of the workflow run. Pushing to `inbox/**`
also triggers the Action automatically.

## Why the CCIL fetch step only works (maybe) on the GitHub Actions path

Good news, discovered while setting this up: **CCIL's Daily Market Analytics
report needs no login at all** — confirmed by testing in an incognito browser.
So `scripts/fetch_ccil.py` attempts a real automated download on the GitHub
Actions path, before falling back to whatever's manually in `inbox/`.

The fetch turned out to need two different mechanisms, both confirmed by
hand-testing:

1. **Finding today's exact URL needs a real rendered page.** The download link
   is generated by client-side JS after the initial page load — a plain HTTP GET
   of the page's HTML doesn't contain it, only the generic placeholder.
   `fetch_ccil.py` uses a headless browser (Playwright) just for this discovery
   step.
2. **Downloading the actual PDF, once you have the URL, needs no browser at
   all** — confirmed with a plain `curl` request, no special headers. So the
   script uses a lightweight `requests.get()` for the actual (often large) file
   download, not the heavier browser context. (An earlier automated fetch
   attempt from a different tool got blocked by bot detection — that turned out
   to be specific to that tool's IP/fingerprint, not a general block on
   non-browser clients, which is why splitting the two steps works.)

This is meaningfully less fragile than login-automation would have been — no
credentials to store or expire — but it's not bulletproof, and it's specific to
GitHub Actions:

- **Confirmed NOT to work on the Routine path at all** — see the network-egress
  finding above. Don't put `fetch_ccil.py` in a Routine's prompt.
- **Not yet proven from GitHub Actions' actual runner IPs.** Datacenter IP
  ranges are sometimes flagged by WAFs even when a home/office connection isn't.
  Test this for real before trusting it unattended — the step is wired with
  `continue-on-error: true` specifically because it may not work every day, or
  ever, from CI, and the pipeline should degrade gracefully to manual `inbox/`
  files rather than fail the whole run.
- **CCIL's page template can change** — `fetch_ccil.py` looks for a
  `guestUserCheck('...')` JS call embedded in the rendered page to find today's
  link; if CCIL redesigns the page, this breaks and needs a manual look/update,
  same as the CCIL/WSS *parsers* already do.
- **WSS (RBI) and Arete are not automated this way yet.** RBI's WSS is also
  genuinely public and worth the same treatment eventually on the GitHub Actions
  path; Arete is a private analyst distribution and almost certainly needs to
  stay a manual download regardless of path.
- **Compliance check still worth doing separately from the technical question:**
  CCIL's site states it does not authorize commercial use of its data without
  written permission. Automated retrieval for internal treasury analysis is a
  judgment call, not something this scaffold resolves for you — worth a quick
  check with compliance/legal.

If `fetch_ccil.py` doesn't work reliably even on the GitHub Actions path, the
fallback is simply: you download manually and drop the file in `inbox/`, same
as the Routine path always requires.

A middle ground that removes even the `git push` step: a small **local folder
watcher** (`scripts/watch_and_push.py`, included) that watches your Downloads
folder and auto-commits+pushes any new CCIL/WSS/Arete-looking file the moment
you save it — so your only manual action is clicking "Download" in the browser.
This works for both paths, since it runs on your own machine, not in a sandbox.

## Repo layout

| Path | Purpose |
|---|---|
| `inbox/` | Drop today's raw downloaded files here (any extension — the script detects ZIP/JPEG/real-PDF by magic bytes, same as we did manually) |
| `data/raw/*.json` | Parsed fields for one day |
| `data/consolidated/history.json` | Rolling time series across all days — this is what makes 3M/6M/9M/1Y trend charts possible without re-parsing everything each time |
| `scripts/` | All pipeline steps, each runnable standalone for debugging |
| `ROUTINE_PROMPT.md` | Paste-in prompt for the Claude Code Routine (primary path) |
| `outputs/YYYY-MM-DD/report.md` | Renders inline on github.com — click it, no download needed |
| `outputs/YYYY-MM-DD/report.html` | Self-contained styled version — download and open in a browser |
| `outputs/YYYY-MM-DD/report.pdf` | Print-ready version |
| `.github/workflows/daily-run.yml` | Only relevant if you set up the GitHub Actions alternative instead of the Routine — not used in the Routine path |

## What Claude does vs. what plain code does

- **Plain code** (deterministic, no LLM, identical in both paths): unzip,
  regex-extract table values, compute derived spreads (10Y-1Y, MMIFOR-OIS, etc.),
  append to history.json. This is the part that must never hallucinate a number,
  so it stays code, not a prompt.
- **The analysis step** (`ROUTINE_PROMPT.md` in Path A, `run_analysis.py` in Path
  B — pick one): takes the clean numeric history.json and writes the narrative —
  signal descriptions, borrowing/hedging recommendation, scorecard tone
  (hawkish/dovish/neutral), gap flags for anything genuinely missing. This is the
  part that benefits from the same judgment applied in our manual runs, whichever
  path is doing it. On the first real Routine run with an empty `inbox/`, this
  worked correctly — it reported zero data and skipped a recommendation rather
  than inventing one, which is the intended behavior, not a bug.

## Notifications (optional, not scaffolded)

Add a step to `daily-run.yml` (Path B) or a line in the Routine prompt (Path A)
to email yourself or post to Slack/Teams with a link to the new
`outputs/YYYY-MM-DD/` commit. Ask if you'd like this wired up.
