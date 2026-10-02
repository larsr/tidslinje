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
- Rå HTML i texten är inte tillåten; `npm run check` stoppar den.

Kolumnernas id:n är medvetet längre än två bokstäver, så att YAML 1.1-tolkare inte gör om till exempel `no` till `false`.

## Bygga och testa

```sh
npm ci
npm test          # check (datakontroll) + build (_site/) + smoke (Chromium-röktest)
npm run serve     # bygger och serverar på http://localhost:8080
```

`npm run check` kontrollerar unika id:n, giltiga perioder och att alla länkar och `same_as` pekar på noder som finns.

## Publicering

`.github/workflows/pages.yml` kör kontroll, bygge och röktest vid varje push till `main` och publicerar `_site/` till GitHub Pages bara om allt går igenom. Pull requests testas men publiceras inte. Datumet för senaste commit skrivs in som "Senast uppdaterad" i sidans fotnot.

Pages måste vara inställt på **Settings → Pages → Source: GitHub Actions**.
