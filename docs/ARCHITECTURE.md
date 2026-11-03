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
| `services/planner.py` | Planning, inhalen van dagen, actuele toekomstige routineplannen en beschermde uitvoeringssnapshots. |
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
| `shell.js` | Vernieuwen, navigatie, schermopbouw, routinepaneel en gedeelde actiecoördinatie. |
| `api.js` | HTTP-verkeer, foutvertaling en mutatie-enveloppen. |
| `calendar.js` | Agenda, taken/routines, gedeelde routinekaart-/stappenmarkup, datumweergave en klok. |
| `groceries.js`, `rewards.js`, `photos.js`, `home.js` | Weergave en functies voor boodschappen, beloningen, Immich en Home Assistant. |
| `editor.js`, `admin.js`, `dialogs.js` | Bewerkformulieren, instellingen, dialooggedrag en invoerbehoud. |
| `helpers.js`, `icons.js`, `celebrations.js` | Gedeelde presentatiehulpen, pictogrammen en voltooiingsanimaties. |
| `actions.js` | Kleine verzameling callbacks voor coördinatie tussen schermonderdelen. |

`actions` wordt één keer door `app.js` gevuld vóórdat gebruikersinteractie wordt gekoppeld.
Zo kunnen schermonderdelen bijvoorbeeld opnieuw renderen of een editor openen zonder
cirkelafhankelijkheden te introduceren. Voeg hier alleen schermcoördinatie aan toe; gewone
hulpfuncties horen bij hun eigen module en krijgen normale imports.

Het routinepaneel bewaart zijn geselecteerde uitvoering (sjabloon, dag en uitvoerings-ID) privé in
`shell.js`. Het gebruikt dezelfde `data-run`-actie en ontvangen uitvoeringen als de
routinetab. Polling vernieuwt de paneelinhoud alleen als de markup verandert en
herstelt de focus op dezelfde stap. Kaarten groeperen alleen gelijke routine-inhoud;
als één persoon een oude uitvoering met voortgang heeft en een ander een nieuw
toekomstplan volgt, opent elke kaart zijn eigen snapshot en stappen. Het paneel geldt als actieve invoer voor de
inactiviteitsbewaking. Voltooiingsanimaties worden in de actieve dialoog geplaatst
om boven de modale achtergrond bedienbaar te blijven.

Foto-object-URL's, downloadannulering en de diavolgorde horen bij `photos.js`. Tijdelijke
formulierinhoud blijft in de editor/dialoog. Zet nieuwe gegevens alleen in `state.js` als
meer dan één onderdeel ze nodig heeft. Imports van veranderlijke exports mogen niet vanuit
een andere module worden overschreven: gebruik een functie van de eigenaar, zoals `stopPhotos()`.

De modulecontrole in `tools/check_frontend.mjs` controleert syntax, ontbrekende imports/exports
en cirkelafhankelijkheden zonder de DOM-code uit te voeren. Browsertests blijven noodzakelijk.
CSS is geformatteerd met behoud van de oorspronkelijke regelvolgorde en de tussentijdse
gebruikerswijzigingen; het samenvoegen van CSS-overschrijvingen is een aparte vervolgstap.

## Gedragsregels die behouden moeten blijven

- Een sjabloon en een uitvoering zijn verschillende records. Taaksnapshots blijven
  behouden. Routines van vandaag en eerdere dagen, en routine-uitvoeringen met
  voortgang, afvinkhistorie of puntenboekingen, behouden eveneens hun snapshot.
  Toekomstige routines zonder die gegevens volgen de actuele planning, ook als ze
  al door een kalenderbezoek zijn aangemaakt. `refresh_future_routines` gebruikt de
  bestaande transactie en verhoogt bij gewijzigde inhoud het uitvoeringsversienummer.
  Een oudere browser kan daardoor geen oude stapindex op een nieuwe routine toepassen.
  Heropenen maakt een uitvoering niet opnieuw wijzigbaar: de historie blijft tellen.
  Niet meer geplande toekomstige, onaangeraakte uitvoeringen worden bij selectie
  verborgen; opslagrecords, historie en puntenboekingen worden niet verwijderd.
  Verversen gebeurt bij routinewijzigingen, planning inhalen en vóór routinevoortgang
  wordt opgeslagen. Ook een mutatie van een vervallen plan wordt geweigerd.
