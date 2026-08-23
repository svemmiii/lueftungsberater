<p align="center">
  <img src="custom_components/lueftungsberater/brand/icon@2x.png" width="180" alt="Lüftungsberater">
</p>

# Lüftungsberater

**Alpha-Version für Home Assistant.**

Lüftungsberater bewertet Innen- und Außenbedingungen und gibt für jeden Raum eine verständliche Lüftungsempfehlung aus. Je nach vorhandener Hardware können Temperatur, Luftfeuchtigkeit, CO₂, Fenster-/Türkontakte, Thermostate, Wetterdaten und Warnmeldungen berücksichtigt werden.

> **Status:** frühe Alpha. Die Integration läuft bereits im Alltag, wird aber noch aktiv getestet und weiterentwickelt.

## Funktionen

- Eigene Lüftungsempfehlung pro Raum
- Grün/Gelb/Rot-Status mit konkreter Begründung
  - **Grün:** Lüften ist aktuell sinnvoll
  - **Gelb:** nur eingeschränkt sinnvoll / besser abwarten oder beobachten
  - **Rot:** Lüften ist aktuell klar nicht sinnvoll; Fenster besser geschlossen halten
- Absolute Feuchtigkeit innen/außen
- Optionaler CO₂-Sensor pro Raum
- Automatischer Lüftungsverlauf mit Fenster-/Türkontakt
- Erkennung einer bestätigten Lüftung ab 5 Minuten
- Wetterdienst über eine normale Home-Assistant-`weather.*`-Entity
- Optionale Warn-App / Warndienst
- Erweiterte Unterstützung für DWD und NINA
- Kurzzeit-Failsafe bei CO₂-Sensorausfällen
- Detaillierte Raumkarte
- Kompakte Mehrraumübersicht
- Karten erscheinen im Home-Assistant-Kartenpicker
- Natürliche Oberfläche und Empfehlungen auf Deutsch, Englisch und Türkisch
- Dashboard-Karten folgen der Sprache des aktuell angemeldeten Home-Assistant-Benutzers
- Unterstützung für Celsius- und Fahrenheit-Setups
- Ruhigere Empfehlungen durch Hysterese an normalen CO₂-/Feuchte-/Temperaturgrenzen
- Optionaler Schimmelschutz über einen kalten/kritischen Oberflächentemperatursensor
- Optionale Gefahrenbenachrichtigung bei offenem Fenster/Tür und passenden NINA-/Wetterwarnungen

## Voraussetzungen

- Home Assistant **2026.6.0 oder neuer**
- HACS für die empfohlene Installation
- Mindestens pro Raum:
  - Innentemperatur
  - relative Luftfeuchtigkeit innen
- Ein Wetterdienst mit Außentemperatur und Außenluftfeuchtigkeit

Optional:
- CO₂-Sensor
- Fenster-/Türkontakte
- Climate-/Thermostat-Entity
- Temperatur-Sensor an einer kalten/kritischen Oberfläche für zusätzlichen Schimmelschutz
- Warnintegration wie NINA oder DWD Weather Warnings
- `notify`-Entity für gezielte Warnungen bei offenem Fenster/Tür

## Installation über HACS – Custom Repository

1. HACS öffnen.
2. Oben rechts auf **⋮ → Custom repositories**.
3. Repository eintragen:

   `https://github.com/svemmiii/lueftungsberater`

4. Typ **Integration** auswählen.
5. Repository hinzufügen und **Lüftungsberater** installieren.
6. Home Assistant neu starten.
7. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Lüftungsberater**.

## Einrichtung

### 1. Gemeinsame Außendaten

Beim ersten Einrichten wählst du:

- **Wetterdienst**
- optional **Warn-App / Warndienst**
- optional ein **Benachrichtigungsziel** und die Warnkategorien, bei denen ein offenes Fenster/eine offene Tür gemeldet werden soll

