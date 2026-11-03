# Requirements — lokaal gezinsdashboard
Versie 0.4 — 31 oktober 2026

## 1. Doel en uitgangspunten

Doel: een zelfstandig te hosten gezinsdashboard dat planning, taken, routines, boodschappen, Home Assistant en een Immich-fotolijst combineert.

| Uitgangspunt | Status |
|---|---|
| De toepassing draait via Docker, zonder afhankelijkheden van een specifiek NAS-merk. | Deels: Compose-configuratie aanwezig; runtimeacceptatie open |
| De interface werkt op kleine en grote touchscreens, tablets en mobiele telefoons, in liggende en staande oriëntatie. | Deels: browser-viewports getest; fysieke apparaten niet getest |
| De broncode en installatie-instructies worden publiek op GitHub gepubliceerd. | Deels: code en instructies aanwezig; repository nog niet gepubliceerd |
| Lokale basisfunctionaliteit vereist geen abonnement of externe clouddienst. | Gereed |
| Lokale taken, routines en boodschappen werken zonder agenda-integratie. CalDAV is optioneel en voegt privéafspraken toe. | Gereed |
| Home Assistant en Immich zijn bestaande, afzonderlijke services. | Gereed |
| Recepten, maaltijdplanning, voedingswaarden en voorraadbeheer vallen buiten scope. | Buiten scope |

Dit document beschrijft de gewenste eigen toepassing. HiveFamily dient als functionele inspiratie; het document pretendeert geen volledige reconstructie van de ingelogde Hive-app.

## 2. Prioriteiten

- **P0:** eerste bruikbare versie.
- **P1:** latere uitbreiding.
- **Open keuze:** vóór implementatie beslissen.

Status betekent:
- **Gereed**: implementatie is aanwezig en door de vastgelegde tests of bestandscontrole gedekt.
- **Deels**: implementatie is aanwezig, maar een deel van de eis of acceptatie moet nog worden gecontroleerd.
- **Open (P1)**: bewust uitgesteld; geen blokkade voor de eerste bruikbare versie.
- **Open**: implementatie, besluit of acceptatie staat nog open.
- **Buiten scope**: bewust geen functionaliteit of opleveractie voor deze versie.

**Statussamenvatting op 31 oktober 2026:** van de 96 requirement-ID’s zijn er 71 gereed, 19 deels gereed (verdere acceptatie open) en 6 bewust uitgesteld als P1. De eigenaar heeft de agenda-integratie, Immich en Home Assistant handmatig gevalideerd. Er is geen P0-ID waarvan de kernfunctionaliteit nog gebouwd moet worden; resterende P0-TODO’s zijn aanvullende randgevallen en technische acceptatie.

