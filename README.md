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
- Warnintegration wie NINA oder DWD Weather Warnings

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

Eigene Außensensoren können bei Bedarf unter den erweiterten Optionen verwendet werden. Werden konfigurierte Außensensoren vorübergehend `unavailable` oder `unknown`, fällt Lüftungsberater für Temperatur und Luftfeuchtigkeit unabhängig voneinander automatisch auf die aktuelle `weather.*`-Entity zurück, sofern der jeweilige Wert dort verfügbar ist. Die Raumkarte kennzeichnet einen solchen aktiven Fallback direkt am betroffenen Außenwert mit **Wetterdienst**.

### 2. Räume hinzufügen

Für jeden Raum können konfiguriert werden:

- Temperatur
- Luftfeuchtigkeit
- optional CO₂
- optional Fenster-/Türkontakte
- optional Thermostat / Climate
- Solltemperatur

Ohne Fensterkontakt arbeitet der Raum rein beobachtend. Mit Fensterkontakt erkennt Lüftungsberater automatisch, wann tatsächlich gelüftet wurde.

### Wetterwarnungen und Regen

Regen allein ist kein roter Zustand. Normaler Regen und auch der Home-Assistant-Wetterzustand `pouring` werden als Niederschlag behandelt und führen grundsätzlich zu Gelb, sofern kein stärkerer Grund greift.

Bei DWD Weather Warnings berücksichtigt Lüftungsberater die Warnstufe:

- Stufe 1/2 bzw. Vorabinformation → **Gelb / Vorsicht**
- Stufe 3/4 (Unwetter / extremes Unwetter) → **Rot / geschlossen halten**

Damit kann z. B. eine amtliche Starkregenwarnung der Stufe 2 vor dem Lüften warnen, ohne automatisch dieselbe Bewertung wie eine echte Unwetterwarnung zu erhalten.

## Sprache und Einheiten

Lüftungsberater unterstützt aktuell **Deutsch, Englisch und Türkisch**. Empfehlungen werden nicht als kurze technische Meldungen oder wortwörtliche Maschinenübersetzungen erzeugt, sondern für jede Sprache natürlich formuliert. Die Dashboard-Karten richten sich nach der Sprache des jeweils angemeldeten Home-Assistant-Benutzers; Backend-Attribute verwenden die Home-Assistant-Systemsprache. Nicht unterstützte Sprachen fallen aktuell auf Englisch zurück.

Texte von externen Warnanbietern wie DWD oder NINA werden nicht automatisch übersetzt. Lüftungsberater erzeugt daraus eine eigene lokalisierte Begründung und bewahrt den Originaltext zusätzlich im Attribut `original_warning_text` auf.

Temperaturwerte werden intern einheitlich in °C verarbeitet. Anzeige und Eingabe der Fallback-Solltemperatur folgen dem in Home Assistant eingestellten Einheitensystem, sodass auch Fahrenheit-Setups korrekt funktionieren.

## Dashboard

Nach dem Neustart stehen im Kartenpicker zwei Karten zur Verfügung:

### Lüftungsberater – Raum

Detaillierte Ansicht für einen Raum mit Empfehlung, Grund und Messwerten.

### Lüftungsberater – Übersicht

Die Übersicht ist bewusst sehr kompakt: Pro Raum werden nur Name, aktuelle Empfehlung, Statusfarbe und – falls zutreffend – ein kleines **offen**-Badge gezeigt. Ein Tipp auf einen Raum erzeugt erst in diesem Moment eine vollständige Raumkarte in einem Dialog; eine separat eingerichtete Raumkarte ist dafür nicht erforderlich und es laufen keine unsichtbaren Raumkarten im Hintergrund.

Sind mehrere lokale Lüftungsberater-Instanzen vorhanden, gruppiert dieselbe Übersicht die Räume automatisch nach Instanz. Bei nur einer Instanz wird diese Zwischenebene übersprungen.

Die Dashboard-Ressource wird bei normalen Home-Assistant-Dashboards automatisch registriert.


## Mehrere Instanzen und Tailscale-Remote

Ab v0.6.10 können mehrere lokale Lüftungsberater-Instanzen parallel eingerichtet werden, zum Beispiel für mehrere Wohnungen. Die gemeinsame Übersicht gruppiert sie automatisch und öffnet die Räume erst nach Auswahl der jeweiligen Instanz.

Zusätzlich kann eine andere Home-Assistant-Installation als **Tailscale-Remote** eingebunden werden. Dafür muss das entfernte Home Assistant ebenfalls Lüftungsberater v0.6.10 oder neuer ausführen und über seine Tailscale-IP oder einen MagicDNS-Namen erreichbar sein. Die Einrichtung verlangt zusätzlich einen gültigen Home-Assistant-Long-Lived-Access-Token.

Remote-Verbindungen sind absichtlich auf Tailscale beschränkt. Beim laufenden Abruf wird erneut geprüft, dass das Ziel ausschließlich auf Tailscale-Adressen auflöst. Zusätzlich akzeptiert der Snapshot-Endpunkt selbst nur Anfragen, deren Quell-IP aus einem Tailscale-Adressbereich stammt. Ein gültiger Home-Assistant-Token allein reicht außerhalb des Tailnets daher nicht aus. Übertragen werden nur die aktuellen Lüftungsberater-Hauptzustände und deren aktuelle Detailwerte – keine Recorder-Historie und keine fremden Sensor-Entities werden im empfangenden Home Assistant angelegt.

Die entfernten Snapshots werden nur im Arbeitsspeicher gehalten und bei neuen Daten ersetzt. Die Remote-Verbindung prüft alle 30 Sekunden. Kurze LTE-/Tailscale-Aussetzer werden toleriert; erst nach ungefähr 3 Minuten ohne erfolgreichen Abruf wird die Instanz als **Nicht erreichbar** angezeigt. Sobald die Verbindung wieder steht, wird wieder ein aktueller Snapshot geladen.

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
