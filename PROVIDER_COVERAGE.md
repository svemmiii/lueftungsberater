# Automatische Wetter- und Warnquellen – COMPLETE(11)

Stand der Implementierung und Prüfung: 02.10.2026. Integrationsversion bleibt 0.11.0.

| Land / Gebiet | Wetter | Amtliche Warnquellen | Bevölkerungsschutz |
| --- | --- | --- | --- |
| Deutschland (DE) | DWD-Stationsdaten / MOSMIX, vorhandene Wetter-Fallbacks | NINA: MoWaS, KATWARN, BIWAPP, DWD, Hochwasser, Polizei | Ja, über die von NINA veröffentlichten Quellen |
| Österreich (AT) | Automatischer Wetteradapter | MeteoAlarm + AT-Alert | Ja, über AT-Alert |
| Belgien (BE) | Automatischer Wetteradapter | MeteoAlarm + BE-Alert | Ja, über den öffentlichen BE-Alert-CAP-Feed |
| Schweiz (CH) | Automatischer Wetteradapter | MeteoAlarm + Alertswiss | Ja, über Alertswiss |
| USA (US) | Automatischer Wetteradapter | NWS-Punktabfrage | Wetterwarnungen; kein vollständiger nationaler Zivilschutzadapter |
| Weitere unten genannte MeteoAlarm-Länder | Automatischer Wetteradapter | MeteoAlarm | Wetterwarnungen; kein zusätzlicher nationaler Zivilschutzadapter |
| Andere Länder / nicht auflösbarer Standort | Automatischer Wetteradapter, soweit erreichbar | Keine automatische Warnquelle | Nicht unterstützt; keine automatische Entwarnung |

Weitere MeteoAlarm-Länder: AD, BA, BG, HR, CY, CZ, DK, EE, FI, FR, GR, HU, IS, IE, IL, IT, LV, LT, LU, MT, MD, ME, NL, MK, NO, PL, PT, RO, RS, SK, SI, ES, SE, UA, GB. Die tatsächliche Verfügbarkeit hängt zusätzlich von den veröffentlichten Feeds und ihrer erfolgreichen Gebietsauflösung ab.

## Standort und GPS

Die Länderwahl folgt den Koordinaten, nicht der Zeitzone. Die mitgelieferten Natural-Earth-Länderpolygone sind kartographische Grenzen; Grenzlinien, Küsten und kleine Gebiete sind keine amtliche Katasterauflösung. Ein nicht eindeutig zuordenbarer Punkt wird als unbekannt behandelt.

Bei einem mobilen Tracker gelten Positionsmeldungen höchstens fünf Minuten als frisch. Vorhandene `gps_timestamp` oder `location_updated_at` werden bevorzugt; ansonsten dient Home Assistants `last_reported`, ersatzweise `last_updated`, als Meldungszeit. Ein weiter verfügbarer, aber nicht mehr meldender Tracker gilt somit nicht unbegrenzt als aktuell. Die letzte Position darf bis insgesamt 30 Minuten seit der letzten Positionsmeldung gehalten werden. Danach sind die automatischen Quellen nicht verfügbar. Es erfolgt kein stiller Wechsel auf den Heimstandort.

Wenn `gps_accuracy` vorhanden ist, muss es ein endlicher, nicht negativer Zahlenwert bis einschließlich 250 Metern sein. Schlechtere oder ungültige Angaben werden nicht als aktuelle neue Position akzeptiert. Die letzte ausreichend genaue Position kann weiterhin bis insgesamt 30 Minuten seit ihrer Meldung gehalten werden; wiederholte schlechte Meldungen setzen diese Uhr nicht zurück. Ohne vorherige gültige Position, insbesondere direkt nach einem Neustart, bleiben die automatischen Quellen unbekannt. Die 250-Meter-Grenze ist eine konservative Betriebsentscheidung dieser Integration, keine Vorgabe von Home Assistant. Fehlende optionale Genauigkeitsangaben werden aus Kompatibilitätsgründen weiterhin akzeptiert.

Ein Tracker, der alte Koordinaten ständig neu meldet und keinen tatsächlichen GPS-Zeitstempel liefert, lässt sich von einer gültigen wiederholten Positionsmeldung nicht unterscheiden. Für solche Geräte sollte der Tracker einen echten GPS-Zeitstempel bereitstellen.

## MeteoAlarm-Gebiete

CAP-Polygone und Kreise werden direkt geprüft. EMMA_ID und bekannte NUTS-Aliase werden über den mitgelieferten Regionsdatensatz aufgelöst. Die Originalgeometrien werden ohne Koordinatenrundung mitgeliefert. Unbekannte Codes, ungültige Gebiete und nicht abrufbare CAP-Details führen zu einer nicht verfügbaren Quelle, nicht zu einer Entwarnung. Alle verlinkten CAP-Dokumente werden verarbeitet; parallele Abrufe sind begrenzt. Fehlgeschlagene Abrufe werden nicht als erfolgreiche Cache-Einträge gespeichert.

Der Regionsdatensatz ist ein Snapshot vom 06.10.2025 mit 2.054 EMMA-Gebieten und 758 Aliaszuordnungen (Aliasstand 19.10.2023). Er stammt aus der öffentlichen Verteilung des MeteoAlarm-Geocodes-Datensatzes. Neue bzw. geänderte Regionen benötigen eine aktualisierte Datendatei. Die aktuelle offizielle Metadata-API benötigt Authentifizierung; diese Version fordert keinen API-Key an und behauptet keine laufende automatische Synchronisierung dieser API.

## Nationale Dienste und Sicherheitsmodell

