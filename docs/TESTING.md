# QE-acceptatie met Playwright

Uitgangspunt: [requirements v0.4 met status per requirement en resterende TODO’s](REQUIREMENTS.md). P1 is geen acceptatiecriterium voor deze eerste versie. Een geslaagde testset is geen verklaring dat alle P0-eisen zijn afgetekend.

## Uitvoeren

```sh
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python tools/format_css.py --check
.venv/bin/python -m pytest -q
npm ci --ignore-scripts
npm run format:check
node --check app/static/app.js
node --experimental-vm-modules tools/check_frontend.mjs
.venv/bin/python -m playwright install chromium firefox webkit
.venv/bin/python -m pytest tests/e2e --browser chromium --browser firefox --browser webkit --tracing retain-on-failure --screenshot only-on-failure --junitxml=test-results/results.xml
```

Op Linux is voor installatie van browserafhankelijkheden `python -m playwright install --with-deps` beschikbaar. Alleen backendtests draaien met de gewone `pytest`-opdracht; de browsermap wordt expliciet gekozen. Browserdependencies staan apart van productiedependencies.

`requirements-dev.txt` bevat de testdependencies plus Ruff en de CSS-formatter. JavaScript gebruikt Prettier, vastgepind in `package-lock.json`; Node/npm zijn alleen nodig voor ontwikkelchecks, niet voor installatie of productie. De modulecontrole gebruikt alleen Node, controleert ook imports/exports en weigert cyclische imports. De CI-workflow voert de backendtests, Ruff-controle, JavaScript-syntaxcontrole en containerchecks uit. De browsermatrix draait apart; zie `.github/workflows/browser-tests.yml`.

Iedere browsertest start een echte Uvicorn-server op een vrije lokale poort met een nieuwe tijdelijke SQLite-database, een afzonderlijke fotocache en een fictief beheerwachtwoord. De tests lezen geen `.env`, gebruiken geen echte integratieaccounts en raken `data/family.db` niet aan. Twee-apparatentests gebruiken afzonderlijke browsercontexts met eigen cookies en localStorage. Playwright bewaart bij fouten screenshots en traces in `test-results/`. De GitHub-workflow voert dezelfde suite per browser uit en bewaart die bestanden 14 dagen.

De kindmodusregressie controleert de volledige taak-/routine-/beloningsflow op
390×664, 750×342 en 768×1024, inclusief horizontale overflow en kaartgrenzen.
Linux-lettertypen horen bij deze controle: met Ubuntu's DejaVu Sans werd overflow
zichtbaar die op macOS en met Liberation Sans niet optrad. Gebruik voor lokale
Linux-reproductie ook `fonts-dejavu-core`. De aanraakmaat blijft minimaal 48 CSS-pixels;
de geometrieasserties tolereren alleen 0,001 pixel meetafronding voor Firefox.

## Unittests en backendregressies

`tests/test_container_storage.py` controleert echte eerste startup met lege,
root-owned opslag, zowel benoemde volumes als bind mounts op het Linux-bestandssysteem
van de Docker-host. Eerst wordt de oorspronkelijke SQLite-fout zonder voorbereiding
gereproduceerd. Daarna moeten de echte Compose-services de opslag voorbereiden,
de app als UID/GID 10001 starten, een lege database maken en de frontend en state-API
aanbieden. Na containervervanging moeten fictieve opgeslagen instellingen behouden zijn.
Alle resources hebben unieke testnamen en worden na afloop verwijderd. Geen echte
`.env`, databases of integratiegegevens worden gebruikt.
Beide opslagvormen worden uit hetzelfde `compose.yaml` opgebouwd via de standaard
volumes of de padvariabelen `DATA_VOLUME`/`CACHE_VOLUME`. De tests controleren ook de
door Compose daadwerkelijk opgeloste image en mounts, zodat de Portainer-variant
geen afwijkende configuratie kan krijgen.
De vervangingsfase zet een consistente fictieve database terug met een andere UID/GID
en reproduceert de `PermissionError` bij `chmod`. Ook private submappen en bestanden
worden teruggezet. Na init moeten hun eigenaar, map-/bestandsrechten en inhoud kloppen,
de database moet intact zijn en de app moet als UID/GID 10001 starten. Links naar
bestanden en mappen buiten de opslag worden niet gevolgd; hardlinks worden geweigerd.

