# Häufige Fragen und Fehlersuche

[← Zur Übersicht](../README.md)

## Die Integration erscheint nicht im Einrichtungsdialog

Prüfe zuerst, ob Home Assistant die unterstützte Mindestversion erfüllt und ob Lüftungsassistent in HACS tatsächlich installiert wurde. Starte Home Assistant nach der Installation neu. Unter **Einstellungen → System → Protokolle** findest du Hinweise, falls die Integration beim Start nicht geladen werden konnte.

## Ich sehe keine automatischen amtlichen Warnungen

Eine automatische Warnquelle ist nur dort verfügbar, wo der jeweilige Provider unterstützt wird. Das bedeutet nicht, dass es für jeden Standort einen vollständigen nationalen Bevölkerungsschutzfeed gibt. Prüfe den aktiven Standort, die Warnquelleneinstellung und die Diagnoseattribute `warning_provider_coverage` und `warning_provider_error`. Mehr dazu in [Warnungen](WARNUNGEN.md) und [Anbieterabdeckung](../PROVIDER_COVERAGE.md).

## Die Wetterdaten wirken alt oder fehlen

Prüfe, ob die ausgewählte Wetterquelle verfügbar ist und ob ein eigener Außensensor gerade `unknown` oder `unavailable` meldet. Bei automatisch bestimmten Quellen kann auch der Standort fehlen. Mobile Tracker brauchen regelmäßige aktuelle Positionsmeldungen; nach längeren Ausfällen pausieren standortgebundene Abrufe, statt einfach den Home-Standort zu verwenden. Eine unveränderte feste Zone (`zone.*`) benötigt dagegen keine regelmäßige GPS-Aktualisierung. Wenn trotzdem wiederholt alle Außenwerte ausfallen, prüfe in den Diagnoseattributen die Anbieterfehler und ob die ausgewählte Zone verfügbar ist.

## Eine harte Fenstersperre bleibt nach einer Warnung sichtbar

Eine fehlende oder vorübergehend ausgefallene Warnquelle ist nicht automatisch eine Entwarnung. Der Assistent kann bestätigte Schutzlagen zeitlich begrenzt erhalten, um eine Warnung nicht durch einen bloßen Netzfehler aufzuheben. Prüfe Warnungsquelle, Gültigkeit, aktiven Sperrgrund und die Quelle einer gemeldeten Entwarnung.

## Meine Messwerte werden angezeigt, aber die Karte empfiehlt nichts

Ein Sensor kann zwar vorhanden, aber zu alt oder für eine Entscheidung unplausibel sein. Prüfe insbesondere Innentemperatur, Innenfeuchte und mögliche `unavailable`-Zustände. Die Detailansicht der Raumkarte zeigt zusätzliche Diagnosehinweise.

## Eine neue Karte oder Änderung erscheint nicht

Starte nach einem Integrationsupdate Home Assistant neu und lade die Dashboard-Seite vollständig neu. Die Auswahl zwischen kompakter und ausgeklappter Raumkarte bleibt **pro Gerät/Browser** gespeichert, sodass zwei Geräte unterschiedlich aussehen können.

## Kann ich vorhandene Räume nach einem Update behalten?

Ja, für normale Updates solltest du die Integration **nicht löschen**, sondern aktualisieren. Ein Backup ist trotzdem sinnvoll. Prüfe nach dem Neustart die Sensorzuordnungen und deine Dashboard-Karten.

## Wo melde ich einen Fehler?

Im [GitHub-Issue-Tracker](https://github.com/svemmiii/lueftungsberater/issues). Hilfreich sind:

- Home-Assistant- und Lüftungsassistent-Version
- Eine kurze Beschreibung des erwarteten und des tatsächlichen Verhaltens
- Betroffene Entitäten mit ihren **nicht sensiblen** Zuständen
- Relevante Protokollmeldungen und Schritte zum Nachstellen

**Bitte vorher private Daten entfernen:** Zugangstoken, genaue GPS-Positionen, persönliche Adressen und andere vertrauliche Angaben gehören nicht in ein öffentliches Issue.

[← Zur Übersicht](../README.md)
