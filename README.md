# Världstidslinje 1000–idag

En interaktiv tabell över världshistorien i 20-årssteg, med en kolumn per region eller tema
och en förklarande artikel bakom varje punkt. Publiceras på <https://larsr.github.io/tidslinje/>.

Texterna är skrivna med AI och är inte faktagranskade.

## Data

Allt innehåll ligger i `data/` som YAML med Markdown-text:

- `data/index.yaml` – perioderna och kolumnerna i visningsordning.
- `data/<kolumn>.yaml` – noderna i en kolumn. Ordningen i filen är ordningen i tabellcellen.

En nod:

```yaml
stockholms-blodbad-1520:          # id: a-z, 0-9 och bindestreck, börjar med bokstav
  period: 1520                    # första året i 20-årsperioden
  label: "Stockholms blodbad 1520"  # texten i tabellen
  title: "Stockholms blodbad 1520"  # rubriken i popupen
  wiki:                           # Wikipedia-länkar, språk:Artikel
    - "sv:Stockholms blodbad"
  text: |                         # Markdown
    Under Kalmarunionen … se [Gustav Vasa 1523](#gustav-vasa-1523).
```

- `[text](#id)` i texten blir en länk till en annan nod: hovra för sammanfattning, klicka för att öppna den.
- `same_as: <id>` i stället för `title`/`text`/`wiki` gör att noden visar en annan nods artikel.
- Rå HTML i texten är inte tillåten; `uv run scripts/check.py` stoppar den.

Kolumnernas id:n är medvetet längre än två bokstäver, så att YAML 1.1-tolkare inte gör om till exempel `no` till `false`.

Texterna radbryts vid 70 tecken (indraget räknas inte) så att filerna går att läsa
i en texteditor och i GitHubs filvisning. Markdown behandlar radbrytningar inuti ett
stycke som mellanslag; stycken skiljs åt med en tom rad.

## Verktyg

Skripten är Python och körs med [uv](https://docs.astral.sh/uv/). Varje skript
anger sina egna beroenden, så inget behöver installeras i förväg.

```sh
uv run scripts/format.py        # radbryt texterna efter redigering (--check: ändra inget)
uv run scripts/check.py         # datakontroll: id:n, perioder, länkar, same_as, ingen rå HTML
uv run scripts/test_format.py   # formateringen får inte ändra hur någon text renderas
uv run scripts/build.py         # bygger _site/ med "Senast uppdaterad"
uv run scripts/smoke.py         # röktest i Chromium mot _site/
python3 -m http.server -d _site 8080   # titta lokalt
```

Röktestet behöver Chromium första gången:
`uv run --with playwright==1.56.0 playwright install chromium`.

`check.py` varnar (utan att stoppa bygget) för textrader över 100 tecken.

## Publicering

`.github/workflows/pages.yml` kör kontroll, formateringstest, bygge och röktest vid
varje push till `main` och publicerar `_site/` till GitHub Pages bara om allt går
igenom. Pull requests testas men publiceras inte. Tiden för senaste commit skrivs in
som "Senast uppdaterad" i sidans fotnot.

Pages är inställt på **Settings → Pages → Source: GitHub Actions**.

JS-biblioteken som sidan använder ligger i `vendor/` (se `vendor/README.md`).
