# Amtliche Warnungen und Fenstersicherheit

[← Zur Übersicht](../README.md)

Amtliche Warnungen sind eine zusätzliche Sicherheitsebene neben der normalen Lüftungsberatung. Sie sollen nicht nur eine Ampelfarbe verändern, sondern deutlich machen, **wann ein Fenster aus einem konkreten Schutzgrund geschlossen bleiben soll**.

## Wann entsteht eine harte Sperre?

Eine harte Fenstersperre kann ausgelöst werden, wenn eine **gültige, zum Standort und Zeitpunkt passende amtliche Warnung**

1. eine eindeutige Schutzanweisung enthält, beispielsweise Fenster und Türen geschlossen zu halten oder Außenluftzufuhr zu vermeiden, oder
2. **eindeutig angekündigte Windböen ab 90 km/h** für den betroffenen Standort vorsieht.

Für die zweite Regel beginnt die Sperre bis zu **30 Minuten vor dem angekündigten Böenbeginn**. Ein bekannter späterer Böenbeginn darf nicht einfach durch den früheren allgemeinen Beginn der gesamten CAP-Meldung ersetzt werden.

Die Integration prüft, ob Zahlen und Aussagen tatsächlich **Böen** betreffen – nicht bloß mittleren Wind – und ob Orts-, Höhen- oder Zeiteinschränkungen zum aktuellen Standort passen. Strikte Angaben wie „unter 90 km/h“ sind nicht automatisch 90 km/h. Warntexte mit ausdrücklichen Verneinungen oder widersprüchlichen Aussagen müssen vorsichtig eingeordnet werden.

Ein amtlicher Gefahrenfarbcode allein reicht **nicht** für dieselbe harte Fenstersperre. Die bereits vorhandene Hagelsicherheitsbewertung ist davon unabhängig.

## Und wenn gerade keine amtliche Warnung vorliegt?

Gemessener starker Wind, Böen aus Wetterdaten, Regen oder eine ungünstige Wetterprognose beeinflussen weiterhin die **normale** Empfehlung. Beispielsweise wird ab etwa **50 km/h Dauerwind** beziehungsweise **65 km/h Böen** vorsichtiger bewertet.

**Wichtig:** Selbst eine extreme live gemessene Böe löst in dieser Fassung *ohne passende amtliche Meldung* nicht automatisch denselben absoluten amtlichen Wind-Hardlock aus. Eine starke CO₂-Belastung kann daher im normalen Abwägungspfad weiterhin eine kurze, vorsichtige Lüftungsempfehlung beeinflussen. Wer konkrete Gefahren vor Ort sieht, sollte sich nicht auf die Ampel als Freigabe verlassen.

## Was geschieht bei Störungen oder Entwarnungen?

- Ausbleibende Providerdaten sind **keine bestätigte Entwarnung**.
- Bereits bestätigte amtliche Schutzsperren können bei vorübergehenden Quellenausfällen für eine begrenzte Sicherheitsfrist erhalten bleiben.
- Eine passende, verifizierte Vollentwarnung kann die zugehörige Sperre aufheben. Teilentwarnungen oder eine Entwarnung aus einer anderen Quelle dürfen eine weiterhin geltende Warnung nicht einfach beseitigen.
- Unbekannte Gebiete, widersprüchliche Messwerte und nicht eindeutig zuordenbare Zeiten werden nicht stillschweigend als „alles sicher“ interpretiert.

Warnungsdiagnosen sind auf den Raumkarten sichtbar. Die Attribute `warning_provider_coverage` und `warning_provider_error` helfen dabei, fehlende automatische Abdeckung und Abrufprobleme zu erkennen.

## Welche amtlichen Quellen werden verwendet?

Die automatische Auswahl hängt vom Standort ab:

| Region | Beispiele für automatische Quellen |
| --- | --- |
| Deutschland | NINA, DWD-bezogene Wetterdaten und Warninformationen |
| Österreich | MeteoAlarm und AT-Alert |
| Schweiz | MeteoAlarm und Alertswiss |
| Belgien | MeteoAlarm und BE-Alert |
| USA | NWS-Wetterwarnungen |
| Weitere unterstützte europäische Regionen | MeteoAlarm-Wetterwarnungen, soweit deren räumliche Zuordnung möglich ist |

**Wetterwarnungen sind nicht überall gleichbedeutend mit vollständigem Bevölkerungsschutz.** Für Länder ohne passende automatische amtliche Warnquelle zeigt die Integration diese fehlende Abdeckung an. Du kannst, soweit unterstützt, eine eigene Home-Assistant-Warnintegration ergänzen.

Eine ausführliche Liste von Grenzen und Quellen steht in [PROVIDER_COVERAGE.md](../PROVIDER_COVERAGE.md).

## CAP und Sprachen

CAP (*Common Alerting Protocol*) ist ein verbreitetes Format amtlicher Warnungen. Solche Meldungen können strukturierte Felder, mehrere Sprachfassungen, Zeiträume und Gebiete enthalten.

Der Lüftungsassistent trennt die **Oberflächensprache** von der **Warnsprache**. Die Oberfläche bietet Deutsch, Englisch und Türkisch. Für amtliche Warntexte gibt es dafür eigene Parser-Einstiege; weitere Sprachen werden für ausgewählte Formulierungen unterstützt. Strukturierte, anbieterspezifische CAP-Werte können unabhängig vom Freitext verarbeitet werden, sofern Parametername, Einheit und Geltungsbereich zuverlässig erkannt werden.

Eine zusätzliche UI-Übersetzung bedeutet **nicht**, dass damit automatisch alle freien Wetterwarntexte dieser Sprache sicher verstanden werden. Originalmeldungen bleiben zur Kontrolle einsehbar. Es findet keine automatische Vollübersetzung amtlicher Warntexte statt.

## Benachrichtigungen bei Gefahr

Warn- und Entwarnungshinweise können über eine eingerichtete `notify`-Entity verschickt werden. Bei schweren Gefahren ist insbesondere ein vorhandener offener Fenster-/Türkontakt relevant; die verfügbaren Meldungsarten sind konfigurierbar. Eine rote Ampel bedeutet nicht automatisch, dass eine Push-Nachricht verschickt wird.

[← Zur Übersicht](../README.md)
