"""Testar scripts/format.py mot det riktiga datat:

- formateringen ändrar aldrig hur en text renderas (samma HTML, bortsett från
  radbrytningar som Markdown ändå behandlar som mellanslag)
- inga andra fält i YAML-filerna ändras
- formateringen är idempotent
- vanliga stycken blir högst WIDTH tecken breda, utom ord som själva är längre

    uv run scripts/test_format.py
"""
import re
import sys
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from format import DATA, WIDTH, format_file, wrap_paragraph  # noqa: E402

md = MarkdownIt("commonmark")


def render(text: str | None) -> str:
    return re.sub(r"\s+", " ", md.render(text or "")).strip()


def unit_tests() -> list[str]:
    fails = []
    # Ord som skulle starta en lista, rubrik eller ett citat får aldrig börja en rad.
    for risky in ["-", "+", "#", ">", "1.", "2)", "===", "---", "```", "|"]:
        text = ("ord " * 16) + risky + " slut " + ("ord " * 16)
        for w in (10, 20, 30, 70):
            lines = wrap_paragraph(text, w)
            if any(l.split()[0] == risky for l in lines):
                fails.append(f"'{risky}' började en rad vid bredd {w}")
            if render("\n".join(lines)) != render(text):
                fails.append(f"'{risky}' ändrade renderingen vid bredd {w}")
    return fails


def main() -> int:
    fails = unit_tests()
    texts = 0
    for p in sorted(DATA.glob("*.yaml")):
        src = p.read_text(encoding="utf-8")
        once = format_file(src)
        if format_file(once) != once:
            fails.append(f"{p.name}: formateringen är inte idempotent")
        a, b = yaml.safe_load(src) or {}, yaml.safe_load(once) or {}
        if list(a) != list(b):
            fails.append(f"{p.name}: nycklarna ändrades")
            continue
        for k in a:
            if not isinstance(a[k], dict):
                if a[k] != b[k]:
                    fails.append(f"{p.name}: {k} ändrades")
                continue
            x, y = dict(a[k]), dict(b[k])
            tx, ty = x.pop("text", None), y.pop("text", None)
            if x != y:
                fails.append(f"{p.name} [{k}]: andra fält än text ändrades")
            if tx is not None:
                texts += 1
                if render(tx) != render(ty):
                    fails.append(f"{p.name} [{k}]: renderingen ändrades")
                for line in (ty or "").splitlines():
                    # En för lång rad är bara tillåten om den inte går att bryta.
                    if len(line) > WIDTH and len(wrap_paragraph(line, WIDTH)) > 1:
                        fails.append(f"{p.name} [{k}]: rad på {len(line)} tecken")
                        break
    if fails:
        print(f"{len(fails)} fel:\n" + "\n".join(fails[:50]), file=sys.stderr)
        return 1
    print(f"OK: formateringen ändrar inte renderingen av {texts} texter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