```sh
CONTAINER_TEST_IMAGE=ruudv/family-dashboard:0.3.0 .venv/bin/python -m pytest tests/test_container_storage.py -q
```

Zonder `CONTAINER_TEST_IMAGE` worden deze Docker-tests overgeslagen.

De Docker-contextregressie gebruikt de echte Docker-builder met uitsluitend fictieve
bestanden in een tijdelijke map. Ze controleert onder andere geneste Python-caches,
losse bytecode, `.env`, gegevens, back-ups en testartefacten. Hiervoor is een lokale
Docker-daemon nodig; de gewone backendrun slaat deze test over:

```sh
RUN_CONTAINER_TESTS=1 .venv/bin/python -m pytest tests/test_container_packaging.py -q
```

De beveiligingsregressie controleert het daadwerkelijk gebouwde runtime-image op musl,
afwezigheid van glibc, minimaal zlib 1.3.2-r1 en python-dotenv 1.2.2, UID/GID 10001, tijdzones, SQLite en
HTTP-antwoorden. Ze gebruikt tijdelijke gegevens, geen netwerk en een alleen-lezen
container met dezelfde beveiligingsbeperkingen als Compose. Voer haar per gebouwde
architectuur uit (de standaard backendrun slaat haar over):

```sh
BUILDX_GIT_INFO=false docker build --pull -t family-dashboard:security-test .
CONTAINER_TEST_IMAGE=family-dashboard:security-test .venv/bin/python -m pytest tests/test_container_security.py -q
docker scout cves --exit-code local://family-dashboard:security-test
```

De scan controleert alle door Scout herkende CVE's, zonder filter op CVE of ernst.
`tests/unit/test_dotenv_security.py` simuleert de cross-device rename-fallback en
controleert dat set/unset een symbolisch-linkdoel niet overschrijven (CVE-2026-28684).
De bestaande configuratietest controleert dat `.env` lezen omgevingswaarden respecteert.
De containerjob
in CI voert de runtime-regressie uit na de Compose-build, vóór de healthcheck.

De standaardrun ontdekt tests onder `tests/`, met uitzondering van `e2e/`. Alleen de nieuwe unittests draaien met `.venv/bin/python -m pytest tests/unit -q`. Deze starten geen server, openen geen database en maken geen netwerkverbinding.

De unitreview voegde 35 gevallen toe: planning rond startdatum en schrikkeldag, weekdagen, individuele en gezamenlijke uitvoering, archivering, invoergrenzen voor stappen/punten/tijdvensters, datum-normalisatie, Home Assistant-selectie en hergebruik van geheimen. Twee aanvullende API-regressies controleren dat zowel opslaan als ontdekken een gewijzigd CalDAV- of Immich-adres weigert voordat een opgeslagen geheim wordt doorgestuurd. Bij weigering blijft de eerdere configuratie intact.

**Backendrun na de beloningsimplementatie: 68 geslaagd** (33 unit- en 35 API/backendtests). De latere run na de agenda-aanpassing staat onderaan.

## Koppeling aan requirements

