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

**Statussamenvatting op 31 oktober 2026:** van de 95 requirement-ID’s zijn er 70 gereed, 19 deels gereed (verdere acceptatie open) en 6 bewust uitgesteld als P1. De eigenaar heeft de agenda-integratie, Immich en Home Assistant handmatig gevalideerd. Er is geen P0-ID waarvan de kernfunctionaliteit nog gebouwd moet worden; resterende P0-TODO’s zijn aanvullende randgevallen en technische acceptatie.

## 3. Navigatie en responsive interface

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| UI-01 | P0 | Vier permanent zichtbare hoofdtabs: Kalender, Home Assistant, Immich en Boodschappen. | Gereed |
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

## 4. Gezinsprofielen en toegang

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| GEZ-01 | P0 | Gezinsleden beheren met naam, kleur en optionele avatar. | Gereed |
| GEZ-02 | P0 | Gezamenlijke overzichten en filtering per gezinslid. | Gereed |
| GEZ-03 | P0 | Onderscheid tussen beheerrechten en dagelijkse bediening op een gedeeld scherm. | Gereed |
| GEZ-04 | P0 | Profielkeuze zonder herhaald inloggen op het gedeelde scherm; profielkeuze geldt niet als authenticatie. | Gereed |
| GEZ-05 | P0 | Beheerinstellingen en integratiegeheimen afschermen met authenticatie. | Gereed |

## 5. Lokale agenda en optionele CalDAV

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| AG-01 | P0 | Dag-, 3-daags en weekoverzicht met gezinsleden, kleuren en filters. Toon lokale taken altijd bovenaan op de juiste datum, visueel gescheiden van afspraken. Toon een scrollbaar 24-uursrooster met afspraken op hun tijd en hoogte naar duur; open rond de huidige tijd met 2 uur terug en 4 uur vooruit, en markeer de huidige tijd op de tijdlijn. Hele-dagafspraken blijven apart zichtbaar. | Gereed |
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
| TK-01 | P0 | Taken met titel, icoon, beschrijving, verantwoordelijke, datum en optionele punten. | Gereed |
| TK-02 | P0 | Eenmalige en herhalende taken, met een aparte voltooiingsstatus per uitvoering. | Gereed |
| TK-03 | P0 | Afvinken, ongedaan maken en historie bewaren. | Gereed |
| TK-04 | P0 | Bij meerdere verantwoordelijken kiezen tussen individuele uitvoeringen en één gezamenlijke uitvoering. | Gereed |
| RT-01 | P0 | Routines maken uit geordende stappen met pictogram en tekst. | Gereed |
| RT-02 | P0 | Routines toewijzen aan gezinsleden, weekdagen en tijdvensters. | Gereed |
| RT-03 | P0 | Voortgang per persoon en uitvoering tonen. Nieuwe uitvoeringen beginnen opnieuw zonder historie te wijzigen. | Gereed |
| RT-04 | P0 | Gemiste stappen nooit automatisch voltooien. | Gereed |

## 7. Punten en beloningen

| ID | Prioriteit | Requirement | Status |
|---|---|---|---|
| BEL-01 | P1 | Optioneel puntensaldo per persoon en beloningen met instelbare puntenprijs. | Gereed |
| BEL-02 | P1 | Punten als herleidbare transacties bewaren; dubbele verzoeken leveren geen dubbele punten op. | Gereed |
| BEL-03 | P1 | Ongedaan maken corrigeert de oorspronkelijke puntentoekenning. | Gereed |
| BEL-04 | P1 | Beloningen aanvragen en door een ouder laten goedkeuren. | Gereed |
| BEL-05 | P1 | Onbedoelde dubbele beloning van routine en onderliggende stappen voorkomen. | Gereed |

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
| DEP-01 | P0 | De volledige applicatie wordt via Docker Compose gestart, inclusief eventuele database. | Deels: configuratie aanwezig; containerstart niet uitgevoerd |
| DEP-02 | P0 | Geen afhankelijkheid van NAS-specifieke apps, paden, API’s of besturingssystemen. | Gereed (configuratie-/codecontrole) |
| DEP-03 | P0 | Containerimages ondersteunen Linux amd64 en arm64; dezelfde configuratieopzet geldt voor beide. | Deels: CI-configuratie aanwezig; builds niet uitgevoerd |
| DEP-04 | P0 | Frontend wordt vanuit de containeropstelling aangeboden; clients hebben alleen een ondersteunde browser nodig. | Deels: container-runtime niet geverifieerd |
| DEP-05 | P0 | Persistente opslag voor gegevens en configuratie; cache afzonderlijk begrensd en vervangbaar. | Deels: configuratie aanwezig; Docker-volumeherstel open |
| DEP-06 | P0 | Configureerbare poorten, volumes, serviceadressen en tijdzone. | Gereed (configuratie aanwezig) |
| DEP-07 | P0 | Automatisch herstarten en healthchecks. | Gereed (Compose-configuratie aanwezig) |
| DEP-08 | P0 | Geen privileged-modus of toegang tot de Docker-socket vereist. | Gereed (Compose-configuratie gecontroleerd) |
| DEP-09 | P0 | Installatie vereist geen ontwikkeltools op de host. | Gereed (Compose-installatie beschreven) |
| DEP-10 | P0 | Minimale hostvereisten en ondersteunde browsers documenteren op basis van verificatie. | Deels: minimumvereisten en volledige browserondersteuning nog vaststellen |

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
| GH-01 | P0 | Broncode bevat geen persoonlijke gegevens, echte serveradressen, geheimen of privéfoto’s. | Deels: voorbeelden zijn fictief; controle vóór publicatie open |
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

Herhalingssjablonen en concrete uitvoeringen van taken en routines worden afzonderlijk opgeslagen, zodat wijzigingen geen historie herschrijven. **Status: gereed; snapshots en historie zijn door backendtests gedekt.**

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
| 12 | Containervervanging behoudt opgeslagen gegevens. | Open: Docker-runtime niet getest |
| 13 | Een back-up kan naar een lege installatie worden hersteld. | Deels: SQLite-herstel getest; Docker-volumeherstel open |
| 14 | Beheerinstellingen en integratiegeheimen zijn niet toegankelijk vanuit onbevoegde dagelijkse bediening. | Deels: API- en login-tests geslaagd; echte HA-rechten en distributiecontrole open |
| 15 | De publieke repository en distributie bevatten uitsluitend veilige voorbeeldgegevens. | Deels: voorbeelden zijn fictief; eindcontrole/publicatie open |

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