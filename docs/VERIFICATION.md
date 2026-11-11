# Verificatie 0.1.0

## Privacy en Docker-distributie — 31 oktober 2026

Zie [PRIVACY_AUDIT.md](PRIVACY_AUDIT.md) voor scope, bevindingen en beperkingen.

- Geautomatiseerde bron-/geschiedenisscan: 82 oorspronkelijke gevolgde bestanden en
  384 historische bestandsblobs; geen aangetroffen echte credentials of eigen privéinhoud.
  Git-auteursmetadata bevat wel een persoonlijke naam en e-mailadres.
- Werkelijke Docker-build en inspectie van alle lagen vonden lokale bytecode met
  gebruikers-/werkpaden. Na recursieve `.dockerignore`-uitsluitingen ontbreken alle
  26 lokale bytecodebestanden. Git-bronmetadata met accountnaam verdween bij de
  gecontroleerde build met `BUILDX_GIT_INFO=false`.
- Definitieve arm64-export: negen lagen, 11.568 entries, 46 projectbestanden en negen
  JSON-metadataobjecten gecontroleerd; geen aangetroffen eigen geheimen, persoonlijke
  gebruikers-/werkpaden of lokale gegevensbestanden.
- `RUN_CONTAINER_TESTS=1 .venv/bin/python -m pytest tests/test_container_packaging.py -q`:
  **1/1 geslaagd**, met echte Docker-filtering en uitsluitend fictieve tijdelijke bestanden.
- `.venv/bin/python -m pytest -q`: **104 geslaagd, 1 bewust overgeslagen** (Docker opt-in),
  één bestaande Starlette/httpx-deprecationwaarschuwing.
- Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`, JavaScript-syntax
  en modulegrenzen: geslaagd.
- Beide gevolgde screenshots visueel gecontroleerd: lege installatie. ExifTool-controle:
  geen GPS-/auteurs-/apparaatmetadata aangetroffen.
- Geen push naar Docker Hub, amd64-build, browserrun, dependencykwetsbaarheidsscan of
  productie-runtimeacceptatie uitgevoerd. De eerste build met netwerk uit kon geen
  dependencies downloaden; de daaropvolgende gewone build en herbouw zijn geslaagd.

## Beheersessie en automatische verversing — 31 oktober 2026

| Controle | Resultaat |
|---|---|
| Backend, `.venv/bin/python -m pytest -q` | **96 geslaagd**; één upstream Starlette/httpx-deprecationwaarschuwing |
| Ruff lint en formattercontrole | Geslaagd |
| `git diff --check` | Geslaagd |
| Regresstest voor dashboardpolling | Vijf publieke `/api/state`-verzoeken wijzigen de beheersessie niet; een daaropvolgende beheerinstellingenaanvraag slaagt |

Codecontrole bevestigt dat polling `/api/state` aanroept, die route geen beheercontrole heeft,
en dat de beheersessie 30 minuten geldt en proceslokaal wordt opgeslagen. Geen handmatige
ontwikkelserver-herstarttest uitgevoerd.

## Pictogramkiezer voor beloningen — 31 oktober 2026

| Controle | Resultaat |
|---|---|
| Backend, `.venv/bin/python -m pytest -q` | **95 geslaagd**; één upstream Starlette/httpx-deprecationwaarschuwing |
| Ruff lint en formattercontrole | Geslaagd |
| `git diff --check` | Geslaagd |
| Browserregressie beloningspictogram | Bijgewerkt; Chromium crashte bij opstart met een macOS `bootstrap_check_in`-toegangsfout |
| JavaScript-opmaak en modulechecks | Niet uitgevoerd: `npm` en `node` zijn niet beschikbaar in deze omgeving |

Geen handmatige browsercontrole uitgevoerd.

## Beheervensters blijven na opslaan beschikbaar — 31 oktober 2026

| Controle | Resultaat |
|---|---|
| Backend, `.venv/bin/python -m pytest -q` | **95 geslaagd**; één upstream Starlette/httpx-deprecationwaarschuwing |
| Ruff lint en formattercontrole | Geslaagd |
| CSS formattercontrole | Geslaagd |
| `git diff --check` | Geslaagd |
| Browserregressies voor profiel-, belonings- en instellingenvensters | Bijgewerkt; vijf relevante gevallen konden niet starten omdat Chromium crashte met een macOS `bootstrap_check_in`-toegangsfout |
| JavaScript-opmaak en modulechecks | Niet uitgevoerd: `npm` en `node` zijn niet beschikbaar in deze omgeving |

Dezelfde terugkeer geldt voor gezinslid- en beloningsformulieren en voor algemene en apparaatinstellingen.
De Immich-albumkiezer opent als apart dialoogvenster en laat het beheerpaneel eronder staan.
Geen handmatige browsercontrole uitgevoerd.

## Profielrol en kindmodus — 31 oktober 2026

| Controle | Resultaat |
|---|---|
| Backend, `.venv/bin/python -m pytest -q` | **95 geslaagd**; één upstream Starlette/httpx-deprecationwaarschuwing |
| Ruff lint en formattercontrole | Geslaagd |
| CSS formattercontrole | Geslaagd |
| `git diff --check` | Geslaagd |
| Kindmodusbrowserregressie (Chromium) | Niet uitgevoerd: Playwright-browser crashte bij opstart door macOS `bootstrap_check_in`-toegangsfout |
| JavaScript-opmaak en modulechecks | Niet uitgevoerd: `npm` en `node` zijn niet beschikbaar in deze omgeving |

De backendregressie controleert opslag van de kind- en ouderrol en weigering van ongeldige rollen.
De browserregressie controleert dat de kindmodus alleen kinderprofielen toont; die browsercontrole
is toegevoegd maar kon lokaal niet starten. Geen handmatige browsercontrole uitgevoerd.

## Architectuurherstructurering — 31 oktober 2026

Stappen 1–5 uitgevoerd in de huidige werkboom, inclusief tussentijdse gebruikerswijzigingen
voor klokpopup, dialoogsluiting en agendataken. De onderstaande eerdere oplevernotities blijven
historisch bewijs; deze sectie beschrijft de laatste controle.

| Controle | Resultaat |
|---|---|
| Backend en units, `.venv/bin/python -m pytest -q` | **94 geslaagd**, inclusief 10 nieuwe architectuurgevallen |
| Volledige browsermatrix, Chromium en WebKit | **132 geslaagd** (66 per browser), 220,81 seconden |
| Ruff lint en formattercontrole | Geslaagd |
| Prettier JavaScript-opmaak en CSS-formattercontrole | Geslaagd |
| JavaScript-entrypoint en modulecontrole | **17 modules** correct geparseerd/gekoppeld, geen cyclische imports |
| `git diff --check` | Geslaagd |
| Vergelijking met tussentijdse gebruikerswijzigingen | Alle frontendmodules inhoudelijk behouden, behalve gecorrigeerde synchronisatiehulptekst; alle bestaande CSS-regels in dezelfde volgorde behouden |
| Vergelijking oorspronkelijke planning en puntenregels | Functie-inhoud ongewijzigd na verplaatsing naar services |

De eerste uitgangscontrole vóór herstructurering was 84 backend-/unittests en 120 browsergevallen.
De suite groeide daarna door de architectuurtests, gebruikerswijzigingen en de navigatieregressie.
De uiteindelijke applicatie- en testbronbestanden bleven tijdens de laatste volledige browserrun
ongewijzigd (gecontroleerd met bestandsvingerafdrukken).

Nieuwe regressies toetsen geïsoleerde app-instanties en startupconfiguratie, atomair terugrollen
van voltooiing/punten/historie, onafhankelijke integraties, gewijzigde instellingen tijdens
synchronisatie, ingetrokken foto-downloads en behoud van geldige downloads bij ongewijzigde
albumverversing. Netwerkantwoorden zijn fixtures, geen echte integratieaccounts.

Gevonden en opgelost tijdens verificatie:
- De interactieve klok kon op tabletbreedtes de knop Boodschappen bedekken. De navigatie
  krijgt daar een eigen rij; klok en hoofdnavigatie zijn samen getest op 768, 1024 en 1280 pixels.
- De routinevieringstest kon twee stappen opslaan voordat de eerste opslag was bevestigd.
  De test wacht nu expliciet op de bevestigde eerste stap en controleert nog steeds alle tien
  vieringsvarianten. Na een eerdere timingfout is de volledige matrix opnieuw groen gedraaid.
- De aanvankelijk gekozen JavaScript-formatter wijzigde een genest HTML-template. De wijziging
  is teruggedraaid en JavaScript gebruikt nu vastgepinde Prettier. Een structurele vergelijking
  bevestigde daarna behoud van alle templates en gebruikerslogica.

De browsertests starten een echte tijdelijke HTTP-server met expliciete configuratie en lezen
geen productie-`.env`. Ze testen onder meer agenda/taken/routines, boodschappen, beloningen,
instellingen, invoerbehoud, conflicten, foto’s, de klokpopup en de nieuwe dialoogbediening.

Grenzen: Firefox, fysieke apparaten, Docker/architectuurbuilds en echte CalDAV/Immich/HA-services
zijn in deze ronde niet opnieuw gevalideerd. De bestaande handmatige acceptatie hieronder wordt
hiermee niet vervangen. CI is bijgewerkt maar niet op GitHub uitgevoerd. Afhankelijkheden geven
nog de bestaande waarschuwingen over FastAPI/Starlette-TestClient en een pytest-Playwright-fixture;
de uitgevoerde tests slagen. De Node-modulecontrole gebruikt de expliciete experimentele VM-vlag.

Zie [architectuur en onderhoud](ARCHITECTURE.md) voor modulegrenzen, transactie- en lockafspraken,
en [testinstructies](TESTING.md) voor het opnieuw uitvoeren van de controles.


Gecontroleerd op 30 oktober 2026. Dit document onderscheidt implementatie van daadwerkelijke acceptatie. De aangeleverde requirements blijven het doel; 0.1.0 is nog geen volledig afgetekende P0-release.

## Handmatige integratievalidatie — 31 oktober 2026

De eigenaar heeft bevestigd dat de agenda-integratie, Immich en Home Assistant handmatig werken in de eigen omgeving. De integraties zijn daarom niet langer een algemene open acceptatie-TODO. Specifieke randgevallen blijven open waar ze niet afzonderlijk zijn bevestigd: CalDAV-herhalingen/uitzonderingen, tijdzones en storingen; HA-rechten op een gedeeld scherm; Immich-albumintrekking, cache-opruiming en EXIF-oriëntatie. Dit is een vastgelegde gebruikersvalidatie, geen onafhankelijk herhaalde test.

## IM-13 — analoge klok en eerstvolgende afspraak

De vaste datumweergave in het topmenu toont een analoge klok met twaalf cijfers en de eerstvolgende toekomstige afspraak. Als er geen afspraak is, staat er “Geen volgende afspraak gepland”. Gerichte Chromium-tests controleerden klokverversing, doorgaan naar de volgende afspraak en weergave zonder horizontale overflow op 320, 390, 750, 768 en 1440 CSS-pixels. Resultaat: **6/6 gerichte tests geslaagd**.

## QE-update: Playwright, 30 oktober 2026

- **28 scenario’s × Chromium en WebKit = 56 geslaagde browsertests**, Playwright 1.64.1 op macOS arm64; volledige run 80,50 seconden inclusief de Firefox-opstartpogingen.
- **26 backendtests geslaagd** (0,53 seconden). JavaScript-syntaxcontrole en compilatie van de testbestanden geslaagd.
- Firefox kon niet starten: `Could not find profile folder`. Alle 28 Firefox-gevallen eindigden tijdens browserinitialisatie; dit is geen geslaagde Firefox-acceptatie. Ook met volledig opgeloste macOS-paden trad de fout op.
- Hersteld: mobiele subnavigatie maakte de knop Taken circa 38,7 pixels breed. Minimum nu 48 pixels; regressietest slaagt op 320 pixels en in liggende mobiele weergave, in Chromium en WebKit.
- Dekking omvat echte HTTP-opslag, twee afzonderlijke browsersessies, gelijktijdige taakvoltooiing, versieconflicten, verloren opslagantwoord, fout-/offlinepaden, wintertijdweergave, routinehistorie, toetsenbord, tekstescaping, diavoorstelling en inactiviteitsguards.
- Testgegevens en caches zijn tijdelijk en gescheiden van de echte installatie. Externe integratie-antwoorden zijn fixtures; echte integraties zijn hiermee niet afgetekend.
- Zie [testplan, requirementdekking en uitvoerinstructies](TESTING.md). JUnit-uitvoer staat lokaal in `test-results/results.xml`; screenshots/traces worden bij fouten bewaard. De nieuwe GitHub Actions-browsermatrix is geconfigureerd, niet op GitHub uitgevoerd.

De onderstaande oorspronkelijke controles zijn historische oplevernotities; bovenstaande resultaten vervangen de oudere testaantallen en de beperkte browsercontrole. Fysieke apparaten, Docker-runtime en de duurtest blijven open.

## Uitgevoerde controles

- **15 pytest-tests geslaagd**, lokaal met Python 3.14.6, FastAPI TestClient en tijdelijke SQLite-databases.
- Beheertoegang, geheimenfiltering, cross-origin schrijfblokkering en ongeldige item-ID’s.
- Boodschappen-idempotentie, herstel van afgevinkte items en versieconflicten.
- Twee gelijktijdige voltooiingen van een gezamenlijke taak: één mutatie, één historie-item.
- Individuele uitvoeringen, routinevoortgang per dag/persoon en conflicten op verschillende stappen.
- Sjabloonwijzigingen bewaren snapshots; inhalen van gemiste dagen vóór wijziging.
- SQLite online back-up naar een lege installatie, inclusief herstel van integratiegeheimen; weigering van nieuwere schemaversies.
- CalDAV-fixtures: herhalingen, uitzondering, verschoven afspraak, hele-dagafspraak en overgang zomertijd/wintertijd in Europe/Amsterdam.
- CalDAV-mocks: wijzigen, verwijderen en behouden van de laatst succesvolle kopie bij een fout.
- Immich-mocks: niet-geselecteerde foto weigeren, ingetrokken albumfoto uit cache verwijderen en cache begrenzen.
- `python -m compileall` en `docker compose config --quiet` geslaagd.
- Browsercontrole in de Codex in-app browser: laden zonder JavaScript-fouten, beheerlogin, profiel toevoegen, boodschap toevoegen, routine maken, stap afvinken en herladen met behoud van voortgang.
- Desktopweergave op 1440 × 1000 gecontroleerd; schermafbeelding opgeslagen als `docs/screenshot.png`.
- Mobiele viewport 320 × 740: bij de boodschappenweergave was documentbreedte gelijk aan viewportinhoud (305 CSS-pixels exclusief scrollbar); geen horizontale overflow. De drie hoofdtabs blijven zichtbaar.

De TestClient geeft één upstream deprecation-waarschuwing over httpx versus httpx2. Dit is geen testfout; de dependencyversies zijn vastgelegd.

## Nog niet geverifieerd

- Docker-daemon was niet beschikbaar. Compose is syntactisch gecontroleerd, maar containerbuild/start, persistentie bij containervervanging en herstel naar een Docker-volume zijn lokaal niet uitgevoerd.
- Linux amd64- en arm64-builds staan in GitHub Actions. De workflow is nog niet op GitHub uitgevoerd; geen vooraf gebouwde images gepubliceerd.
- Echte CalDAV-, Immich- en HA-servers waren tijdens deze oorspronkelijke verificatieronde niet beschikbaar. De eigenaar heeft deze integraties op 31 oktober 2026 handmatig gevalideerd; zie de update hierboven.
- Home Assistant-iframe: echte login, cookies, frameheaders, mixed content, mobiele bediening en rechtenbeperking moeten met de eigen installatie worden gecontroleerd. Een directe link naar hetzelfde dashboard is beschikbaar als iframe-weergave niet werkt.
- Immich-oriëntatie en previewkwaliteit hangen af van de previews die Immich levert. Geen echte foto-/EXIF-test uitgevoerd.
- Nog geen 72-uurs duurtest of gemeten 200-ms/2-seconden prestatierapport, en geen meting van minimale RAM/CPU-hostvereisten.
- Geen volledige browsermatrix. De UI gebruikt moderne CSS Grid, dialog, fetch en Intl. Recente Chrome/Edge/Firefox/Safari zijn beoogd; alleen de genoemde in-app browser is daadwerkelijk gecontroleerd. Geen toezegging voor oude webviews of kioskbrowsers.
- Geen twee fysieke apparaten tegelijk getest. API-concurrentie is getest; automatische verversing is geïmplementeerd met 1,5-seconde polling.

## Acceptatieoverzicht

| Scenario uit requirements | Stand 0.1.0 |
|---|---|
| 1–2 Navigatie en 320 pixels | Geïmplementeerd; beperkte mobiele browsercontrole uitgevoerd |
| 3–4 CalDAV en tijdzones | Fixture-/mocktests geslaagd; echte server nog nodig |
| 5 Routinehistorie | Automatisch en in browser gecontroleerd |
| 6 Gelijktijdige taakvoltooiing | Automatisch gecontroleerd |
| 7–8 Gedeelde boodschappen | CRUD, polling en conflictcontrole geïmplementeerd; API en één browser getest |
| 9 Integratie-uitval geïsoleerd | Adapterfoutpaden getest; volledige netwerk-/HA-uitval nog testen |
| 10 Inactiviteit | Guards geïmplementeerd; nog geen lange browsertest met echte fotolijst |
| 11–12 Docker/platform/persistentie | Configuratie en CI aanwezig; runtimevalidatie open |
| 13 Back-up/herstel | SQLite-herstel getest; Docker-volumeherstel open |
| 14 Beheer afgeschermd | API-tests en browserlogin geslaagd |
| 15 Veilige distributie | Geen echte accounts/geheimen/foto’s in bron; publicatie nog niet uitgevoerd |

## Bewuste beperkingen / keuzes

- CalDAV alleen-lezen; afspraken kunnen niet via het dashboard worden aangemaakt, gewijzigd of verwijderd. Synchronisatievenster 90 dagen terug tot circa één jaar vooruit.
- Afzonderlijke uitvoeringen worden bij bekijken alvast vastgelegd, ook voor toekomstige datums. Sjabloonwijzigingen herschrijven deze niet. Inhalen van verlopen uitvoeringen is begrensd op twee jaar.
- Historie bevat mutaties en een puntenledger met herleidbare transacties, maar geen individuele actoridentiteit: dagelijks profielgebruik is geen authenticatie.
- Geen aparte achterstallige-takenlijst, geen routinevensters over middernacht en geen offline schrijfbuffer.
- Integratie- en beheersessiestaat deels proceslokaal: één applicatieproces/worker vereist.
- Integratiegeheimen staan onversleuteld in het beschermde servervolume; toegang tot host en back-ups is vertrouwelijk.
- De gedeelde dagelijkse API vertrouwt het thuisnetwerk. Externe toegang, fijnmazige rechten en publicatie zijn niet ingericht.
- Profielfoto’s worden verkleind naar JPEG en via een versiegebonden endpoint geladen; de profielstatus bevat alleen de URL. CalDAV/Immich-configuratie komt in de database; schermvoorkeuren blijven in de browser.
- Licentie: PolyForm Noncommercial 1.0.0, gekozen voor niet-commercieel gebruik en opgenomen in broncode en container. Nog geen publieke GitHub-repository.

## Eerste echte acceptatieronde

1. Start Compose en controleer `/api/health`, herstart en vervang daarna de container met behoud van volumes.
2. Configureer één echt account per integratie; test wijzigingen, uitzonderingen, verwijderingen en uitval.
3. Open op telefoon en gedeeld scherm; test gelijktijdige edits en afvinken.
4. Test het ingesloten HA-dashboard en de aanmelding op het daadwerkelijke scherm; controleer ook de frameheaders en browser-cookie-instellingen.
5. Test Immich-albumintrekking, een kapotte foto, EXIF-rotatie, shuffle en inactiviteit tijdens invoer.
6. Herstel een back-up naar een leeg Docker-volume. Draai vervolgens de 72-uurs duurtest en leg geheugen-/latencymetingen vast.


## Home Assistant-dashboard

Het HA-tabblad laadt het ingestelde Home Assistant-dashboard in een iframe; Samen haalt geen entiteiten op en rendert ze niet zelf. De browserproef bevestigt dat het ingestelde dashboardpad wordt gebruikt en dat er geen HA-entiteiten-API wordt aangeroepen. Deze proef gebruikt een nagebootste HA-pagina. Een echte HA-server was niet beschikbaar om login/cookies en frameheaders te verifiëren; controleer die instellingen bij ingebruikname. De link onder het dashboard opent dezelfde HA-pagina rechtstreeks in een nieuw tabblad.

## Update: punten en beloningen

BEL-01 t/m BEL-05 zijn geïmplementeerd. Voltooide taken boeken de ingestelde punten per uitvoering; een gedeelde taak boekt punten voor ieder toegewezen gezinslid. Een routine boekt uitsluitend punten wanneer alle stappen voltooid zijn, niet per onderliggende stap. Een voltooiing ongedaan maken maakt een herleidbare tegenboeking; een nieuwe voltooiing is een nieuwe transactie. SQLite-schema versie 1 migreert bij starten naar versie 2.

De beloningscatalogus wordt door een beheerder beheerd. Een gezinslid kan vanuit het tabblad Beloningen een aanvraag indienen; de punten worden gereserveerd zolang deze openstaat en pas bij beheergoedkeuring afgeschreven. Afwijzen geeft de reservering vrij. Aanvragen, besluiten en puntentransacties worden bewaard; request-ID’s en unieke ledger-bronnen voorkomen dubbele mutaties.

Dagelijkse profielkeuze blijft een filter en geen authenticatie. De nieuwe API-tests en browserflow controleren transacties, herroeping, reservering, idempotentie, catalogusbeheer en oudergoedkeuring. Echte gezinsacceptatie en gelijktijdige fysieke apparaten blijven onderdeel van de bredere acceptatieronde.

## Update: taken in de agenda zonder CalDAV

Lokale taakuitvoeringen staan in een aparte rij boven de afspraken in de dag-, drie-daagse en weekagenda, inclusief direct afvinken en filtering per gezinslid. Afspraken staan op een tijdlijn van 07:00 tot 22:00 met hoogte naar duur; overlappende afspraken krijgen aparte kolommen. Hele-dagafspraken en afspraken buiten die uren blijven in aparte rijen zichtbaar. De drie-daagse weergave toont de geselecteerde dag en de twee volgende dagen; voor een weekoverzicht vraagt de API alle zeven dagen op. CalDAV is optioneel en voegt uitsluitend privéafspraken toe; zonder account werkt de gezinsplanner normaal.

Gecontroleerd: **70 backend-/unittests** en **32 Chromium-end-to-endtests** geslaagd. De nieuwe acceptatietest controleert een dagelijkse taak op alle dagen van een week zonder CalDAV-koppeling.

## Update: tijdschaal in de agenda

Taken staan in een aparte rij boven de agenda-afspraken. Het tijdrooster beslaat 24 uur en scrolt verticaal; het opent rond de huidige tijd met twee uur terug en vier uur vooruit. Een rode horizontale indicator markeert de huidige tijd en beweegt mee met de klok. Tijdgebonden afspraken staan op hun werkelijke tijd en zijn proportioneel geplaatst; overlappende afspraken delen de beschikbare kolomruimte. Hele-dagafspraken blijven apart zichtbaar. Op mobiel scrollen de meerdaagse en weekroosters binnen de agenda.

Gecontroleerd: **78 backend-/unittests** en **50 Chromium-end-to-endtests** geslaagd, inclusief positie/duur, overlap, tijden buiten de oorspronkelijke schaal en mobiele weergave.

## Update: avatar-knoppen voor kindmodus

De Kindmodus-knop is uit het gezinsfilter verwijderd. In de header staat nu links van de hoofdtabs een ronde avatar-knop voor ieder kinderprofiel; die opent direct het gekozen kind. Avatars en tabs vormen één gecentreerde navigatiegroep. UI-12 is hierop aangepast; de browserregressie controleert de directe profielkeuze, de uitlijning en het terugicoon.

Gecontroleerd op 31 oktober 2026: backend **96/96 geslaagd**; Ruff lint en formatcheck geslaagd; CSS formatcheck geslaagd; `git diff --check` geslaagd. Na de uitlijningsaanpassing zijn de CSS-check, Ruff en `git diff --check` opnieuw geslaagd. De klok schaalt mee met de logomark en heeft geen extra rechter marge; de browserregressie controleert gelijke hoogte en marge. De oorspronkelijke Chromium-run kon toen niet starten door macOS `bootstrap_check_in`-toegangsfout 1100 en de JavaScriptchecks konden niet draaien doordat Node.js en npm ontbraken. Inmiddels is Node.js/npm geïnstalleerd en is Chromium buiten de sandbox gestart. De volledige Chromium-suite is op 31 oktober 2026 opnieuw uitgevoerd: **69/69 geslaagd**; de JavaScriptcontroles staan bij de update over dubbele taken hieronder.

## Update: profielfoto’s voor gezinsleden

Bij gezinsleden kan een JPEG-, PNG- of WebP-foto van maximaal 12 MB worden gekozen. De browser verkleint de foto naar maximaal 256 pixels en JPEG; de server valideert het formaat en de maximale opgeslagen grootte. De database bewaart de fotodata bij het profiel, dashboardverversingen sturen alleen een versiegebonden afbeeldings-URL en wijzigingen aan naam/kleur behouden de huidige foto. Foto verwijderen herstelt de initialenweergave. Historie bewaart geen fotodata.

Gecontroleerd op 31 oktober 2026: backend **100/100 geslaagd**, inclusief upload, URL-weergave, versiecontrole, behoud, verwijderen en ongeldige fotodata. Ruff lint/format, CSS-format en `git diff --check` geslaagd. De Chromium-profielregressie controleert upload, behoud en verwijderen en slaagt in de volledige Chromium-suite (**69/69**). Node.js/npm zijn inmiddels beschikbaar; de JavaScriptchecks slagen volgens de verificatie hieronder.

## Update: dubbele taak na wijziging van uitvoering

Na omschakelen tussen individuele en gezamenlijke uitvoering verbergt de dashboardselectie
vervangen open uitvoeringen wanneer voor dezelfde taak en dag een uitvoering met de actuele
verdeling bestaat. Dit geldt ook na eerder afvinken en heropenen. Opgeslagen snapshots,
historie en puntenboekingen blijven behouden; afgeronde uitvoeringen blijven zichtbaar.

Gecontroleerd op 31 oktober 2026:

- Backend-/unittests: **104/104 geslaagd**. Vier nieuwe API-regressiegevallen controleren
  beide omschakelrichtingen, toekomstige dagen, herhaald ophalen, behoud van snapshots,
  dagen zonder vervanging, afgeronde/heropende uitvoeringen en ongewijzigde puntenboekingen.
- Gerichte Chromium-/WebKit-run: **6/6 geslaagd**, voor individuele/gezamenlijke toewijzing
  en de nieuwe duplicaatregressie. Na uitbreiding van de duplicaatregressie met vooraf
  afvinken en heropenen is deze opnieuw uitgevoerd: **2/2 geslaagd**, inclusief herladen
  en afvinken van de overgebleven gezamenlijke taak. Browsers startten buiten de sandbox;
  binnen de sandbox blokkeerde macOS de browserstart. Volledige browsermatrix en Firefox
  zijn voor deze wijziging niet uitgevoerd.
- Ruff lint/format, CSS-format, Prettier (na `npm ci --ignore-scripts`), JavaScript-syntax,
  modulegrenzen en `git diff --check`: geslaagd.
- De volledige Chromium-suite is op 31 oktober 2026 buiten de sandbox uitgevoerd:
  **69/69 geslaagd**. Daarmee is ook de eerder geblokkeerde klok- en profielfotoregressie
  in Chromium gecontroleerd.
- Aanvullende geautomatiseerde alleen-lezen controle van de gemelde lokale taak:
  de aangepaste selectie levert voor 31 oktober precies één gezamenlijke uitvoering.
  Hiervoor is de bestaande database niet gewijzigd; dit is geen handmatige visuele acceptatie.

De runs bevatten alleen bestaande upstream-deprecationwaarschuwingen en Nodes waarschuwing
over experimentele VM-modules.

## Update: ronde uitsnede van profielfoto’s — 31 oktober 2026

De gedeelde avatarstijl knipt foto’s nu af aan de ronde rand. De bestaande
`object-fit: cover` vult de cirkel met behoud van de beeldverhouding.

- Geautomatiseerde Chromium-/WebKit-regressie: **4/4 geslaagd**, op 390×664 en
  1440×1000. Controleert geladen foto’s, ronde clipping, vierkante afmetingen en
  vulling in gezinsfilter, header, beheer, fotovoorbeeld en kindwelkomstscherm.
  Browserstart binnen de sandbox mislukte; de geslaagde run draaide buiten de sandbox.
- Backend-/unittests: **104/104 geslaagd**.
- Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`,
  JavaScript-syntax, modulegrenzen en `git diff --check`: geslaagd.
