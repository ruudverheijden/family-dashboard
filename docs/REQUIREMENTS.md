# Requirements — lokaal gezinsdashboard
Versie 0.3 — 30 oktober 2026

## 1. Doel en uitgangspunten

Bouw een zelfstandig te hosten gezinsdashboard dat planning, taken, routines, boodschappen, Home Assistant en een Immich-fotolijst combineert.

- De toepassing draait via Docker, zonder afhankelijkheden van een specifiek NAS-merk.
- De interface werkt op kleine en grote touchscreens, tablets en mobiele telefoons, in liggende en staande oriëntatie.
- De broncode en installatie-instructies worden publiek op GitHub gepubliceerd.
- Lokale basisfunctionaliteit vereist geen abonnement of externe clouddienst.
- CalDAV is de enige externe agendakoppeling.
- Home Assistant en Immich zijn bestaande, afzonderlijke services.
- Recepten, maaltijdplanning, voedingswaarden en voorraadbeheer vallen buiten scope.

Dit document beschrijft de gewenste eigen toepassing. HiveFamily dient als functionele inspiratie; het document pretendeert geen volledige reconstructie van de ingelogde Hive-app.

## 2. Prioriteiten

- **P0:** eerste bruikbare versie.
- **P1:** latere uitbreiding.
- **Open keuze:** vóór implementatie beslissen.

## 3. Navigatie en responsive interface

| ID | Prioriteit | Requirement |
|---|---|---|
| UI-01 | P0 | Drie permanent zichtbare hoofdtabs: Kalender, Home Assistant en Immich. |
| UI-02 | P0 | Vanuit ieder onderdeel met één tik naar de andere hoofdtabs kunnen wisselen, zonder browsernavigatie of opnieuw aanmelden. |
| UI-03 | P0 | Kalender is het standaardtabblad en bevat de gezinsplanner, met subnavigatie naar Agenda, Taken, Routines en Boodschappen. |
| UI-04 | P0 | Beheerinstellingen zijn bereikbaar via een afzonderlijke beveiligde beheerknop. |
| UI-05 | P0 | De indeling past zich aan beschikbare schermruimte aan; op mobiel mag een weekoverzicht veranderen in een leesbare dag- of lijstweergave. |
| UI-06 | P0 | Geen vaste afhankelijkheid van schermresolutie, apparaatmodel of oriëntatie. Ondersteun minimaal 320 CSS-pixels breedte zonder verlies van kernfunctionaliteit. |
| UI-07 | P0 | Aanraakvlakken minimaal 48 × 48 CSS-pixels; bediening vereist geen hover. Ondersteun ook toetsenbordbediening en zichtbare focus. |
| UI-08 | P0 | Nederlandse interface, 24-uursklok, maandag als eerste weekdag en configureerbare tijdzone, standaard Europe/Amsterdam. |
| UI-09 | P0 | Bij wisselen van tabblad relevante toestand behouden, zoals de geselecteerde kalenderdatum. |
| UI-10 | P0 | Niet-opgeslagen invoer beschermen tegen onbedoeld verlies. |
| UI-11 | P0 | Gezinsleden herkenbaar maken met naam en kleur; kleur mag niet het enige onderscheid zijn. |

## 4. Gezinsprofielen en toegang

| ID | Prioriteit | Requirement |
|---|---|---|
| GEZ-01 | P0 | Gezinsleden beheren met naam, kleur en optionele avatar. |
| GEZ-02 | P0 | Gezamenlijke overzichten en filtering per gezinslid. |
| GEZ-03 | P0 | Onderscheid tussen beheerrechten en dagelijkse bediening op een gedeeld scherm. |
| GEZ-04 | P0 | Profielkeuze zonder herhaald inloggen op het gedeelde scherm; profielkeuze geldt niet als authenticatie. |
| GEZ-05 | P0 | Beheerinstellingen en integratiegeheimen afschermen met authenticatie. |
| GEZ-06 | P1 | Per gezinslid configureerbare rechten en oudergoedkeuring voor geselecteerde handelingen. |

## 5. Agenda via CalDAV

| ID | Prioriteit | Requirement |
|---|---|---|
| AG-01 | P0 | Dag- en weekoverzicht met gezinsleden, kleuren en filters. |
| AG-02 | P0 | Eén of meer CalDAV-accounts configureren via serveradres en inloggegevens. |
| AG-03 | P0 | Beschikbare agenda’s ophalen, selecteren en aan gezinsleden koppelen. |
| AG-04 | P0 | Afspraken, herhalingen, uitzonderingen, hele-dagafspraken en tijdzones correct verwerken. |
| AG-05 | P0 | Nieuwe, gewijzigde en verwijderde afspraken synchroniseren zonder duplicaten. |
| AG-06 | P0 | Laatste succesvolle synchronisatie en fouten tonen; eerder opgehaalde gegevens bij storingen behouden. |
| AG-07 | P0 | CalDAV is de bron voor afspraken; lokaal wordt een gesynchroniseerde kopie bewaard. |
| AG-08 | P0 | Inloggegevens uitsluitend server-side gebruiken. |
| AG-09 | P1 | Maandoverzicht en herinneringen. |
| AG-10 | Open keuze | Afspraken via het dashboard aanmaken, wijzigen en verwijderen. Indien ondersteund: terugschrijven via CalDAV, alleen-lezen agenda’s respecteren en conflicten zichtbaar afhandelen. |