## 3. Navigatie en responsive interface

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| UI-01 | P0 | Vijf hoofdtabs in de ouderweergave: Kalender, Spelletjes, Home Assistant, Immich en Boodschappen. | Gereed |
| UI-02 | P0 | Vanuit ieder onderdeel met één tik naar de andere hoofdtabs kunnen wisselen, zonder browsernavigatie of opnieuw aanmelden. | Gereed |
| UI-03 | P0 | Kalender is het standaardtabblad en bevat de gezinsplanner, met subnavigatie naar Agenda, Taken, Routines en Beloningen. Eén gedeelde datumselectie boven het gezinsfilter geldt voor deze datumgebonden onderdelen; boodschappen is een afzonderlijk hoofdtabblad. De agenda toont lokale taakuitvoeringen op hun geplande datum, ook zonder CalDAV. | Gereed |
| UI-04 | P0 | Beheerinstellingen zijn bereikbaar via een afzonderlijke beveiligde beheerknop. | Gereed |
| UI-05 | P0 | De indeling past zich aan beschikbare schermruimte aan; op mobiel mag een weekoverzicht veranderen in een leesbare dag- of lijstweergave. De interactieve klok en hoofdnavigatie mogen elkaar niet overlappen; op tabletbreedtes kan de navigatie een eigen rij gebruiken. | Gereed |
| UI-06 | P0 | Geen vaste afhankelijkheid van schermresolutie, apparaatmodel of oriëntatie. Minimaal ondersteund mobiel apparaat: iPhone 13, in staande en liggende oriëntatie, zonder verlies van kernfunctionaliteit. Verifieer beschikbare browser-viewports van 390×664 en 750×342 CSS-pixels. | Deels: fysieke apparaten niet getest |
| UI-07 | P0 | Aanraakvlakken minimaal 48 × 48 CSS-pixels; bediening vereist geen hover. Ondersteun ook toetsenbordbediening en zichtbare focus. | Gereed |
| UI-08 | P0 | Nederlandse interface, 24-uursklok, maandag als eerste weekdag en configureerbare tijdzone, standaard Europe/Amsterdam. | Deels: echte apparaat-/tijdzoneacceptatie open |
| UI-09 | P0 | Bij wisselen van tabblad relevante toestand behouden, zoals de geselecteerde kalenderdatum. | Gereed |
| UI-10 | P0 | Niet-opgeslagen invoer beschermen tegen onbedoeld verlies. | Gereed |
| UI-11 | P0 | Gezinsleden herkenbaar maken met naam en kleur; kleur mag niet het enige onderscheid zijn. | Gereed |
| UI-12 | P0 | Een optionele kindmodus is via een ronde avatar-knop per kinderprofiel links van de hoofdtabs bereikbaar. De knop opent direct een eigen kinddashboardtab en toont de taken, routines en beloningen van vandaag en een ingang naar Spelletjes, met grote bediening, zichtbare voltooiing en de volledige datum. Het voltooien van een routine-stap toont dezelfde confetti als het voltooien van een kalender-taak; het afronden van de volledige routine behoudt de routineviering en speelt een extra supersonisch geluid af. De gewone hoofdnavigatie blijft beschikbaar; de Kalender-tab herstelt de eerdere ouderplannerweergave. Verberg beheerinstellingen zolang de kindmodus actief is. Toon bij routines één routine tegelijk: standaard de op dat moment lopende, nog niet afgeronde getimede routine, anders de eerstvolgende nog niet afgeronde getimede routine. Als die ontbreekt, toon een nog niet afgeronde routine zonder tijd; na getimede routines zijn alle overige routines van vandaag bereikbaar met navigatie vooruit en terug. Getimede routines tonen hun starttijd met een analoge en digitale klok. Toon ook de analoge huidige tijd in de bovenbalk. Een open kinddashboard schakelt bij de dagovergang of terugkeer naar het tabblad automatisch naar vandaag in de ingestelde tijdzone; nieuwe dagelijkse uitvoeringen beginnen onafgevinkt en eerdere voortgang blijft bewaard. Gezinsleden hebben de rol kind of ouder; alleen kinderen kunnen de kindmodus openen. Dit is een vereenvoudigde bediening, geen beveiligingsgrens of authenticatie. | Gereed |

## 4. Gezinsprofielen en toegang

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| GEZ-01 | P0 | Gezinsleden beheren met naam, kleur en optionele profielfoto. Profielfoto’s vullen hun ronde avatar met behoud van verhouding en worden aan de cirkelrand afgeknipt. | Gereed |
| GEZ-02 | P0 | Gezamenlijke overzichten en filtering per gezinslid. | Gereed |
| GEZ-03 | P0 | Onderscheid tussen beheerrechten en dagelijkse bediening op een gedeeld scherm. | Gereed |
| GEZ-04 | P0 | Profielkeuze zonder herhaald inloggen op het gedeelde scherm; profielkeuze geldt niet als authenticatie. | Gereed |
| GEZ-05 | P0 | Beheerinstellingen en integratiegeheimen afschermen met authenticatie. | Gereed |

## 5. Lokale agenda en optionele CalDAV

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| AG-01 | P0 | Dag-, 3-daags en weekoverzicht met gezinsleden, kleuren en filters. Toon lokale taken altijd bovenaan op de juiste datum, visueel gescheiden van afspraken. Toon een scrollbaar 24-uursrooster met afspraken op hun tijd en hoogte naar duur; open rond de huidige tijd met 2 uur terug en 4 uur vooruit, en markeer de huidige tijd op de tijdlijn. Hele-dagafspraken blijven apart zichtbaar. Toon lokale routine-uitvoeringen op hun ingeplande dagen: met tijdvenster tussen de afspraken (eigen herkenbare kaart, overlapindeling gedeeld), zonder tijdvenster boven het rooster. Bij terugkeer naar de agenda wordt direct het volledige zichtbare datumbereik geladen; een verouderd dagantwoord mag dat bereik niet overschrijven. Kaarten tonen personen en voortgang; openen toont stappen in een paneel zonder de agenda te verlaten. Afgeronde routines blijven zichtbaar als Klaar. | Gereed |
| AG-02 | P0 | Optioneel één of meer CalDAV-accounts configureren via serveradres en inloggegevens voor privéafspraken. | Gereed (handmatig door gebruiker gevalideerd) |
| AG-03 | P0 | Beschikbare agenda’s ophalen, selecteren en aan gezinsleden koppelen. | Gereed (handmatig door gebruiker gevalideerd) |
| AG-04 | P0 | Afspraken, herhalingen, uitzonderingen, hele-dagafspraken en tijdzones correct verwerken. | Deels: integratie handmatig bevestigd; randgevallen via fixtures getest, niet allemaal live geaccepteerd |
| AG-05 | P0 | Nieuwe, gewijzigde en verwijderde afspraken synchroniseren zonder duplicaten. | Deels: integratie handmatig bevestigd; alle wijzigings-/duplicaatgevallen niet afzonderlijk bevestigd |
| AG-06 | P0 | Laatste succesvolle synchronisatie en fouten tonen; eerder opgehaalde gegevens bij storingen behouden. | Deels: foutbehoud getest; live storingsgedrag niet afzonderlijk bevestigd |
| AG-07 | P0 | Voor gekoppelde privéafspraken is CalDAV de bron en wordt lokaal een gesynchroniseerde kopie bewaard. Taken en routines zijn lokale gegevens en vereisen geen CalDAV. | Gereed |
| AG-08 | P0 | Inloggegevens uitsluitend server-side gebruiken. | Gereed |
| AG-09 | P1 | Maandoverzicht en herinneringen. | Open (P1) |
| AG-10 | P0 | Het dashboard toont agenda-afspraken uitsluitend-lezen. Afspraken aanmaken, wijzigen of verwijderen via het dashboard en terugschrijven naar CalDAV vallen buiten scope. | Gereed |