- Geen handmatige visuele acceptatie, volledige browsermatrix of Firefox-run uitgevoerd.

## Consistente marges in de taakpopup — 31 oktober 2026

De toevoeg-/bewerkpopup gebruikt 8 px tussen labels en invoer en 16 px tussen
veldgroepen, zonder opgetelde ondermarges onder de titel, beschrijving of gezinsleden.

- Geautomatiseerd: **6/6 gerichte Chromium-/WebKit-tests geslaagd**. De nieuwe regressie
  meet afstanden bij toevoegen en bewerken op 390×664 en 1440×1000, met verborgen
  en zichtbare weekdagkeuze; de bestaande pictogramselectie is ook gecontroleerd.
- Backend-/unittests: **104/104 geslaagd**.
- Ruff lint/format, CSS-format, Prettier (na `npm ci --ignore-scripts`), JavaScript-syntax,
  modulegrenzen en `git diff --check`: geslaagd.
- Screenshots van de bewerkpopup op beide afmetingen visueel geïnspecteerd.
- Browserstart binnen de sandbox mislukte; de geslaagde run draaide buiten de sandbox.
  Een eerste run daar gebruikte een onjuiste labelselector in de nieuwe test; na correctie
  van die selector zijn alle zes gevallen opnieuw uitgevoerd en geslaagd.
- Volledige browsermatrix, Firefox en fysieke apparaten zijn voor deze wijziging niet getest.


## Lokale Docker-build voor DS918+ — 31 oktober 2026

- Image `ruudv/family-dashboard:0.1.0` lokaal gebouwd met Docker Buildx voor
  `linux/amd64` op Docker Desktop 4.97.0 (Mac arm64; uitvoering via emulatie).
  Image-ID: `sha256:93ed79ddf4a605aea4f775c4a6ef1a269b5f070db90d293a835ba0f859fd2259`.
- Geautomatiseerde containercontrole met fictief beheerwachtwoord, uitsluitend tijdelijke
  tmpfs-opslag, geen extern netwerk, read-only rootfilesystem, init, alle capabilities
  verwijderd en `no-new-privileges`: Docker-healthstatus `healthy`; health-API,
  startpagina, login met sessiecookie en state-API geslaagd.
  Eerste twee loginprobes hadden onvolledige browserheaders en kregen 403;
  met de vereiste `X-Family-Request`- en Origin-headers is login geslaagd.
- In `/app` zijn geen `.env`, databasebestanden of Python-bytecode aangetroffen.
  Docker-buildcontextregressie met fictieve bestanden: **1/1 geslaagd**.
- Backend-/unittests: **104 geslaagd, 1 standaard overgeslagen Docker-test**;
  de Docker-test is vervolgens expliciet uitgevoerd en geslaagd, zoals hierboven vermeld.
- Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`, JavaScript-syntax
  en modulegrenzen: geslaagd. Bestaande upstream-deprecationwaarschuwing zichtbaar.
- De tijdelijke testcontainer is verwijderd. Echte configuratie is niet ingeladen.
- Niet uitgevoerd: Docker Hub-publicatie, uitvoering op de fysieke Synology,
  configuratieherstel op de NAS, containervervanging met persistent volume en browsermatrix.


## Docker Hub-publicatie — 31 oktober 2026

- `docker push ruudv/family-dashboard:0.1.0` geslaagd.
- Aansluitend `docker buildx imagetools inspect` tegen Docker Hub uitgevoerd:
  tag beschikbaar met `linux/amd64`-manifest en digest
  `sha256:93ed79ddf4a605aea4f775c4a6ef1a269b5f070db90d293a835ba0f859fd2259`.
- Repositoryzichtbaarheid zonder authenticatie, installatie op de NAS en
  configuratieherstel zijn nog niet gecontroleerd.


## Docker Hub-installatiehandleiding — 31 oktober 2026

- README lokaal en op GitHub bijgewerkt met de gepubliceerde amd64-tag 0.1.0,
  Compose-/Portainer-installatie, omgevingsvariabelen, volumes, updates en
  verwijzingen voor back-up/herstel. Bestaande lokale README-aanpassingen behouden;
  alleen de gerichte distributiewijzigingen naar GitHub geschreven.
- Voorstel voor de Docker Hub-overview opgeslagen in `docs/DOCKER_HUB.md`.
- `docker compose config --quiet` op het gedocumenteerde voorbeeld met een fictief
  wachtwoord en zonder echte `.env`: geslaagd. README na schrijven opnieuw via
  GitHub opgehaald en inhoud gecontroleerd; exact gelijk aan de bedoelde wijziging.
- YAML-blokken voor Compose in beide documenten geparseerd en vergeleken met
  de imagenaam en volumedeclaraties; geldig. `git diff --check`: geslaagd.
- Geen applicatiecode gewijzigd; backend- en browsertests niet opnieuw uitgevoerd.
- De Docker Hub-beschrijving is nog niet geplaatst. NAS-installatie en herstel
  blijven ongeverifieerd.

## Containerbeveiliging zlib/glibc — 31 oktober 2026

- De meldingen op de bestaande `ruudv/family-dashboard:0.1.0` (amd64,
  digest `sha256:93ed79ddf4a605aea4f775c4a6ef1a269b5f070db90d293a835ba0f859fd2259`)
  opnieuw bevestigd met Docker Scout 1.27.0: CVE-2026-85091 in Debian zlib
  `1:1.3.dfsg+really1.3.1-1` en CVE-2026-84243 in glibc `2.41-12+deb13u4`.
- Bronnen geraadpleegd: [Debian zlib-tracker](https://security-tracker.debian.org/tracker/CVE-2026-85091),
  [Debian glibc-tracker](https://security-tracker.debian.org/tracker/CVE-2026-84243)
  en [Alpine zlib-tracker](https://security.alpinelinux.org/vuln/CVE-2026-85091).
  Debian Trixie heeft voor beide nog geen opgeloste pakketversie. De precieze
  getroffen zlib-versiereeks is upstream onderwerp van discussie; de scannerbevinding
  is niet onderdrukt. Alpine vermeldt zlib `1.3.2-r1` als opgelost.
- Dockerfile omgezet naar `python:3.12-alpine3.23` (musl, geen glibc), met
  `apk upgrade`, minimaal zlib `1.3.2-r1` en tijdzonedata. UID/GID blijven 10001.
  Bestaande Python-dependencies installeren op beide architecturen zonder extra
  compiler of glibc-compatibiliteitslaag.
- Beide images daadwerkelijk met `--pull` gebouwd en lokaal getest op Docker Desktop
  op een arm64-Mac; amd64 via emulatie:
  - `family-dashboard:security-amd64`:
    `sha256:6603372a14c20a76ca8cacb4964829add60b1cfd4c9b25d909bdc9c4de525145`.
  - `family-dashboard:security-arm64`:
    `sha256:fe60bdfa01a436b32c24136a9700ba76648642fda8dbd63a3609a2e4a63c7500`.
- Automatisch: `docker scout cves --exit-code --only-cve-id
  CVE-2026-85091,CVE-2026-84243 local://family-dashboard:security-<architectuur>`
  vindt op beide images **geen van deze twee CVE's** (exitcode 0, 93 pakketten).
  Dit was een gerichte scan, geen uitspraak over alle andere CVE's.
