# Samen · lokaal gezinsdashboard

Een rustige, Nederlandstalige plek voor agenda, taken, routines, boodschappen en herinneringen. Zelf te hosten, zonder abonnement, NAS-afhankelijkheid of externe frontenddiensten.

**Versie 0.1.0 — eerste werkende ontwikkelversie.** De lokale gezinsplanner is bruikbaar. Integratieadapters zijn geïmplementeerd en deels met fixtures getest; een volledige P0-acceptatie op echte CalDAV-, Home Assistant- en Immich-installaties staat nog open. Zie [verificatie en beperkingen](docs/VERIFICATION.md) en de [oorspronkelijke requirements](docs/REQUIREMENTS.md).

![Samen gezinsdashboard](docs/screenshot.png)

## Wat werkt

- Vaste hoofdnavigatie: Kalender, Home Assistant, Immich en Boodschappen. Eén gedeelde datumselectie boven het gezinsfilter voor agenda, taken, routines en beloningen. Nederlandse datums, maandag als weekstart, 24-uursklok en instelbare tijdzone.
- Gezinsleden met naam, kleur en emoji-avatar; gezamenlijk overzicht of filter per persoon.
- Dag- en weekagenda toont lokale taakuitvoeringen op hun geplande dagen, met voltooiing direct vanuit de agenda. CalDAV is optioneel voor privéafspraken; de gezinsplanner werkt ook zonder gekoppelde agenda.
- CalDAV-accountbeheer, agenda-ontdekking, selectie en gezinskoppeling. Alleen-lezen privéafspraken met herhalingen, uitzonderingen en tijdzones.
- Taken met beschrijving, datum, icoon, punten per uitvoering, dag/weekherhaling en individuele of gezamenlijke uitvoering.
- Routines met geordende stappen, personen, weekdagen en tijdvenster. Punten worden één keer toegekend als alle stappen af zijn; voortgang blijft server-side bewaard en gemiste stappen blijven open.
- Gedeelde boodschappen met hoeveelheid, notitie, bewerken, afvinken, herstellen en opruimen.
- Automatische verversing elke 1,5 seconde; versienummers voorkomen stil overschrijven. Dubbele verzoeken worden herkend.
- Beveiligd beheer, server-side integratiegeheimen, historie, SQLite-back-up en healthcheck.
- Puntensaldi en herleidbare transacties per gezinslid, beheerbare beloningen, aanvragen met gereserveerde punten en oudergoedkeuring. Een voltooiing ongedaan maken boekt de bijbehorende punten terug.
- Home Assistant-dashboard rechtstreeks ingesloten vanuit het zelfgekozen HA-dashboardpad. Immich-fotolijst uit geselecteerde albums, pauze/vorige/volgende, voorladen, begrensde servercache en schermspecifieke voorkeuren.

Beloningsaanvragen zijn zichtbaar voor het gezin; het gezinsprofiel is een filter en geen authenticatie. Alleen een beheerder kan de beloningscatalogus beheren en aanvragen goedkeuren. Recepten en maaltijdplanning zijn niet opgenomen.

## Installeren met Docker Compose

Benodigd: Docker Engine met Compose v2 op een Linux amd64- of arm64-host. De Dockerfile bouwt vanuit de officiële multi-architectuur Python-image. Architectuurbuilds staan in CI, maar zijn in deze opleveromgeving niet uitgevoerd: Docker Engine draaide hier niet. Er zijn geen Node-, Python- of NAS-ontwikkeltools op de host nodig.

1. Kopieer deze projectmap naar de server (of clone de repository zodra die is gepubliceerd).
2. Kopieer `.env.example` naar `.env`. Vervang `ADMIN_PASSWORD` door een eigen wachtwoord. Pas eventueel `PORT` aan.
3. Start in de projectmap:

   ```sh
   docker compose up -d --build
   docker compose ps
   ```

4. Open `http://<serveradres>:8080` in een browser (of de ingestelde poort). Open de beheerknop rechtsboven, meld je aan en voeg gezinsleden toe. De app start leeg: geen fictief gezin en geen voorbeeldafspraken in je echte database.

De standaardpoort luistert op de netwerkinterfaces van de Docker-host. Beperk inkomend verkeer met de hostfirewall tot je vertrouwde thuisnetwerk en stel geen router-port-forward of andere publieke toegang in. Gebruik deze versie alleen op een vertrouwd thuisnetwerk. Een internetverbinding is alleen nodig voor installatie/updates of wanneer de gekozen integraties extern draaien. Lokale taken, routines en boodschappen werken zonder internet zolang de server bereikbaar is.

## Configuratie