Geen afzonderlijke ICS-import of leveranciersspecifieke agenda- en schoolkoppelingen.

## 6. Taken en routines

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| TK-01 | P0 | Taken met titel, icoon, beschrijving, verantwoordelijke, datum en optionele punten. De toevoeg-/bewerkpopup gebruikt 8 px tussen labels en invoer en 16 px tussen veldgroepen. | Gereed |
| TK-02 | P0 | Eenmalige en herhalende taken, met een aparte voltooiingsstatus per uitvoering. | Gereed |
| TK-03 | P0 | Afvinken, ongedaan maken en historie bewaren. Speel bij succesvol voltooien een voltooid-geluid; ongedaan maken blijft stil. | Gereed |
| TK-04 | P0 | Bij meerdere verantwoordelijken kiezen tussen individuele uitvoeringen en één gezamenlijke uitvoering. Na wijziging van deze keuze verdwijnen vervangen open uitvoeringen uit het overzicht zodra een uitvoering met de nieuwe verdeling voor dezelfde dag bestaat; afgeronde uitvoeringen en historie blijven behouden. | Gereed |
| RT-01 | P0 | Routines maken uit geordende stappen met pictogram en tekst. | Gereed |
| RT-02 | P0 | Routines toewijzen aan gezinsleden en weekdagen, met optioneel tijdvenster. Gebruik de keuze Tijdvenster gebruiken: aan vereist beide tijden, uit slaat geen tijdvenster op. Beide tijden leegmaken schakelt de keuze ook uit. Het routineoverzicht toont uitsluitend uitvoeringen op de geselecteerde dag. Een lege dag toont één melding en, indien gepland, een knop naar de eerstvolgende routinedag voor het gezinsfilter. Toekomstige uitvoeringen zonder vinkjes, afvinkhistorie of puntenboekingen volgen gewijzigde naam, stappen, personen, dagen en tijdvenster, ook na eerder bekijken. Oude schermen mogen geen oude stappen toepassen na zo’n wijziging. Bij archiveren of planningwijziging verdwijnen vervallen onaangeraakte toekomstplannen uit de weergave, met behoud van hun opslagrecord. Routines beheren toont alle sjablonen met personen, weekdagen, startdatum en tijdvenster; andere dagen worden niet als uitvoerbare kaarten bij een lege dag getoond. | Gereed |
| RT-03 | P0 | Voortgang per persoon en ingeplande kalenderdag tonen, volgens de ingestelde weekdagen. Elke ingeplande dag krijgt een afzonderlijke uitvoering die onafgevinkt begint; op niet-ingeplande dagen is er geen uitvoering. Terugbladeren toont de bewaarde voortgang van die datum. Voltooiingshistorie met tijdstippen blijft behouden. Agenda, routineoverzicht en kindmodus delen dezelfde voortgang. Het agendapaneel volgt vernieuwde voortgang, ondersteunt heropenen en houdt bij openen van een andere dag de gedeelde datumselectie bij. Speel bij het succesvol afvinken van een routinestap een voltooid-geluid; heropenen blijft stil. | Gereed |
| RT-04 | P0 | Gemiste stappen nooit automatisch voltooien. | Gereed |