- Automatisch: nieuwe containerregressie op beide images **1/1 geslaagd**:
  musl, geen glibc/compatibiliteitspakketten, gepatchte zlib-pakketversie en
  compressie/decompressie, UID/GID, Amsterdamse winter-/zomertijd, schrijfbare
  gegevensmappen, health/frontend/state en SQLite-integriteit. Uitgevoerd zonder
  netwerk, met alleen-lezen rootfilesystem, verwijderde capabilities en tijdelijke data.
- Automatisch: complete backendset op host én in beide Python 3.12-images:
  telkens **104 geslaagd, 2 opt-in Docker-tests overgeslagen**. De nieuwe runtimecheck
  is afzonderlijk uitgevoerd zoals hierboven vermeld. De bestaande verpakkingsregressie
  is in deze ronde niet opnieuw uitgevoerd. Bekende Starlette-deprecationwaarschuwing.
- Automatisch: beide images met het echte Uvicorn-entrypoint gestart, fictief
  beheerwachtwoord en tijdelijke tmpfs-opslag; health en frontend geven HTTP 200.
  Testcontainers daarna gestopt en verwijderd. Geen echte `.env` of gezinsdata gebruikt.
- Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`, JavaScript-syntax,
  modulegrenzen en `git diff --check`: geslaagd op de gecombineerde werkboom.
- Runtime-regressie toegevoegd aan de containerjob in CI; die workflow is niet op
  GitHub uitgevoerd. README, requirements en testinstructies bijgewerkt.
- Niet uitgevoerd: nieuwe Docker Hub-publicatie/herscan, NAS-uitvoering, browsermatrix
  en volumeherstel. De gepubliceerde `0.1.0` bevat deze fix nog niet; publiceer een
  nieuwe versietag en vervang de container om bestaande installaties bij te werken.


## Eerste start met lege opslag — 31 oktober 2026

Oorzaak: de app maakt een ontbrekende database al aan, maar UID/GID 10001 kan niet
schrijven in lege bind-mountmappen die bijvoorbeeld van root zijn (mode 0755).
`storage-init` in Compose stelt nu eerst de eigenaar en mode 0700 van de twee
opslagmappen in. Alleen deze korte service draait als root met CHOWN/FOWNER, zonder
netwerk. Het dashboard wacht op exitcode 0, behoudt zijn gewone gebruiker en krijgt
geen extra capabilities. De initializer verandert geen onderliggende bestanden.
Er is voor deze fix geen wijziging van de applicatie-image nodig.

Geautomatiseerd uitgevoerd op Docker Desktop op een arm64-Mac:

- Nieuwe regressie `tests/test_container_storage.py` tegen drie bestaande images:
  `ruudv/family-dashboard:0.1.0` (**2/2 geslaagd**, 16,10 s),
  `family-dashboard:security-amd64` (**2/2**, 13,54 s) en
  `family-dashboard:security-arm64` (**2/2**, 15,74 s).
- Elke run gebruikt twee lege root-owned opslagmappen, zowel benoemde Docker-volumes
  als echte bind mounts op het Linux-bestandssysteem van de Docker-host. Zonder de
  initializer is de oorspronkelijke SQLite-openfout gereproduceerd. Vervolgens
  starten de echte Compose-services, maakt de app een lege database met schema,
  worden health/frontend/state aangeboden en draait de app als UID/GID 10001.
  Na verwijderen en opnieuw aanmaken van beide containers blijven fictieve
  instellingen en SQLite-integriteit behouden. Alle testresources opgeruimd.
  amd64-uitvoering gebruikt emulatie; dit is geen fysieke Synology-test.
- Backend/unittests: **104 geslaagd, 4 opt-in Docker-gevallen overgeslagen** (4,08 s).
  De twee nieuwe Docker-gevallen zijn apart uitgevoerd zoals hierboven vermeld.
  De bestaande packaging-/securitytests zijn in deze ronde niet herhaald.
- `docker compose config --quiet`: geldig voor `compose.yaml`,
  `compose.portainer.yaml` en beide gedocumenteerde voorbeelden, met fictief
  beheerwachtwoord en zonder echte `.env`.
- Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`,
  JavaScript-syntax en modulegrenzen geslaagd. Bestaande Starlette- en
  experimentele-VM-modulewaarschuwingen blijven zichtbaar.

README, requirements, architectuur en testinstructies bijgewerkt. De aparte
`compose.portainer.yaml` gebruikt bestaande lokale NAS-mappen en standaardpoort
8090; bron-Compose blijft benoemde volumes gebruiken. De herstelopdracht in README
krijgt tijdelijk expliciete bestands-capabilities om toegang te houden tot de
nu afgeschermde datamap. Die herstelprocedure is niet opnieuw uitgevoerd.

Niet uitgevoerd: deployment op de NAS, Synology-ACL-controle, back-upherstel naar
Docker-opslag, browsermatrix, GitHub Actions of nieuwe imagepublicatie.


## Eén Compose-bestand en privacy van wijzigingen — 31 oktober 2026

- `compose.yaml` is nu het gedeelde installatiebestand voor Compose en Portainer.
  Beide services gebruiken `DASHBOARD_IMAGE` (standaard de gepubliceerde 0.1.0).
  `DATA_VOLUME` en `CACHE_VOLUME` kiezen standaard dezelfde benoemde volumes als
  eerder, of absolute hostpaden. Het aparte `compose.portainer.yaml` is verwijderd.
  Bronbuild en CI zijn aangepast aan expliciet bouwen en dezelfde image gebruiken.
- README, Docker Hub-voorstel en architectuur leggen de afweging voor `storage-init`
  uit: alleen de korte voorbereidingsservice heeft root met CHOWN/FOWNER; de webapp
  blijft zonder rootrechten. `Exited (0)` is normaal, de container wordt niet
  automatisch verwijderd. Migratie-instructies behouden bestaande paden, poort,
  wachtwoord en stacknaam; `STORAGE_ROOT` is vervangen door de twee padvariabelen.
- Geautomatiseerde opslagregressies en Docker-contextfiltering tegen
  `ruudv/family-dashboard:0.1.0`: **3/3 geslaagd** (15,11 s). Beide opslagtests
  gebruiken nu het echte gedeelde Compose-bestand en controleren de opgeloste
  image/mounts, gevolgd door eerste startup en containervervanging met behoud van
  fictieve instellingen. Geen echte data of `.env` gebruikt.
- `docker compose config --format json` controleert beide opslagvormen. De YAML in
  README en Docker Hub-voorstel is exact gelijk aan `compose.yaml`.
- Backend/unittests: **104 geslaagd, 4 opt-in Docker-tests overgeslagen** (3,97 s).
  De packagingtest en twee opslaggevallen zijn afzonderlijk uitgevoerd zoals hierboven.
- Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`, JavaScript-syntax,
  modulegrenzen en `git diff --check`: geslaagd.
- Git- en Docker-uitsluitingen uitgebreid voor `.env.*`, met behoud van `.env.example`.
  De echte Docker-contexttest controleert ook `.env.local` en `.env.production`.
- Alleen-lezen privacycontrole van 87 gevolgde en niet-genegeerde bronbestanden:
  vergeleken met het lokale beheerwachtwoord, integratiegegevens en namen uit SQLite;
  aanvullende controle op persoonlijke ontwikkelpaden en herkenbare sleutelpatronen.
  Overeenkomsten betroffen algemene programmatermen en boodschappenfixtures die al
  in HEAD aanwezig waren. Geen onverklaarde kandidaten of nieuwe privéconfiguratie.
  Referentiewaarden zijn niet in dit rapport of de controle-uitvoer opgenomen.
  `.env`, lokale varianten, databases, cache en back-ups worden door Git genegeerd.
- Handmatige gebruikersbevestiging: de eerdere NAS-installatie met de aparte
  Portainer-configuratie werkt. De nieuwe gedeelde configuratie is nog niet op de
  NAS uitgevoerd. Geen browsermatrix, CI-run, imagepublicatie, commit of push gedaan.


## Rechten na terugzetten van database en bestanden — 31 oktober 2026

De eerdere init wijzigde alleen de twee opslagmappen. Een gekopieerde database kon
wel worden geopend, maar `db.connect()` kon mode 0600 niet instellen als het bestand
nog van de kopieergebruiker was. De init verwerkt nu ook submappen en gewone bestanden
in `/data` en `/cache`: UID/GID 10001, mappen 0700, bestanden 0600. De inhoud wordt
niet gewijzigd. Alleen de tijdelijke service krijgt aanvullend DAC_OVERRIDE voor
het openen van private teruggezette bestanden en mappen; de apprechten blijven gelijk.
Bestandsdescriptoren, `O_NOFOLLOW` en niet-volgende traversal voorkomen het volgen
van symbolische links. Speciale bestanden worden overgeslagen en hardlinks naar
gewone bestanden worden geweigerd om gedeelde inodes buiten de opslag te beschermen.

Uitgevoerd:

- Nieuwe herstelfase van de bind-mountregressie eerst tegen de oude init uitgevoerd:
  **verwacht mislukt**, met dezelfde `PermissionError` op `family.db.chmod` (10,48 s).
- Na herstel van de init, beide containerregressies tegen de gepubliceerde
  `ruudv/family-dashboard:0.1.0`: **2/2 geslaagd** (19,27 s), op Docker Desktop
  arm64 met amd64-emulatie. Benoemde volumes en echte Linux-bind-mounts getest.
  Een consistente fictieve databaseback-up is met afwijkende UID/GID teruggezet;
  private geneste bestanden en mappen zijn met mode 000 aangemaakt. Na voorbereiding
  start de app zonder root, de database-integriteit is goed en de opgeslagen
  instellingen en fictieve bestandsinhoud zijn behouden. Eigenaar en modes kloppen.
  Symbolische links naar `/app` en de licentie blijven links zonder doelwijziging.
  Een gewone hardlink veroorzaakt de verwachte initfout. Testresources opgeruimd.
- Backend-/unittests: **104 geslaagd, 4 opt-in Docker-gevallen overgeslagen** (4,01 s).
  De twee opslaggevallen zijn apart uitgevoerd zoals hierboven vermeld.
- Compose gevalideerd zonder echte `.env`; README en Docker Hub-voorbeeld exact
  gelijk aan `compose.yaml`. Ruff lint/format, CSS-format, Prettier na
  `npm ci --ignore-scripts`, JavaScript-syntax/modulegrenzen en `git diff --check`
  geslaagd. Bekende upstream-/VM-modulewaarschuwingen blijven zichtbaar.
- Geen echte database of integratiegegevens gebruikt; alleen fictieve testbestanden.
  Geen imagewijziging of -publicatie, commit, push, browsermatrix of NAS-uitvoering.

Bij een restore: stop eerst het dashboard, zet uitsluitend een consistente database
terug en deploy de volledige stack met de aangepaste init. Alleen het dashboard
herstarten voert de aparte voorbereidingsservice niet opnieuw uit.
## Controle Prettier-fout in child-mode.js — 31 oktober 2026

- `npm ci --ignore-scripts` uitgevoerd. De huidige lokale `child-mode.js` bevatte
  de opmaakcorrectie al; Prettier `--write` rapporteerde `unchanged`.
- `npm run format:check`, JavaScript-syntax en modulegrenzen: geslaagd.
- Backend/unittests: **104 geslaagd, 4 opt-in Docker-tests overgeslagen**.
- Ruff lint/format, CSS-format en `git diff --check`: geslaagd.
- Geen browsertests of GitHub Actions uitgevoerd; uitsluitend opmaak gecontroleerd,
  zonder nieuwe gedragswijzigingen.


## Release 0.2.0 naar Docker Hub — 31 oktober 2026

- Versie in health-API en OCI-label naar `0.2.0` bijgewerkt; Compose, `.env.example`,
  README, SECURITY, Docker Hub-overviewbestand en testinstructies verwijzen naar 0.2.0.
  Bestaande historische verificatie van 0.1.0 blijft behouden.
- Nieuwe API-regressie bevestigt het volledige healthantwoord inclusief versie.
  Backend-/unittests: **105 geslaagd, 4 opt-in Docker-gevallen overgeslagen**.
- Exacte releaseimages lokaal gebouwd voor linux/amd64 en linux/arm64. Per architectuur
  beveiligings- en opslagregressies uitgevoerd: **3/3 geslaagd** (22,15 s en 15,96 s).
  Inclusief echte Compose-start, frontend/health/state, lege root-owned opslag,
  volumes en Linux-bind-mounts, herstel met afwijkende eigenaar en containervervanging.
  Alleen fictieve configuratie en tijdelijke opslag; testresources opgeruimd.
- Docker-buildcontextregressie afzonderlijk uitgevoerd: **1/1 geslaagd**.
- Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`, JavaScript-syntax,
  modulegrenzen en `git diff --check`: geslaagd. Compose-voorbeelden in README en
  `docs/DOCKER_HUB.md` geparseerd en exact gelijk aan `compose.yaml`.