| Requirements | Geautomatiseerd bewijs |
|---|---|
| UI-01–09, UI-11 | Hoofdtabs en subnavigatie, geselecteerde datum, maandag, iPhone 13: 390×664, 750×342, 768×1024, 1024×768, 1440×1000; overflow en aanraakmaten; toetsenbordfocus; herkenbare profielen |
| UI-10 | Weigeren van navigatie en Escape bij conceptinvoer; behoud na opslagfout en versieconflict |
| UI-12 | Kindmodus als eigen hoofdnavigatietab voor het gekozen kinderprofiel, taken/routines/beloningsaanvraag, selectie en navigatie van routines met starttijdklokken, zichtbare hoofdnavigatie en bovenbalkklok, verborgen beheerbediening en terugkeer naar de planner via Kalender; kaartgrenzen, overflow en aanraakmaten op mobiel en tablet |
| GEZ-01–05 | Inloggen met fout/goed wachtwoord, profiel maken/bewerken, foto uploaden/vervangen/verwijderen en behouden bij andere wijzigingen, filtering, vergrendelen en onbevoegde API-toegang |
| UI-03, AG-01 | Lokale taakuitvoeringen zichtbaar in een aparte rij boven de agenda op hun geplande dagen in dag-, drie-daagse en weekweergave; filter per gezinslid en direct afvinken |
| AG-01, AG-04 | Scrollbaar 24-uursrooster dat initieel de huidige tijd ±2/4 uur toont, met actuele-tijdindicator; duurafhankelijke afspraakhoogte en overlapindeling; vroege/late en hele-dagafspraken, tijdzones en meerdaagse afspraken; browserfixtures |
| AG-02–08, AG-10 | CalDAV optioneel en uitsluitend-lezen; backendtests voor herhaling, uitzonderingen, atomair vervangen/verwijderen, behoud bij storing en geheimen; eigenaar heeft de agenda-integratie handmatig gevalideerd |
| TK-01–04 | Taak met beschrijving/punten, individuele en gezamenlijke toewijzing, dagelijkse uitvoering, voltooien/heropenen, herladen, historie en gezinsfilter |
| RT-01–04 | Geordende stappen, voortgang persistent na herladen, volgende dag leeg en vorige dag ongewijzigd; backendtests voor conflict/snapshots/inhaalperiode |
| BEL-01–05 | Punten per taakuitvoering en volledig afgeronde routine, tegenboeking bij ongedaan maken, unieke transacties, gedeelde taakbeloning per verantwoordelijke, gereserveerde aanvraag, beheergoedkeuring/-afwijzing en idempotente herhaling |
| BO-01–08 | Toevoegen, details, bewerken, verwijderen, afvinken/herstellen/opruimen; tweede browser ziet toevoeging binnen 2 seconden; conflict bewaart invoer; verloren antwoord en herhaling veroorzaken geen duplicaat |
| HA-01, HA-03–05 | Ingesloten Home Assistant-dashboard, ingesteld dashboardpad, schermvullende weergave en afwezigheid van de oude entiteiten-API; backendtests voor instellingen en verwijdering van oude HA-geheimen |
| IM-02–06, IM-09–12 | Foto vooruit/achteruit/pauze, standaard contain, niet-beschikbare afbeeldingen, navigatie, fotoaanraking, inactiviteit en guards voor formulier/concept/routine |
| IM-01, IM-05, IM-07–08 | Backendtests voor toelatingslijst, ingetrokken albumrechten en cachelimiet; eigenaar heeft Immich handmatig gevalideerd, maar EXIF-oriëntatie en albumintrekking niet afzonderlijk bevestigd |
| IM-13 | Analoge klok met twaalf zichtbare cijfers, eerstvolgende toekomstige afspraak, wisseling naar volgende afspraak en lege toestand; responsive overflow |
| SYS-01–05, SYS-08 | Lokale HTTP-server zonder externe diensten, verbroken verbinding/herstel, mislukte opslag, dubbele taakvoltooiing vanaf twee browsers met één historie-item, XSS-tekstescaping en schermlokale voorkeuren |
| SYS-06–07 | Bestaande backendtests voor back-up/herstel en weigeren nieuwere schemaversie |
| GH-04 | Vastgelegde testdependencies, bestaande backend/containerworkflow en nieuwe browsermatrix met foutartefacten |

## Grenzen van dit bewijs

- Integratie-fixtures testen de frontend, niet interoperabiliteit met echte CalDAV-, Home Assistant- of Immich-installaties. Geheimen, caching en synchronisatie worden aanvullend server-side getest.
- De eigenaar heeft op 31 oktober 2026 bevestigd dat agenda-integratie, Home Assistant en Immich in de eigen omgeving werken. Dit is handmatige acceptatie en geen door deze testset reproduceerbare of onafhankelijk herhaalde controle.
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

## Update: analoge klok en eerstvolgende afspraak (IM-13)

