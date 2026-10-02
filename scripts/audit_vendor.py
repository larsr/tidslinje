"""Kontrollerar JS-biblioteken i vendor/ mot vendor/libs.yaml:

- att varje fil finns och har den kontrollsumma (sha256) som står i libs.yaml,
  så att versionsnumret som granskas verkligen motsvarar filen som publiceras
- att OSV (https://osv.dev) inte känner till sårbarheter i den versionen
- varnar (utan att stoppa) om en nyare version finns i npm-registret

    uv run scripts/audit_vendor.py
"""
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

import yaml

VENDOR = Path(__file__).resolve().parent.parent / "vendor"
CI = bool(os.environ.get("GITHUB_ACTIONS"))
OSV = "https://api.osv.dev/v1"


def http_json(url: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 – fasta https-adresser
        return json.load(r)


def annotate(level: str, msg: str) -> None:
    if CI:
        print(f"::{level} file=vendor/libs.yaml,title=JS-bibliotek::{msg}")


def main() -> int:
    libs = yaml.safe_load((VENDOR / "libs.yaml").read_text(encoding="utf-8"))
    problems = 0

    for lib in libs:
        f = VENDOR / lib["file"]
        if not f.exists():
            print(f"✗ {lib['file']} saknas")
            annotate("error", f"{lib['file']} saknas")
            problems += 1
            continue
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if digest != lib["sha256"]:
            msg = f"{lib['file']} har sha256 {digest}, libs.yaml anger {lib['sha256']}"
            print(f"✗ {msg}")
            annotate("error", msg)
            problems += 1

    queries = [{"package": {"name": l["name"], "ecosystem": l["ecosystem"]}, "version": str(l["version"])} for l in libs]
    results = http_json(f"{OSV}/querybatch", {"queries": queries})["results"]
    for lib, res in zip(libs, results):
        vulns = res.get("vulns") or []
        if not vulns:
            print(f"✓ {lib['name']} {lib['version']}: inga kända sårbarheter")
        for v in vulns:
            detail = http_json(f"{OSV}/vulns/{v['id']}")
            aliases = ", ".join(a for a in detail.get("aliases", []) if a.startswith("CVE-"))
            msg = f"{lib['name']} {lib['version']}: {v['id']}{f' ({aliases})' if aliases else ''} – {detail.get('summary', '')}"
            print(f"✗ {msg}")
            annotate("error", msg)
            problems += 1

        if lib["ecosystem"] == "npm":
            try:
                latest = http_json(f"https://registry.npmjs.org/{lib['name']}/latest")["version"]
                if latest != str(lib["version"]):
                    msg = f"{lib['name']}: version {latest} finns (vendor/ har {lib['version']})"
                    print(f"! {msg}")
                    annotate("warning", msg)
            except OSError as e:
                print(f"! kunde inte fråga npm om {lib['name']}: {e}")

    if problems:
        print(f"{problems} problem i vendor/", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