Standardmäßig lösen nur **ernste Außenluftgefahren** (z. B. Brandrauch/Gefahrstoffe) und **schwere Wettergefahren** eine solche Benachrichtigung aus. Vorsorgliche Luft- oder Wetterhinweise können zusätzlich aktiviert werden. Eine rote Empfehlung allein ist ausdrücklich kein Benachrichtigungsauslöser.

Eigene Außensensoren können bei Bedarf unter den erweiterten Optionen verwendet werden. Werden konfigurierte Außensensoren vorübergehend `unavailable` oder `unknown`, fällt Lüftungsberater für Temperatur und Luftfeuchtigkeit unabhängig voneinander automatisch auf die aktuelle `weather.*`-Entity zurück, sofern der jeweilige Wert dort verfügbar ist. Die Raumkarte kennzeichnet einen solchen aktiven Fallback direkt am betroffenen Außenwert mit **Wetterdienst**.

### 2. Räume hinzufügen

Für jeden Raum können konfiguriert werden:

- Temperatur
- Luftfeuchtigkeit
- optional CO₂
- optional Fenster-/Türkontakte
- optional Thermostat / Climate
- optional Temperatur einer kalten/kritischen Oberfläche
- Solltemperatur

Ohne Fensterkontakt arbeitet der Raum rein beobachtend. Mit Fensterkontakt erkennt Lüftungsberater automatisch, wann tatsächlich gelüftet wurde.

Die Sensor-Auswahl wird nach Home-Assistant-Geräteklassen gefiltert: Temperatur, Luftfeuchtigkeit und CO₂ werden nur in den jeweils passenden Sensorfeldern angeboten; bei Fenster-/Türkontakten erscheinen passende Öffnungs-, Fenster-, Tür- und Garagentor-Binary-Sensoren.

### Optionaler Schimmelschutz

Die normale Feuchtebewertung funktioniert weiterhin ohne zusätzliche Hardware. Optional kann pro Raum die Temperatur einer besonders kalten bzw. kritischen Oberfläche angegeben werden, zum Beispiel an einer bekannten Wärmebrücke. Lüftungsberater berechnet aus Raumtemperatur, Raumfeuchte und dieser Oberflächentemperatur die relative Feuchte direkt an der Oberfläche. Ab **80 % relativer Oberflächenfeuchte** wird das Risiko in der Empfehlung berücksichtigt. Der Wert wird bewusst nicht als zusätzliche große Kartenzeile in den Vordergrund gestellt, sondern dient der Entscheidung im Hintergrund.

Der Grenzwert ist bewusst konservativ gewählt: Das Umweltbundesamt beschreibt bei etwa 70–80 % relativer Feuchte an Materialoberflächen bereits mögliche Wachstumsbedingungen; bei rund 80 % sind die Bedingungen für viele innenraumrelevante Schimmelpilze erreicht.

### Wetterwarnungen und Regen

Regen allein ist kein roter Zustand. Normaler Regen und auch der Home-Assistant-Wetterzustand `pouring` werden als Niederschlag behandelt und führen grundsätzlich zu Gelb, sofern kein stärkerer Grund greift.

Bei DWD Weather Warnings berücksichtigt Lüftungsberater die Warnstufe:

- Stufe 1/2 bzw. Vorabinformation → **Gelb / Vorsicht**
- Stufe 3/4 (Unwetter / extremes Unwetter) → **Rot / geschlossen halten**

Damit kann z. B. eine amtliche Starkregenwarnung der Stufe 2 vor dem Lüften warnen, ohne automatisch dieselbe Bewertung wie eine echte Unwetterwarnung zu erhalten.

## Wie die Empfehlung stabil bleibt