De vaste datumweergave toont nu een analoge klok met de cijfers 1–12 en de eerstvolgende toekomstige agenda-afspraak. De gerichte Chromium-tests controleren ook het bijwerken naar de daaropvolgende afspraak, de lege toestand en viewportbreedtes van 320 tot 1440 pixels.

- Gerichte Chromium-tests: **6/6 geslaagd**.
- De volledige browser- en backendtestsuites zijn voor deze wijziging niet opnieuw uitgevoerd.

## Mobiele ondergrens — iPhone 13

De minimale mobiele acceptatie is iPhone 13, staand en liggend. De Playwright-apparaatprofielen gebruiken 390×664 en 750×342 CSS-pixels beschikbare browserruimte, inclusief ruimteverlies door browserbediening. De eerdere grens van 320 pixels is vervangen; er is geen vaste minimale paginabreedte toegevoegd.

Verificatie op 31 oktober 2026: 20 navigatie-, datum- en adminpaneelcontroles en 4 iPhone 13-emulatietests geslaagd in Chromium en WebKit. De emulatietests controleren aanraaknavigatie, horizontale pagina-overflow en het opslaan van apparaatinstellingen in beide oriëntaties. Dit is geen test op een fysieke iPhone.

## Herstelde testverwachtingen — 31 oktober 2026

De browsertests volgen nu de huidige interface: lokale taken worden zonder CalDAV weergegeven en afgevinkt zonder een aparte informatietekst; Home Assistant laadt rechtstreeks in het ingebouwde dashboard; de datum blijft zichtbaar in de bovenbalk bij Home Assistant en Immich. De tests blijven het geladen HA-dashboard, de afwezigheid van losse entiteitsaanroepen en volledige schermvulling onder de bovenbalk controleren. De schermvulling wordt ook in liggende iPhone 13-afmetingen gecontroleerd, inclusief horizontale overflow.

Volledige browserrun: **92/92 geslaagd** in Chromium en WebKit (116,20 seconden). Eén deprecation-waarschuwing uit pytest-playwright; geen testfouten.

## Architectuurregressies

`tests/test_architecture.py` controleert onafhankelijke applicatie-instanties zonder `.env`,
atomair terugrollen van taakvoltooiing bij een puntenfout, niet-blokkerende CalDAV/Immich-afhandeling,
en het verwerpen van verouderde synchronisatie- en fotoantwoorden na gewijzigde instellingen.
De bestaande API- en browsercontracten blijven het vangnet voor de herstructurering.

De browserfixture start `create_app(AppConfig(...))` met tijdelijke paden en fictieve credentials.
Zij gebruikt expliciete configuratie, zodat de productie-`.env` niet wordt gelezen.

Formatters toepassen: `.venv/bin/ruff format .`, `npm run format` en `.venv/bin/python tools/format_css.py`.
De CSS-formatter wijzigt geen regelvolgorde. Na wijzigingen aan schermgedrag moeten ook de
browserchecks draaien; formatter- en modulecontroles bewijzen geen correct schermgedrag.

## Laatste architectuurcontrole — 31 oktober 2026

- Backend en units: **94 geslaagd**, inclusief de 10 architectuurregressies.
- Chromium en WebKit: **132 geslaagd** (66 scenario’s per browser).
- Python/JavaScript/CSS-opmaak, Ruff, JavaScript-syntax en modulegrenzen: geslaagd.
- De navigatieregressie controleert ook dat de interactieve klok geen tabknoppen overlapt.
- Zie [VERIFICATION.md](VERIFICATION.md) voor de volledige uitslag en niet-uitgevoerde controles.

## Dagovergang van een open dashboard

`tests/e2e/test_day_rollover.py` gebruikt de Playwright-klok rond middernacht in de
geconfigureerde tijdzone. De tests controleren de zichtbare datum in kindmodus,
nieuwe onafgevinkte dagelijkse taken en routines, behoud van de vorige voortgang,
terugkeer naar het tabblad na een tijdsprong en behoud van bewust gekozen
ouderdatums. Ze gebruiken de echte state-API met tijdelijke gegevens.

Gericht uitvoeren:

