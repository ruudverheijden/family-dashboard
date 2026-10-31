# Beveiliging

Dit is versie 0.1.0 voor een vertrouwd thuisnetwerk. Dagelijkse bediening is bewust gedeeld: iedereen die de app bereikt kan gezinsgegevens lezen en taken, routines en boodschappen wijzigen. Profielkeuze is een filter, geen authenticatie. Beheerinstellingen en gezinsprofielen vereisen een beheerwachtwoord.

- Kies een eigen `ADMIN_PASSWORD`. Beheersessies verlopen na 30 minuten en bij serverherstart. Vijf foutieve pogingen per IP blokkeren aanmelden vijf minuten. Daarnaast geldt voor alle IP-adressen samen een limiet van vijf aanmeldpogingen ineens en één extra poging per tien seconden. Die gedeelde limiet wordt in SQLite bewaard en geldt over worker- en serverherstarts heen. Configureer ook limieten op de reverse proxy als je die inzet.
- Docker publiceert de poort op de netwerkinterfaces van de host zodat apparaten op het thuisnetwerk de app kunnen bereiken. Beperk inkomend verkeer met de hostfirewall tot het vertrouwde LAN en stel geen router-port-forward of andere publieke toegang in. Gebruik HTTPS via een eigen reverse proxy als het netwerk niet volledig vertrouwd is; stel daarbij `COOKIE_SECURE=true` in. Stuur de oorspronkelijke Host en scheme correct door; vertrouw proxyheaders uitsluitend van de proxy.
- JSON-verzoeken met een body groter dan 1 MiB worden geweigerd, ook als de grootte niet vooraf in `Content-Length` is opgegeven.
- CalDAV-wachtwoorden, Home Assistant-tokens en Immich-sleutels staan server-side in de database. Ze zijn niet op applicatieniveau versleuteld: bescherm de host, het datavolume en back-ups. De configuratie-API geeft bestaande geheimen nooit terug.
- Integratie-URL’s mogen interne adressen gebruiken; een beheerder is vertrouwd en kan de server verbindingen laten maken naar het thuisnetwerk. Geef het beheerwachtwoord dus niet aan dagelijkse gebruikers.
- Gebruik voor Home Assistant een token van een apart niet-beheeraccount. Alleen expliciet geselecteerde entiteiten worden getoond; de backend staat uitsluitend aan/uit toe voor light, switch en input_boolean. De selectie is beschikbaar aan iedereen op het gedeelde dashboard. Opgeslagen tokens worden niet teruggestuurd naar browsers, en upstream redirects worden niet gevolgd.
- Geef de Immich-sleutel alleen leesrechten voor benodigde albums en thumbnails. CalDAV wordt alleen gelezen. Gebruik waar mogelijk ook aan serverzijde alleen-lezen accounts.
- Cross-origin schrijfacties zijn geblokkeerd met een eigen requestheader, Origin-controle en SameSite-cookies. De frontend laadt geen externe scripts, lettertypen of tracking.

## Kwetsbaarheid melden

Publiceer geen geheimen, privéfoto’s of reproduceerbare exploitatiedetails in een openbaar issue. Na GitHub-publicatie: gebruik **Security → Report a vulnerability** (de beheerder moet private vulnerability reporting eerst inschakelen). Zolang er nog geen publiek project/contactkanaal is, meld een probleem rechtstreeks aan de projectbeheerder; verzin geen openbaar contactadres. Voeg de versie, impact en minimale reproductiestappen zonder echte gezinsgegevens toe.

0.1.x is de enige huidige ontwikkellijn. Er is nog geen onafhankelijke beveiligingsaudit uitgevoerd.