Lüftungsberater bewertet weiterhin den tatsächlichen Nutzen des Lüftens statt nur einzelne Grenzwerte. Für normale Grenzbereiche verwendet v0.6.17 zusätzlich kleine Hysteresen: Eine bereits aktive CO₂-Empfehlung wird beispielsweise nicht sofort bei 999 ppm wieder verworfen, und auch Feuchte-/Temperaturentscheidungen erhalten einen kleinen Rücklaufbereich. Dadurch flattert die Karte bei Messrauschen deutlich weniger. Kritisches CO₂ sowie echte Außenluft- und Unwettergefahren umgehen diese Beruhigung und wirken sofort.

Der Hauptsensor bleibt bewusst die zentrale Automation-Schnittstelle. Eine zusätzliche Binary-Entity „Lüften empfohlen“ wird nicht erzeugt, weil die Zustände des Hauptsensors (`open_now`, `keep_open`, `close_now`, `wait` usw.) bereits gezieltere Automationen erlauben.

## Sprache und Einheiten

Lüftungsberater unterstützt aktuell **Deutsch, Englisch und Türkisch**. Empfehlungen werden nicht als kurze technische Meldungen oder wortwörtliche Maschinenübersetzungen erzeugt, sondern für jede Sprache natürlich formuliert. Die Dashboard-Karten richten sich nach der Sprache des jeweils angemeldeten Home-Assistant-Benutzers; Backend-Attribute verwenden die Home-Assistant-Systemsprache. Nicht unterstützte Sprachen fallen aktuell auf Englisch zurück.

Texte von externen Warnanbietern wie DWD oder NINA werden nicht automatisch übersetzt. Lüftungsberater erzeugt daraus eine eigene lokalisierte Begründung und bewahrt den Originaltext zusätzlich im Attribut `original_warning_text` auf.

Temperaturwerte werden intern einheitlich in °C verarbeitet. Anzeige und Eingabe der Fallback-Solltemperatur folgen dem in Home Assistant eingestellten Einheitensystem, sodass auch Fahrenheit-Setups korrekt funktionieren.

## Dashboard

Nach dem Neustart stehen im Kartenpicker zwei Karten zur Verfügung:

### Lüftungsberater – Raum

Detaillierte Ansicht für einen Raum mit Empfehlung, Grund und Messwerten.

### Lüftungsberater – Übersicht

Die Übersicht ist bewusst sehr kompakt: Pro Raum werden nur Name, aktuelle Empfehlung, Statusfarbe und – falls zutreffend – ein kleines **offen**-Badge gezeigt. Ein Tipp auf einen Raum erzeugt erst in diesem Moment eine vollständige Raumkarte in einem Dialog; eine separat eingerichtete Raumkarte ist dafür nicht erforderlich und es laufen keine unsichtbaren Raumkarten im Hintergrund. Der Dialog wird beim Schließen oder beim Verlassen der Dashboard-Ansicht vollständig entfernt, sodass Handy, Tablet und PC jeweils einen rein lokalen Dialogzustand besitzen.

Sind mehrere Lüftungsberater-Instanzen vorhanden, gruppiert dieselbe Übersicht die Räume automatisch nach Instanz. Bei nur einer sichtbaren Instanz wird diese Zwischenebene übersprungen. Im visuellen Karteneditor lassen sich lokale und Tailscale-Remote-Installationen sowie einzelne Räume ein-/ausblenden und per Pfeiltasten sortieren.

Lokale Raumkarten verlinken echte Mess- und Statuswerte weiterhin auf Home Assistants More-Info-/Verlaufsansicht. Ab v0.6.12 gilt das auch für die **CO₂-Bewertung** sowie die **absolute Feuchtedifferenz Δ g/m³**, die dafür einen eigenen Sensor erhält. Ab v0.6.17 öffnet ausschließlich der **farbige Kopf-/Statusbereich** die Lüftungsberater-Hauptentity; Erklärungstexte und die empfohlene Lüftungsdauer sind reine Texte und lösen keine Navigation aus.

Die Dashboard-Ressource wird bei normalen Home-Assistant-Dashboards automatisch registriert.


## Mehrere Instanzen und Tailscale-Remote

