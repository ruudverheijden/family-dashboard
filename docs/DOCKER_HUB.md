# Samen · lokaal gezinsdashboard

Samen is een zelf te hosten, Nederlandstalig gezinsdashboard voor agenda, taken,
routines, punten, beloningen en gedeelde boodschappen. Optionele koppelingen met
CalDAV, Home Assistant en Immich brengen privéagenda's, je HA-dashboard en een
fotolijst samen op één scherm.

- [Broncode en volledige installatiehandleiding op GitHub](https://github.com/ruudverheijden/family-dashboard)
- [Problemen melden en ideeën indienen](https://github.com/ruudverheijden/family-dashboard/issues)
- [Back-up en herstel](https://github.com/ruudverheijden/family-dashboard#back-up-en-herstel)
- [Verificatie en bekende beperkingen](https://github.com/ruudverheijden/family-dashboard/blob/main/docs/VERIFICATION.md)

## Beschikbare image

`ruudv/family-dashboard:0.2.1` — **Linux amd64 en arm64**, waaronder de
Synology DS918+ (amd64). Er is geen `latest`-tag beschikbaar.

0.2.1 bevat de beveiligingsupdate voor python-dotenv en verwijdert pip uit de runtime.
De volledige scan meldt
nog CVE-2025-60876 in BusyBox wget; de applicatie roept wget niet aan. Zie de
verificatie voor de bekende beperking en het upstream-vervolg.

Dit is een eerste werkende ontwikkelversie, bedoeld voor een vertrouwd thuisnetwerk.

## Starten met Docker Compose of Portainer

Sla de volgende YAML op als `compose.yaml`. In Portainer kun je hem plakken via
**Stacks → Add stack → Web editor**.

```yaml
services:
  storage-init:
    image: ${DASHBOARD_IMAGE:-ruudv/family-dashboard:0.2.1}
    user: "0:0"
    command:
      - python
      - -c
      - |
        import os, stat
        def fail(error):
            raise error
        for directory in ("/data", "/cache"):
            for _, _, files, parent in os.fwalk(directory, follow_symlinks=False, onerror=fail):
                os.fchown(parent, 10001, 10001)
                os.fchmod(parent, 0o700)
                for name in files:
                    if not stat.S_ISREG(os.stat(name, dir_fd=parent, follow_symlinks=False).st_mode):
                        continue
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                    try:
                        info = os.fstat(fd)
                        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                            raise RuntimeError("Opslag bevat een onveilig bestand of hardlink")
                        os.fchown(fd, 10001, 10001)
                        os.fchmod(fd, 0o600)
                    finally:
                        os.close(fd)
    volumes: &storage
      - ${DATA_VOLUME:-family-data}:/data
      - ${CACHE_VOLUME:-family-cache}:/cache
    network_mode: none
    read_only: true
    cap_drop: [ALL]
    cap_add: [CHOWN, FOWNER, DAC_OVERRIDE]
    security_opt:
      - no-new-privileges:true
    healthcheck:
      disable: true
    restart: "no"
  dashboard:
    image: ${DASHBOARD_IMAGE:-ruudv/family-dashboard:0.2.1}
    depends_on:
      storage-init:
        condition: service_completed_successfully
    ports:
      - "${PORT:-8080}:8080"
    environment:
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:?Stel ADMIN_PASSWORD in via .env}
      TZ: ${TZ:-Europe/Amsterdam}
      COOKIE_SECURE: ${COOKIE_SECURE:-false}
      CACHE_MB: ${CACHE_MB:-128}
      DATA_DIR: /data
      CACHE_DIR: /cache
    volumes: *storage
    restart: unless-stopped
    init: true
    read_only: true
    tmpfs:
      - /tmp:size=32m
    cap_drop: [ALL]
    security_opt:
      - no-new-privileges:true
volumes:
  family-data:
  family-cache:
```

Maak bij Docker Compose daarnaast een `.env` met een uniek beheerwachtwoord:

```dotenv
ADMIN_PASSWORD=kies-hier-een-eigen-uniek-wachtwoord
```

In Portainer voeg je `ADMIN_PASSWORD` toe onder **Environment variables**.
Start met **Deploy the stack**, of voer in de installatiemap uit:

```sh
docker compose pull
docker compose up -d
```

Open `http://<serveradres>:8080` en meld je via beheer aan met je gekozen wachtwoord.
Voeg je eigen gezin toe; een nieuwe installatie start leeg.
De integraties zijn optioneel. Stel deze versie niet rechtstreeks bloot aan internet.

## Gegevens en instellingen

- `/data`: SQLite-database, gezinsgegevens, gezamenlijke instellingen en integratiegeheimen.
- `/cache`: vervangbare fotocache.
- `ADMIN_PASSWORD`: beheerwachtwoord; wijziging vereist containervervanging met de nieuwe waarde.
- `PORT`: hostpoort, standaard 8080.
- `TZ`: standaard Europe/Amsterdam.
- `COOKIE_SECURE`: zet op `true` bij uitsluitend HTTPS.
- `CACHE_MB`: maximale fotocache in MB, standaard 128.

De volumes blijven bij containervervanging behouden. Gebruik geen
`docker compose down -v`, want dat verwijdert gegevens.
Bij eigen hostmappen moet UID/GID 10001 kunnen schrijven.
De service `storage-init` stelt bij deployment de eigenaar en rechten van de mappen,
submappen en gewone bestanden in (UID/GID 10001, mappen 0700, bestanden 0600), waarna het dashboard
zelf een ontbrekende database aanmaakt. `Exited (0)` voor `storage-init` is normaal.
De app blijft als gewone gebruiker draaien. Bestaande databasebestanden worden niet
vervangen; bij herstel worden ook hun rechten voorbereid. Stop eerst het dashboard,
zet een consistente back-up terug en deploy daarna de stack zodat de init opnieuw draait.
Symbolische links worden niet gevolgd, speciale bestanden overgeslagen en hardlinks
naar gewone bestanden geweigerd. De bestandsinhoud wordt niet veranderd.
Dezelfde Compose-configuratie ondersteunt eigen hostmappen via `DATA_VOLUME` en
`CACHE_VOLUME`: stel beide in op je bestaande absolute paden. Behoud bij een update
je poort, opslagpaden en stacknaam om dezelfde gegevens te blijven gebruiken.
De korte voorbereidingsservice krijgt beperkte bestandsrechten, zonder netwerk;
zo heeft de webapp zelf nooit rootrechten nodig. `Exited (0)` is een normale eindstatus.
Dit is een bewuste scheiding van rechten, geen verplicht Docker-patroon.
De mapvoorbereiding vereist lokale opslag waarop eigenaarswijzigingen zijn toegestaan.
Gebruik Docker Standalone; deze configuratie is niet voor Swarm.
Gebruik voor SQLite lokale opslag op de Docker-host, geen SMB/NFS-mount.

Je kunt bestaande instellingen overzetten met een consistente databaseback-up en
je eigen omgevingsvariabelen; zie de GitHub-handleiding. Instellingen onder
**Dit apparaat** staan apart in de browser.

## Updates

Maak eerst een back-up. Kies de gewenste gepubliceerde versietag in je Compose-bestand
of Portainer-stack en vervang de container met behoud van dezelfde volumes.
Met Compose: `docker compose pull` gevolgd door `docker compose up -d`.

## Licentie

[PolyForm Noncommercial 1.0.0](https://github.com/ruudverheijden/family-dashboard/blob/main/LICENSE).
Niet-commercieel gebruiken, aanpassen en delen is toegestaan onder de licentievoorwaarden.
De broncode is beschikbaar; de licentie beperkt commercieel gebruik en is geen
OSI-open-sourcelicentie. Componenten van derden behouden hun eigen licenties.