## 7. Punten en beloningen

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| BEL-01 | P1 | Optioneel puntensaldo per persoon en beloningen met instelbare puntenprijs. | Gereed |
| BEL-02 | P1 | Punten als herleidbare transacties bewaren; dubbele verzoeken leveren geen dubbele punten op. | Gereed |
| BEL-03 | P1 | Ongedaan maken corrigeert de oorspronkelijke puntentoekenning. | Gereed |
| BEL-04 | P1 | Beloningen aanvragen en door een ouder laten goedkeuren. | Gereed |
| BEL-05 | P1 | Onbedoelde dubbele beloning van routine en onderliggende stappen voorkomen. | Gereed |
| BEL-06 | P1 | Ouders kunnen per gezinslid een puntencorrectie boeken; een reden is optioneel, transacties zijn herleidbaar en verlagingen tasten gereserveerde beloningspunten niet aan. | Gereed |

## 8. Boodschappenlijst

De gedeelde boodschappenlijst is onderdeel van de eerste versie en staat los van recepten of maaltijdplanning.

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| BO-01 | P0 | Eén gedeelde boodschappenlijst voor het gezin. | Gereed |
| BO-02 | P0 | Items toevoegen, wijzigen en verwijderen. | Gereed |
| BO-03 | P0 | Per item een naam, optionele hoeveelheid/eenheid en optionele notitie vastleggen. | Gereed |
| BO-04 | P0 | Items afvinken en opnieuw openzetten. | Gereed |
| BO-05 | P0 | Openstaande en afgevinkte items duidelijk scheiden; afgevinkte items kunnen opruimen. | Gereed |
| BO-06 | P0 | Beheren vanaf zowel het gedeelde touchscreen als een telefoon. | Deels: fysieke apparaten niet getest |
| BO-07 | P0 | Opgeslagen wijzigingen automatisch zichtbaar maken op andere verbonden apparaten. | Gereed |
| BO-08 | P0 | Gelijktijdige wijzigingen afhandelen zonder stil gegevensverlies; een opnieuw verstuurd verzoek mag hetzelfde item niet dubbel aanmaken. | Gereed |
| BO-09 | P1 | Categorieën en handmatige sortering, bijvoorbeeld op winkelindeling. | Open (P1) |
| BO-10 | P1 | Meerdere benoemde lijsten, bijvoorbeeld per winkel. | Open (P1) |

## 9. Home Assistant

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| HA-01 | P0 | Een Home Assistant-weergave binnen het eigen tabblad, met behoud van de vaste hoofdnavigatie. | Gereed (handmatig door gebruiker gevalideerd) |
| HA-02 | P0 | Serveradres en dashboard configureerbaar; geen hardgecodeerde apparaten of entiteiten. | Gereed |
| HA-03 | P0 | Aanmelding en bediening werken zonder de gezinsapp te verlaten. | Gereed (handmatig door gebruiker gevalideerd) |
| HA-04 | P0 | Een storing blijft beperkt tot dit onderdeel; Kalender en Immich blijven bereikbaar. | Gereed |
| HA-05 | P0 | Gevoelige acties en beheerrechten niet standaard ontsluiten op een gedeeld scherm. | Deels: rechten-/iframe-gedrag met echte HA-installatie controleren |
| HA-06 | P1 | Geselecteerde bediening rechtstreeks integreren, zoals verlichting, scènes en temperatuur. | Open (P1) |
| HA-07 | P1 | Aanwezigheid en dag/nachtinformatie gebruiken voor optioneel schermgedrag. | Open (P1) |

Tijdens implementatie vaststellen of het bestaande dashboard betrouwbaar kan worden ingesloten. Zo niet, een geïntegreerde weergave kiezen die de vaste tabnavigatie behoudt. Een configureerbaar extern dashboard moet zelf eveneens geschikt zijn voor mobiel gebruik.

## 10. Immich-fotolijst

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| IM-01 | P0 | Foto’s uitsluitend uit expliciet geselecteerde Immich-albums tonen. | Deels: Immich handmatig gevalideerd; albumtoegangsrandgevallen open |
| IM-02 | P0 | Fotolijst altijd handmatig bereikbaar via het tabblad Immich. | Gereed |
| IM-03 | P0 | Instelbare wisseltijd, willekeurige volgorde en vorige/volgende/pauze. | Gereed |
| IM-04 | P0 | Foto’s correct roteren en zonder vervorming tonen; volledig weergeven is standaard, uitsnijden optioneel. | Deels: Immich handmatig gevalideerd; EXIF-oriëntatie niet afzonderlijk getest |
| IM-05 | P0 | Vooruit laden en een begrensde lokale cache gebruiken. | Gereed |
| IM-06 | P0 | Niet-beschikbare foto’s overslaan; een duidelijke lege toestand tonen wanneer geen foto’s beschikbaar zijn. | Gereed |
| IM-07 | P0 | Albumwijzigingen verwerken en niet langer toegestane foto’s uit de cache verwijderen. | Deels: Immich handmatig gevalideerd; intrekking en cache-opruiming niet afzonderlijk bevestigd |
| IM-08 | P0 | Geen bronfoto’s of albums wijzigen of verwijderen. | Gereed |
| IM-09 | P0 | Na configureerbare inactiviteit automatisch naar Immich kunnen wisselen; uitschakelbaar per scherm. | Gereed |
| IM-10 | P0 | De drie hoofdtabs blijven zichtbaar tijdens de diavoorstelling. | Gereed |
| IM-11 | P0 | Tijdens invoer of actieve routinebediening niet automatisch wisselen. | Gereed |
| IM-12 | P0 | Aanraken van een foto activeert geen bediening van een ander tabblad. | Gereed |
| IM-13 | P1 | Analoge klok met cijfers 1–12 en eerstvolgende agenda-afspraak tonen in het vaste topmenu naast de datum. | Gereed |

