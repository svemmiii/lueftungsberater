# Changelog

## 0.6.2
- HACS/Hassfest-Korrekturen für die erste Alpha.
- `manifest.json` in Hassfest-Reihenfolge gebracht (`domain`, `name`, danach alphabetisch).
- Config-Subentry-Übersetzungen auf `entry_type` aktualisiert.
- Überflüssige Integrationstitel aus den Custom-Translations entfernt.
- MIT-Lizenz ergänzt.
- Normaler Regen (`regen`) ist jetzt Gelb statt Rot.
- Unwetter-/Gefahrenmodi bleiben unverändert Rot.


## 0.6.1 – erste HACS-Alpha
- Repository für HACS-Custom-Repository vorbereitet.
- Branding unter `custom_components/lueftungsberater/brand/` ergänzt.
- GitHub/HACS-Metadaten auf `svemmiii/lueftungsberater` gesetzt.
- HACS- und Hassfest-Validierung ergänzt.


## 0.6.1
- Keine Änderung an der Entscheidungslogik (`engine.py` unverändert).
- Dashboard-JavaScript wird bei Lovelace im normalen Storage-Modus automatisch als Ressource registriert.
- Vorhandene manuelle Lüftungsberater-Ressourcen werden erkannt und auf die neue versionierte URL aktualisiert statt dupliziert.
- Beide Karten sind für den Home-Assistant-Kartenpicker registriert.
- Raumkarte hat jetzt einen visuellen Editor mit Raum-Auswahl und optionalem Kartennamen.
- Mehrraumübersicht hat jetzt einen visuellen Editor für Titel und Raumauswahl.
- Kein manuelles YAML mehr nötig, um eine Karte hinzuzufügen.
- Picker-Vorschau deaktiviert, damit leere Stub-Konfigurationen den Kartenpicker nicht stören.
- Karten heißen im Picker „Lüftungsberater – Raum“ und „Lüftungsberater – Übersicht“.
- Nur bei ausdrücklich per YAML verwalteten Lovelace-Ressourcen bleibt eine manuelle Resource-Zeile nötig.
- ZIP weiterhin flach gepackt.

## 0.6.0
- Vereinfachte Wetter-/Warndienst-Einrichtung.