| Instelling | Plaats | Betekenis |
|---|---|---|
| `ADMIN_PASSWORD` | `.env` | Beheerwachtwoord; wijzigen vereist containerherstart |
| `PORT` | `.env` | Gepubliceerde poort; standaard 8080 |
| `TZ` | `.env` | Containertijdzone; standaard Europe/Amsterdam |
| Tijdzone | Beheer | Functionele agenda-/uitvoeringstijdzone, standaard Europe/Amsterdam |
| `COOKIE_SECURE` | `.env` | `true` bij uitsluitend HTTPS; standaard `false` voor lokaal HTTP |
| `CACHE_MB` | `.env` | Bovengrens vervangbare fotocache; standaard 128 MB |
| CalDAV, HA en Immich | Beheer | Gezamenlijke instellingen, persistent in SQLite |
| Inactiviteit, shuffle, uitsnijden | Beheer → Dit apparaat | Alleen deze browser, in localStorage |

De volumes `family-data` en `family-cache` bevatten respectievelijk database/configuratie en vervangbare foto’s. Compose geeft ze een projectprefix. Voor eigen opslagpaden kunnen de volumemounts worden gewijzigd; de container draait als UID/GID 10001 en moet daar kunnen schrijven. Gebruik een lokale schijf voor SQLite, geen databasebestand op SMB/NFS.

### Optionele privéagenda via CalDAV

Een CalDAV-koppeling is niet nodig voor de gezinsplanner: taken en routines worden lokaal beheerd en verschijnen vanzelf op hun geplande datum in het agendaoverzicht. Voeg alleen een CalDAV-account toe als je ook privéafspraken uit een externe agenda wilt zien.

Open **Beheer → Account toevoegen**, vul een CalDAV-serveradres, gebruikersnaam en wachtwoord in en kies **Agenda’s ophalen**. Selecteer agenda’s, wijs een gezinslid toe en sla op. Meerdere accounts zijn mogelijk. Bij hetzelfde serveradres behoudt een leeg wachtwoord het bestaande geheim. Vul bij wijziging van het CalDAV-serveradres opnieuw het wachtwoord in; verwijderen van het account verwijdert ook de gekoppelde lokale agenda’s.

Synchronisatie gebeurt bij het starten en daarna elke twee minuten (plus looptijd), of met **Nu synchroniseren**. De app vervangt de lokale kopie pas nadat alle geselecteerde agenda’s van dat account succesvol zijn opgehaald. Wijzigingen en verwijderingen worden zo zonder extra kopieën verwerkt. Bij fouten blijft de vorige kopie staan en worden fout en laatste succesmoment getoond. Het venster loopt van 90 dagen terug tot ongeveer één jaar vooruit. Agenda’s daarbuiten worden niet geladen.