## 11. Docker en platformonafhankelijkheid

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| DEP-01 | P0 | De volledige applicatie wordt via Docker Compose gestart, inclusief eventuele database. | Lokaal geverifieerd met lege opslag en echte Compose-services; fysieke NAS-acceptatie open |
| DEP-02 | P0 | Geen afhankelijkheid van NAS-specifieke apps, paden, API’s of besturingssystemen. | Gereed (configuratie-/codecontrole) |
| DEP-03 | P0 | Containerimages ondersteunen Linux amd64 en arm64; dezelfde configuratieopzet geldt voor beide. | 0.2.0 gepubliceerd voor amd64 en arm64; beide builds, runtime en opslag lokaal getest (amd64 via emulatie); fysieke NAS-acceptatie open |
| DEP-04 | P0 | Frontend wordt vanuit de containeropstelling aangeboden; clients hebben alleen een ondersteunde browser nodig. | Frontend via echte Compose-services geverifieerd op 0.2.0 voor amd64 en arm64; fysieke NAS-acceptatie open |
| DEP-05 | P0 | Persistente opslag voor gegevens en configuratie; cache afzonderlijk begrensd en vervangbaar. | Containervervanging behoudt instellingen in Docker-volumes en Linux-bind-mounts; Docker-volumeherstel open |
| DEP-06 | P0 | Configureerbare poorten, volumes, serviceadressen en tijdzone. | Gereed (configuratie aanwezig) |
| DEP-07 | P0 | Automatisch herstarten en healthchecks. | Gereed (Compose-configuratie aanwezig) |
| DEP-08 | P0 | Geen privileged-modus of toegang tot de Docker-socket vereist. | Gereed (Compose-configuratie gecontroleerd) |
| DEP-09 | P0 | Installatie vereist geen ontwikkeltools op de host. | Gereed (Compose-installatie beschreven) |
| DEP-10 | P0 | Minimale hostvereisten en ondersteunde browsers documenteren op basis van verificatie. | Deels: minimumvereisten en volledige browserondersteuning nog vaststellen |
| DEP-11 | P0 | De vervangende containerimage bevat de zlib-fix voor CVE-2026-85091 en geen kwetsbare glibc voor CVE-2026-84243. | 0.2.0 gepubliceerd voor amd64/arm64 met Alpine/musl en zlib 1.3.2-r1; gerichte Docker Scout-scans rechtstreeks op beide registry-images schoon |
| DEP-12 | P0 | Eerste installatie start met lege lokale data- en cachemappen zonder vooraf gekopieerde database of handmatige eigenaarswijziging. Een aparte voorbereidingsservice stelt de maprechten in; de app draait daarna als UID/GID 10001 en behoudt bestaande gegevens. | Lokaal geverifieerd met root-owned volumes en Linux-bind-mounts op gepubliceerde 0.1.0 en beide security-images (amd64/arm64); fysieke NAS-acceptatie open |
| DEP-13 | P0 | Eén Compose-bestand voor opdrachtregel en Portainer, met configureerbare image en optionele absolute opslagpaden; geen privéconfiguratie in gedeelde YAML. | Lokaal geverifieerd met beide opslagvormen en de gepubliceerde image; voorbeelden identiek aan compose.yaml; nieuwe versie nog niet op NAS uitgevoerd |
| DEP-14 | P0 | De opslagvoorbereiding herstelt ook de eigenaar en rechten van teruggezette bestanden en submappen, zonder inhoud te wijzigen of symbolische links te volgen. Hardlinks naar gewone bestanden worden geweigerd. | Geautomatiseerd geverifieerd op gepubliceerde 0.1.0 met volumes en Linux-bind-mounts; inhoud en instellingen behouden, links niet gevolgd en hardlinks geweigerd; NAS-acceptatie open |
| DEP-15 | P0 | De container bevat de python-dotenv-fix voor CVE-2026-28684; de veiligheidscontrole inspecteert alle CVE's zonder filter op ernst of CVE-ID. | python-dotenv 1.2.2 in patchrelease 0.2.1; pip 26.2.2 alleen tijdens de build, verwijderd uit de runtime; regressies en volledige scan vastgelegd in VERIFICATION.md. BusyBox CVE-2025-60876 blijft open bij Alpine |