- Bij een gewijzigde taakverdeling verbergt de dashboardselectie oude open uitvoeringen
  wanneer dezelfde taak en dag uitvoeringen met de actuele verdeling hebben. Ook eerder
  heropende uitvoeringen vallen hieronder; opgeslagen snapshots, historie en puntenboekingen
  blijven intact. Afgeronde uitvoeringen en dagen zonder vervanging blijven zichtbaar.
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
- Terugkeer naar de agenda vraagt direct het bijbehorende dag-/drie dagen-/weekbereik
  op. `shell.js` vergelijkt de query na ontvangst opnieuw met de actuele selectie;
  verouderde antwoorden worden niet gepubliceerd. Een tijdens een lopend verzoek
  gevraagde geforceerde verversing wordt direct na afloop uitgevoerd.
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

## Containeropslag bij eerste start

`compose.yaml` wordt gedeeld door Compose en Portainer. Standaard gebruikt het
benoemde volumes; `DATA_VOLUME` en `CACHE_VOLUME` kunnen absolute hostpaden bevatten.
Beide services gebruiken dezelfde opslag en `DASHBOARD_IMAGE`. Eerst draait `storage-init`.
Deze service gebruikt dezelfde image en draait kort als root met CHOWN/FOWNER en
DAC_OVERRIDE, zonder netwerk. Ze stelt recursief de eigenaar van `/data`, `/cache`,
submappen en gewone bestanden in op 10001:10001, met mappen 0700 en bestanden 0600.
Ze wijzigt geen inhoud en opent databases niet via SQLite. Symbolische links worden
niet gevolgd en speciale bestanden overgeslagen; hardlinks naar gewone bestanden
worden geweigerd. Bestandsdescriptoren met `O_NOFOLLOW` voorkomen dat bij openen
alsnog een symlink gevolgd wordt. Onleesbare mappen veroorzaken een fout in plaats
van stilzwijgend overgeslagen te worden. DAC_OVERRIDE maakt verwerking van private
teruggezette bestanden mogelijk, ook als ze nog van een andere gebruiker zijn.
Het dashboard wacht via `service_completed_successfully` en blijft draaien als
UID/GID 10001 met alle capabilities verwijderd. `db.init()` blijft verantwoordelijk
voor een ontbrekende database en de schema-initialisatie. Een opslagfout stopt de
voorbereiding; de app wijkt nooit stilzwijgend uit naar niet-persistente opslag.


## Spelletjes

`app/games/` bevat per spel de geïsoleerde regels met `create(photos)`,
`play(board, value)` en `view(board)`. De registry in `__init__.py` koppelt een
stabiele spel-ID aan regels en catalogusteksten. `view` schermt verborgen
Memory-kaarten af. Een spelregel kent geen HTTP, database of puntenledger.

`services/games.py` beheert prijsversies, aankopen, sessies en geldige zetten.
Schema 3 voegt `game_settings` en `game_sessions` toe; bestaande gegevens blijven
behouden. Aankoop, afschrijving, historie en verzoekdeduplicatie gebruiken één
`BEGIN IMMEDIATE`-transactie. Acties gebruiken versies en verzoeknummers binnen
dezelfde transactie. Iedere aankoopretry leest de actuele sessie terug en start
geen nieuw bord of nieuwe timer. Geldigheid wordt ook op de server gecontroleerd;
verlopen records blijven bewaard maar tellen niet als actieve sessie.

Een foto-snapshot wordt vóór de databasetransactie opgehaald. Geen nieuwe
upstream-aanvragen, cache of fotolock binnen de puntentransactie. De bestaande
foto-API blijft de actuele albumrechten controleren. De browser controleert de
zes foto's vóór aankoop; een latere upstreamstoring geeft geen automatische
restitutie. Een profiel blijft een filter, zoals bij bestaande beloningen;
het is geen nieuwe authenticatiegrens.

