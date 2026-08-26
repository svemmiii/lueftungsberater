## v0.7.0 – Lüftungsassistent

v0.7.0 ist ein größeres Funktions- und Architekturupdate. Der sichtbare deutsche Name lautet ab jetzt **Lüftungsassistent**, international **Fresh Air Assistant**; die technische Domain `lueftungsberater` bleibt unverändert, damit bestehende Installationen, Entities und Automationen kompatibel bleiben.

### Highlights
- Amtliche Warnungen werden nicht mehr nach Ereignisart oder Severity „nachbewertet“. Entscheidend ist die konkrete offizielle Schutzanweisung: **Fenster/Türen schließen, Lüftung/Klima abschalten oder Außenluftzufuhr vermeiden = Safety-Lock**.
- Entwarnungen heben die amtliche Sperre auf, bleiben während des aktiven Entwarnungseintrags als Hinweis sichtbar und geben die Bewertung anschließend wieder an die normale Engine zurück. Negierte Formulierungen wie „noch keine Entwarnung“ werden berücksichtigt.
- Nachtlüftung bekommt pro Raum ein frei einstellbares **Von–Bis-Zeitfenster** (Standard 22:00–07:00), inklusive Zeiträumen über Mitternacht und Schichtzeiten.
- Temperaturbedingte Raumstatus-Wechsel erhalten eine robustere Hysterese, die den tatsächlichen Raumbedarf unabhängig vom gleichzeitigen Lüftungsmodus speichert.
- Tailscale-Remote wird granular: Räume werden auf der Quelle freigegeben und auf der Gegenseite bewusst ausgewählt. Neue Räume werden nicht automatisch übernommen.
- Die Quellübersicht zeigt, wenn Räume aktuell remote abgefragt werden; betroffene Räume erhalten ein Remote-Symbol.
- Remote-Hubs sind konsequent read-only und werden nicht mehr als Ziel für lokale Räume angeboten.
- Remote-Protokoll v2 bleibt bei Rolling Upgrades mit v1-Gegenstellen kompatibel.
- Bestehende Karteninformationen bleiben vollständig erhalten; große Advisor-Attribute werden weiterhin nicht vom Recorder historisiert und Remote-Snapshots bleiben auf kartennotwendige aktuelle Daten begrenzt.

### Benachrichtigungen
Standardmäßig bleibt das bisher bewusst zurückhaltende Verhalten erhalten: Warnmeldungen werden handlungsbezogen ausgelöst, wenn ein überwachtes Fenster/eine Tür offen ist oder während einer aktiven Gefahr geöffnet wird. Optional lassen sich zusätzlich ernste amtliche Schutzwarnungen bei bereits geschlossenen Fenstern und Entwarnungen aktivieren. Bei geschlossenen Fenstern sagt die Nachricht ausdrücklich, dass die überwachten Fenster/Türen bereits geschlossen sind.

### Kompatibilität
Die technische Domain, bestehende Entity-IDs und das GitHub-Repository bleiben unverändert. Bestehende Räume erhalten bei der Migration automatisch die bisherige Nacht-Endzeit 07:00 und behalten ihre Remote-Freigabe, damit vorhandene Remote-Setups nicht unerwartet verschwinden. Neu angelegte Räume sind dagegen nicht automatisch remote freigegeben.