“Platformonafhankelijk” betekent ondersteuning van de gedocumenteerde Docker- en browseromgevingen, zonder productspecifieke hardwarevereisten.

Kioskmodus, fysiek scherm uitschakelen en helderheidsregeling zijn optionele apparaatfuncties. De kernapplicatie moet zonder deze functies volledig werken.

## 12. Beveiliging, betrouwbaarheid en gegevens

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| SYS-01 | P0 | Lokale taken, routines en boodschappen blijven zonder internet werken zolang server en thuisnetwerk bereikbaar zijn. | Gereed (lokale backendtests) |
| SYS-02 | P0 | Bij uitval van de eigen backend geen succesvolle opslag suggereren. Offline wijzigingen synchroniseren valt buiten P0. | Gereed |
| SYS-03 | P0 | Gelijktijdige wijzigingen en dubbele verzoeken veilig verwerken. | Gereed |
| SYS-04 | P0 | Geheimen server-side bewaren; geen tokens, wachtwoorden of gevoelige inhoud in frontendbundels en logs. | Deels: opslag en API-tests gedekt; distributie-/logcontrole open |
| SYS-05 | P0 | Integratiefouten isoleren en begrijpelijk tonen. | Gereed (foutpaden getest) |
| SYS-06 | P0 | Back-up en getest herstel van gegevens en configuratie documenteren. | Deels: SQLite getest; herstel naar Docker-volume open |
| SYS-07 | P0 | Updates, gegevensmigraties en versiecompatibiliteit documenteren. | Gereed (documentatie en migratietests) |
| SYS-08 | P0 | Instellingen voor een specifiek scherm gescheiden houden van gedeelde gezinsinstellingen. | Gereed |

Voorgestelde prestatiedoelen onder gedocumenteerde testomstandigheden:

| Doel | Status |
|---|---|
| Zichtbare feedback op een tik binnen 200 ms. | Open: niet gemeten |
| Opgeslagen wijzigingen normaal binnen 2 seconden zichtbaar op andere verbonden apparaten. | Deels: functionele 2-secondenassertie getest; prestatierapport/netwerkmeting ontbreekt |
| Geen vastlopers of onbeperkte geheugengroei tijdens een test van 72 uur. | Open: duurtest niet uitgevoerd |

## 13. Publiek GitHub-project

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| GH-01 | P0 | Broncode bevat geen persoonlijke gegevens, echte serveradressen, geheimen of privéfoto’s. | Bron en lokale image gecontroleerd op 31 oktober; bytecodelek hersteld. Git-auteursmetadata bevat persoonsgegevens; zie PRIVACY_AUDIT.md |
| GH-02 | P0 | Voorbeeldconfiguratie met placeholders en uitsluitend fictieve demonstratiegegevens. | Gereed (bestandscontrole) |
| GH-03 | P0 | README met functies, installatie, configuratie, updates, back-up/herstel en bekende beperkingen. | Gereed |
| GH-04 | P0 | Reproduceerbare build en geautomatiseerde controles voor relevante applicatielogica en containerbuilds. | Deels: workflows aanwezig; CI/containerbuild niet op GitHub uitgevoerd |
| GH-05 | P0 | Beveiligingsbeleid met instructies voor het melden van kwetsbaarheden. | Gereed |
| GH-06 | P0 | Geen Hive-merkassets, overgenomen recepten of andere niet-vrij beschikbare inhoud meeleveren. | Gereed (bestandscontrole) |
| GH-07 | P0 | Projectlicentie is PolyForm Noncommercial 1.0.0 en wordt met de broncode en container meegeleverd. Publiek zichtbare broncode is niet automatisch open source. | Gereed |
| GH-08 | P1 | Bijdragerichtlijnen, release-instructies en versiegebonden containerimages. | Open (P1) |

## 14. Technische indeling

| Technisch uitgangspunt | Status |
|---|---|
| Responsive webinterface voor gedeelde schermen en persoonlijke apparaten. | Gereed; fysieke apparaattest open |
| Backend met lokale database voor gezinsgegevens. | Gereed |
| Afzonderlijke integratiemodules voor CalDAV, Home Assistant en Immich. | Gereed; eigenaar heeft de integraties handmatig gevalideerd |
| Achtergrondprocessen voor synchronisatie en terugkerende taken. | Gereed |
| Docker Compose voor installatie en beheer. | Deels: configuratie aanwezig; runtimeacceptatie open |