- `BUILDX_GIT_INFO=false docker buildx build --platform linux/amd64,linux/arm64
  --provenance=false --sbom=false --tag ruudv/family-dashboard:0.2.0 --push .`: geslaagd.
  Geen Git-bronmetadata/attestations gepubliceerd. Tag bestond vooraf nog niet.
- Daarna het manifest rechtstreeks bij Docker Hub gecontroleerd:
  - Index: `sha256:1b202a4cbddab4ae3dbbb62cfc60cbf7a9e9e4d55acd7421819d299e3c10cdc3`.
  - amd64: `sha256:c77be2cb6b0382ee54299a774662f094c291a2a1d496ffbf22d2278bb57f700e`.
  - arm64: `sha256:4135bdc81edfa33d0187f909647ad4973051058a97be6a7b335769da2dc85dfd`.
  Beide platformdigests zijn exact gelijk aan de vooraf geteste lokale images.
- Docker Scout 1.27.0 vóór én na publicatie uitgevoerd. Na publicatie met
  `docker scout cves --platform linux/<architectuur> --exit-code --only-cve-id
  CVE-2026-85091,CVE-2026-84243 registry://ruudv/family-dashboard:0.2.0`:
  **beide gerichte scans schoon**, exitcode 0, elk 93 pakketten. Dit is geen volledige
  CVE-scan of bevestiging van de asynchrone Docker Hub-webscan.
- Niet uitgevoerd: fysieke NAS-installatie, browsermatrix, GitHub Actions of Git-push.
  Docker Hub-overview alleen lokaal bijgewerkt; de webbeschrijving is niet aangepast.
  Tag 0.1.0 en een eventuele latest-tag zijn niet gewijzigd.


## python-dotenv CVE-2026-28684 / release 0.2.1 — 31 oktober 2026

