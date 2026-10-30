# Verificatie 0.1.0

Gecontroleerd op 30 oktober 2026. Dit document onderscheidt implementatie van daadwerkelijke acceptatie. De aangeleverde requirements blijven het doel; 0.1.0 is nog geen volledig afgetekende P0-release.

## QE-update: Playwright, 30 oktober 2026

- **28 scenario’s × Chromium en WebKit = 56 geslaagde browsertests**, Playwright 1.64.1 op macOS arm64; volledige run 80,50 seconden inclusief de Firefox-opstartpogingen.
- **26 backendtests geslaagd** (0,53 seconden). JavaScript-syntaxcontrole en compilatie van de testbestanden geslaagd.
- Firefox kon niet starten: `Could not find profile folder`. Alle 28 Firefox-gevallen eindigden tijdens browserinitialisatie; dit is geen geslaagde Firefox-acceptatie. Ook met volledig opgeloste macOS-paden trad de fout op.
- Hersteld: mobiele subnavigatie maakte de knop Taken circa 38,7 pixels breed. Minimum nu 48 pixels; regressietest slaagt op 320 pixels en in liggende mobiele weergave, in Chromium en WebKit.
- Dekking omvat echte HTTP-opslag, twee afzonderlijke browsersessies, gelijktijdige taakvoltooiing, versieconflicten, verloren opslagantwoord, fout-/offlinepaden, wintertijdweergave, routinehistorie, toetsenbord, tekstescaping, diavoorstelling en inactiviteitsguards.
- Testgegevens en caches zijn tijdelijk en gescheiden van de echte installatie. Externe integratie-antwoorden zijn fixtures; echte integraties zijn hiermee niet afgetekend.
- Zie [testplan, requirementdekking en uitvoerinstructies](TESTING.md). JUnit-uitvoer staat lokaal in `test-results/results.xml`; screenshots/traces worden bij fouten bewaard. De nieuwe GitHub Actions-browsermatrix is geconfigureerd, niet op GitHub uitgevoerd.

De onderstaande oorspronkelijke controles zijn historische oplevernotities; bovenstaande resultaten vervangen de oudere testaantallen en de beperkte browsercontrole. Fysieke apparaten, echte integraties, Docker-runtime en de duurtest blijven open.

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
- Echte CalDAV-, Immich- en HA-servers waren niet beschikbaar. Bibliotheek- en mocktests vervangen geen interoperabiliteitstest.
- Home Assistant-iframe: echte login, cookies, frameheaders, mixed content, mobiele bediening en rechtenbeperking moeten met de eigen installatie worden gecontroleerd. Een directe HA-client als fallback is nog niet gebouwd.
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

- CalDAV alleen-lezen; synchronisatievenster 90 dagen terug tot circa één jaar vooruit.
- Afzonderlijke uitvoeringen worden bij bekijken alvast vastgelegd, ook voor toekomstige datums. Sjabloonwijzigingen herschrijven deze niet. Inhalen van verlopen uitvoeringen is begrensd op twee jaar.
- Historie bevat mutaties, geen individuele actoridentiteit: dagelijks profielgebruik is geen authenticatie. Punten zijn metadata; P1-beloningen zijn niet gebouwd.
- Geen aparte achterstallige-takenlijst, geen routinevensters over middernacht en geen offline schrijfbuffer.
- Integratie- en beheersessiestaat deels proceslokaal: één applicatieproces/worker vereist.
- Integratiegeheimen staan onversleuteld in het beschermde servervolume; toegang tot host en back-ups is vertrouwelijk.
- De gedeelde dagelijkse API vertrouwt het thuisnetwerk. Externe toegang, fijnmazige rechten en publicatie zijn niet ingericht.
- Profielavatars zijn emoji’s; geen avatarupload. CalDAV/Immich-configuratie komt in de database; schermvoorkeuren blijven in de browser.
- Licentie: PolyForm Noncommercial 1.0.0, gekozen voor niet-commercieel gebruik. Nog geen publieke GitHub-repository.

## Eerste echte acceptatieronde

1. Start Compose en controleer `/api/health`, herstart en vervang daarna de container met behoud van volumes.
2. Configureer één echt account per integratie; test wijzigingen, uitzonderingen, verwijderingen en uitval.
3. Open op telefoon en gedeeld scherm; test gelijktijdige edits en afvinken.
4. Test HA-login en beperkte rechten op het daadwerkelijke scherm; bepaal daarna of een alternatieve client nodig is.
5. Test Immich-albumintrekking, een kapotte foto, EXIF-rotatie, shuffle en inactiviteit tijdens invoer.
6. Herstel een back-up naar een leeg Docker-volume. Draai vervolgens de 72-uurs duurtest en leg geheugen-/latencymetingen vast.


## Update: Home Assistant-tokenauthenticatie

De eerdere iframe-implementatie is vervangen door een eigen HA-entiteitenweergave met een server-side Long-Lived Access Token. De eerdere opmerkingen over iframe-login, cookies, frameheaders en de ontbrekende directe client zijn daarmee vervallen. Het originele Lovelace-dashboard wordt niet weergegeven.

19 applicatietests slagen, inclusief vier nieuwe HA-tests: geheimen afschermen/behouden/verwijderen, Bearer-authenticatie en entiteit-/actiecontrole, geschoonde foutmelding bij een geweigerd token, en opnieuw invoeren van het token bij een gewijzigd serveradres. Deze tests gebruiken een nagebootste HA-server. Een echte HA-server/token was niet beschikbaar voor een integratietest.
