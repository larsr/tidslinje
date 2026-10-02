# /// script
# requires-python = ">=3.11"
# dependencies = ["tzdata"]
# ///
"""Bygger sajten till _site/: kopierar index.html, data/ och vendor/ och skriver
in tiden för senaste commit som "Senast uppdaterad" i fotnoten.

    uv run scripts/build.py
"""
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
MONTHS = ["januari", "februari", "mars", "april", "maj", "juni", "juli",
          "augusti", "september", "oktober", "november", "december"]


def commit_time() -> datetime:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        return datetime.fromisoformat(out)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return datetime.now(timezone.utc)


def main() -> None:
    when = commit_time().astimezone(ZoneInfo("Europe/Stockholm"))
    stamp = f"{when.day} {MONTHS[when.month - 1]} {when.year} kl. {when:%H:%M}"
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    html = re.sub(r"<!--UPDATED-->.*?<!--/UPDATED-->",
                  f'<time datetime="{when.isoformat()}">{stamp}</time>', html, count=1, flags=re.S)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    for d in ("data", "vendor"):
        shutil.copytree(ROOT / d, OUT / d)
    (OUT / ".nojekyll").touch()
    print(f"Byggt till _site/ (senast uppdaterad {stamp}).")


if __name__ == "__main__":
    main()