| Bron van gegevens | Status |
|---|---|
| CalDAV blijft de bron voor afspraken, Home Assistant voor huisautomatisering en Immich voor foto’s. | Gereed; integraties handmatig gevalideerd door eigenaar |

Herhalingssjablonen en concrete uitvoeringen van taken en routines worden afzonderlijk opgeslagen, zodat wijzigingen geen historie herschrijven. Toekomstige routine-uitvoeringen zonder voortgang, afvinkhistorie of puntenboekingen volgen het actuele sjabloon; vandaag, eerdere dagen en eerder afgevinkte uitvoeringen behouden hun snapshot, ook na heropenen. **Status: gereed; snapshots en historie zijn door backendtests gedekt.**

## 15. Acceptatiescenario’s voor P0

| # | Acceptatiescenario | Status |
|---|---|---|
| 1 | Alle drie de hoofdtabs blijven bereikbaar op mobiel, tablet en groot touchscreen, in beide oriëntaties. | Deels: viewporttests gedaan; fysieke apparaten niet getest |
| 2 | De interface werkt op een iPhone 13 in staande en liggende oriëntatie zonder horizontale pagina-overflow of essentiële bediening buiten beeld (browser-viewports 390×664 en 750×342 CSS-pixels). | Gereed in browser-viewports; fysieke acceptatie open |
| 3 | CalDAV-afspraken worden correct ingelezen en bijgewerkt; het dashboard maakt of wijzigt geen afspraken. | Deels: agenda-integratie handmatig bevestigd; alle wijzigings-/duplicaatgevallen niet afzonderlijk bevestigd |
| 4 | Herhalingen, uitzonderingen en zomer-/wintertijd worden correct weergegeven. | Deels: fixtures geslaagd; volledige live acceptatie van randgevallen niet bevestigd |
| 5 | Een routine behoudt voortgang na herladen; de volgende uitvoering begint opnieuw. | Gereed |
| 6 | Twee apparaten voltooien dezelfde taak tegelijk; er ontstaat één voltooiing. | Gereed via geïsoleerde browsercontexts/API-test |
| 7 | Een boodschappenitem wordt op een telefoon toegevoegd en verschijnt op het gedeelde scherm. | Deels: twee browsercontexts getest; fysieke apparaten niet getest |
| 8 | Afvinken en herstellen van boodschappen werkt op beide apparaten zonder duplicaten. | Deels: browser/API-tests geslaagd; fysieke apparaten niet getest |
| 9 | Uitval van CalDAV, Home Assistant of Immich blokkeert de overige onderdelen niet. | Deels: foutfixtures getest; echte integraties werken handmatig, maar live uitval niet getest |
| 10 | Automatisch wisselen naar Immich respecteert actieve invoer en behoudt de tabnavigatie. | Gereed in browsertests; langdurige fysieke schermtest open |
| 11 | De toepassing start met de gedocumenteerde Compose-configuratie op amd64 en arm64. | Open: containerstart en architectuurbouw niet uitgevoerd |
| 12 | Containervervanging behoudt opgeslagen gegevens. | Lokaal geverifieerd met fictieve instellingen, benoemde volumes en Linux-bind-mounts; fysieke NAS-acceptatie open |
| 13 | Een back-up kan naar een lege installatie worden hersteld. | Deels: SQLite-herstel getest; Docker-volumeherstel open |
| 14 | Beheerinstellingen en integratiegeheimen zijn niet toegankelijk vanuit onbevoegde dagelijkse bediening. | Deels: API- en login-tests geslaagd; echte HA-rechten en distributiecontrole open |
| 15 | De publieke repository en distributie bevatten uitsluitend veilige voorbeeldgegevens. | Deels: bron/geschiedenis en lokaal image gecontroleerd; Git-auteursmetadata beoordelen en definitieve publicatie open |

## 16. Resterende TODO’s

Deze oorspronkelijke bouwvolgorde is grotendeels uitgevoerd. De onderstaande open punten zijn de resterende TODO’s; status per requirement staat hierboven.

### P0: resterende implementatie- en acceptatie-TODO’s

Er zijn volgens de huidige inventaris geen P0-requirements waarvan de kernfunctionaliteit nog gebouwd moet worden. Resterend P0-werk is verificatie of acceptatie:

1. **Integratie-randgevallen:** CalDAV-herhalingen/uitzonderingen/tijdzones, dubbele of verwijderde afspraken en storingsbehoud; HA-rechten op een gedeeld scherm; Immich-albumintrekking, cache-opruiming en EXIF-oriëntatie.
2. **Docker/platformacceptatie (DEP-01, DEP-03–DEP-05, GH-04):** Compose starten, amd64/arm64-builds draaien, container vervangen en persistentie controleren.
3. **Back-up/herstel in Docker (SYS-06):** herstel naar een leeg Docker-volume uitvoeren.
4. **Doelapparaten en prestaties (UI-06, UI-08, BO-06):** telefoon/gedeeld touchscreen en ondersteunde browsers testen; feedback-, synchronisatie-, 72-uurs- en hostvereisten meten.
5. **Distributiecontrole (GH-01, GH-04):** repository, voorbeeldconfiguratie, geheimen/logs en containerdistributie voor publicatie nalopen; CI daadwerkelijk uitvoeren.

