# TEST COMPLETE(11) – Prüfbericht

Prüfdatum: 02.10.2026. Integration bleibt 0.11.0; bestehende Migration bleibt Minor-Version 14.

| Umgebung / Prüfung | Ergebnis |
| --- | --- |
| Python 3.14.7, HA 2026.10.0b0, pytest-homeassistant-custom-component 0.13.368 | 730 Tests bestanden, 11,99 s |
| Python 3.14.7, HA 2026.6.0, pytest-homeassistant-custom-component 0.13.336 | 730 Tests bestanden, 10,11 s |
| Gezielte GPS-/Sprach-/BE-Alert-/Provider-/Sicherheitsprüfungen | 212 Tests bestanden, 3,67 s |
| Ruff F,E9 | Bestanden |
| Python compileall | Bestanden |
| Frontend-Cache-Test | Bestanden |

## Neue Prüfungen

- `gps_accuracy` in Metern: 0, Dezimalwerte und Grenzwert 250 m werden akzeptiert; größere Werte, negative Werte, NaN/Infinity, ungültige Texte, null und boolesche Angaben werden verworfen. Fehlende optionale Genauigkeit bleibt kompatibel.
- Grenzfall Eupen (BE) → Aachen (DE): Wiederholte brandneue Meldungen mit 3.000 m Unsicherheit ändern die gehaltene Position und ihren Meldungszeitpunkt nicht. Nach 31 Minuten ist sie nicht mehr verfügbar; eine neue genaue Meldung erlaubt den Wechsel. Neustart nur mit ungenauem GPS erzeugt keine akzeptierte Position.
- Amtliche NL/FR/IT-Schließ-/Lüftungsformeln erzeugen eine harte Sperre. Negationen, Öffnungsfreigaben, bloße Gefahrstexte und Teilentwarnungen werden getrennt geprüft. Vollständige Entwarnungen und CAP Cancel können kopierte alte Schutzanweisungen aufheben.
- BE-Alert: aktueller Feed, Datum, Punktzuordnung und Lebensdauer; ungültige Gebiete und unvollständige CAP-Abrufe führen zu UNKNOWN; ausgefallene Details werden erneut angefragt. Probeangaben werden auch bei CAP-Status Actual gefiltert. Meldungen mit ausdrücklich „kein Test“ bleiben erhalten. MeteoAlarm kann einen ausgefallenen BE-Alert-Dienst nicht entwarnen.
- Alle bisherigen Tests einschließlich DWD-Grad/Minuten, EMMA_ID, GPS-Meldungsalter, Migration, Quellenzusammenführung und Deutschland → Belgien → Deutschland bleiben aktiv. Kein Test entfernt oder übersprungen.

## Online-Prüfung

Die offizielle BE-Alert-Website verlinkt den öffentlichen Gateway. Dessen eigener JavaScript-Client ruft `feed?outdated=false` ab und verarbeitet `items` und die publizierten Polygonkoordinaten. Der Adapter verwendet diese amtliche Datenquelle; bei einem passenden Gebiet prüft er zusätzlich das vollständige CAP-Dokument.

Der aktive BE-Alert-Feed wurde am 02.10.2026 um 20:56 Uhr MESZ erneut direkt abgerufen: aktueller `pubDate`, 0 aktive Datensätze, 0 Fehler bei der Gebiets-/Zeitprüfung. Eine archivierte amtliche CAP-Testmeldung wurde separat gelesen: Status Actual und Event Test LB-SMS. Diese Beobachtung begründet die zusätzliche Probe-Erkennung. Sie ersetzt keinen Live-Test eines echten gegenwärtigen Gefahrenereignisses.

Für Sprachregeln wurden amtliche NL-Alert-Nachrichtenvorlagen, FR-Alert-Schutztexte und italienische Protezione-Civile-Anweisungen herangezogen. Die URLs stehen in PROVIDER_COVERAGE.md.

## Noch offene Grenzen

Kein Test auf dem tatsächlichen Home-Assistant-System oder mit dem physischen GPS-/ESP-Gerät des Nutzers. Die 250-m-Grenze ist eine konservative Integrationsentscheidung. Kartographische Ländergrenzen und Tracker ohne echte Positionszeit oder ohne Genauigkeitsangabe besitzen weiterhin die dokumentierten Grenzen.

Automatischer nationaler Bevölkerungsschutz ist für DE, AT, CH und BE integriert. Das ursprüngliche Ziel einer weitergehenden internationalen Abdeckung bleibt offen. NL-Alert wurde recherchiert, aber sein von der offiziellen Website benannter Datenendpunkt lieferte hier keine prüfbare JSON-Antwort. Für FR und IT wurden keine nationalen aktiven Adapter aktiviert. Diese Länder behalten MeteoAlarm. Sprachregeln sind eine begrenzte Erkennung konkreter Formulierungen, keine Übersetzung beliebiger amtlicher Texte. Es wird weiterhin keine neue HA-weather-Entity erzeugt.

Paket, aktueller Changelog-Eintrag, Abdeckungsübersicht und dieser Bericht führen COMPLETE(11). Frühere COMPLETE(10)-Changelog-Einträge bleiben als Versionsgeschichte erhalten. ESP-Vertrag, Firmware, Lüftungsberechnung und bestehende Konfigurationsmigration wurden in diesem Schritt nicht geändert.