```sh
.venv/bin/python -m pytest tests/e2e/test_day_rollover.py --browser chromium --browser webkit -q
```

De aanvullende oudermodusregressie controleert ook expliciet ingestelde weekdagen:
voltooien op de eerste dag, geen uitvoering op een overgeslagen dag, een lege
uitvoering op de volgende ingeplande dag en terugbladeren met onveranderde
uitvoeringsgegevens en voltooiingshistorie inclusief tijdstip.

## Routines in de agenda en het dagoverzicht

`tests/e2e/test_routine_agenda.py` controleert de echte dagelijkse uitvoeringen via
geïsoleerde API-fixtures, met uitsluitend een afspraak als CalDAV-browserfixture:

- Dag-, drie dagen- en weekweergave op mobiel (390×664) en desktop (1440×1000),
  ingeplande kaarten met tijdvenster in het rooster, kaarten zonder tijdvenster
  erboven, gezinsfilter, aanraakmaten en overlap met afspraken.
- Routine openen in een paneel, afvinken/heropenen per persoon, gedeelde voortgang
  met het routineoverzicht, afgeronde kaarten zichtbaar als Klaar en persistentie
  na herladen. Escape/sluiten herstelt de focus op de kaart.
- Openen van een andere dag werkt de gedeelde datumselectie bij. Het paneel volgt
  externe voortgangswijzigingen; na een netwerkfout blijft de stap beschikbaar om
  opnieuw te proberen, met een foutmelding in het paneel.
- Een lege routinedag toont geen sjablonen van andere dagen; de vervolgknop opent
  de eerstvolgende geplande dag. Routines beheren toont planning los van uitvoeringen.
- Nieuwe routines kunnen vanuit de editor zonder tijdvenster worden opgeslagen,
  zowel via Tijdvenster gebruiken als door beide velden leeg te maken. Opnieuw
  inschakelen herstelt geldige tijden. Dit vangt ook de native WebKit-validatie af.

De validator-unitchecks testen lege tijdvensters, onvolledige vensters en ongeldige
tijden. Routine-uitvoeringen van vandaag en eerdere dagen en uitvoeringen met
voortgang of afvinkhistorie behouden hun snapshot. Onaangeraakte toekomstige
routine-uitvoeringen volgen wijzigingen, ook na eerder bekijken.


De bereikregressies in `test_routine_agenda.py` installeren en pauzeren de browserklok
vóór het herladen. Ze controleren dat terugkeer vanuit het daggebonden routineoverzicht
direct de volledige agenda ophaalt, zonder een volgende polling-tick af te wachten.
Een afzonderlijke test houdt het dagantwoord tegen tot na de terugkeer; dat antwoord
mag de weekgegevens niet vervangen. Een routine met startdatum vandaag verschijnt op
alle drie komende dagen en alle zeven dagen van de volgende kalenderweek, maar niet
vóór de startdatum.


## Eerder bekeken toekomstplannen van routines

De API-regressies in `tests/test_app.py` controleren dat gewijzigde naam, tijd en
stappen ook worden toegepast op reeds aangemaakte toekomstplannen. Een versieconflict
voorkomt dat een oude browser de oude stapindex opslaat. Herhaald verversen blijft
stabiel en een volgende wijziging blijft mogelijk zolang er geen afvinkhistorie is.
Gedeeltelijk voltooide, voltooide en heropende toekomstuitvoeringen behouden hun
snapshot, historie en punten. Gewijzigde weekdagen, personen, startdatum en
archivering verbergen vervallen onaangeraakte plannen zonder opslagrecords te
wissen; opnieuw activeren gebruikt dezelfde uitvoerings-ID's.

De browserregressie `test_previously_viewed_future_week_updates_after_routine_is_renamed_and_rescheduled`
bootst de eerder bekeken werkweek met een ochtendroutine na, waarna die routine
naar elke avond verhuist. Alle zeven kaarten en de stappen in het paneel moeten
vervolgens de nieuwe routine tonen. Eerder opgeslagen historische uitvoeringen
worden via de API vergeleken met hun oorspronkelijke inhoud.