### P1: bewust uitgestelde uitbreidingen

- **AG-09:** maandoverzicht en herinneringen.
- **BO-09/BO-10:** boodschappen categoriseren/sorteren en meerdere lijsten.
- **HA-06/HA-07:** directe bediening van geselecteerde apparaten en aanwezigheid/dag-nachtinformatie.
- **GH-08:** bijdragerichtlijnen, release-instructies en versiegebonden containerimages.

BEL-01 t/m BEL-05 waren oorspronkelijk P1 maar zijn inmiddels geïmplementeerd. GEZ-06 en SYS-09/SYS-10 zijn op verzoek uit scope verwijderd.

## 17. Open keuzes

Geen. Toegang buitenshuis en gegevens-export zijn geen requirements voor deze versie.

Specifieke NAS-modellen en touchscreenmodellen zijn geen vereiste invoer voor de implementatie.


## Spelletjes — uitbreiding 2 november 2026

De eerdere statussamenvatting hierboven betreft de oorspronkelijke requirements.
Onderstaande eisen voegen het afzonderlijke spelletjesonderdeel toe.

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| GAME-01 | P0 | Eigen hoofdtabblad Spelletjes, ook bereikbaar vanuit kindmodus, met expliciete spelerkeuze en beschikbaar saldo. | Gereed: Chromium/WebKit-regressies |
| GAME-02 | P0 | Beheerder stelt per spel een positieve puntenprijs in. Aankoop boekt direct één sessie af, met behoud van reserveringen, atomair en bestand tegen dubbele verzoeken. | Gereed: API-regressies |
| GAME-03 | P0 | Eén actieve sessie per gezinslid; server bewaart voortgang, versie en vaste eindtijd. Hervatten/herladen verlengt de sessie niet. Einde bij doel, bevestigd stoppen of 180 seconden; geen automatische restitutie. | Gereed: API-regressies |
| GAME-04 | P0 | Foto-memory met zes paren uit geselecteerde Immich-albums; minstens zes beschikbare foto's. Browser controleert laden vóór aankoop. Verborgen kaarten blijven op de server. | Gereed: API en fictieve Immich-browserregressie |
| GAME-05 | P0 | Dierenorkest met oplopende reeksen tot zes, visuele aanwijzingen, optionele lokaal opgeslagen echte dieropnames, opnieuw tonen en zonder strafpunten na een fout. Een fout toont eerst 2 seconden een duidelijke vervaagde foutoverlay en speelt bij ingeschakeld geluid een kort, onderscheidend foutgeluid. Iedere ronde begint met een 3–2–1-overlay met vervaagde achtergrond die het hele spelvenster zonder binnenranden bedekt. De bediening blijft erboven bereikbaar. Daarna volgt 1,5 seconde rust vóór de reeks. Geluid is met een icoonknop naast Stoppen te schakelen; iedere volgende ronde en een nieuwe poging na een fout krijgen de aftelling; handmatig herhalen binnen een ronde niet. De ruimere popup heeft een muziekicoon bij de titel, extra binnen- en buitenmarge en afstand tussen uitleg en dierenknoppen. De herhaalknop staat midden onderaan en heeft grote ronde pijlen, het korte label Opnieuw en een toegankelijke naam. Op lage, liggende schermen staan de vier dieren naast elkaar. Afronden van het hele spel toont de routinefeestanimatie met alle vier de dieren; minder beweging toont het rustige eindscherm. | Gereed: Chromium/WebKit; dieropnames door gebruiker goedgekeurd |
| GAME-06 | P0 | Eén willekeurig oplosbaar doolhof met schermpijlen en toetsenbordbediening. | Gereed: API en Chromium/WebKit-regressies |
| GAME-07 | P0 | Spelregels, aankoop/sessiebeheer en browserrenderers zijn afzonderlijke modules met registries voor uitbreiding. Geen netwerkaanvragen tijdens puntentransacties. | Gereed: code, API- en modulecontrole |
| GAME-08 | P0 | Touchbediening, eindscherm, alleen laatste 30 seconden aftellen, geluid standaard aan met een dempknop en geen inactiviteitswissel tijdens spelen. | Deels: touchgeometrie en eindschermen getest; aftelling, inactiviteit en fysieke bediening handmatig open |