Mehrere lokale Lüftungsberater-Instanzen können parallel eingerichtet werden, zum Beispiel für mehrere Wohnungen. Jede Installation verwendet Home Assistants eigene Config-Entry-ID; eine künstliche `unique_id` wird bewusst nicht vergeben, weil lokale Berater manuell wiederholbare Konfigurationen und keine einzelne physische Hardware sind. Die gemeinsame Übersicht gruppiert die Installationen unabhängig voneinander und öffnet die Räume erst nach Auswahl der jeweiligen Instanz.

Zusätzlich kann eine andere Home-Assistant-Installation als **Tailscale-Remote** eingebunden werden. Dafür muss das entfernte Home Assistant Lüftungsberater v0.6.10 oder neuer ausführen und über seine Tailscale-IP oder einen MagicDNS-Namen erreichbar sein. Die Einrichtung verlangt zusätzlich einen gültigen Home-Assistant-Long-Lived-Access-Token. Ab v0.6.12 zeigt Home Assistant während der Prüfung einen Fortschrittsdialog und anschließend eine Zusammenfassung der gefundenen Lüftungsberater und Räume, bevor die Verbindung gespeichert wird.

Für die Übersicht unter **Einstellungen → Geräte & Dienste** spiegelt v0.6.12 die erreichbare Remote-Struktur zusätzlich nur als Geräte-Metadaten: **Remote Home Assistant → Lüftungsberater → Räume**. Dafür werden ausdrücklich keine Remote-Sensor-Entities erzeugt; die entfernten Messwerte bleiben reine flüchtige Snapshots ohne lokalen Recorder-Verlauf.

Remote-Verbindungen sind absichtlich auf Tailscale beschränkt. Beim laufenden Abruf wird erneut geprüft, dass das Ziel ausschließlich auf Tailscale-Adressen auflöst. Zusätzlich akzeptiert der Snapshot-Endpunkt selbst nur Anfragen, deren Quell-IP aus einem Tailscale-Adressbereich stammt. Ein gültiger Home-Assistant-Token allein reicht außerhalb des Tailnets daher nicht aus. Übertragen werden nur die aktuellen Lüftungsberater-Hauptzustände und deren aktuelle Detailwerte – keine Recorder-Historie und keine fremden Sensor-Entities werden im empfangenden Home Assistant angelegt.

Die entfernten Snapshots werden nur im Arbeitsspeicher gehalten und bei neuen Daten ersetzt. Die Remote-Verbindung prüft alle 30 Sekunden. Kurze LTE-/Tailscale-Aussetzer werden toleriert; erst nach ungefähr 3 Minuten ohne erfolgreichen Abruf wird die Instanz als **Nicht erreichbar** angezeigt. Während dieser Karenz bleibt auch eine bereits geöffnete Remote-Raumansicht bestehen. Sobald die Verbindung wieder steht, wird wieder ein aktueller Snapshot geladen. Fehlen dagegen nur notwendige Temperatur-/Feuchtewerte auf der erreichbaren Remote-Instanz, bleibt der Raum sichtbar und zeigt gelb **„Aktuell keine zuverlässige Empfehlung möglich“** statt als offline zu gelten.

In der Remote-Detailansicht sind Messwerte reine Anzeige und nicht anklickbar. Lokale Raumkarten bleiben unverändert: Dort funktionieren More-Info und Recorder-Verlauf weiterhin.

Für eine möglichst enge Netzfreigabe empfiehlt sich zusätzlich eine Tailscale-Grant/ACL-Regel, die vom abfragenden Home-Assistant-Gerät nur TCP-Port 8123 des entfernten Home Assistants erlaubt.

## Unterstützte Wetter- und Warndienste

Grundsätzlich kann jede passende Home-Assistant-`weather.*`-Entity verwendet werden, sofern die benötigten Werte vorhanden sind.

Besonders berücksichtigt werden aktuell:

- DWD Weather
- DWD Weather Warnings
- NINA

