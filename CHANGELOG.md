# Änderungen

Hier stehen die **zusammengefassten Änderungen pro Version**, nicht einzelne interne Testläufe oder unfertige Zwischenstände. Für ältere tatsächlich veröffentlichte Fassungen ist die [GitHub-Releaseübersicht](https://github.com/svemmiii/lueftungsberater/releases) die maßgebliche Quelle.

## v0.11.9

### Automatische Datenquellen und weniger unnötige Abrufe

- Gemeinsame, verteilte HTTP-Abrufe für Wetter, Luftqualität und Warnungen mit begrenzter Parallelität.
- Standortbezogene Stationsauswahl: verfügbare, frische DWD- und UBA-Messwerte werden je Messgröße bevorzugt; fehlende Daten können aus geeigneten Modellen ergänzt werden.
- Dringliche Warnungsabrufe werden bei freier Kapazität bevorzugt, ohne das übrige Abrufsystem grundsätzlich zu umgehen.

### Amtliche Warnungen und Sicherheit

- Mehrsprachige CAP-Informationsblöcke bleiben mit ihren eigenen Zeit-, Gebiets- und Herkunftsangaben erhalten.
- Strukturierte Böenwerte unterstützter Anbieter werden unabhängig davon geprüft, ob der begleitende Freitext sprachlich erkannt wird.
- Für eindeutig zugeordnete amtliche Böen ab **90 km/h** kann eine Fenstersperre **30 Minuten vor dem erwarteten Beginn** greifen.
- Angaben zu Einheiten, strikt offenen Geschwindigkeitsgrenzen, Orten, Höhen und einzelnen Zeitfenstern werden differenzierter behandelt; verneinte oder widersprüchliche Aussagen werden nicht einfach gleichgesetzt.
- Die Warntextverarbeitung besitzt getrennte Spracheinstiege für Deutsch, Englisch und Türkisch; weitere unterstützte Textsprachen werden separat verwaltet.
- Bestätigte Schutzsperren werden bei bloßen Provider-Ausfällen nicht automatisch als entwarnt behandelt.

### Home Assistant und Darstellung

- Zeitzonenauflösung in asynchronen Abläufen so angepasst, dass neue Zeitzonen nicht direkt auf dem Event-Loop-Thread von der Festplatte geladen werden müssen.
- Vorhandene Raumkonfigurationen und Sensorzuordnungen werden bei einem normalen Update weiterverwendet; die Oberfläche und der HTTP-Planer bleiben in ihren bisherigen Aufgabenbereichen erhalten.
- Zusätzliche Regressionstests für Warnungen, Zeitangaben und die Zusammenarbeit mit der Sicherheitslogik.

### Wichtige Grenzen

- Es handelt sich weiterhin um eine **Alpha-Version**. Nicht jeder Standort besitzt automatische amtliche Warnabdeckung.
- Sehr starke **gemessene** Böen ohne passende amtliche Warnung sind nicht automatisch derselbe Hardlock wie eine amtliche Windwarnung.
- Für ein produktives Update empfiehlt sich ein Home-Assistant-Backup.

Ausführliche aktuelle Bedien- und Sicherheitshinweise stehen unter [Dokumentation](README.md#dokumentation).

---

**Frühere Veröffentlichungen:** [GitHub Releases](https://github.com/svemmiii/lueftungsberater/releases). Die früheren, nicht veröffentlichten internen Testzwischenstände werden hier bewusst nicht als eigene Versionen aufgeführt.
