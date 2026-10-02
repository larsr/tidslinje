"""Radbryter Markdown-texterna i data/*.yaml så att de går att läsa i en
vanlig texteditor eller i GitHubs filvisning.

    uv run scripts/format.py           skriver om filerna
    uv run scripts/format.py --check   visar bara vilka filer som skulle ändras

Bara blocken under `text: |` ändras, och bara vanliga stycken: raderna i ett
stycke slås ihop och bryts om vid WIDTH tecken (indraget räknas inte).
Stycken med listor, rubriker, citat eller kod lämnas orörda, liksom allt
annat i filen, även kommentarer.
"""
import re
import sys
from pathlib import Path

WIDTH = 70
DATA = Path(__file__).resolve().parent.parent / "data"

# Ett ord som inte får hamna först på en rad: Markdown skulle då kunna tolka
# raden som rubrik, lista, citat, kodblock, tabell eller rubrikstreck.
RISKY = re.compile(r"^(#{1,6}|[-+*]|=+|-+|>|`{3,}|~{3,}|\||\d{1,9}[.)])$|^(#|>|```|~~~|\|)")
# Stycken med egen Markdown-struktur skrivs inte om.
STRUCTURED = re.compile(r"^\s*([-+*]\s|\d{1,9}[.)]\s|#{1,6}\s|>|```|~~~|\||\s{4})")
TEXT_KEY = re.compile(r"^(\s*)text: \|[-+]?\s*$")


def wrap_paragraph(text: str, width: int = WIDTH) -> list[str]:
    """Bryter ett stycke vid mellanslag så att ingen rad blir längre än width,
    utom när ett enskilt ord (eller ett ord med fastklistrat riskabelt ord)
    själv är längre."""
    units: list[str] = []
    for word in text.split():
        if units and RISKY.search(word):
            units[-1] += " " + word  # får aldrig börja en rad
        else:
            units.append(word)
    lines: list[str] = []
    line = ""
    for u in units:
        if line and len(line) + 1 + len(u) > width:
            lines.append(line)
            line = u
        else:
            line = f"{line} {u}" if line else u
    if line:
        lines.append(line)
    return lines


def format_block(block: list[str], indent: str) -> list[str]:
    paras: list[list[str]] = []
    cur: list[str] = []
    for line in block:
        if not line.strip():
            if cur:
                paras.append(cur)
            cur = []
        else:
            cur.append(line[len(indent):])
    if cur:
        paras.append(cur)
    out: list[str] = []
    for i, p in enumerate(paras):
        if i:
            out.append("")
        if any(STRUCTURED.match(l) for l in p):
            out += [indent + l for l in p]
        else:
            out += [indent + l for l in wrap_paragraph(" ".join(l.strip() for l in p))]
    return out


def format_file(src: str) -> str:
    lines = src.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        out.append(lines[i])
        m = TEXT_KEY.match(lines[i])
        i += 1
        if not m:
            continue
        key_indent = len(m.group(1))
        # Blocket fortsätter så länge raderna är tomma eller mer indragna än nyckeln.
        block: list[str] = []
        while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > key_indent):
            block.append(lines[i])
            i += 1
        trailing: list[str] = []  # tomma rader före nästa nyckel
        while block and not block[-1].strip():
            trailing.insert(0, block.pop())
        if block:
            first = next(l for l in block if l.strip())
            indent = first[: len(first) - len(first.lstrip())]
            out += format_block(block, indent)
        out += trailing
    return "\n".join(out)


def main() -> int:
    check_only = "--check" in sys.argv
    changed = 0
    for p in sorted(DATA.glob("*.yaml")):
        src = p.read_text(encoding="utf-8")
        res = format_file(src)
        if res != src:
            changed += 1
            if check_only:
                print(f"skulle formateras: data/{p.name}")
            else:
                p.write_text(res, encoding="utf-8")
                print(f"formaterad: data/{p.name}")
    if not changed:
        print("Alla filer är redan formaterade.")
    elif check_only:
        print(f"{changed} filer behöver formateras: kör uv run scripts/format.py")
    return 1 if check_only and changed else 0


if __name__ == "__main__":
    sys.exit(main())