`static/js/games/index.js` bezit aankoopretry's, de spelerkeuze, de modal en
sessiecoördinatie. Private speltoestand komt niet in `state.js`. Renderers onder
`static/js/games/` implementeren `mount(root, board, move, sound)` en leveren een
cleanupfunctie voor timers en eventlisteners. Alleen gewijzigde sessieversies
bouwen het spel opnieuw op; dashboardpolling onderbreekt een spel niet. De
server bewaart de voortgang; de browser voegt alleen presentatie, tonen en
animaties toe. De modal sluit via expliciet stoppen of het eindscherm; Escape
volgt dezelfde stopactie. De bestaande inactiviteitswissel raadpleegt
`isGameOpen()`.

Een nieuw spel voegt een engine en renderer toe en registreert dezelfde ID in
beide registries. Voeg daarbij regeltests, API-/sessietests en browseracceptatie
toe. Prijzen en de algemene levenscyclus hoeven daarvoor niet te worden aangepast.


De Dierenorkest-aftelling gebruikt een transparante blurlaag over de volledige
spelmodal. De kop blijft erboven bedienbaar. Tijdens het aftellen wordt de modal
naar boven gezet en scrollen tijdelijk geblokkeerd, zodat cijfers op liggende
schermen zichtbaar blijven. De renderer ruimt die tijdelijke klasse samen met
zijn timers op. Elke nieuwe ronde en nieuwe poging krijgt de voorbereiding;
handmatig herhalen binnen een ronde start zonder nieuwe aftelling.


Dierenorkest bewaart het resultaat van de laatste geldige zet als `feedback`
in zijn serverbord: `mistake` bij een verkeerde keuze, leeg bij een juiste.
De browser toont daarop 2 seconden foutfeedback vóór de nieuwe voorbereiding.
Polling bouwt een ongewijzigde sessie niet opnieuw op en herhaalt daardoor
het foutgeluid niet. Een volgende zet wist het vorige resultaat.

`games/orchestra-audio.js` bevat een private pool van lokale audio-elementen,
met één tegelijk klinkend fragment. Opnames worden vooraf geladen en lopen
bij gewone renderupdates door, zodat een snelle API-respons de dierenroep niet
afbreekt. De optionele rendererhook `stopAudio()` wordt door de sessiecoördinator
aangeroepen bij dempen, sessie-einde en sluiten. Audiofouten geven een melding;
visueel spelen blijft mogelijk. Zie `ORCHESTRA_AUDIO.md` voor bronopnames,
licenties en de bewerkingen van de lokale WAV-bestanden.


Een renderer kan ook `celebrateCompletion(memberName, container)` aanbieden.
De sessiecoördinator roept deze alleen aan bij de overgang van actief naar
voltooid en bewaart de teruggegeven opruimfunctie. Dierenorkest gebruikt de
bestaande routineviering met een eigen dierenvariant; de routinevariantrotatie
blijft onafhankelijk. `celebrateRoutineCompletion` accepteert optioneel een
variant en een sluitcallback en geeft een idempotente opruimfunctie terug.
Ongewijzigde terminale sessieantwoorden bouwen de modal niet opnieuw op, zodat
een laat pollingantwoord de viering niet afbreekt of opnieuw start. De viering
respecteert minder beweging en wordt opgeruimd bij sluiten of een nieuw spel.
Geluid begint aan; de keuze voor dempen blijft binnen de geladen pagina behouden.


De spelmodal krijgt `data-game` voor gescheiden layoutregels per spel. Een
renderer kan optioneel `titleIcon` aanbieden; de sessiecoördinator ontsnapt die
waarde en plaatst het decoratieve icoon bij de titel. Dierenorkest groepeert de
uitleg en onderbediening afzonderlijk. De ruimere popup en de compacte variant
met vier dieren naast elkaar op lage schermen zijn uitsluitend op dit spel
van toepassing; andere spelmodules behouden hun eigen layout.
