# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "markdown-it-py>=3"]
# ///
"""Kontrollerar att datat i data/ är konsistent:

- giltig YAML och unika id:n (a-z, 0-9, bindestreck, börjar med bokstav)
- giltiga perioder, och att label, title, text och wiki finns och har rätt form
- att same_as och alla [text](#id)-länkar pekar på noder som finns
- att Markdown-texten inte innehåller rå HTML
- varnar (utan att stoppa bygget) för textrader längre än 100 tecken
  exklusive indrag; uv run scripts/format.py bryter om dem

    uv run scripts/check.py
"""
import os
import re
import sys
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

DATA = Path(__file__).resolve().parent.parent / "data"
ID = re.compile(r"^[a-z][a-z0-9-]*$")
WIKI = re.compile(r"^[a-z]{2,3}:.+")
LONG = 100
CI = bool(os.environ.get("GITHUB_ACTIONS"))
errors: list[str] = []
warnings: list[str] = []


def err(f: str, nid: str | None, msg: str) -> None:
    errors.append(f"{f}{f' [{nid}]' if nid else ''}: {msg}")


def load(name: str):
    try:
        return yaml.safe_load((DATA / name).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        err(name, None, f"ogiltig YAML: {e}")
        return None


def long_lines(f: str, src: str) -> None:
    """Varnar för långa rader i text-blocken (indraget räknas inte)."""
    in_text, key_indent = False, 0
    for no, line in enumerate(src.split("\n"), 1):
        indent = len(line) - len(line.lstrip())
        m = re.match(r"^(\s*)text: \|", line)
        if m:
            in_text, key_indent = True, len(m.group(1))
            continue
        if in_text and line.strip() and indent <= key_indent:
            in_text = False
        if in_text and len(line.strip()) > LONG:
            msg = f"rad {no} är {len(line.strip())} tecken (över {LONG}); kör uv run scripts/format.py"
            warnings.append(f"data/{f}: {msg}")
            if CI:
                print(f"::warning file=data/{f},line={no},title=Lång rad::{msg}")


def walk(tokens):
    for t in tokens:
        yield t
        if t.children:
            yield from walk(t.children)


def main() -> int:
    index = load("index.yaml")
    if not index:
        print("\n".join(errors), file=sys.stderr)
        return 1
    p = index["perioder"]
    periods = set(range(p["start"], p["slut"] + 1, p["steg"]))

    nodes: dict[str, dict] = {}
    cols: set[str] = set()
    for c in index["kolumner"]:
        cid = c.get("id")
        if not isinstance(cid, str) or not ID.match(cid):
            err("index.yaml", str(cid), "ogiltigt kolumn-id")
            continue
        if cid in cols:
            err("index.yaml", cid, "kolumnen finns två gånger")
        cols.add(cid)
        f = f"{cid}.yaml"
        if not (DATA / f).exists():
            err(f, None, "filen saknas")
            continue
        src = (DATA / f).read_text(encoding="utf-8")
        long_lines(f, src)
        for nid, n in (load(f) or {}).items():
            if not isinstance(nid, str) or not ID.match(nid):
                err(f, str(nid), "id måste bestå av a-z, 0-9 och bindestreck och börja med en bokstav")
                continue
            if nid in nodes:
                err(f, nid, f"id:t används redan i {nodes[nid]['_file']}")
            if not isinstance(n, dict):
                err(f, nid, "noden är tom")
                continue
            if n.get("period") not in periods:
                err(f, nid, f"ogiltig period {n.get('period')!r}")
            if not isinstance(n.get("label"), str) or not n["label"].strip():
                err(f, nid, "label saknas")
            if not n.get("same_as"):
                if not isinstance(n.get("title"), str):
                    err(f, nid, "title saknas")
                if not isinstance(n.get("text"), str) or not n["text"].strip():
                    err(f, nid, "text saknas")
                for w in n.get("wiki") or []:
                    if not isinstance(w, str) or not WIKI.match(w):
                        err(f, nid, f'ogiltig wiki-post "{w}" (ska vara språk:Artikel)')
            nodes[nid] = {**n, "_file": f}

    md = MarkdownIt("commonmark")
    links = 0
    for nid, n in nodes.items():
        f = n["_file"]
        if n.get("same_as") and n["same_as"] not in nodes:
            err(f, nid, f'same_as pekar på okänd nod "{n["same_as"]}"')
        if not n.get("text"):
            continue
        for t in walk(md.parse(n["text"])):
            if t.type in ("html_block", "html_inline"):
                err(f, nid, f"rå HTML i texten: {t.content.strip()[:40]}")
            if t.type == "link_open":
                href = t.attrGet("href") or ""
                if href.startswith("#"):
                    links += 1
                    target = href[1:]
                    if target not in nodes:
                        err(f, nid, f'länk till okänd nod "#{target}"')
                    elif target == nid:
                        err(f, nid, "noden länkar till sig själv")

    if warnings and not CI:
        print(f"{len(warnings)} varningar:\n" + "\n".join(warnings[:20]) + ("\n…" if len(warnings) > 20 else ""))
    if errors:
        print(f"{len(errors)} fel:\n" + "\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {len(cols)} kolumner, {len(nodes)} noder, {links} interna länkar, {len(warnings)} varningar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
