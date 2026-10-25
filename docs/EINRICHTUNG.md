# Installation und Einrichtung

[← Zur Übersicht](../README.md)

## Voraussetzungen

- Home Assistant **2026.6.0 oder neuer**
- Für jeden Raum ein Sensor für **Innentemperatur** und **relative Luftfeuchtigkeit**
- Optional HACS (empfohlener Installationsweg), CO₂-Sensor, Fenster-/Türkontakte, Thermostat, Oberflächentemperatur- und weitere Luftsensoren

Ein separater Wetterdienst oder eine Warnintegration ist für den Standardstart nicht nötig, sofern für deinen Standort automatische Quellen unterstützt werden. Außerhalb der abgedeckten Warnregionen funktioniert die normale Lüftungsberatung trotzdem weiter.

## Installation mit HACS

1. Öffne HACS.
2. Wähle **⋮ → Custom repositories**.
3. Trage `https://github.com/svemmiii/lueftungsberater` ein und wähle **Integration**.
4. Installiere Lüftungsassistent und starte Home Assistant neu.
5. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen → Lüftungsassistent**.

Falls HACS vor der Installation kein eigenes Symbol anzeigt, kann das ein Darstellungsproblem sein. Die Integration bringt eigene lokale Branding-Dateien mit.

## Ersten Assistenten einrichten

Beim Anlegen der lokalen Installation legst du zunächst die gemeinsamen Einstellungen fest:

- **Wetterquelle:** `Automatisch` oder eine eigene Home-Assistant-`weather.*`-Entity.
- **Warnquelle:** `Automatisch`, eine eigene Warnintegration oder – wo angeboten – die Kombination aus beidem.
- **Ampel:** Lüftungsbedarf oder Lüftungsampel. Die Entscheidung selbst ist für beide identisch; nur die Blickrichtung der Anzeige ändert sich.
- **Zusätzliche Außensensoren:** Beispielsweise Temperatur, Feuchte, Schadstoffe oder CO₂ direkt am Gebäude.
- **Benachrichtigungen:** Optional eine `notify`-Entity und die gewünschten Ereignisse.

Wenn ein eigener Außensensor ausfällt, kann für einzelne Werte eine gültige Wetterquelle einspringen. Die Raumkarte kennzeichnet diesen Fallback am jeweiligen Wert.

## Räume hinzufügen

Lege anschließend pro Raum die benötigten Innen-Sensoren fest. Optional kannst du einen bestehenden **Home-Assistant-Bereich**, einen eigenen Raumnamen, CO₂, Fenster-/Türkontakte, ein Thermostat, eine Solltemperatur und einen Oberflächentemperatursensor ergänzen.

Die Einstellungen sind im Einrichtungsdialog thematisch unterteilt, etwa in **Raumklima**, **Nachtlüftung**, **Zusatzsensoren** und **Fenster & Türen**. Ohne Fensterkontakt ist keine automatische Erkennung einer tatsächlich durchgeführten Lüftung möglich; Empfehlungen funktionieren trotzdem.

Bei einem Sensor an einer besonders kalten Wand- oder Fensteroberfläche kann der Assistent die Feuchte an dieser *gemessenen* Oberfläche zusätzlich bewerten. Ohne solchen Sensor wird keine Oberflächentemperatur geschätzt. Die Anzeige ist eine Beratungshilfe, keine Schimmeldiagnose.

## Standort und automatische Quellen

Standardmäßig wird der Standort von Home Assistant verwendet. Stattdessen kannst du eine feste `zone.*`-Entity oder einen mobilen `device_tracker.*` auswählen. Das ist insbesondere für mobile Installationen sinnvoll.

**Bei mobilen Trackern:** Eine Positionsmeldung soll höchstens fünf Minuten alt sein. Eine bereits gültige Position kann bei einem kurzen Ausfall insgesamt bis zu 30 Minuten seit der letzten gültigen Meldung gehalten werden. Danach pausieren die automatischen standortgebundenen Quellen, statt unbemerkt auf den Heimstandort zu springen. Sofern `gps_accuracy` gemeldet wird, werden ungenaue Werte über 250 m nicht als neue verlässliche Position akzeptiert.

Die tatsächliche Abdeckung der Wetter- und Warnquellen findest du in [PROVIDER_COVERAGE.md](../PROVIDER_COVERAGE.md).

## Benachrichtigungen

Für Mitteilungen wird eine konfigurierte Home-Assistant-`notify`-Entity über `notify.send_message` verwendet. Du kannst schwere Wetter- und Außenluftgefahren melden lassen, wenn ein hinterlegter Kontakt tatsächlich offen ist. Optional sind vorsorgliche Hinweise sowie Meldungen wie „Lüften ist wieder sinnvoll“ oder „Lüften kann beendet werden“ möglich.

Die Anzeige einer roten Lüftungsempfehlung allein löst nicht automatisch eine Meldung aus. Lautstärke, Vibration und Zustellpriorität hängen vom gewählten Notify-Ziel ab.

## Bereits installierte Version aktualisieren

1. Erstelle ein **Home-Assistant-Backup**.
2. Aktualisiere die Integration über HACS beziehungsweise ersetze die Integrationsdateien entsprechend deiner Installationsart.
3. **Entferne nicht erst die vorhandene Integration:** Dadurch könntest du bestehende Zuordnungen verlieren.
4. Starte Home Assistant neu.
5. Kontrolliere Räume, Sensorquellen, Dashboard-Karten und das Protokoll.

Falls HACS noch denselben Versionsstand anzeigt, prüfe, ob im Repository bereits ein tatsächlich neuer Release-Tag veröffentlicht wurde.

## Gut zu wissen

Im globalen Home-Assistant-Dialog für „Raum hinzufügen“ können unter Umständen auch Remote-Instanzen angeboten werden. Ein lokaler Raum lässt sich dort dennoch nicht an einen Remote-Hub anhängen; die Integration lehnt das ab. Verwende dafür einen lokalen Assistenten.

[← Zur Übersicht](../README.md)
