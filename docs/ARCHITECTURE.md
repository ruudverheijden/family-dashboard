# Architectuur en onderhoud

Dit dashboard blijft één FastAPI-applicatie met SQLite en een frontend zonder buildstap.
De herstructurering van 31 oktober 2026 maakt verantwoordelijkheden expliciet; zij verandert
geen API-adressen, gegevensformaat, databaseversie of functionele planningsregels.

## Backend: waar hoort een wijziging?

| Onderdeel | Verantwoordelijkheid |
|---|---|
| `app/main.py` | Alleen het Uvicorn-entrypoint `app.main:app`. |
| `application.py`, `config.py`, `runtime.py` | Applicatie samenstellen, configuratie bij startup en eigen instanties voor database, sessies en integraties. |
| `routes.py`, `schemas.py` | HTTP-verzoeken, autorisatiegrenzen, verzoekmodellen en antwoorden. |
| `auth.py`, `security.py` | Beheersessies, loginbeperking, cookiebeleid, verzoekgrootte en oorsprongcontrole. |
| `validation.py`, `errors.py` | Bestaande normalisatie/validatieregels en fouten die de HTTP-grens vertaalt. |
| `services/planner.py` | Planning, inhalen van dagen en onveranderlijke uitvoeringssnapshots. |
| `services/entities.py` | Versiebeveiligde mutaties, voltooiing, historie en herkenning van dubbele verzoeken. |
| `services/points.py`, `services/rewards.py` | Puntenboekingen, tegenboekingen, reserveringen en ouderbeslissingen. |
| `services/dashboard.py` | Het bestaande samengestelde dashboardantwoord en historie. |
| `services/settings.py` | Instellingen valideren, geheimen afschermen en verouderde integratiegegevens intrekken. |
| `db.py`, `backup.py` | SQLite-verbindingen, schema-initialisatie/compatibiliteit, gegevens lezen en online back-up. |
| `integrations/caldav.py` | Alleen-lezen CalDAV-adapter en eigen synchronisatiebewaking. |
| `integrations/immich.py` | Immich-adapter, toegestane foto's, downloads en begrensde cache. |
| `integrations/common.py`, `scheduler.py` | Endpointbeleid, veilige foutdiagnose en onafhankelijke periodieke taken. |

Afhankelijkheden lopen van HTTP naar services en opslag/adapters. Services importeren geen
FastAPI en hoeven geen HTTP-server te starten. `DomainError` wordt uitsluitend aan de
applicatiegrens naar een HTTP-status en Nederlandse melding vertaald.

`create_app(AppConfig(...))` maakt geïsoleerde applicaties mogelijk. De configuratie wordt
bij startup gebruikt, en expliciete configuratie leest nooit `.env`. Het productie-entrypoint
laadt de omgeving bij startup; importeren start geen achtergrondwerk en berekent geen
wachtwoordhash. Gebruik nog steeds één Uvicorn-worker: sessies en foto-toelatingslijsten
zijn bewust per applicatie-instantie in het geheugen opgeslagen.

## Frontend

`app/static/app.js` importeert `js/app.js`. De browser laadt native ES-modules; er is geen
npm-installatie of bundler nodig voor productie. Alleen de ontwikkelchecks gebruiken npm voor de vastgepinde Prettier-formatter.

| Module | Verantwoordelijkheid |
|---|---|
| `app.js` | Opstarten, callbacks aansluiten, globale gebruikersinteractie en timers. |
| `state.js` | Expliciete gedeelde schermtoestand: datum, filter, navigatie, ontvangen gegevens en voorkeuren. |
| `shell.js` | Vernieuwen, navigatie, schermopbouw en gedeelde actiecoördinatie. |
| `api.js` | HTTP-verkeer, foutvertaling en mutatie-enveloppen. |
| `calendar.js` | Agenda, taken/routines, datumweergave en klok. |
| `groceries.js`, `rewards.js`, `photos.js`, `home.js` | Weergave en functies voor boodschappen, beloningen, Immich en Home Assistant. |
| `editor.js`, `admin.js`, `dialogs.js` | Bewerkformulieren, instellingen, dialooggedrag en invoerbehoud. |
| `helpers.js`, `icons.js`, `celebrations.js` | Gedeelde presentatiehulpen, pictogrammen en voltooiingsanimaties. |
| `actions.js` | Kleine verzameling callbacks voor coördinatie tussen schermonderdelen. |

`actions` wordt één keer door `app.js` gevuld vóórdat gebruikersinteractie wordt gekoppeld.
Zo kunnen schermonderdelen bijvoorbeeld opnieuw renderen of een editor openen zonder
cirkelafhankelijkheden te introduceren. Voeg hier alleen schermcoördinatie aan toe; gewone
hulpfuncties horen bij hun eigen module en krijgen normale imports.

Foto-object-URL's, downloadannulering en de diavolgorde horen bij `photos.js`. Tijdelijke
formulierinhoud blijft in de editor/dialoog. Zet nieuwe gegevens alleen in `state.js` als
meer dan één onderdeel ze nodig heeft. Imports van veranderlijke exports mogen niet vanuit
een andere module worden overschreven: gebruik een functie van de eigenaar, zoals `stopPhotos()`.

