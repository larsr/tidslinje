# Världstidslinje 1000–idag

Världshistorien i 20-årsperioder, med en kolumn per region eller tema och en
förklarande artikel bakom varje punkt: <https://larsr.github.io/tidslinje/>

Texterna är skrivna med AI och inte faktagranskade.

## Innehåll

Allt innehåll finns i `data/`. `index.yaml` listar kolumnerna, och varje kolumn
har en egen fil, till exempel `data/sverige.yaml`:

```yaml
stockholms-blodbad-1520:
  period: 1520                      # första året i perioden
  label: "Stockholms blodbad 1520"  # texten i tabellen
  title: "Stockholms blodbad 1520"  # rubriken i artikeln
  wiki:
    - "sv:Stockholms blodbad"
  text: |
    Markdown. [Gustav Vasa](#gustav-vasa-1523) länkar till en annan punkt.
```

En punkt som ska visa en annan punkts artikel anger `same_as: <id>` i stället
för `title`, `wiki` och `text`.

## Arbetsgång

```sh
uv run scripts/format.py   # radbryt texterna efter redigering
uv run scripts/check.py    # kontrollera datat
uv run scripts/build.py && python3 -m http.server -d _site 8080
```

Varje push till `main` testas och publiceras automatiskt. Bygget, testerna och
säkerhetskontrollerna beskrivs i [docs/BUILD.md](docs/BUILD.md), kodstilen i
[docs/CODE.md](docs/CODE.md).