Andere Anbieter können über die standardisierten Home-Assistant-Wetterdaten bzw. generische Warnstrukturen teilweise ebenfalls funktionieren.

## Hinweise zur Alpha

Bitte beachte:

- Nicht jede Kombination aus Wetter- und Warnintegration ist bereits getestet.
- Die Entscheidungslogik wird aktuell weiter geprüft.
- Bei ungewöhnlichen Zuständen bitte ein GitHub-Issue mit Home-Assistant-Version, Lüftungsberater-Version und den betroffenen Entity-Zuständen anlegen.

## Datenschutz

Ohne konfigurierte Remote-Verbindung verarbeitet Lüftungsberater die vorhandenen Entities ausschließlich lokal. Wird Tailscale-Remote verwendet, stellt die entfernte Lüftungsberater-Installation nur über eine authentifizierte, auf Tailscale-Quell- und Zieladressen beschränkte Home-Assistant-API aktuelle Raum-Snapshots bereit. Eine Recorder-Historie wird dabei nicht übertragen oder auf der empfangenden Instanz angelegt. Externe Wetter-/Warndienste können unabhängig davon eigene Cloud-Verbindungen verwenden.

## Fehler melden

Issues:

https://github.com/svemmiii/lueftungsberater/issues

## Lizenz

MIT License

## HACS-Alpha und Releases

Die Software ist weiterhin als Alpha gekennzeichnet, die GitHub-Releases für
HACS-Tester werden aber als normale Releases veröffentlicht. Dadurch nutzt HACS
die Versionsnummer des Releases statt den Commit-Hash des Default-Branches.

## Branding in HACS

Home Assistant verwendet das mitgelieferte lokale Brand-Icon nach der Installation.
Die HACS-Oberfläche kann bei Custom Integrations vor der Installation weiterhin
einen Platzhalter anzeigen, obwohl `brand/icon.png` korrekt enthalten ist.


### Hinweis zu v0.6.17

v0.6.17 vereinheitlicht die Klicklogik der Raumkarte, filtert die Sensorauswahl nach passenden Geräteklassen, beruhigt Grenzbereiche mit Hysterese und ergänzt optionalen Schimmelschutz sowie gezielte Warn-Benachrichtigungen bei tatsächlich offenem Fenster/Tür. Die bestehenden Wetter-/Radarwege bleiben bewusst unverändert.

### Hinweis zu v0.6.16

v0.6.16 ist ein kleiner UI-Fix: Die Begründung unter **„Warum diese Empfehlung?“** ist jetzt ausschließlich Text. Sie wird nicht mehr als Verlauf-/More-Info-Link dargestellt und löst beim Antippen keine Navigation aus. Messwerte und echte Statuswerte bleiben weiterhin anklickbar.

### Hinweis zu v0.6.15

v0.6.15 ist ein kleiner Warnquellen-Hotfix. NINA/DWD und andere erkannte Warnanbieter sind im lokalen Einrichtungsdialog wieder auswählbar; der Warndienst bleibt weiterhin optional und `Kein Warndienst` ist der Standard.

### Hinweis zu v0.6.14

v0.6.14 ist ein kleiner Test- und Config-Flow-Hotfix. Er hält die Remote-Erfolgsseite zuverlässig als Bestätigungsdialog offen, macht die NINA-Auswertung robuster gegenüber fehlendem Entity Registry in Test-/Startup-Kontexten und korrigiert den GitHub-Pytest-Workflow.

### Hinweis zu v0.6.13

v0.6.13 behebt einen Fehler im neuen Remote-Fortschrittsdialog von v0.6.12, durch den erfolgreiche Tailscale-Verbindungen nach der Prüfung nicht gespeichert werden konnten. Außerdem wurde der lokale Mehrfach-Setup-Pfad vereinfacht und die automatische Pytest-Prüfung im GitHub-Workflow ausdrücklich aktiviert.