- [Upstream-advisory](https://github.com/theskumar/python-dotenv/security/advisories/GHSA-mf9w-mj56-hr94)
  en [CVE-record](https://www.cve.org/CVERecord?id=CVE-2026-28684) gecontroleerd:
  `python-dotenv 1.1.1` is kwetsbaar; de fix staat in `1.2.2`.
  De fout betreft schrijven via set_key/unset_key. De applicatie gebruikt alleen
  load_dotenv; geen aanroepen van set_key/unset_key, wget of subprocess in `app/` gevonden.
- `requirements.txt` naar python-dotenv 1.2.2 bijgewerkt. Nieuwe regressie voor
  set én unset simuleert een cross-device rename-fout met uitsluitend tijdelijke,
  fictieve bestanden. Met 1.1.1 eerst **2/2 verwacht mislukt**: het symlinkdoel werd
  daadwerkelijk overschreven. Na de update slagen beide gevallen.
- Volledige scan van de eerste kandidaat toonde daarnaast zes pip-meldingen en
  BusyBox CVE-2025-60876. Pip upgraden alleen bleek onvoldoende: daarin gebundelde
  msgpack/urllib3/setuptools leverden extra scanmeldingen op. Definitieve Dockerfile
  gebruikt pip 26.2.2 tijdens de build, controleert dependencies met `pip check` en
  verwijdert pip inclusief zijn vendored dependencies vóór afronding van de image.
  Er zijn geen applicatiedependencies voor deze pip-meldingen gewijzigd.
- Versie in health-API/OCI-label en actuele installatievoorbeelden naar 0.2.1.
  Containerregressie controleert nu ook minimaal python-dotenv 1.2.2 en afwezigheid
  van pip. README en Docker Hub-overviewbestand beschrijven de resterende melding.
- Automatisch op de host: **107 backend-/unittests geslaagd, 4 opt-in Docker-gevallen
  overgeslagen**. In de definitieve amd64- en arm64-images dezelfde complete set:
  elk **107 geslaagd, 4 overgeslagen**. Bekende Starlette-deprecationwaarschuwing.
- Automatisch op de definitieve images per architectuur: beveiligings- en
  opslagregressies elk **3/3 geslaagd** (amd64 32,21 s, arm64 16,42 s). Echte Compose-start,
  health/frontend/state, lege root-owned opslag, volumes en Linux-bind-mounts,
  teruggezette eigenaars/rechten en containervervanging getest. Tijdelijke data en
  fictieve credentials gebruikt; testresources opgeruimd. amd64 via emulatie op een arm64-Mac.
- Docker-buildcontextregressie afzonderlijk **1/1 geslaagd**.
- Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`, JavaScript-syntax,
  modulegrenzen en `git diff --check`: geslaagd. Compose-voorbeelden in README en
  Docker Hub-overview geparseerd en exact gelijk aan `compose.yaml`.
- Volledige Docker Scout 1.27.0-scans van beide definitieve lokale images zonder CVE-
  of ernstfilter: elk **0 critical, 0 high, 1 medium, 0 low**, 92 pakketten.
  CVE-2026-28684, de eerdere zlib/glibc-meldingen en de pip-meldingen ontbreken.
  Exitcode 2 wegens de enige resterende melding: **BusyBox 1.37.0-r30,
  CVE-2025-60876 (wget)**. Niet onderdrukt. De
  [Alpine-tracker](https://security.alpinelinux.org/vuln/CVE-2025-60876)
  vermeldt geen als opgelost gemarkeerde versie. De applicatie gebruikt wget niet;
  dit is geen bewijs dat het aanwezige pakket gepatcht is.
- Na expliciete toestemming voor 0.2.1, publicatie met
  `BUILDX_GIT_INFO=false docker buildx build --platform linux/amd64,linux/arm64
  --provenance=false --sbom=false --tag ruudv/family-dashboard:0.2.1 --push .`: geslaagd.
  0.2.1 bestond vooraf niet. Geen Git-bronmetadata/attestations gepubliceerd.
- Het manifest daarna rechtstreeks op Docker Hub gecontroleerd:
  - Index: `sha256:3045f95ca6307957bb01fda9d2a49666d5f78c393c0c5b9c94c6dcabcf5c40d8`.
  - amd64: `sha256:e8d55aa8482c42abf247f2f4c21b868464ca160bba726ca63a670a3817ad0ead`.
  - arm64: `sha256:cfbeb7055682a3eacaa16b3efe34eb0088c2485a1b311bd7270310f155a0ddbc`.
  Platformdigests exact gelijk aan de geteste definitieve lokale images.
- Niet uitgevoerd: browsermatrix, fysieke NAS-installatie, GitHub Actions, commit
  of Git-push. Docker Hub-webbeschrijving alleen lokaal voorbereid. Oudere tags
  en een eventuele latest-tag niet gewijzigd.
- Na publicatie dezelfde volledige scans rechtstreeks tegen
  `registry://ruudv/family-dashboard:0.2.1` uitgevoerd met respectievelijk
  `--platform linux/amd64` en `--platform linux/arm64`: elk dezelfde 92 pakketten,
  **0 critical, 0 high, 1 medium, 0 low**; uitsluitend BusyBox CVE-2025-60876.
  Beide exitcode 2 wegens die open melding. Dit is Docker Scout tegen de registry,
  geen bevestiging dat de asynchrone Docker Hub-webscan al is afgerond.

## Playwright-fouten in GitHub Actions — 31 oktober 2026

- Logs en WebKit-screenshot/trace van [run 41243103441](https://github.com/ruudverheijden/family-dashboard/actions/runs/41243103441)
  geïnspecteerd. Chromium slaagde; Firefox faalde op twee 48-pixelmetingen en
  kindmodus-overflow; WebKit faalde op dezelfde kindmodus-overflow.
- Automatisch vóór de fix onder Linux gereproduceerd: Firefox rapporteert
  47,99997 pixels voor een 48-pixelknop. Met `fonts-dejavu-core` gebruiken Firefox
  en WebKit DejaVu Sans als fallback; beide kindmodustests faalden dan opnieuw.
  Het raster werd circa 375,4 pixels breed bij 351 pixels beschikbare ruimte;
  de pagina kreeg een scrollbreedte van 401 bij een viewport van 390 pixels.
- Fix: begrensde rasterkolom en afbreekbare mobiele welkomstbalk. De bestaande
  minimum-aanraakmaat blijft 48 CSS-pixels; alleen de meetasserties krijgen
  0,001 pixel afrondingstolerantie. De kindmodusflow controleert nu ook kaartgrenzen
  en draait op 390×664, 750×342 en 768×1024.
- Automatisch na de fix: volledige Linux-browsermatrix **225/225 geslaagd**
  (75 per browser, 1052,14 seconden), zonder retries. Ubuntu 24.04 arm64 via
  `mcr.microsoft.com/playwright/python:v1.64.1-noble`, Python 3.12, Playwright 1.64.1,
  vastgepinde testdependencies en DejaVu Sans. Uitsluitend gekopieerde broncode,
  tijdelijke databases/caches en fictieve credentials; geen `.env` of echte data.
  De bekende pytest-playwright-deprecationwaarschuwing blijft zichtbaar.
- Aanvullend de mobiele WebKit-kindmodus **1/1 geslaagd** en de volledige
  paginascreenshot visueel geïnspecteerd: welkomstbalk, terugknop en alle kaarten
  passen binnen de viewport; de taaktekst breekt af.
- Automatisch op de host: **107 backend-/unittests geslaagd, 4 opt-in Docker-tests
  overgeslagen**. Ruff lint/format, CSS-format, Prettier na `npm ci --ignore-scripts`,
  JavaScript-syntax, modulegrenzen en `git diff --check`: geslaagd.
- Niet uitgevoerd: nieuwe GitHub Actions-run op de fix, Linux amd64-browsermatrix,
  fysieke apparaten, commit of Git-push. De tijdelijke Linux-testcontainer is opgeruimd.

## Datum en dagovergang kinddashboard — 1 november 2026

- Fix: volledige datum bij de begroeting; kindmodus vraagt bij de dagovergang of
  terugkeer naar het tabblad vandaag op in de ingestelde tijdzone. De ouderweergave
  schuift mee als die vandaag toonde; bewust gekozen andere datums blijven behouden.
  Ook de opgeslagen ouderdatum voor terugkeer uit kindmodus schuift zo nodig mee.
- Automatisch: `tests/e2e/test_day_rollover.py` en de bestaande
  `test_child_mode_personal_tasks_routines_and_rewards`, samen **14/14 geslaagd**
  in Chromium en WebKit (33,22 seconden). De nieuwe regressies simuleren middernacht
  en terugkeer na een tijdsprong zonder timerticks; taken en routinestappen beginnen
  op de nieuwe dag onafgevinkt en de vorige dag blijft via de echte API afgevinkt.
  De bestaande flow controleert ook kaartgrenzen, overflow en aanraakmaten op
  390×664, 750×342 en 768×1024, nu met de extra datum.
- Automatisch: backend/units **107 geslaagd, 4 opt-in Docker-tests overgeslagen**.
  Ruff lint/format, CSS-opmaak, Prettier na `npm ci --ignore-scripts`,
  JavaScript-syntax, modulegrenzen en `git diff --check`: geslaagd.
- Browserstart binnen de sandbox mislukte vóór applicatiebezoek; de geslaagde
  browserrun hierboven is buiten de sandbox uitgevoerd met de geïsoleerde fixtures.
- Niet uitgevoerd: volledige browsersuite, Firefox, fysieke apparaten, een echte
  nachtelijke duurtest of deployment. De terugkeertest simuleert het visibility-event;
  zij test geen daadwerkelijke OS-sluimerstand. Geen handmatige visuele controle.

### Aanvullende controle ouderdashboard en routinedagen — 1 november 2026

- Opslag en selectie geïnspecteerd: routine-uitvoeringen zijn uniek per sjabloon,
  kalenderdag en persoon. Alleen ingestelde weekdagen vanaf de startdatum krijgen
  een uitvoering. Afvinken wijzigt uitsluitend die uitvoering en legt een
  historie-item met tijdstip vast; dagovergangen wissen die gegevens niet.
- Extra browserregressie: routine in oudermodus afvinken, naar een niet-ingeplande
  dag overgaan (geen uitvoering), doorgaan naar de volgende ingeplande dag
  (nieuwe ID en lege voortgang), terugbladeren naar de originele afgevinkte dag.
  De volledige oorspronkelijke uitvoering en historie inclusief tijdstip blijven
  ongewijzigd via de echte API.
- Definitieve run van `tests/e2e/test_day_rollover.py`: **10/10 geslaagd** in
  Chromium en WebKit, 18,13 seconden. Een eerdere versie van de nieuwe test
  gebruikte een onvolledige knopnaam; na correctie hierboven opnieuw uitgevoerd.
  Ruff lint/format en `git diff --check`: geslaagd.
- Geen verdere productielogica gewijzigd: de eerdere fix voor het volgen van
  vandaag omvat ook de ouderweergave. RT-03 en de gebruikersdocumentatie verduidelijkt.
  Geen deployment of controle tegen de echte gezinsdatabase uitgevoerd.


## Routines als onderdeel van agenda en dagoverzicht — 1 november 2026

- Geïmplementeerd: routinekaarten per ingeplande dag in dag-, drie dagen- en
  weekagenda, met tijdvenster in het rooster en zonder tijdvenster in een aparte
  rij erboven. Gedeelde overlapindeling met afspraken; korte kaarten houden een
  aanraakvlak van minimaal 48 pixels. Voltooide kaarten blijven zichtbaar als Klaar.
- Een agendakaart opent een paneel met dezelfde stappen/uitvoerings-ID's als de
  routinetab. Afvinken/heropenen, voortgang per persoon, actuele versies, externe
  wijzigingen, foutmelding na mislukte opslag, datumselectie en focusterugkeer
  zijn in de browser gecontroleerd. Het paneel is opgenomen in de bestaande
  invoerbewaking; hiervoor is geen afzonderlijke inactiviteitstest uitgevoerd.
- Het routineoverzicht toont alleen de gekozen dag. Lege dagen tonen één brede
  melding en zo mogelijk een knop naar de volgende routinedag. Routines beheren
  toont sjablonen met personen, weekdagen, startdatum en tijdvenster.
- Tijdvensters zijn optioneel. De editor heeft een expliciete keuze; beide velden
  leegmaken schakelt die ook uit. Eén ontbrekende tijd wordt geweigerd. Bestaande
  uitvoeringen en hun historie blijven onveranderd bij sjabloonbewerkingen.
- Automatisch: backend/units **110 geslaagd, 4 opt-in Docker-tests overgeslagen**.
  Ruff lint/format, CSS-format, Prettier, JavaScript-syntax, modulegrenzen en
  `git diff --check`: geslaagd. `npm ci --ignore-scripts` was in deze sessie uitgevoerd.
- De brede browserrun leverde **179 geslaagd en 1 fout** (322,43 seconden): WebKit
  blokkeerde lege optionele tijdvelden met native invalid-events, hoewel de
  geraadpleegde validity-status geldig leek. De expliciete tijdvensterkeuze en
  het uitschakelen van lege velden verhelpen dit; beide invoerroutes krijgen een
  regressietest. De volledige matrix is na deze correctie niet opnieuw gedraaid;
  alle getroffen routine- en kindmodusflows zijn opnieuw gekozen.
- Definitieve gerichte browserrun: **40/40 geslaagd** in Chromium en WebKit
  (89,98 seconden), met `pytest tests/e2e --browser chromium --browser webkit
  -k "routine or child_mode"`. Inclusief beide manieren om tijdvensters uit te
  schakelen, de definitieve compacte kaarten en de bestaande routine-editors.
- Handmatig visueel: mobiele screenshots van het paneel en de tijdlijn
  geïnspecteerd. Het paneel kreeg een ondoorzichtige achtergrond; lege foutmeldingen
  zijn verborgen. Korte tijdlijnkaarten zijn compacter gemaakt met tijd naast het
  routinelabel en zichtbare voortgang.
- De publieke HTML, kalender-/shell-JavaScript en CSS van de bestaande lokale
  server op poort 8081 kwamen bij controle overeen met de werkbestanden.
- Niet uitgevoerd: Firefox, fysieke apparaten, Linux-browsermatrix, Dockerchecks,
  nieuwe release/image, commit of push. Browserdata blijft tijdelijk en fictief;
  er zijn geen tests tegen de echte gezinsdatabase uitgevoerd.

## Volledig routinebereik na terugkeer naar de agenda — 1 november 2026

- Geïsoleerd gereproduceerd vóór de fix: na het dagelijkse routineoverzicht wordt
  bij terugkeer naar de weekagenda geen weekverzoek verstuurd totdat de volgende
  poll loopt. De regressie pauzeert de klok vóór herladen en faalde vervolgens
  op het ontbreken van dat weekantwoord binnen vijf seconden.
- Fix in `shell.js`: directe geforceerde verversing bij terugkeer naar de agenda,
  afwijzen van antwoorden die niet meer bij de actuele datum/periode passen en
  direct uitvoeren van een geforceerde verversing die tijdens een lopend verzoek
  werd gevraagd. Gewone polling wordt bij een lopend verzoek niet extra ingepland.
- Nieuwe browserregressies: volledige week direct na het routineoverzicht, een
  vertraagd dagantwoord dat pas na terugkeer arriveert en een dagelijkse routine
  vanaf vandaag in drie dagen en de volledige volgende week. Datums vóór de
  startdatum krijgen geen uitvoering. De zes gerichte controles slaagden in
  Chromium en WebKit (vier in 7,55 seconden, twee in 3,92 seconden).
- Lokale state-API gecontroleerd: de dagelijkse routine start op 31 oktober 2026;
  de huidige kalenderweek eindigt op zondag 1 november. De week-API bevat voor
  die routine 31 oktober en 1 november. Deze controle gebruikt de normale
  state-API, die volgens het bestaande contract uitvoeringen kan aanmaken.
  De startdatum en weekdagen zijn niet aangepast.
- Backend/units: **110 geslaagd, 4 opt-in Docker-tests overgeslagen** (3,54 seconden).
  Ruff lint/format, CSS-opmaak, Prettier, JavaScript-syntax, modulegrenzen en
  `git diff --check`: geslaagd. Geen test gebruikt de echte gezinsdatabase.
- Volledige browseracceptatie na de fix: **188/188 geslaagd** in Chromium en
  WebKit (94 per browser, 355,61 seconden), zonder retries. Inclusief alle nieuwe
  bereikregressies, bestaande navigatie, kalender, routinepaneel, kindmodus,
  beloningen, inactiviteit, formulieren en verbindingsherstel. Alleen de bestaande
  pytest-playwright-deprecationwaarschuwing. Dit vervangt de eerdere gedeeltelijk
  geslaagde browserrun als meest recente volledige verificatie.
- De lokale server op 8081 levert de nieuwe `shell.js` byte voor byte gelijk aan
  het werkbestand. Een reeds geopend tabblad moet de gewijzigde JavaScript-module
  opnieuw laden. Firefox, fysieke apparaten en Dockerchecks zijn niet uitgevoerd.

## Concrete oorzaak en herstel van ‘Naar bed’ — 1 november 2026

- De echte lokale database alleen-lezen onderzocht. De dagelijkse routine had de
  juiste planning, maar tien toekomstige uitvoeringen (twee personen, 2–6 november)
  bevatten nog de oudere naam ‘Ochtend’, 07:00–08:00 en oude stappen. De eerdere
  navigatiefix loste deze opgeslagen toekomstige snapshots niet op.
- Vóór de codewijziging een consistente SQLite-back-up gemaakt:
  `backups/before-future-routine-repair-2026-11-01-e05c6c59.db` (0600; map genegeerd
  door Git). De bestaande vijf beschermde routine-uitvoeringen en de complete
  historie- en puntentabellen zijn met SHA-256 vastgelegd voor vergelijking.
- Planner herstelt voortaan toekomstige routines zonder vinkjes, afvinkhistorie of
  puntenboekingen naar het actuele sjabloon, binnen de bestaande transactie. Een
  gewijzigd uitvoeringsversienummer weigert oude stapindices. Heropenen beschermt
  de oorspronkelijke uitvoering via zijn historie. Vervallen, onaangeraakte plannen
  worden verborgen en kunnen niet vanaf een oude kaart worden voltooid; de records
  worden niet verwijderd. Vandaag en eerdere uitvoeringen worden niet herschreven.
- Bij routinewijzigingen gebeurt dit in dezelfde transactie als opslag, historie en
  verzoekdeduplicatie. Bestaande verouderde toekomstplannen worden ook bij normaal
  inhalen/ophalen hersteld. Er is geen handmatige SQL-update op de echte data gebruikt.
- Het lokale proces heeft na herladen tien lege toekomstplannen gecorrigeerd. Vergelijking
  met de back-up bevestigt uitsluitend wijzigingen op 2–6 november, met lege voortgang
  en één versieverhoging. Alle achttien gecontroleerde toekomstige uitvoeringen van
  ‘Naar bed’ bevatten daarna de juiste naam en 18:30–19:30. De beschermde uitvoeringen,
  historische tabel en puntentabel zijn exact gelijk gebleven.
- De echte lokale week-API voor 2–8 november levert ‘Naar bed’ op alle zeven dagen,
  twee personen per dag, 18:30–19:30 en de vier juiste stappen. Dit is een controle
  tegen de lokale installatie; alle geautomatiseerde tests gebruiken fictieve,
  geïsoleerde databases. De normale state-API kan geplande uitvoeringen aanmaken.
- Backend/units: **118 geslaagd, 4 opt-in Docker-tests overgeslagen** (4,28 seconden).
  Acht nieuwe API-regressies dekken herhaald wijzigen, oude browserversies, gedeeltelijk/
  volledig voltooide en heropende uitvoeringen, punten/historie, gewijzigde weekdagen,
  personen, startdatum, archivering en heractivering zonder records te verwijderen.
- De gerichte browserreproductie met een eerder bekeken ochtendwerkweek die naar
  elke avond verhuist slaagt in Chromium en WebKit (**2/2**, 5,13 seconden), inclusief
  de juiste stappen in het paneel en behoud van bestaande eerdere snapshots.
- Ruff lint/format, CSS-opmaak, Prettier, JavaScript-syntax, modulegrenzen en
  `git diff --check`: geslaagd. Geen Firefox, fysieke apparaten of Dockerchecks uitgevoerd.
- Definitieve routine-/kindmodusacceptatie: **50/50 geslaagd** in Chromium en
  WebKit (97,30 seconden), zonder retries. Inclusief aparte kaarten en paneelstappen
  voor een beschermde oude uitvoering naast een gewijzigd toekomstplan voor een
  andere persoon. Een bestaande stapassertie is op de juiste routinekaart gericht,
  omdat twee routines dezelfde stapnaam bevatten. De volledige overige browsermatrix
  is na deze snapshotwijziging niet opnieuw uitgevoerd.

## Routinecarrousel en klokken in kindmodus — 2 november 2026

| Controle | Resultaat |
|---|---|
| Kindmodusregressie met vaste klokpositie, `.venv/bin/python -m pytest tests/e2e/test_dashboard.py -k child_mode_personal_tasks_routines_and_rewards --browser chromium --browser webkit -q` | **6 geslaagd** (drie viewports per browser) |
| Firefox | Niet gevalideerd: Playwright Firefox start niet (`Could not find profile folder`), ook niet na herinstallatie en gebruik van `/tmp` |
| CSS, `.venv/bin/python tools/format_css.py --check` | Geslaagd |
| JavaScript-opmaak, `npm run format:check` | Geslaagd |
| JavaScript, `node --check app/static/app.js && node --experimental-vm-modules tools/check_frontend.mjs` | Geslaagd; 23 modules geparseerd/gekoppeld, geen cyclische imports |
| Ruff, `.venv/bin/ruff check tests/e2e/test_dashboard.py && .venv/bin/ruff format --check tests/e2e/test_dashboard.py`; diff, `git diff --check` | Geslaagd |

De browserregressie controleert de lopende routine, automatisch doorschakelen naar
de volgende starttijd en daarna een routine zonder tijd, de analoge en digitale
starttijdklok, de actuele bovenbalkklok en navigatie vooruit en terug. Een extra lange,
meerregelige routinetitel controleert dat de klok niet horizontaal of verticaal verspringt.
Geen handmatige apparaatcontrole uitgevoerd.

## Kinddashboard als hoofdnavigatietab — 2 november 2026

| Controle | Resultaat |
|---|---|
| Kinddashboard en hoofdnavigatie, `.venv/bin/python -m pytest tests/e2e/test_dashboard.py -k child_mode_personal_tasks_routines_and_rewards --browser chromium --browser webkit -q` | **6 geslaagd** (drie viewports per browser) |
| Terugkeer naar de ouderplanner, `.venv/bin/python -m pytest tests/e2e/test_day_rollover.py -k child_day_rollover --browser chromium -q` | **2 geslaagd** |
| Spelletjes en terug naar het kinddashboard, `.venv/bin/python -m pytest tests/e2e/test_games.py -k game_price_admin_and_child_entry --browser chromium -q` | **1 geslaagd** |
| JavaScript-, CSS- en Ruff-controles | Geslaagd |

De kindmodus opent nu een eigen tabblad naast de gewone hoofdtabbladen. De actuele
tijdklok blijft in de normale bovenbalk; de aparte knop om naar de ouderweergave te
gaan is verwijderd. De Kalender-tab herstelt de eerder geopende planner. Op smalle
schermen blijven de hoofdnavigatie en klok zichtbaar en voldoen de knoppen aan de
minimale aanraakmaat.


## Spelletjes als puntenbeloning — 2 november 2026

Automatisch gecontroleerd tegen de gecombineerde werkmap, met uitsluitend
fictieve profielen, tijdelijke databases en een lokale fictieve Immich-server:

| Controle | Uitgevoerd resultaat |
|---|---|
| `.venv/bin/python -m pytest -q` | **129 geslaagd, 4 overgeslagen**; containercontroles niet uitgevoerd |
| Nieuwe API-regressies `tests/test_games.py` | **8 geslaagd**, onderdeel van de backendrun |
| Spelletjes + betrokken navigatie: `.venv/bin/python -m pytest tests/e2e/test_games.py tests/e2e/test_dashboard.py -k 'game or child_mode_personal or points_reward_request or navigation_responsive or iphone13_touch' --browser chromium --browser webkit -q --tracing retain-on-failure --screenshot only-on-failure` | **36 geslaagd, 2 gefaald**; alle 16 spelletjesgevallen geslaagd. De twee fouten waren een dubbelzinnige saldo-selector in de bestaande beloningstest, door hetzelfde saldo in verborgen beheerinhoud. Selector gericht op `.rewards-summary`. |
| Hertest na die selectorcorrectie: `tests/e2e/test_dashboard.py -k points_reward_request --browser chromium --browser webkit -q` | **2 geslaagd**; daarmee zijn alle 38 betrokken gevallen over deze run en hertest geslaagd |
| `.venv/bin/ruff check .` en `.venv/bin/ruff format --check .` | Geslaagd |
| `.venv/bin/python tools/format_css.py --check` | Geslaagd, bestaande CSS-regelvolgorde behouden |
| `npm ci --ignore-scripts` en `npm run format:check` | Geslaagd |
| `node --check app/static/app.js` en `node --experimental-vm-modules tools/check_frontend.mjs` | Geslaagd; **23 modules**, geen cyclische imports |
| `git diff --check` | Geslaagd |
| Firefox-startpoging bij spelletjesmatrix | Niet gevalideerd: Playwright Firefox stopt vóór de tests met `Could not find profile folder` |

De speltests omvatten aankoop, onvoldoende saldo en reserveringen, beheerrechten,
prijsconflicten, twee gelijktijdige aankopen, idempotente verzoeken en zetten,
servergestuurd verlopen en stoppen, verborgen Memory-kaarten, alle drie
speldoelen, hervatten met dezelfde eindtijd, visuele orkestreeksen, mislukte
foto-preflight zonder afschrijving, behoud van andere instellingsconcepten en
onzekere HTTP-antwoorden na een al verwerkte aankoop/zet. De browsercontrole
gebruikt 390×664, 750×342 en 768×1024 en controleert ook de bestaande responsive
hoofdnavigatie en kindmodus. De navigatietest controleert zichtbare tabs, omdat
het gelijktijdig toegevoegde kinddashboardtab in de ouderweergave verborgen is.

Een eerder gestarte volledige browsermatrix is afgebroken omdat de kindnavigatie
en bijbehorende tests tijdens die run gelijktijdig wijzigden. Daarna is de
bovenstaande gerichte set uitgevoerd. De volledige overige browsermatrix is
na de laatste gecombineerde wijzigingen niet opnieuw afgetekend.

**Niet handmatig uitgevoerd:** fysieke touchscreens, hoorbare kwaliteit van de
synthetische dierentonen, de laatste-30-secondenaftelling, automatische
inactiviteitsonderdrukking en de echte Immich-installatie. Verlopen is wel via
de API getest. De browserproeven gebruiken testfoto's, geen persoonlijke albums.

## Confetti bij routine-stappen in kinddashboard — 2 november 2026

| Controle | Resultaat |
|---|---|
| `.venv/bin/python -m pytest tests/e2e/test_dashboard.py -k 'child_mode_personal_tasks_routines_and_rewards and size0' --browser chromium -q` | **1 geslaagd** |
| `node --check app/static/app.js` en `node --experimental-vm-modules tools/check_frontend.mjs` | Geslaagd; **23 modules**, geen cyclische imports |
| `npm run format:check`, Ruff voor de aangepaste E2E-test en `git diff --check` | Geslaagd |

De kindmodusregressie bevestigt dat zowel een gewone kindtaak als een afzonderlijke
routine-stap dezelfde confetti-animatie activeert. De bestaande routineviering blijft
voorbehouden aan het voltooien van de volledige routine.


## Dierenorkest: voorbereiding en geluidsknop — 2 november 2026

- Automatisch: `tests/e2e/test_games.py -k orchestra --browser chromium --browser webkit -q`
  geeft **8 geslaagd**. Naast het volledige spel controleert een gepauzeerde
  Playwright-klok de cijfers 3, 2 en 1 op telkens één seconde, daarna exact
  1,5 seconde zonder dier-aanwijzing en vervolgens de start van de reeks.
- Dezelfde regressie controleert op 390×664, 750×342 en 768×1024 dat de
  geluidsknop een icoon en toegankelijke aan/uit-status heeft, naast Stoppen
  staat en tijdens de overlay bedienbaar blijft. Schakelen onderbreekt de
  aftelling niet; herhaling en volgende rondes starten zonder nieuwe aftelling.
  Stoppen ruimt de presentatie-timers op zonder browserfouten.
- Automatisch: backendrun **129 geslaagd, 4 containercontroles overgeslagen**;
  Ruff lint/opmaak, CSS-opmaak, Prettier, JavaScript-syntax en modulegrenzen
  (**23 modules**, geen cycli) en `git diff --check` geslaagd.
- Geen nieuwe handmatige apparaat- of geluidscontrole uitgevoerd. Firefox
  is voor deze aanpassing niet opnieuw geprobeerd; de eerdere startbeperking
  blijft open. De overige volledige browsermatrix is niet herhaald.

- Aanvullend automatisch: `tests/e2e/test_games.py -k 'maze_purchase or game_price_admin'
  --browser chromium --browser webkit -q` geeft **8 geslaagd** voor de gedeelde
  spelkop, sessiebediening en de doolhof-layout op de drie schermformaten.

## Voltooid-geluid bij taken en routines

- `.venv/bin/python -m pytest tests/e2e/test_dashboard.py -k child_mode_personal_tasks_routines_and_rewards --browser chromium --browser webkit -q`: **6 geslaagd**. Een gemockte Web Audio-context bevestigt dat voltooien van een taak en routinestap het gewone geluid start, heropenen stil blijft en alleen de laatste routinestap in het kinddashboard het extra supersonische geluid afspeelt.
- `npm run format:check`, `npm run check:modules`, Ruff voor de aangepaste E2E-test en `git diff --check`: geslaagd; **23 modules**, geen cycli.
- Het supersonische geluid is het Pixabay-effect [Success 1](https://pixabay.com/sound-effects/film-special-effects-success-1-6297/) van Leszek_Szary (Freesound), onder de Pixabay Content License; lokaal opgenomen als `app/static/audio/routine-success-6297.mp3`. De browserregressie bevestigt dat het MP3-bestand wordt opgehaald en gedecodeerd. De hoorbare klank is niet handmatig op fysieke apparaten beoordeeld.


## Dierenorkest: vensterbrede blur en aftellen per ronde — 2 november 2026

- Automatisch: `tests/e2e/test_games.py -k orchestra --browser chromium --browser webkit -q`
  geeft **8 geslaagd**. De aangepaste regressie controleert een transparante
  blur van 12px, dekking tot de spelvensterrand, een volledig zichtbaar en
  gecentreerd cijfer op 390×664, 750×342 en 768×1024, en 3–2–1 plus 1,5 seconde
  rust bij zowel de eerste als de volgende ronde. De volledige spelstroom met
  zes reeksen slaagt in beide browsers. Handmatig herhalen binnen een ronde
  start zonder nieuwe aftelling; stoppen ruimt de timers en scrollblokkering op.
- Visuele controle: Chromium-screenshots van de daadwerkelijke spelmodal op
  390×664 en 750×342 bekeken. De blur volgt de buitenrand zonder binnenrechthoek;
  het cijfer is ook liggend volledig zichtbaar. Geluid en Stoppen blijven erboven
  bedienbaar. Dit is screenshotcontrole, geen fysieke touchscreenacceptatie.
- Backend: **129 geslaagd, 4 containercontroles overgeslagen**. Ruff lint/opmaak,
  CSS-opmaak, Prettier, JavaScript-syntax en modulegrenzen (**23 modules**, geen
  cycli), plus `git diff --check`: geslaagd.
- Firefox, fysieke apparaten en hoorbare geluidskwaliteit niet opnieuw getest.
  De volledige overige browsermatrix is voor deze kleine frontendwijziging
  niet herhaald. Deze wijziging vervangt de eerdere startaftelling die alleen
  bij een nieuw spel werd getoond.


## Dierenorkest: foutfeedback en echte dieropnames — 2 november 2026

- Backendrun: **129 geslaagd, 4 containercontroles overgeslagen**. De bestaande
  API-regressie controleert nu ook `feedback=mistake` na een foute keuze en het
  wissen daarvan na een juiste keuze.
- `tests/e2e/test_games.py -k 'mistake or local_audio or recording_can_play'
  --browser chromium --browser webkit -q`: **8 geslaagd**. Met geluid aan/uit
  worden foutoverlay, exact 2 seconden feedback, het juiste foutbestand,
  opnieuw aftellen, dezelfde ronde, ongewijzigd puntensaldo en herstel na een
  juiste keuze gecontroleerd. Beide browsers decoderen alle vijf lokale WAV's
  met de verwachte duur en zonder clipping. Een afzonderlijke test bevestigt
  dat de echte opname na inschakelen van geluid daadwerkelijk kan starten.
- `tests/e2e/test_games.py -k 'orchestra_visual or orchestra_countdown'
  --browser chromium --browser webkit -q`: **8 geslaagd** voor het volledige
  spel, aftellen per ronde, blur, headerbediening en de drie schermformaten.
- Visuele screenshotcontrole: foutoverlay in Chromium op 390×664 en 750×342
  bekeken; tekst en retry-symbool zijn volledig zichtbaar, de vensterbrede blur
  blijft intact en Geluid/Stoppen zijn bereikbaar. Geen fysieke apparaatcontrole.
- De vijf WAV-bestanden zijn lokaal opgenomen. De vier dieropnames zijn op hun
  primaire Freesound-pagina als CC0 gecontroleerd; bronnen en bewerkingen staan
  in `ORCHESTRA_AUDIO.md`. Piekniveau na bewerking is 0,60 voor de dieren; het
  eigen foutgeluid is zachter. Totale bestandsgrootte ongeveer 115 kB.
- Ruff lint/opmaak, CSS-opmaak, Prettier, JavaScript-syntax en modulegrenzen
  (**24 modules**, geen cyclische imports), plus `git diff --check`: geslaagd.
- Niet uitgevoerd: luisteren via de speakers van het uiteindelijke scherm,
  fysieke touchscreens, Firefox en de volledige overige browsermatrix.
  Geautomatiseerd starten/decoderen bewijst afspeelbaarheid; luisteracceptatie
  van herkenbaarheid en volume op het echte apparaat blijft handmatig open.


## Dierenorkest: dierenfeest, geluid standaard aan en herhaalicoon — 2 november 2026

- Automatisch: `tests/e2e/test_games.py -k orchestra --browser chromium --browser
  webkit -q`: **22 geslaagd**. De volledige zesrondenflow controleert het feest
  uitsluitend bij spelvoltooiing, 42 icoontjes met precies kikker/poes/hond/kuiken,
  zichtbare animatie-opacity, leesbare inhoud op 390×664, 750×342 en 768×1024,
  automatisch en handmatig sluiten en de rustige variant bij minder beweging.
  Een bewust vertraagd terminale-sessieantwoord mag de viering niet afbreken.
- Dezelfde set controleert standaard ingeschakeld geluid (ook echt afspelen na
  alleen de aankoopknop), expliciet dempen, foutfeedback en de herhaalknop met
  een zichtbaar SVG-icoon van minimaal 36px en toegankelijke naam.
- Automatisch: `tests/e2e/test_dashboard.py -k
  routine_completion_celebrates_only_the_last_step_with_rotating_variants
  --browser chromium --browser webkit -q`: **2 geslaagd**. De bestaande routine-
  animaties behouden tien wisselende thema's en niet-herhalende boodschappen.
- Visueel: Chromium-screenshots van het dierenfeest op 390×664 en 750×342
  bekeken met lopende animatie, plus de grote herhaalknop op mobiel. Alle vier
  de dieren zijn zichtbaar; tekst en sluitknop passen binnen de spelmodal.
- Backendrun: **129 geslaagd, 4 containercontroles overgeslagen**. Ruff lint en
  opmaak, CSS-opmaak, Prettier, JavaScript-syntax en modulegrenzen (**24 modules**,
  geen cycli), plus `git diff --check`: geslaagd. Een reeds gewijzigde kloktest
  is daarbij uitsluitend met Ruff geformatteerd; bestaande inhoud behouden.
- De gebruiker heeft de nieuwe dierengeluiden in deze chat goedgekeurd.
  Geen nieuwe fysieke touchscreen- of Firefox-controle en geen volledige
  overige browsermatrix uitgevoerd.


## Dierenorkest: ruimere popup en gecentreerde onderbediening — 2 november 2026

- Automatisch: `tests/e2e/test_games.py -k orchestra --browser chromium --browser
  webkit -q`: **24 geslaagd**. De uitgebreide layoutcontrole gebruikt 390×664,
  750×342, 768×1024 en 1280×900. Ze controleert het muziekicoon, de horizontaal
  gecentreerde herhaalknop, minstens 16px ruimte tussen uitleg/bord/onderbediening,
  ruimte onder de knop en een breder venster op grotere schermen. De bestaande
  timing-, foutfeedback-, audio- en dierenvieringstests slagen eveneens.
- Visueel: Chromium-screenshots van de actieve popup op 390×664, 750×342 en
  1280×900 bekeken. De titel heeft muzieknoten, uitleg en knoppen hebben meer
  ruimte, en Opnieuw staat midden onderaan. De lage liggende variant heeft vier
  dieren naast elkaar en behoudt zichtbare ondermarge. Ook de viering is in deze
  formaten via de tijdelijke screenshotrun uitgevoerd (**3 geslaagd**).
- Backendrun: **129 geslaagd, 4 containercontroles overgeslagen**. Ruff lint en
  opmaak, CSS-opmaak, Prettier, JavaScript-syntax en modulegrenzen (**24 modules**,
  geen cycli), plus `git diff --check`: geslaagd.
- Geen fysieke apparaat- of Firefox-controle en geen volledige overige
  browsermatrix uitgevoerd. De layoutaanpassing is op Dierenorkest begrensd.

## Release 0.3.0 — 3 november 2026

- Backend: 129 geslaagd, 4 optionele containercontroles overgeslagen.
- Ruff lint en opmaak, CSS-opmaak, Prettier, JavaScript-syntax en modulegrenzen
  (24 modules, geen cycli), en `git diff --check`: geslaagd.
- De release-image is met een vernieuwde basisimage en zonder automatische
  Git-bronmetadata gebouwd voor Linux amd64 en arm64. Beide varianten zijn lokaal
  gestart en gaven via `/api/health` status 200 en versie `0.3.0`.
- Browsermatrix voor 0.3.0: 240 geslaagd, 4 mislukt en 122 fouten.
  De twee varianten van de test voor een routine zonder tijdvenster mislukten
  in Chromium en WebKit. Firefox kon niet starten (122 tests).

## Compose gebruikt standaard latest — 5 november 2026

- `docker compose config` met een fictief wachtwoord en zonder lokale `.env`
  bevestigt dat beide services standaard `latest` gebruiken en de expliciete
  override naar `0.3.0` respecteren. De volledige Compose-voorbeelden in de
  README en het Docker Hub-overzicht zijn identiek aan `compose.yaml`.
- Beide lokale Docker-tags verwijzen naar dezelfde 0.3.0-image. Docker Hub
  weigerde de push met `insufficient_scope`; de publicatie is niet bevestigd.
- Bij de volgende poging zijn `0.3.0` en `latest` gepubliceerd. Controle op
  Docker Hub bevestigde voor beide tags Linux amd64 en arm64 en dezelfde digest:
  `sha256:d7cac0393ebaea1d9922ebc47885e7bacfd8639ebd3272baa71e432f90a94442`.

## Hoofdnavigatie na een frontendupdate — 5 november 2026

- Backend: 130 geslaagd, 4 optionele containercontroles overgeslagen.
  De regressietest bevestigt dat een wijziging in een geneste navigatiemodule
  het adres van de volledige moduleboom wijzigt.
- Playwright: de regressietest voor wisselen tussen Immich en Spelletjes
  is geslaagd in Chromium en WebKit.
- Ruff lint en opmaak, CSS-opmaak, Prettier, JavaScript-syntax, modulegrenzen
  en `git diff --check` zijn geslaagd.
- De installatie van de gebruiker is niet bijgewerkt of handmatig gecontroleerd.

## Spelletjes-icoon in de hoofdnavigatie — 5 november 2026

- Playwright (UI-01): 8 controles geslaagd in Chromium en WebKit op 390, 760,
  761 en 850 px. Het gamepad-icoon blijft zichtbaar met en zonder tablabels.
- Visueel: Chromium-schermafbeeldingen op 390 en 850 px bekeken.
- Ruff lint en opmaak, Prettier, JavaScript-syntax, modulegrenzen en
  `git diff --check` zijn geslaagd.

## Browseracceptatie voor 0.3.1 — 11 november 2026

- De GitHub-traces bevestigen overlappende navigatie en klok, horizontale
  overflow in kindmodus, een te smal aanraakdoel en een verouderde beloningenlijst
  na een gelijktijdige verversing. De Immich-test las een tweede module-instantie
  en de routinetest kon de weekagenda controleren terwijl de dagagenda nog laadde.
- Lokaal op macOS: 38 gerichte Playwright-controles geslaagd in Chromium en
  WebKit, plus de gecontroleerde verversingsregressie in beide browsers. Firefox
  kon lokaal geen tijdelijk browserprofiel openen. De backend gaf 130 geslaagde
  tests en 4 overgeslagen optionele containercontroles.
