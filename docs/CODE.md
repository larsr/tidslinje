# Kodstil

Riktlinjer för kod i det här repot. De två första avsnitten är allmänna och
gäller även andra projekt; resten är konventioner som hör till det här repot.

## 1. Utgå från datat

Programmets tillstånd beskrivs av strukturerade datatyper, och koden byggs runt
dem. I Python är det `dataclass`-klasser. Varje typ ska gå att serialisera till
ett format som inte är bundet till ett programspråk, som YAML, JSON eller
protobuf, och tillbaka utan förlust.

Här är formatet YAML med Markdown-text (`data/`), och det är källan till allt
annat: sidan renderar det och skripten kontrollerar det. Ingen kod ska behöva
känna till något om datat som inte går att läsa ut ur filerna själva.

## 2. Beroenden går bara nedåt

Typerna ordnas i nivåer, från tillämpningsspecifika till allmänna. En typ får
bara bero på typer på lägre nivå. En lägre nivå vet ingenting om de nivåer som
använder den.

```
Tillämpning   TimelineNode, Column              vet om tidslinjen
    ↓
Domän         NodeId, Period, WikiRef,          vet om sina begrepp,
              MarkdownText                      inte om tidslinjen
    ↓
Primitiv      ValidatedString, PositiveInt      vet om strängar och tal
    ↓
Validering    Regex, Grammar, Range             vet bara hur man känner igen
```

Exempel från det här repot:

```python
@dataclass(frozen=True)
class Regex:                      # validering: vet inget om vad som matchas
    pattern: str
    def check(self, s: str) -> bool:
        return re.fullmatch(self.pattern, s) is not None

@dataclass(frozen=True)
class WikiRef:                    # domän: en Wikipedia-artikel, inget om tidslinjer
    lang: str
    article: str
    FORM: ClassVar = Regex(r"[a-z]{2,3}:.+")
    @classmethod
    def from_string(cls, s: str) -> "WikiRef":
        if not cls.FORM.check(s):
            raise ValueError(f'ogiltig wiki-referens "{s}" (ska vara språk:Artikel)')
        lang, article = s.split(":", 1)
        return cls(lang, article)
    def to_string(self) -> str:
        return f"{self.lang}:{self.article}"

@dataclass(frozen=True)
class TimelineNode:               # tillämpning: får använda allt under sig
    id: NodeId
    period: Period
    label: str
    wiki: tuple[WikiRef, ...]
    text: MarkdownText
```

`WikiRef` ska gå att använda oförändrad i ett helt annat projekt.
`Regex` vet inte att det finns Wikipedia.

Det här gör typerna lätta att återanvända, att testa var för sig och att felsöka,
eftersom varje fel hör hemma på en bestämd nivå.

## 3. Valideringen bor i typen

Varje typ kontrollerar sina egna värden, i konstruktorn eller i en
`from_string`/`validate`. Det finns inga separata schemafiler som upprepar
reglerna. Ett verktyg som ska kontrollera data, till exempel `check.py` eller en
editor, anropar typernas egna valideringar och behöver ingen kod som är
specifik för just det här schemat.

Felmeddelanden säger vad som är fel och hur det rättas, på svenska, och anger
fil och id när de finns.

**Undvik:**
- en lägre nivå som importerar eller nämner en högre
- primitiva typer med tillämpningsspecifika regler
- valideringsregler som finns på två ställen
- typer som inte går att serialisera

> De befintliga skripten i `scripts/` är skrivna som enkla funktioner och följer
> ännu inte nivåindelningen fullt ut. Ny kod och större ändringar ska röra sig
> mot den.

## 4. Python i det här repot

- Python 3.11 eller senare, körs med `uv run`. Beroenden står i `pyproject.toml`
  och är låsta i `uv.lock`. Inga paket installeras i systemets Python, och inget
  npm.
- Få beroenden. Standardbiblioteket först; ett nytt paket ska göra verkligt
  arbete.
- Ett skript per uppgift i `scripts/`. Varje skript börjar med en docstring som
  säger vad det gör och hur det körs, och avslutas med `sys.exit(main())`.
- Kort och direkt kod utan onödiga abstraktioner. Ett namn ska säga vad saken är;
  en kommentar förklarar *varför*, inte *vad*.
- Namn i koden på engelska; utskrifter, kommentarer och docstrings på svenska. Skript som körs i CI skriver fel och
  varningar som GitHub-anteckningar (`::error file=…,line=…::`) så att de syns
  vid rätt rad.
- Returkod 0 betyder att allt är i ordning; allt annat stoppar bygget. Det som
  bara är en rekommendation blir en varning, inte ett fel.

## 5. Ändringar som ska bevara beteende

När kod skriver om något som redan fungerar (formatering, konvertering,
omstrukturering) ska det finnas ett test som visar att resultatet är detsamma.
Förebilden är `scripts/test_format.py`, som renderar varje text före och efter
formateringen och kräver identisk HTML. Testet körs mot det riktiga datat, inte
bara mot konstruerade exempel.

## 6. Data som människor läser

- Filerna i `data/` ska gå att läsa och redigera i en vanlig texteditor och i
  GitHubs filvisning: Markdown-texten radbryts vid 70 tecken
  (`uv run scripts/format.py`).
- Id:n är stabila och läsbara (`stockholms-blodbad-1520`). Länkar mellan noder
  går via id, aldrig via text.
- Ingen rå HTML i texterna. Allt som visas passerar DOMPurify.
- Undvik YAML-värden som tolkas olika av olika läsare: inga nycklar som `no`,
  `yes`, `on`; citattecken runt korta strängar; `|` för längre text.

## 7. Säkerhet

- Inga hemligheter i repot, inte heller tillfälligt. Behövs en nyckel i CI ligger
  den som GitHub-secret.
- Actions låses till commit-SHA med versionen som kommentar. Varje jobb får bara
  de rättigheter det behöver.
- Tredjepartskod som checkas in (`vendor/`) anges med version och sha256 i
  `vendor/libs.yaml`.

Hur bygge, tester och säkerhetskontroller hänger ihop står i
[BUILD.md](BUILD.md).
