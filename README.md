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

Eigene Außensensoren können bei Bedarf unter den erweiterten Optionen verwendet werden. Werden konfigurierte Außensensoren vorübergehend `unavailable` oder `unknown`, fällt Lüftungsberater für Temperatur und Luftfeuchtigkeit unabhängig voneinander automatisch auf die aktuelle `weather.*`-Entity zurück, sofern der jeweilige Wert dort verfügbar ist.

### 2. Räume hinzufügen

Für jeden Raum können konfiguriert werden:

- Temperatur
- Luftfeuchtigkeit
- optional CO₂
- optional Fenster-/Türkontakte
- optional Thermostat / Climate
- Solltemperatur

Ohne Fensterkontakt arbeitet der Raum rein beobachtend. Mit Fensterkontakt erkennt Lüftungsberater automatisch, wann tatsächlich gelüftet wurde.

## Dashboard

Nach dem Neustart stehen im Kartenpicker zwei Karten zur Verfügung:

### Lüftungsberater – Raum

Detaillierte Ansicht für einen Raum mit Empfehlung, Grund und Messwerten.

### Lüftungsberater – Übersicht

Kompakte Übersicht über mehrere oder alle Räume.

Die Dashboard-Ressource wird bei normalen Home-Assistant-Dashboards automatisch registriert.

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

Lüftungsberater selbst sendet keine eigenen Daten an einen externen Dienst. Die Integration verarbeitet die in Home Assistant vorhandenen Entities lokal. Externe Wetter-/Warndienste können unabhängig davon eigene Cloud-Verbindungen verwenden.

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