Een aanvullende browserregressie combineert op één toekomstige dag een al afgevinkte
oude ochtenduitvoering voor één persoon en de gewijzigde avondplanning voor een
ander. Kaarten en panelen moeten de afzonderlijke namen, tijden en stappen tonen;
het oude stappenpakket mag het nieuwe plan niet overschrijven bij groeperen.


## Spelletjes

`tests/test_games.py` controleert geïsoleerd de HTTP-contracten voor prijsbeheer,
gereserveerde punten, gelijktijdige aankopen, verzoekdeduplicatie, prijs- en
sessieversies, verstrijken, stoppen en het afronden van alle drie spellen.
`tests/e2e/test_games.py` controleert aankoop, hervatten na herladen, behoud van
voortgang/eindtijd, visueel Dierenorkest, prijsbeheer, toegang vanuit kindmodus
en de drie mobiele/tabletformaten. Aanvullende tests controleren behoud van andere
instellingsconcepten bij het opslaan van een spelprijs en onzekere HTTP-antwoorden
na een reeds verwerkte aankoop of zet. De Memory-test gebruikt een lokale fictieve
Immich-server met zes testafbeeldingen; geen echte fotoaccounts of `.env`.

```sh
.venv/bin/python -m pytest tests/test_games.py -q
.venv/bin/python -m pytest tests/e2e/test_games.py --browser chromium --browser firefox --browser webkit -q --tracing retain-on-failure --screenshot only-on-failure
```

Fysieke touchscreens, luisteracceptatie van de dieropnames op fysieke apparaten en
gebruik met de echte Immich-installatie vragen aparte handmatige acceptatie.


De Dierenorkest-regressie gebruikt een gepauzeerde Playwright-klok om de
3–2–1-overlay, de extra 1,5 seconde rust en het eerste oplichtende dier exact te
controleren. Ze controleert ook dat de geluidsknop naast Stoppen staat op
390×664, 750×342 en 768×1024, dat geluid schakelen de aftelling niet herstart,
dat de overlay het hele spelvenster zonder binnenranden bedekt, het cijfer
binnen het zichtbare venster blijft en
`backdrop-filter: blur(12px)` gebruikt. Ook de volgende ronde telt 3–2–1 af
met 1,5 seconde rust; handmatig herhalen binnen de ronde begint direct.
Stoppen ruimt de timers op.


De foutfeedbackregressie kiest bewust een verkeerd dier en controleert de
foutoverlay gedurende 2 seconden, het juiste foutbestand bij geluid aan,
stilte bij geluid uit, opnieuw aftellen, behoud van de ronde en het saldo,
en het verdwijnen van de fout na een juiste keuze. Afzonderlijke browsertests
decoderen alle vijf lokale WAV-bestanden, controleren duur/piekniveau en
controleren dat een echte opname na inschakelen van geluid kan afspelen.
De API-regressie controleert het vastleggen en wissen van `feedback`.


De volledige Dierenorkest-flow controleert de dierenviering op 390×664,
750×342 en 768×1024: alleen na alle zes reeksen, alle vier de diersoorten in
42 vliegende icoontjes, daadwerkelijk zichtbare CSS-opacity, leesbare tekst,
automatisch en handmatig sluiten, behoud na een laat sessieantwoord en de
rustige variant bij minder beweging. De geluidstests verwachten standaard
inschakeling, controleren echt afspelen na alleen de aankoopknop en behouden
dekking voor expliciet dempen. De herhaalknop heeft een SVG van minstens 36px.
De routinevieringstest controleert na hergebruik nog steeds tien verschillende
thema's en niet-herhalende boodschappen.


De Dierenorkest-layoutregressie controleert ook 1280×900 naast de mobiele en
tabletformaten. Ze controleert het titelicoon, een breder venster op grotere
schermen, zichtbare ruimte tussen uitleg en dierenknoppen, en een gecentreerde
herhaalknop onder het speelbord met ruimte tot de onderrand. De lage liggende
variant zet de vier dieren op één rij. De bestaande overlay- en vieringstests
blijven de venstergrenzen en leesbaarheid controleren.
