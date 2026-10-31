# QE-acceptatie met Playwright

Uitgangspunt: [oorspronkelijke requirements v0.3](REQUIREMENTS.md). P1 is geen acceptatiecriterium voor deze eerste versie. Een geslaagde testset is geen verklaring dat alle P0-eisen zijn afgetekend.

## Uitvoeren

```sh
.venv/bin/pip install -r requirements-test.txt
.venv/bin/python -m playwright install chromium firefox webkit
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/e2e --browser chromium --browser firefox --browser webkit --tracing retain-on-failure --screenshot only-on-failure --junitxml=test-results/results.xml
```

Op Linux is voor installatie van browserafhankelijkheden `python -m playwright install --with-deps` beschikbaar. Alleen backendtests draaien met de gewone `pytest`-opdracht; de browsermap wordt expliciet gekozen. Browserdependencies staan apart van productiedependencies.

Iedere browsertest start een echte Uvicorn-server op een vrije lokale poort met een nieuwe tijdelijke SQLite-database, een afzonderlijke fotocache en een fictief beheerwachtwoord. De tests lezen geen `.env`, gebruiken geen echte integratieaccounts en raken `data/family.db` niet aan. Twee-apparatentests gebruiken afzonderlijke browsercontexts met eigen cookies en localStorage. Playwright bewaart bij fouten screenshots en traces in `test-results/`. De GitHub-workflow voert dezelfde suite per browser uit en bewaart die bestanden 14 dagen.

## Unittests en backendregressies

De standaardrun ontdekt tests onder `tests/`, met uitzondering van `e2e/`. Alleen de nieuwe unittests draaien met `.venv/bin/python -m pytest tests/unit -q`. Deze starten geen server, openen geen database en maken geen netwerkverbinding.

De unitreview voegde 35 gevallen toe: planning rond startdatum en schrikkeldag, weekdagen, individuele en gezamenlijke uitvoering, archivering, invoergrenzen voor stappen/punten/tijdvensters, datum-normalisatie, Home Assistant-selectie en hergebruik van geheimen. Twee aanvullende API-regressies controleren dat zowel opslaan als ontdekken een gewijzigd CalDAV- of Immich-adres weigert voordat een opgeslagen geheim wordt doorgestuurd. Bij weigering blijft de eerdere configuratie intact.

**Nieuwste backendrun na de beloningsimplementatie: 68 geslaagd** (33 unit- en 35 API/backendtests). De eerdere browsermatrix staat hieronder afzonderlijk.

## Koppeling aan requirements

| Requirements | Geautomatiseerd bewijs |
|---|---|
| UI-01–09, UI-11 | Hoofdtabs en subnavigatie, geselecteerde datum, maandag, 320×740, 740×320, 768×1024, 1024×768, 1440×1000; overflow en aanraakmaten; toetsenbordfocus; herkenbare profielen |
| UI-10 | Weigeren van navigatie en Escape bij conceptinvoer; behoud na opslagfout en versieconflict |
| GEZ-01–05 | Inloggen met fout/goed wachtwoord, profiel maken/bewerken, avatar, filtering, vergrendelen en onbevoegde API-toegang |
| UI-03, AG-01 | Lokale taakuitvoeringen zichtbaar op hun geplande dagen in dag- en weekagenda, zonder CalDAV; filter per gezinslid en direct afvinken vanuit agenda |
| AG-01, AG-04 | Dag/week, CalDAV-afspraken, meerdaagse afspraak, tweemaal 02:30 bij wintertijd; browserfixture |
| AG-02–08 | CalDAV optioneel; backendtests voor herhaling, uitzonderingen, atomair vervangen/verwijderen, behoud bij storing en geheimen; echte serveracceptatie blijft open |
| TK-01–04 | Taak met beschrijving/punten, individuele en gezamenlijke toewijzing, dagelijkse uitvoering, voltooien/heropenen, herladen, historie en gezinsfilter |
| RT-01–04 | Geordende stappen, voortgang persistent na herladen, volgende dag leeg en vorige dag ongewijzigd; backendtests voor conflict/snapshots/inhaalperiode |
| BEL-01–05 | Punten per taakuitvoering en volledig afgeronde routine, tegenboeking bij ongedaan maken, unieke transacties, gedeelde taakbeloning per verantwoordelijke, gereserveerde aanvraag, beheergoedkeuring/-afwijzing en idempotente herhaling |
| BO-01–08 | Toevoegen, details, bewerken, verwijderen, afvinken/herstellen/opruimen; tweede browser ziet toevoeging binnen 2 seconden; conflict bewaart invoer; verloren antwoord en herhaling veroorzaken geen duplicaat |
| HA-01, HA-03–05 | Fixture voor geselecteerde lampbediening en alleen-lezen sensor; geïsoleerde fout; backendtests voor token, selectie en toegestane acties |
| IM-02–06, IM-09–12 | Foto vooruit/achteruit/pauze, standaard contain, niet-beschikbare afbeeldingen, navigatie, fotoaanraking, inactiviteit en guards voor formulier/concept/routine |
| IM-01, IM-05, IM-07–08 | Backendtests voor toelatingslijst, ingetrokken albumrechten en cachelimiet; geen live Immich-acceptatie |
| SYS-01–05, SYS-08 | Lokale HTTP-server zonder externe diensten, verbroken verbinding/herstel, mislukte opslag, dubbele taakvoltooiing vanaf twee browsers met één historie-item, XSS-tekstescaping en schermlokale voorkeuren |
| SYS-06–07 | Bestaande backendtests voor back-up/herstel en weigeren nieuwere schemaversie |
| GH-04 | Vastgelegde testdependencies, bestaande backend/containerworkflow en nieuwe browsermatrix met foutartefacten |