AT-Alert, Alertswiss und BE-Alert verwenden die öffentlich von ihren offiziellen Webseiten eingesetzten Endpunkte. Diese sind keine zugesichert stabilen, versionierten APIs. AT-Alert wird paginiert geladen. Bei Alertswiss wird zusätzlich das Alter des Feed-Heartbeats geprüft. Schemafehler und Ausfälle bleiben sichtbar; erfolgreich gelesene Warnungen anderer Quellen bleiben erhalten. Probe- und Übungsalarme werden ignoriert. BE-Alert wird über seinen aktuellen öffentlichen Feed mit `outdated=false` geladen. Der Feed muss seine Aktualität und den Active-Set-Filter bestätigen; passende Gebiete werden anschließend gegen die vollständigen CAP-Dokumente geprüft. Die amtliche Darstellung kennzeichnet manche Probetexte mit CAP-Status `Actual`, deshalb werden ausdrückliche Test-/Übungsangaben zusätzlich geprüft. Ein fehlendes CAP-Dokument kann keine Entwarnung bestätigen.

Warnungen werden zusammengeführt. Eine harte Lüftungssperre entsteht weiterhin nur aus einer relevanten Schließ-/Lüftungsanweisung, nicht allein aus einer hohen Gefahrenstufe. Die Textauswertung unterstützt Deutsch und Englisch sowie ausgewählte konkrete Schutzanweisungen auf Niederländisch, Französisch und Italienisch. Grundlage sind veröffentlichte amtliche Formulierungen; Negationen und qualifizierte/partielle Entwarnungen werden berücksichtigt. MeteoAlarm bevorzugt vorhandene englische CAP-Informationen. Es gibt keine automatische Übersetzung und keine Garantie, dass jede freie Formulierung dieser Sprachen erkannt wird. Andere Sprachen sind weiterhin nicht abgedeckt. Damit ist diese Version kein vollständiges weltweites NINA-Äquivalent.

Die Warnsensorattribute `warning_provider_coverage` und `warning_provider_error` machen Abdeckung und Fehler sichtbar. Verfügbarkeit und persistente Warnsperren behalten die jeweilige Quelle bei, damit die Entwarnung eines anderen Dienstes keine ausgefallene Quelle ersetzt.

## Installation und Migration

Vorhandene manuelle Wetter-Entities und Warnintegrationen bleiben über die bestehende Migration auf Minor-Version 14 erhalten. Die automatischen Wetterdaten werden intern genutzt; es wird weiterhin keine zusätzliche Home-Assistant-`weather.*`-Entity erzeugt. Lüftungsberechnung und ESP-Protokoll bleiben unverändert.

## Quellen

- DWD MOSMIX-Stationskatalog: https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication
- DWD MOSMIX-Verfahrensbeschreibung: https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_verfahrenbeschreibung_gesamt.pdf?__blob=publicationFile&v=6
- MeteoAlarm: https://meteoalarm.org/en/live/ und https://api.meteoalarm.org/metadata/v1/docs/openapi.yaml
- HA-MeteoAlarm-Dokumentation / Regionsübersicht: https://www.home-assistant.io/integrations/meteoalarm/
- Offizieller BE-Alert-Dienst: https://www.be-alert.be/fr und https://publicalerts.be/CapGateway/
- Offizieller AT-Alert-Dienst: https://warnungen.at-alert.at/
- Offizieller Alertswiss-Dienst: https://www.alert.swiss/
- NWS: https://www.weather.gov/documentation/services-web-alerts
- Natural Earth: https://www.naturalearthdata.com/about/terms-of-use/

## Weitere nationale Adapter – weiterhin offen

Der Zielumfang bleibt die automatische amtliche Bevölkerungsschutzquelle je Land. Diese Version deckt diesen Umfang für DE, AT, CH und BE ab. Sie verkleinert das Ziel nicht auf bloße Wetterwarnungen. Für weitere Länder werden erst verifizierte aktive Meldungen samt Warnfläche und belastbarer Entwarnungssemantik eingebunden.

| Land | Geprüfter Dienst | Stand dieser Version |
| --- | --- | --- |
| Niederlande | NL-Alert / actueel.nl-alert.nl | Die offizielle Website benennt `api.public-warning.app` als Datenquelle. Der Endpunkt lieferte während der Prüfung eine „Site Unavailable“-Seite statt JSON; ein nationaler Adapter wurde deshalb noch nicht aktiviert. MeteoAlarm bleibt aktiv. |
| Frankreich | FR-Alert | Öffentliche Warnhistorie und Schutztexte verifiziert; ein zuverlässiger maschinenlesbarer aktiver Feed samt Warnflächen wurde in dieser Prüfung nicht bestätigt. MeteoAlarm bleibt aktiv. |
| Italien | IT-alert / Protezione Civile | Amtliche Schutztexte verifiziert; kein nationaler aktiver Bevölkerungsschutzfeed in dieser Version integriert. MeteoAlarm bleibt aktiv. |

Sprachregeln begründen für sich allein keine nationale Feed-Abdeckung. Eine vorhandene manuelle Warnintegration kann weiterhin als Ergänzung verwendet werden.

Grundlagen der neuen Textregeln:
- NL-Alert-Nachrichtenbuch: https://www.nl-alert.nl/binaries/nlalert/documenten/richtlijnen/2023/09/01/nl-alert-berichtenboek/Berichtenboek%2Bversie%2Bjuni%2B2023.pdf
- FR-Alert-Beispiel: https://fr-alert.gouv.fr/les-alertes/FR-ALERT.1733392235.90000.0
- Italienischer Zivilschutz: https://rischi.protezionecivile.gov.it/it/industriale/sei-preparato/
- HA-Tracker-Genauigkeit: https://www.home-assistant.io/integrations/device_tracker/
