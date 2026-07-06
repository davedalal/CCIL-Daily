#!/usr/bin/env python3
"""
watch_and_push.py  (OPTIONAL - run on your own machine, not in GitHub Actions)
--------------------------------------------------------------------------------
Watches your Downloads folder. The moment a file matching CCIL/WSS/Arete naming
patterns appears, it copies it into inbox/ and runs `git add/commit/push` for you.
This removes the manual git step - your only remaining action each morning is
clicking "Download" on the three portals.

Run this once in a terminal and leave it running (or set it up as a login item /
scheduled task on your machine):

    pip install watchdog
    python scripts/watch_and_push.py --downloads ~/Downloads --repo .

It intentionally does NOT touch your browser or log into any portal - it only
reacts to files that already landed in Downloads because you clicked the button.
"""
import argparse
import re
import shutil
import subprocess
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

PATTERNS = [
    re.compile(r"CCIL_DAILY_ANALYSIS.*\.pdf", re.I),
    re.compile(r"WSS\d+.*\.pdf", re.I),
    re.compile(r"Daily_Fix(e)?d?_Income_Report.*\.pdf", re.I),
]


def matches(name: str) -> bool:
    return any(p.search(name) for p in PATTERNS)


class Handler(FileSystemEventHandler):
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.inbox = repo_root / "inbox"
        self.inbox.mkdir(exist_ok=True)

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not matches(path.name):
            return
        # Downloads can fire the event before the browser finishes writing -
        # wait until file size stabilizes before copying.
        last_size = -1
        for _ in range(20):
            size = path.stat().st_size
            if size == last_size and size > 0:
                break
            last_size = size
            time.sleep(0.5)

        dest = self.inbox / path.name
        shutil.copy(path, dest)
        print(f"Copied {path.name} -> inbox/")

        subprocess.run(["git", "add", "inbox/"], cwd=self.repo_root, check=True)
        commit = subprocess.run(
            ["git", "commit", "-m", f"data: auto-add {path.name}"],
            cwd=self.repo_root,
        )
        if commit.returncode == 0:
            subprocess.run(["git", "push"], cwd=self.repo_root, check=True)
            print("Pushed - GitHub Actions run should start shortly.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", required=True)
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    repo_root = Path(args.repo).resolve()
    downloads = Path(args.downloads).expanduser().resolve()

    observer = Observer()
    observer.schedule(Handler(repo_root), str(downloads), recursive=False)
    observer.start()
    print(f"Watching {downloads} for CCIL/WSS/Arete files. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