Afspraken worden niet lokaal aangemaakt of gewijzigd; CalDAV blijft de bron. Raadpleeg de [python-caldav zoekdocumentatie](https://caldav.readthedocs.io/stable/caldav/collection.html) voor het gebruikte protocolpad. De gebruikte bibliotheek verwerkt herhalingen lokaal met `recurring-ical-events`.

### Home Assistant

Het HA-tabblad toont je Home Assistant-dashboard rechtstreeks in Samen. De bovenbalk met navigatie blijft staan; het dashboard gebruikt de rest van het scherm. De app haalt geen HA-entiteiten op en rendert ze niet zelf; je maakt en beheert de inhoud en bediening volledig in Home Assistant.

1. Open **Beheer → Home Assistant-dashboard**.
2. Vul het HA-serveradres in, bijvoorbeeld `http://homeassistant.local:8123` (zonder `/api` of dashboardpad).
3. Stel het dashboardpad in. Standaard is dit `/lovelace/0`; voor een eigen dashboard gebruik je het pad uit Home Assistant, bijvoorbeeld `/dashboard-gezinsdashboard/overzicht`.
4. Sla de instellingen op en open de tab **Home Assistant**.

Je browser moet het ingestelde HA-adres kunnen bereiken en zo nodig al bij Home Assistant zijn aangemeld. Het HA-dashboard wordt schermvullend onder de bovenbalk getoond; de browser- en HA-configuratie moeten insluiten toestaan. Gebruik op niet-vertrouwde netwerken HTTPS voor zowel Samen als Home Assistant.

Krijg je in Firefox de melding dat Home Assistant niet in een andere website mag worden ingesloten? Dan weigert de HA-server dit via `X-Frame-Options`; Samen kan die beveiligingsheader niet omzeilen. In Home Assistant 2026.8 en nieuwer kun je dit aanpassen via **Instellingen → Systeem → Netwerk → HTTP-server**: schakel **Send X-Frame-Options** uit en bevestig de herstart. In oudere versies voeg je aan `configuration.yaml` toe:

```yaml
http:
  use_x_frame_options: false
```

Herstart Home Assistant daarna. Gebruik dit alleen op een vertrouwd netwerk: uitschakelen vermindert bescherming tegen clickjacking. Als Home Assistant achter een reverse proxy staat, controleer dan ook of die niet zelf `X-Frame-Options` of een beperkende CSP `frame-ancestors`-header toevoegt.

### Immich

Vul het basisadres **zonder `/api`** en een beperkte lees-API-sleutel met **`album.read`, `asset.read` en `asset.view`** in. Voer bij wijziging van het Immich-serveradres de API-sleutel opnieuw in. Kies **Albums ophalen**, selecteer expliciet de gewenste albums en sla op. Zonder selectie worden geen foto’s getoond. Oudere Immich-versies leveren foto's bij de albuminformatie; bij nieuwere versies haalt het dashboard alle pagina's op via `/api/search/metadata`, gefilterd op het geselecteerde album. Voor previews gebruikt het dashboard [asset previews](https://api.immich.app/endpoints/assets/viewAsset).

De backend vraagt previewafbeeldingen op (geen originele bestanden), bewaart maximaal de ingestelde cacheomvang en verwijdert cachebestanden zodra foto’s uit de toegestane selectie verdwijnen. De albums worden elke twee minuten vernieuwd. Als albumrechten niet gecontroleerd kunnen worden, stopt de fotolijst en wordt de cache geleegd. Afbeeldingen worden niet blijvend in de browsercache opgeslagen. De bronalbums en foto’s worden nooit gewijzigd. De Immich-fotolijst gebruikt, net als het HA-tabblad, de volledige ruimte onder de bovenbalk; de diavoorstellingsbediening ligt over de foto.

Onder **Beheer → Dit apparaat** kun je een inactiviteitstimer aanzetten. Standaard is deze uit. Open formulieren, niet-opgeslagen boodschappen en het routinescherm verhinderen automatisch wisselen. Aanrakingen in de geïntegreerde HA-weergave tellen mee als activiteit.

## Uitvoeringen, conflicten en historie

Sjablonen en uitvoeringen zijn aparte records. Een achtergrondtaak maakt verlopen uitvoeringen aan tot vandaag (inhaalperiode maximaal twee jaar); niets wordt automatisch voltooid. Een gekozen datum maakt ook de bijbehorende uitvoeringen aan. Elke uitvoering bevat een snapshot van het sjabloon. Bewerken of archiveren wijzigt bestaande uitvoeringsgegevens, planning en historie niet, ook niet wanneer je een toekomstige datum al hebt bekeken. In het takenoverzicht worden wel de actuele titel, het pictogram, de beschrijving en punten van het sjabloon getoond, zodat een bewerkte taak direct herkenbaar is.

Een routinevenster is een aanwijzing, geen blokkering: je kunt een stap later alsnog afvinken. Vensters over middernacht worden in deze versie niet ondersteund. Niet-afgeronde taken blijven op hun eigen datum zichtbaar; er is nog geen apart overzicht voor alle achterstallige taken.

Wijzigingen gebruiken versienummers. Bij een conflict wordt de wijziging afgewezen en de nieuwste staat opgehaald. Formulierinvoer blijft staan; sluit het formulier en open het item opnieuw voordat je de wijziging opnieuw toepast. Gelijktijdig dezelfde taak voltooien levert één statuswijziging en één historie-item op. Identieke opnieuw verstuurde verzoeken met hetzelfde verzoeknummer worden niet opnieuw uitgevoerd.

Bij verbindingsverlies wordt geen succesvolle opslag gemeld. Er is geen offline wachtrij. Een verlopen beheersessie kan opnieuw worden geopend; bestaande integratiegeheimen komen niet naar de browser terug.

## Back-up en herstel

De SQLite-back-up bevat gezinsgegevens, uitvoeringen, puntenledger, beloningsaanvragen, historie en integratiegeheimen. Bewaar hem privé en versleuteld; neem ook `.env` en eventuele aangepaste Compose-configuratie mee. Foto’s in de cache hoeven niet te worden geback-upt.

Consistente online back-up (gebruik een nieuwe bestandsnaam per back-up):

```sh
mkdir -p backups
docker compose exec dashboard python -m app.backup /tmp/family-backup.db
docker compose cp dashboard:/tmp/family-backup.db ./backups/family-backup.db
```

Het script gebruikt de SQLite Backup API en voert `integrity_check` uit. Het weigert een bestaand doelbestand te overschrijven. Bij een volgende back-up kies je een andere naam; `/tmp` wordt ook gewist bij containervervanging.

Herstel naar een lege installatie, vanuit de projectmap:

```sh
docker compose stop dashboard
docker compose run --rm --no-deps --user root \
  -v "$(pwd)/backups:/restore:ro" dashboard \
  python -c "import pathlib,shutil,os; p=pathlib.Path('/data/family.db'); assert not p.exists(), 'Doel is niet leeg'; shutil.copyfile('/restore/family-backup.db',p); os.chown(p,10001,10001); os.chmod(p,0o600)"
docker compose up -d
```

Gebruik voor herstel een leeg datavolume. Behoud de oude installatie tot je de nieuwe hebt gecontroleerd. Controleer daarna gezinsleden, boodschappen, routinevoortgang en integraties. De applicatietest herstelt de back-up naar een lege map en verifieert gegevens én integratieconfiguratie. De Docker-volumeprocedure moet nog op een draaiende Docker-host worden uitgevoerd.

## Updates en ontwikkeling

Maak eerst een back-up. Vervang de broncode door de gewenste versie en voer `docker compose up -d --build` uit. Normale containervervanging behoudt de volumes. **`docker compose down -v` verwijdert gegevens** en hoort niet bij een update.

Databaseschema: versie 2 via `PRAGMA user_version`; bestaande versie-1-databases krijgen bij starten automatisch de tabellen voor punten en beloningsaanvragen. De applicatie weigert een database met een nieuwere schemaversie. Downgraden na migraties gebeurt door herstel van een versiepassende back-up. Dependencyversies zijn vastgelegd in `requirements.txt`; de Python-basisimage is een onderhoudstag, nog niet op digest vastgezet.

Lokaal ontwikkelen (Python 3.12+, in de oplevering getest met Python 3.14). De app leest `ADMIN_PASSWORD` automatisch uit `.env` als die niet al in de procesomgeving staat:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export ADMIN_PASSWORD='kies-een-uniek-lokaal-wachtwoord'
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
.venv/bin/python -m pytest -q
```

De `export`-regel is alleen nodig als je geen `.env` gebruikt of tijdelijk een andere waarde wilt instellen.

De uitgebreide Playwright-acceptatietests, browsermatrix en koppeling aan de oorspronkelijke requirements staan in [docs/TESTING.md](docs/TESTING.md). Deze tests draaien met afzonderlijke tijdelijke gegevens.

Gebruik **één Uvicorn-worker**: de beheersessies, integratiescheduler en foto-toelatingslijst zijn proceslokaal. De frontend is gewone HTML/CSS/JavaScript zonder bundler of npm-build. De GitHub Actions-workflow voert applicatietests, JavaScript-syntaxcontrole en containerbuilds voor beide architecturen uit, plus een healthcheck op amd64.

## Publieke distributie

Code, voorbeeldconfiguratie en tests bevatten uitsluitend generieke of fictieve gegevens. `.env`, database, cache en back-ups staan in `.gitignore` en `.dockerignore`. Er is nog geen GitHub-repository aangemaakt of gepubliceerd. De projectlicentie is **PolyForm Noncommercial 1.0.0**. Activeer vóór publicatie private vulnerability reporting. Zie [SECURITY.md](SECURITY.md).


## Licentie

Samen wordt aangeboden onder de [PolyForm Noncommercial License 1.0.0](LICENSE) (SPDX: `PolyForm-Noncommercial-1.0.0`). De officiële licentietekst is ongewijzigd opgenomen en wordt ook in de container meegeleverd.

- Niet-commercieel gebruiken, aanpassen en delen is toegestaan onder de licentievoorwaarden, bijvoorbeeld voor een persoonlijk gezinsdashboard of hobbyproject.
- Commercieel gebruik wordt door deze licentie niet toegestaan; daarvoor is een afzonderlijke toestemming van de rechthebbende nodig.
- De licentie staat gebruik door de daarin genoemde organisaties, waaronder onderwijsinstellingen, liefdadigheidsorganisaties en overheidsinstellingen, expliciet toe ongeacht hun financieringsbron.
- Bij verspreiding moeten de licentievoorwaarden of hun URL en eventuele `Required Notice:`-vermeldingen behouden blijven.

De broncode is daarmee beschikbaar voor niet-commercieel gebruik; dit is geen onbeperkte open-sourcelicentie. De volledige [officiële voorwaarden](https://polyformproject.org/licenses/noncommercial/1.0.0) zijn leidend. Afhankelijkheden en andere componenten van derden behouden hun eigen licenties; deze projectlicentie wijzigt die niet.