De modulecontrole in `tools/check_frontend.mjs` controleert syntax, ontbrekende imports/exports
en cirkelafhankelijkheden zonder de DOM-code uit te voeren. Browsertests blijven noodzakelijk.
CSS is geformatteerd met behoud van de oorspronkelijke regelvolgorde en de tussentijdse
gebruikerswijzigingen; het samenvoegen van CSS-overschrijvingen is een aparte vervolgstap.

## Gedragsregels die behouden moeten blijven

- Een sjabloon en een uitvoering zijn verschillende records. Bestaande uitvoeringssnapshots
  wijzigen niet bij het bewerken of archiveren van een sjabloon.
- Het bekijken van een datum kan uitvoeringen aanmaken, ook in de toekomst. `GET /api/state`
  is daardoor bewust nog geen zuivere leesoperatie. Verplaats dit niet zonder apart besluit.
- De taakweergave mag actuele sjabloontekst en punten tonen; de daadwerkelijke puntenboeking
  volgt het uitvoeringssnapshot. Dat bestaande onderscheid is geen onderdeel van deze refactor.
- Een voltooiing, puntenboeking/tegenboeking, historie en idempotent antwoord horen in één
  SQLite-transactie. Helpers gebruiken de bestaande verbinding; ze openen geen eigen transactie.
- Gelijktijdig dezelfde eindstatus opslaan geeft geen dubbele punten. Andere wijzigingen
  met een verouderd versienummer worden afgewezen. Een herhaald verzoeknummer wordt alleen
  hergebruikt als de inhoud overeenkomt.
- Punten voor een beloningsaanvraag worden gereserveerd. Alleen een beheerder mag beslissen;
  goedkeuring controleert opnieuw het beschikbare saldo.
- Een gezinsprofiel is een filter, geen authenticatie. Integratiegeheimen gaan niet naar de
  browser en volgen niet automatisch een gewijzigd serveradres.
- Polling blijft elke 1,5 seconde lopen wanneer het scherm zichtbaar is. Conceptinvoer,
  conflictafhandeling, scrollpositie en de bestaande foto-/inactiviteitsregels blijven behouden.
- Ook de tijdens het werk toegevoegde klokpopup, achtergrondsluiting van dialogen en het
  vertraagd verbergen van voltooide agendataken horen bij de huidige browserregressies.

## Integraties en gelijktijdigheid

CalDAV en Immich hebben elk een eigen synchronisatieslot. Die sloten voorkomen twee
onderling overlappende synchronisaties van dezelfde integratie; ze blokkeren elkaar niet.
De planner, CalDAV en Immich hebben afzonderlijke periodieke taken met een interval van
180 seconden na afloop van hun eigen werk. De CalDAV-startbeperking van 180 seconden geldt
ook bij handmatig synchroniseren.

Netwerkverkeer houdt geen SQLite-transactie of fotocacheslot vast. Een synchronisatie neemt
eerst een configuratiesnapshot, haalt gegevens op en controleert vóór publicatie opnieuw de
configuratieversie. Een antwoord voor een inmiddels gewijzigde configuratie wordt weggegooid.
CalDAV publiceert per account atomair en bewaart de vorige agenda bij een fout.

Immich heeft daarnaast een korte lock voor toegestane foto's en de cache. Bij gewijzigde
albumselectie, endpoint of sleutel wordt de generatie verhoogd en de cache ingetrokken.
Een download controleert na ontvangst opnieuw de generatie en toelating. Ingetrokken foto's
worden zo niet alsnog teruggestuurd of opgeslagen. Een onveranderde albumverversing onderbreekt
een geldige download niet. Als albumrechten niet vastgesteld kunnen worden, wordt de
fotolijst leeg gemaakt en de cache opgeruimd.

**Lockvolgorde:** als beide nodig zijn, eerst de fotolock, dan SQLite. Het dashboard sluit
zijn databasetransactie voordat het een fotosnapshot opvraagt. Er mag geen pad ontstaan dat
SQLite vasthoudt terwijl het op de fotolock wacht.

Publieke foutmeldingen blijven begrijpelijk en generiek. Serverlogs bevatten alleen de
operatie en foutklasse, geen ruwe upstream-antwoorden, credentials of exceptionteksten.

## Verificatie en verdere keuzes

Zie `TESTING.md` voor reproduceerbare checks en `VERIFICATION.md` voor daadwerkelijk
uitgevoerde controles. Tests gebruiken uitsluitend tijdelijke gegevens.

Niet inbegrepen in deze ronde: polling optimaliseren, schema/JSON-opslag vervangen,
versiegestuurde migraties verder uitbouwen, CSS consolideren, historische tabellen begrenzen,
of een andere betekenis geven aan snapshots en getoonde punten. Beoordeel die wijzigingen
apart, met hun eigen gegevens- en gebruikersimpact.
