# Historienkarte und Recorder

[← Zur Übersicht](../README.md)

Mit der Historienkarte kannst du nachvollziehen, wie sich das Raumklima entwickelt hat und welche Empfehlung der Lüftungsassistent zum jeweiligen Zeitpunkt angezeigt hat.

## Karte hinzufügen

Wähle im Dashboard die Historienkarte im Kartenpicker oder lege eine manuelle Karte an:

```yaml
type: custom:lueftungsberater-history-card
entity: sensor.dein_lueftungsassistent_raum
hours: 24
metrics:
  - co2_in
  - co2_out
  - humidity_in
  - pm25_out
colors:
  co2_in: "#3c90df"
  humidity_in: "#2eaa8b"
perspective: room_air
```

Ersetze `sensor.dein_lueftungsassistent_raum` durch die **tatsächliche Haupt-Entity** deines Raums. Wähle unter `metrics` nur Größen, die für diesen Raum vorhanden beziehungsweise sinnvoll eingerichtet sind. Im visuellen Editor lassen sich Messgrößen, Zeitbereiche und Kurvenfarben auswählen.

## Was wird dargestellt?

- Verfügbare Rohmesswerte aus Home Assistants Recorder
- Auf Wunsch aufgezeichnete, zusätzliche Sensorhistorien ab dem Zeitpunkt der Aktivierung
- Frühere Empfehlungen, sofern sie damals tatsächlich gespeichert wurden
- Farbige Qualitätszonen anhand der für die jeweilige Messgröße aktuell verwendeten Bewertungsgrenzen

Der Diagramm-Cursor zeigt Werte am gewählten Zeitpunkt. Er berechnet die damalige Lüftungsempfehlung nicht im Nachhinein neu. Fehlende alte Messpunkte oder Ampelfarben werden nicht erfunden.

## Erste Aktivierung und Berechtigungen

Falls für eine gewünschte Messgröße noch keine eigene Historie existiert, kann die erstmalige Aktivierung einer Aufzeichnung **Administratorrechte** erfordern, da zusätzliche Entities angelegt werden. Bereits aktivierte Historien lassen sich auch von normalen berechtigten Benutzern ansehen.

## Aufbewahrung und Datenhygiene

Der Lüftungsassistent hält den Recorder bewusst schlank. Hauptempfehlung, Innen-Absolutfeuchte, letzte bestätigte Lüftung und harte Gefahrenanzeige haben integrationsseitig eine begrenzte Aufbewahrung von höchstens **20 Tagen**. Einige zusätzliche, abgeleitete Status-Entities werden bei neuen Installationen standardmäßig deaktiviert oder ihr Recorder-Verlauf wird durch die tägliche Wartung entfernt.

Für die Historienkarte zusätzlich aktivierte Sensoraufzeichnungen und vorhandene Originalsensoren gelten deren tatsächliche Speicherwege sowie die jeweils wirksamen Home-Assistant-Recorder-Regeln und Langzeitstatistiken. Deshalb lässt sich **keine pauschale Aufbewahrungsdauer für jede Kurve** garantieren.

Bei älteren Installationen können noch überholte Hilfssensoren aus einer früheren Aufzeichnungsvariante vorhanden sein. Entferne einen solchen alten Sensor erst, nachdem du geprüft hast, dass die neue Kurve funktioniert und keine eigenen Dashboards oder Automationen mehr darauf verweisen.

[← Zur Übersicht](../README.md)