## Grenzen van dit bewijs

- Integratie-fixtures testen de frontend, niet interoperabiliteit met echte CalDAV-, Home Assistant- of Immich-installaties. Geheimen, caching en synchronisatie worden aanvullend server-side getest.
- WebKit is een browserengine-test, geen test op een echte iPhone/Safari-installatie. Viewports vervangen geen fysiek touchscreen.
- De 2-secondenassertie is een functionele grens op een lokale testmachine, geen netwerk-SLA. Geen 72-uurs duurtest, 200-ms responsbenchmark of minimale RAM/CPU-meting.
- Dockerstart, amd64/arm64, containervervanging en herstel naar een Docker-volume blijven aparte acceptatiepunten; de CI-configuratie is geen bewijs dat die workflow al op GitHub is uitgevoerd.
- CalDAV-/albumontdekking via echte servers, EXIF-oriëntatie, grote datasets, publieke repositorycontrole en de overige P1-functies vallen buiten deze browserrun.

## Resultaat van deze uitvoering — 30 oktober 2026

| Controle | Resultaat |
|---|---|
| Chromium 156.0.8078.4 | 28/28 geslaagd |
| WebKit 27.2 | 28/28 geslaagd |
| Firefox (Playwright build 1555) | 28 opstartfouten vóór applicatiebezoek: `Could not find profile folder` op deze Mac |
| Backend | 26/26 geslaagd |
| JavaScript-syntax en Python-testcompilatie | Geslaagd |

De totale browsermatrix duurde 80,50 seconden. Playwright 1.64.1, Python 3.14, macOS arm64. De backendrun duurde 0,53 seconden. Upstream deprecation-waarschuwingen van Starlette/httpx en pytest-playwright/pytest blijven zichtbaar; geen onderdrukte testfouten of retries.

**Gevonden en hersteld:** de mobiele subnavigatie overschreef de minimale knopbreedte met nul; Taken was circa 38,7 pixels breed. De minimummaat is nu 48 pixels. De regressietest controleert de maat en behoud van horizontale passing in beide mobiele oriëntaties.

Firefox blijft in CI opgenomen voor uitvoering op Linux. De lokale Firefox-opstartfout is geen bewijs van een fout in de app en ook geen geslaagde browseracceptatie.

## Update na implementatie BEL-01–05

- Backend en unittests: **68/68 geslaagd**.
- Chromium: **29/29 end-to-endtests geslaagd**.
- WebKit: de nieuwe beloningsaanvraag-/goedkeuringsflow **1/1 geslaagd**; de volledige WebKit-suite is niet opnieuw uitgevoerd.
- Firefox is voor deze update niet opnieuw uitgevoerd.

## Update: lokale taken in de agenda zonder CalDAV

De week-API levert nu geplande taakuitvoeringen voor alle zeven dagen; de agenda toont en laat deze direct afvinken, ook als geen CalDAV-account is ingesteld. De browser toont in dat geval dat CalDAV optioneel is voor privéafspraken.

- Backend en unittests: **70/70 geslaagd**.
- Chromium: **32/32 end-to-endtests geslaagd**, inclusief dagelijks terugkerende taken op alle zeven dagen zonder CalDAV.
