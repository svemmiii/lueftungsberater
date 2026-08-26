# v0.7.1 – Bugfix-Release

v0.7.1 korrigiert die ersten im praktischen Betrieb gefundenen Probleme der neuen v0.7.0-Funktionen.

## Behoben

- Doppelte Benachrichtigungsoptionen entfernt.
- Amtliche Warnungen und Entwarnungen werden nur noch einmal pro Lüftungsassistent statt einmal pro Raum benachrichtigt.
- Konfigurierbare Nacht-Endzeit wird jetzt auch im Forecast-Pfad verwendet.
- Zusätzlicher Timer entfernt den Nachthinweis exakt zur eingestellten Endzeit.
- `display_mode` wird im Remote-Snapshot wieder übertragen.
- Remote-/Tailscale-Einträge werden beim Update erneut als read-only ohne Raum-Subentries veröffentlicht; die dafür notwendige Minor-Migration läuft jetzt tatsächlich.
- CI verdeckt keine versehentlichen Root-Dateien mehr durch vorheriges Löschen.
- Beim Safety-Lock wird nur noch der farbige Kopfbereich der detaillierten Raumkarte weiß.
- Aktiv remote abgefragte Räume erhalten auch in der detaillierten Raumkarte ein kleines Remote-Symbol.
- `localized_texts` mit allen Sprachen gleichzeitig wurde aus den Raum-Zustandsattributen entfernt; Kartentexte werden pro Benutzer-Sprache bei Bedarf erzeugt und gecacht.
- Seltene Warn-/Remote-Attribute erscheinen nur noch, wenn sie tatsächlich benötigt werden.

## Kompatibilität

Die technische Domain bleibt `lueftungsberater`. Bestehende Config Entries, Räume und Entity-IDs werden nicht umbenannt. v0.7.1 ist als direktes Bugfix-Update für v0.7.0 gedacht.