Geen afzonderlijke ICS-import of leveranciersspecifieke agenda- en schoolkoppelingen.

## 6. Taken en routines

| ID | Prioriteit | Requirement |
|---|---|---|
| TK-01 | P0 | Taken met titel, icoon, beschrijving, verantwoordelijke, datum en optionele punten. |
| TK-02 | P0 | Eenmalige en herhalende taken, met een aparte voltooiingsstatus per uitvoering. |
| TK-03 | P0 | Afvinken, ongedaan maken en historie bewaren. |
| TK-04 | P0 | Bij meerdere verantwoordelijken kiezen tussen individuele uitvoeringen en één gezamenlijke uitvoering. |
| TK-05 | P1 | Taken laten rouleren volgens een ingesteld rooster. |
| RT-01 | P0 | Routines maken uit geordende stappen met pictogram en tekst. |
| RT-02 | P0 | Routines toewijzen aan gezinsleden, weekdagen en tijdvensters. |
| RT-03 | P0 | Voortgang per persoon en uitvoering tonen. Nieuwe uitvoeringen beginnen opnieuw zonder historie te wijzigen. |
| RT-04 | P0 | Gemiste stappen nooit automatisch voltooien. |
| RT-05 | P1 | Vakantiepauzes en uitzonderingen. |

## 7. Punten en beloningen

| ID | Prioriteit | Requirement |
|---|---|---|
| BEL-01 | P1 | Optioneel puntensaldo per persoon en beloningen met instelbare puntenprijs. |
| BEL-02 | P1 | Punten als herleidbare transacties bewaren; dubbele verzoeken leveren geen dubbele punten op. |
| BEL-03 | P1 | Ongedaan maken corrigeert de oorspronkelijke puntentoekenning. |
| BEL-04 | P1 | Beloningen aanvragen en door een ouder laten goedkeuren. |
| BEL-05 | P1 | Onbedoelde dubbele beloning van routine en onderliggende stappen voorkomen. |

## 8. Boodschappenlijst

De gedeelde boodschappenlijst is onderdeel van de eerste versie en staat los van recepten of maaltijdplanning.

| ID | Prioriteit | Requirement |
|---|---|---|
| BO-01 | P0 | Eén gedeelde boodschappenlijst voor het gezin. |
| BO-02 | P0 | Items toevoegen, wijzigen en verwijderen. |
| BO-03 | P0 | Per item een naam, optionele hoeveelheid/eenheid en optionele notitie vastleggen. |
| BO-04 | P0 | Items afvinken en opnieuw openzetten. |
| BO-05 | P0 | Openstaande en afgevinkte items duidelijk scheiden; afgevinkte items kunnen opruimen. |
| BO-06 | P0 | Beheren vanaf zowel het gedeelde touchscreen als een telefoon. |
| BO-07 | P0 | Opgeslagen wijzigingen automatisch zichtbaar maken op andere verbonden apparaten. |
| BO-08 | P0 | Gelijktijdige wijzigingen afhandelen zonder stil gegevensverlies; een opnieuw verstuurd verzoek mag hetzelfde item niet dubbel aanmaken. |
| BO-09 | P1 | Categorieën en handmatige sortering, bijvoorbeeld op winkelindeling. |
| BO-10 | P1 | Meerdere benoemde lijsten, bijvoorbeeld per winkel. |

## 9. Home Assistant

| ID | Prioriteit | Requirement |
|---|---|---|
| HA-01 | P0 | Een Home Assistant-weergave binnen het eigen tabblad, met behoud van de vaste hoofdnavigatie. |
| HA-02 | P0 | Serveradres en dashboard configureerbaar; geen hardgecodeerde apparaten of entiteiten. |
| HA-03 | P0 | Aanmelding en bediening werken zonder de gezinsapp te verlaten. |
| HA-04 | P0 | Een storing blijft beperkt tot dit onderdeel; Kalender en Immich blijven bereikbaar. |
| HA-05 | P0 | Gevoelige acties en beheerrechten niet standaard ontsluiten op een gedeeld scherm. |
| HA-06 | P1 | Geselecteerde bediening rechtstreeks integreren, zoals verlichting, scènes en temperatuur. |
| HA-07 | P1 | Aanwezigheid en dag/nachtinformatie gebruiken voor optioneel schermgedrag. |

