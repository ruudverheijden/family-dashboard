# Privacycontrole vóór Docker Hub-publicatie — 31 oktober 2026

De gecontroleerde lokale build bevat na herstel geen aangetroffen eigen persoonsgegevens
of integratiegeheimen. Dit geldt voor de hieronder beschreven build, niet automatisch voor
oude images of toekomstige releases. Er is niets naar Docker Hub gepubliceerd.

## Bevindingen en herstel

1. De oorspronkelijke `.dockerignore` sloot geneste `__pycache__`-mappen niet uit.
   Het werkelijk gebouwde image bevatte 26 lokale bytecodebestanden met de gebruikersnaam
   en het absolute ontwikkelpad, waaronder achtergebleven modules. Recursieve uitsluitingen
   voor caches en losse `.pyc`/`.pyo`-bestanden herstellen dit. Verwijderen in een latere
   imagelaag zou onvoldoende zijn; de nieuwe build kopieert deze bestanden helemaal niet.
2. Docker Buildx voegde automatisch de Git-bron-URL met accountnaam aan provenance toe.
   Een build met `BUILDX_GIT_INFO=false` behoudt provenance maar liet deze Git-informatie
   in de gecontroleerde export weg. Gebruik deze instelling ook bij de releasebuild.
3. De Git-geschiedenis bevat een persoonlijke auteursnaam en e-mailadres. Die zijn geen
   onderdeel van de gecontroleerde image. Openbare Git-publicatie maakt ze wel zichtbaar;
   alleen je huidige Git-configuratie wijzigen verwijdert bestaande auteursgegevens niet.
4. Lokaal zijn `.env`, een database en back-ups aanwezig. Deze zijn geen bronbestanden
   en worden door Git en de huidige Docker-build uitgesloten. Houd ze lokaal. Cache- en
   testresultaatmappen zijn eveneens uitgesloten. Eigen gegevens en bestaande wijzigingen
   zijn niet verwijderd of herschreven.

## Uitgevoerde controle

- Alle 82 bij aanvang gevolgde bestanden en 384 unieke bestandsblobs in de bereikbare
  Git-geschiedenis gescand op herkenbare sleutels/tokens, privésleutels, credentials in
  URL's, e-mailadressen, persoonlijke paden en private IPv4-adressen. Kandidaten voor
  wachtwoordliterals bleken fictieve test- of documentatiewaarden; de lange lockfilewaarde
  is een pakketintegriteitshash.
- Het lokale beheerwachtwoord en tien referentiewaarden uit de bestaande database
  (integratiegegevens/adressen en gezinsnamen) alleen-lezen vergeleken met bron en
  bereikbare historische bestandsblobs. Geen overeenkomsten gevonden; waarden zijn
  niet in het rapport of de terminaluitvoer opgenomen.
- Git-auteursmetadata, commitberichten, externe repositoryconfiguratie, Dockerfile,
  Compose, CI, voorbeeldconfiguratie, standaardinstellingen en geheimenafscherming bekeken.
  De remote-URL bevatte geen credentials. Commitberichten hadden alleen Copilot-e-mailcredits.
- Beide gevolgde screenshots visueel bekeken: lege installatie, geen gezinsgegevens of
  zichtbaar token. ExifTool vond geen GPS-, auteurs- of apparaatmetadata in de bestanden.
- Het herbouwde lokale arm64-image geëxporteerd en alle negen lagen gecontroleerd:
  11.568 entries, 46 projectbestanden en negen JSON-metadataobjecten. Geen eigen geheimen,
  persoonlijke gebruikers-/werkpaden, lokale database, cachefoto's, back-ups, `.env`,
  `.git` of lokale Python-bytecode aangetroffen. Korte gezinsnamen die toevallig ook in
  copyrightteksten van derden voorkomen zijn afzonderlijk beoordeeld; dit zijn geen
  meegeleverde gezinsgegevens.
- De echte Docker-contextregressie is geslaagd met fictieve tijdelijke bestanden,
  inclusief geneste caches en losse bytecode. De backendrun slaagde met 104 tests;
  de Docker-test is in die standaardrun bewust overgeslagen en afzonderlijk uitgevoerd.

## Release en grenzen

```sh
BUILDX_GIT_INFO=false docker build -t family-dashboard:release .
```

Tag en publiceer uitsluitend het nieuw gebouwde image. De Docker Hub-accountnaam en
repositorynaam zijn zichtbaar op Docker Hub. Oude images kunnen nog lokale bytecode
bevatten, ook als de bron inmiddels is hersteld.

Geen controle van een gepushte release, amd64-build, remote Git-geschiedenis die lokaal
niet beschikbaar is, onbereikbare/verwijderde Git-objecten, GitHub-instellingen, kwetsbare
dependencies, Docker-volumeherstel of productie-/browserruntime uitgevoerd in deze ronde.
Dit is een gerichte privacy- en distributiecontrole, geen onafhankelijke beveiligingsaudit
of garantie dat alle mogelijke geheimformaten herkend worden.


## Aanvullende controle van de Compose-wijzigingen — 31 oktober 2026

De gedeelde Compose-configuratie bevat geen eigen opslagpad, hostadres of geheim.
Afwijkende opslagpaden en het beheerwachtwoord worden via lokale omgevingsvariabelen
of Portainer ingesteld. De openbare Docker Hub- en GitHub-repositorynamen blijven
bewust in de distributiehandleiding staan.

87 gevolgde en niet-genegeerde bronbestanden zijn opnieuw alleen-lezen gecontroleerd
op overeenkomsten met lokale configuratie-/databasereferenties, persoonlijke paden
zoals een ontwikkelhomemap, en herkenbare sleutelpatronen. Overeenkomsten met algemene
programmeertaal en al bestaande fictieve boodschappenvoorbeelden zijn apart beoordeeld.
Geen onverklaarde privacykandidaten aangetroffen. Er zijn geen lokale referentiewaarden
in dit verslag opgenomen. Dit is een gerichte controle, geen garantie voor alle mogelijke
geheimformaten of bestaande Git-auteursmetadata.

`.env.*` is nu ook uitgesloten van Git en de Docker-context; `.env.example` blijft
beschikbaar als generiek voorbeeld. De Docker-filtering is met fictieve bestanden
getest. Er is voor deze wijziging geen commit of push gemaakt; bestaande Git-geschiedenis
en auteursinstellingen zijn niet herschreven. Zie VERIFICATION.md voor uitgevoerde checks.
