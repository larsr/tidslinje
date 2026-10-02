"""Röktest: öppnar den byggda sidan (_site/) i Chromium och kontrollerar att
tabellen renderas, att sökning, popup och interna länkar fungerar och att
inga skriptfel uppstår. Typsnitt och Wikipedia blockeras, så testet behöver
inget nät.

    uv run scripts/build.py && uv run scripts/smoke.py

Första gången: uv run playwright install chromium
"""
import functools
import http.server
import os
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent / "_site"
CI = bool(os.environ.get("GITHUB_ACTIONS"))
failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"{'✓' if ok else '✗'} {msg}")
    if not ok:
        failed.append(msg)
        if CI:
            print(f"::error title=Röktest::{msg}")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".yaml": "text/yaml; charset=utf-8"}

    def log_message(self, *args):  # noqa: D401
        pass


def main() -> int:
    if not (SITE / "index.html").exists():
        print("_site/ saknas: kör uv run scripts/build.py först", file=sys.stderr)
        return 1
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=SITE))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1400, "height": 900})
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.route("**/*", lambda r: r.abort() if not r.request.url.startswith(url) else r.continue_())

            page.goto(url)
            page.wait_for_selector("li.has", timeout=15000)
            n = page.locator("li.has").count()
            check(n > 1000, f"tabellen visar {n} punkter")
            check("ej byggd" not in page.text_content("footer"), "fotnoten visar byggdatum")

            page.fill("#q", "elektricitet")
            page.wait_for_timeout(400)
            hits = page.text_content("#hits") or ""
            check(hits.split(" ")[0].isdigit(), f"sökning ger träffar ({hits})")
            page.fill("#q", "kalmarunionen")  # ord som i Markdown-källan kan vara radbrutna
            page.wait_for_timeout(400)
            check((page.text_content("#hits") or "").split(" ")[0].isdigit(), "sökning hittar text i artiklarna")
            page.fill("#q", "")
            page.wait_for_timeout(400)

            page.click("li.has")
            page.wait_for_selector("#pop:not([hidden]) .md p")
            check(True, "popup öppnas med artikeltext")
            ref = page.query_selector("#pop a.ref")
            check(ref is not None, "artikeln har en intern länk")
            if ref:
                before = page.text_content("#pop h2")
                ref.click()
                page.wait_for_timeout(300)
                check(page.text_content("#pop h2") != before, "intern länk öppnar en annan artikel")
                check(page.query_selector("#pop .back") is not None, "tillbaka-knappen visas")

            nid = page.evaluate("Object.keys(NODES)[5]")
            page.goto(f"{url}?direkt#{nid}")
            page.wait_for_selector("#pop:not([hidden]) h2", timeout=5000)
            check(True, "direktlänk med #id öppnar artikeln")
            check(not errors, "inga skriptfel" + (": " + "; ".join(errors) if errors else ""))
        except Exception as e:  # noqa: BLE001
            check(False, f"undantag: {str(e).splitlines()[0]}")
        finally:
            browser.close()
            server.shutdown()

    if failed:
        print(f"{len(failed)} test misslyckades", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