Tijdens implementatie vaststellen of het bestaande dashboard betrouwbaar kan worden ingesloten. Zo niet, een geïntegreerde weergave kiezen die de vaste tabnavigatie behoudt. Een configureerbaar extern dashboard moet zelf eveneens geschikt zijn voor mobiel gebruik.

## 10. Immich-fotolijst

| ID | Prioriteit | Requirement |
|---|---|---|
| IM-01 | P0 | Foto’s uitsluitend uit expliciet geselecteerde Immich-albums tonen. |
| IM-02 | P0 | Fotolijst altijd handmatig bereikbaar via het tabblad Immich. |
| IM-03 | P0 | Instelbare wisseltijd, willekeurige volgorde en vorige/volgende/pauze. |
| IM-04 | P0 | Foto’s correct roteren en zonder vervorming tonen; volledig weergeven is standaard, uitsnijden optioneel. |
| IM-05 | P0 | Vooruit laden en een begrensde lokale cache gebruiken. |
| IM-06 | P0 | Niet-beschikbare foto’s overslaan; een duidelijke lege toestand tonen wanneer geen foto’s beschikbaar zijn. |
| IM-07 | P0 | Albumwijzigingen verwerken en niet langer toegestane foto’s uit de cache verwijderen. |
| IM-08 | P0 | Geen bronfoto’s of albums wijzigen of verwijderen. |
| IM-09 | P0 | Na configureerbare inactiviteit automatisch naar Immich kunnen wisselen; uitschakelbaar per scherm. |
| IM-10 | P0 | De drie hoofdtabs blijven zichtbaar tijdens de diavoorstelling. |
| IM-11 | P0 | Tijdens invoer of actieve routinebediening niet automatisch wisselen. |
| IM-12 | P0 | Aanraken van een foto activeert geen bediening van een ander tabblad. |
| IM-13 | P1 | Optionele klok en eerstvolgende afspraak als overlay. |

## 11. Docker en platformonafhankelijkheid

| ID | Prioriteit | Requirement |
|---|---|---|
| DEP-01 | P0 | De volledige applicatie wordt via Docker Compose gestart, inclusief eventuele database. |
| DEP-02 | P0 | Geen afhankelijkheid van NAS-specifieke apps, paden, API’s of besturingssystemen. |
| DEP-03 | P0 | Containerimages ondersteunen Linux amd64 en arm64; dezelfde configuratieopzet geldt voor beide. |
| DEP-04 | P0 | Frontend wordt vanuit de containeropstelling aangeboden; clients hebben alleen een ondersteunde browser nodig. |
| DEP-05 | P0 | Persistente opslag voor gegevens en configuratie; cache afzonderlijk begrensd en vervangbaar. |
| DEP-06 | P0 | Configureerbare poorten, volumes, serviceadressen en tijdzone. |
| DEP-07 | P0 | Automatisch herstarten en healthchecks. |
| DEP-08 | P0 | Geen privileged-modus of toegang tot de Docker-socket vereist. |
| DEP-09 | P0 | Installatie vereist geen ontwikkeltools op de host. |
| DEP-10 | P0 | Minimale hostvereisten en ondersteunde browsers documenteren op basis van verificatie. |

“Platformonafhankelijk” betekent ondersteuning van de gedocumenteerde Docker- en browseromgevingen, zonder productspecifieke hardwarevereisten.

Kioskmodus, fysiek scherm uitschakelen en helderheidsregeling zijn optionele apparaatfuncties. De kernapplicatie moet zonder deze functies volledig werken.

## 12. Beveiliging, betrouwbaarheid en gegevens

| ID | Prioriteit | Requirement |
|---|---|---|
| SYS-01 | P0 | Lokale taken, routines en boodschappen blijven zonder internet werken zolang server en thuisnetwerk bereikbaar zijn. |
| SYS-02 | P0 | Bij uitval van de eigen backend geen succesvolle opslag suggereren. Offline wijzigingen synchroniseren valt buiten P0. |
| SYS-03 | P0 | Gelijktijdige wijzigingen en dubbele verzoeken veilig verwerken. |
| SYS-04 | P0 | Geheimen server-side bewaren; geen tokens, wachtwoorden of gevoelige inhoud in frontendbundels en logs. |
| SYS-05 | P0 | Integratiefouten isoleren en begrijpelijk tonen. |
| SYS-06 | P0 | Back-up en getest herstel van gegevens en configuratie documenteren. |
| SYS-07 | P0 | Updates, gegevensmigraties en versiecompatibiliteit documenteren. |
| SYS-08 | P0 | Instellingen voor een specifiek scherm gescheiden houden van gedeelde gezinsinstellingen. |
| SYS-09 | P1 | Export van gezinsgegevens in een gangbaar formaat. |
| SYS-10 | P1 | Beveiligde toegang buitenshuis documenteren. Een publieke GitHub-repository betekent niet dat de draaiende toepassing publiek toegankelijk moet zijn. |

