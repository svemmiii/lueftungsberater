# Changelog

## 0.6.5
- HACS-Mindestversion von Home Assistant auf 2026.6.0 gesenkt.
- Damit ist die Alpha auf Home Assistant 2026.6.x installierbar.
- Keine Änderung an Entscheidungslogik, Sensoren oder Dashboard-Karten.
- Ältere Versionen bis mindestens 2026.3 sind technisch vielversprechend,
  werden aber noch nicht offiziell als unterstützt markiert.


## 0.6.4
- Manifest-Typ von `helper` auf `hub` geändert.
- Dadurch erscheint Lüftungsberater als normale Integration unter
  Einstellungen → Geräte & Dienste → Integrationen und nicht mehr im Helfer-Bereich.
- Keine Änderung an der Entscheidungslogik gegenüber v0.6.3.
- Für HACS-Alpha-Tester sollte dieses Release als normales GitHub-Release
  veröffentlicht werden (nicht als GitHub Pre-release), damit HACS keine
  Commit-ID als vermeintlich neuere Version anzeigt.


## 0.6.3
- Hassfest: `config_subentries.room.initiate_flow` für Hinzufügen und Konfigurieren ergänzt.
- Keine weitere Änderung an der Lüftungslogik gegenüber v0.6.2.


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
