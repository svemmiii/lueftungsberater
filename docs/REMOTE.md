# Zweites Home Assistant über Tailscale einbinden

[← Zur Übersicht](../README.md)

Du kannst mehrere **lokale** Lüftungsassistent-Installationen verwenden oder die aktuellen Räume einer weiteren Home-Assistant-Installation über **Tailscale** anzeigen lassen.

## Voraussetzungen

- Beide Home-Assistant-Installationen sind über Tailscale verbunden.
- Die entfernte Installation ist über eine Tailscale-IP oder einen passenden MagicDNS-Namen erreichbar.
- Für die Verbindung wird ein gültiger **Long-Lived-Access-Token eines Home-Assistant-Administrators** der entfernten Installation benötigt.
- Die gewünschten Räume sind auf der Quellinstallation ausdrücklich für Remote-Abfragen freigegeben.

Für die vollständige aktuelle Remote-Anzeige ist es am sinnvollsten, **beide Installationen auf derselben Lüftungsassistent-Version** zu betreiben. Ältere Snapshot-Protokolle werden nur soweit unterstützt, wie ihre Felder eindeutig verstanden werden können.

## Einrichtung

1. Richte den Lüftungsassistenten zunächst normal auf beiden Home-Assistant-Installationen ein.
2. Stelle sicher, dass die Tailscale-Verbindung funktioniert.
3. Erzeuge auf der entfernten Instanz einen geeigneten langlebigen Administrator-Token und behandle ihn wie ein Passwort.
4. Gib auf der Quellinstallation die Räume frei, die von anderen Instanzen gelesen werden dürfen.
5. Füge auf der empfangenden Installation eine **Tailscale-Remote** hinzu und wähle nur die gewünschten Räume aus.
6. Prüfe anschließend die Remote-Übersicht und die Verbindungsdiagnose.

Neue Räume werden nicht ungefragt übernommen. Sie müssen auf der Quellseite freigegeben und auf der empfangenden Seite bewusst ausgewählt werden.

## Sicherheit und Datenschutz

Die Remote-Verbindung akzeptiert nur die vorgesehenen Tailscale-Adressbereiche. Der Client prüft die Zieladressen vor dem Abruf und bindet die Verbindung an die geprüfte Adresse; die Gegenseite verlangt authentifizierte Home-Assistant-**Administratorrechte**. Diese Regeln ergänzen sich, ersetzen aber nicht die Sicherheit deines Tailscale-Netzes und Tokens.

Übertragen werden **aktuelle Zustände und Detailwerte**, keine vollständigen Recorder-Historien. Auf der empfangenden Installation werden keine gespiegelten Messsensoren samt eigener Recorder-Datenbank angelegt.

Für eine besonders enge Freigabe kannst du in Tailscale zusätzlich eine Regel einrichten, die zwischen den beiden beteiligten Geräten nur **TCP 8123** erlaubt.

## Was passiert bei Verbindungsproblemen?

Die Remote-Verbindung prüft ungefähr alle **30 Sekunden** auf neue Daten. Kurze Aussetzer werden abgefangen; nach ungefähr **drei Minuten** ohne erfolgreichen Abruf wird die Instanz als nicht erreichbar gekennzeichnet. Wird die Verbindung wiederhergestellt, erscheinen wieder aktuelle Snapshots.

Wenn die entfernte Installation erreichbar ist, aber notwendige Temperatur- oder Feuchtewerte fehlen, ist das **kein Netzwerkausfall**: Der Raum bleibt sichtbar und zeigt an, dass gerade keine zuverlässige Empfehlung möglich ist.

Wenn ein Token widerrufen wurde oder abgelaufen ist, kann Home Assistant über die normale erneute Authentifizierung einen Ersatz anfordern.

[← Zur Übersicht](../README.md)