Voorgestelde prestatiedoelen onder gedocumenteerde testomstandigheden:

- Zichtbare feedback op een tik binnen 200 ms.
- Opgeslagen wijzigingen normaal binnen 2 seconden zichtbaar op andere verbonden apparaten.
- Geen vastlopers of onbeperkte geheugengroei tijdens een test van 72 uur.

## 13. Publiek GitHub-project

| ID | Prioriteit | Requirement |
|---|---|---|
| GH-01 | P0 | Broncode bevat geen persoonlijke gegevens, echte serveradressen, geheimen of privéfoto’s. |
| GH-02 | P0 | Voorbeeldconfiguratie met placeholders en uitsluitend fictieve demonstratiegegevens. |
| GH-03 | P0 | README met functies, installatie, configuratie, updates, back-up/herstel en bekende beperkingen. |
| GH-04 | P0 | Reproduceerbare build en geautomatiseerde controles voor relevante applicatielogica en containerbuilds. |
| GH-05 | P0 | Beveiligingsbeleid met instructies voor het melden van kwetsbaarheden. |
| GH-06 | P0 | Geen Hive-merkassets, overgenomen recepten of andere niet-vrij beschikbare inhoud meeleveren. |
| GH-07 | Open keuze | Vóór publicatie een licentie kiezen en vastleggen. Publiek zichtbare broncode is niet automatisch open source. |
| GH-08 | P1 | Bijdragerichtlijnen, release-instructies en versiegebonden containerimages. |

## 14. Technische indeling

- Responsive webinterface voor gedeelde schermen en persoonlijke apparaten.
- Backend met lokale database voor gezinsgegevens.
- Afzonderlijke integratiemodules voor CalDAV, Home Assistant en Immich.
- Achtergrondprocessen voor synchronisatie en terugkerende taken.
- Docker Compose voor installatie en beheer.

CalDAV blijft de bron voor afspraken, Home Assistant voor huisautomatisering en Immich voor foto’s.

Herhalingssjablonen en concrete uitvoeringen van taken en routines worden afzonderlijk opgeslagen, zodat wijzigingen geen historie herschrijven.

## 15. Acceptatiescenario’s voor P0

1. Alle drie de hoofdtabs blijven bereikbaar op mobiel, tablet en groot touchscreen, in beide oriëntaties.
2. De interface werkt vanaf 320 CSS-pixels breedte zonder dat essentiële bediening buiten beeld verdwijnt.
3. CalDAV-aanmaak, wijzigingen en verwijderingen worden correct verwerkt.
4. Herhalingen, uitzonderingen en zomer-/wintertijd worden correct weergegeven.
5. Een routine behoudt voortgang na herladen; de volgende uitvoering begint opnieuw.
6. Twee apparaten voltooien dezelfde taak tegelijk; er ontstaat één voltooiing.
7. Een boodschappenitem wordt op een telefoon toegevoegd en verschijnt op het gedeelde scherm.
8. Afvinken en herstellen van boodschappen werkt op beide apparaten zonder duplicaten.
9. Uitval van CalDAV, Home Assistant of Immich blokkeert de overige onderdelen niet.
10. Automatisch wisselen naar Immich respecteert actieve invoer en behoudt de tabnavigatie.
11. De toepassing start met de gedocumenteerde Compose-configuratie op amd64 en arm64.
12. Containervervanging behoudt opgeslagen gegevens.
13. Een back-up kan naar een lege installatie worden hersteld.
14. Beheerinstellingen en integratiegeheimen zijn niet toegankelijk vanuit onbevoegde dagelijkse bediening.
15. De publieke repository en distributie bevatten uitsluitend veilige voorbeeldgegevens.

## 16. Bouwvolgorde

1. Responsive navigatie, Docker-opstelling en technische validatie van integraties.
2. Gezinsprofielen en CalDAV-agenda.
3. Taken, routines en gedeelde boodschappenlijst.
4. Home Assistant-weergave en Immich-fotolijst.
5. Beveiliging, herstel, tests en documentatie voor publieke distributie.
6. Geselecteerde P1-uitbreidingen.

## 17. Open keuzes

- Alleen CalDAV lezen, of ook afspraken aanmaken, wijzigen en verwijderen?
- Welke licentie krijgt het publieke project?
- Moet toegang buitenshuis onderdeel zijn van de eerste versie?

Specifieke NAS-modellen en touchscreenmodellen zijn geen vereiste invoer voor de implementatie.