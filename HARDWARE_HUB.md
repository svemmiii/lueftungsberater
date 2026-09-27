# Hardware-Hub / ESP-NOW – Zielarchitektur v0.10.1

> v0.10.1 räumt zuerst die **Home-Assistant-Seite** auf. Home Assistant ist die Quelle der Wahrheit für Stationsrolle, Raum, Master-Zuordnung und die vorbereitete Netzwerk-/WireGuard-Konfiguration. Die einheitliche ESP-Firmware wird anschließend genau gegen diesen Vertrag gebaut.

> **Sicherheit:** Der Provisioning-Endpunkt für die spätere Firmware ist aktuell nur für Home-Assistant-Administratoren freigegeben, weil ein importiertes Remote-Master-Profil auch den WireGuard-Private-Key enthalten kann. Für die ESP-Firmware wird danach ein eigener Geräte-/Provisioning-Auth-Weg definiert.

## Grundprinzip: eine Firmware, Rollen aus Home Assistant

Alle Lüftungsstationen sollen später dasselbe ESP-Programm erhalten. Die Hardware muss beim Flashen nicht in „Master“ und „Slave“ getrennt werden.

Home Assistant speichert stattdessen pro Station eine Rolle:

- **`standalone` – Einzelstation:** eigener SCD41 + Display, direkte Verbindung zu Home Assistant/ESPHome, kein ESP-NOW-Master nötig.
- **`master` – ESP-NOW-Master:** eigener SCD41 + Display **und** Gateway für weitere Stationen. Der Master ist also selbst weiterhin eine vollständige Raumstation.
- **`node` – ESP-NOW-Raumstation:** eigener SCD41 + Display; Rohwerte/Displayantwort laufen über den in Home Assistant ausgewählten Master.

Die Rolle ist von der Transportart getrennt. Ein Master kann seine eigenen Sensorwerte direkt über ESPHome liefern, während seine Nodes über den Master-/Hardware-API-Pfad laufen.

## Station zuerst, Raum automatisch

Eine Hardwarestation braucht ab v0.10.1 keinen vorher manuell angelegten Lüftungsassistent-Raum mehr.

Beim Stationssetup wird gewählt:

1. Rolle der Station,
2. physisches Gerät / Hardware-ID,
3. **neuen Raum automatisch anlegen** oder einen vorhandenen Raum verwenden,
4. bei neuem Raum: Name und optional Home-Assistant-Bereich.

Ein automatisch erzeugter Raum ist ein normaler `room`-Subentry und erhält dieselben ruhigen Defaults wie ein manuell angelegter Raum:

- Solltemperatur 21 °C,
- Nacht-Hinweis 22:00–07:00,
- Raum-Lüftungsbenachrichtigungen aus,
- Remote-Freigabe aus.

Temperatur, Feuchte und CO₂ werden nicht zusätzlich im Raum verdoppelt. Solange die Station dem Raum zugeordnet ist, kommen diese drei Innenwerte von der Station.

## Master-Zuordnung

Ein ESP-NOW-Node bekommt keinen beliebigen Freitext-Master mehr. Home Assistant zeigt nur tatsächlich als `master` konfigurierte Stationen an.

Intern wird bei neuen Nodes nur die stabile **Master-Subentry-ID** als dauerhafte Beziehung gespeichert. Die aktuelle Hardware-ID des Masters wird bei Bedarf aus dieser Subentry abgeleitet und als Protokollkennung an die Firmware ausgegeben.

Damit kann ein Master umbenannt oder sogar physisch ersetzt werden, ohne dass die Node-Konfiguration umgeschrieben werden muss. Legacy-v0.10.0-Nodes ohne stabile Beziehung behalten vorerst ihren alten Hardware-ID-Fallback.

Neue Nodes werden im Home-Assistant-Gerätemodell über `via_device_id` direkt dem konkret ausgewählten Master-Gerät zugeordnet. Der alte synthetische „Lüftungsstation-Master“ bleibt nur als Legacy-Fallback für v0.10.0-Zuordnungen ohne expliziten Master bzw. unbekannte Discovery-Master bestehen.

## Lokaler und entfernter Master

Beim Anlegen eines Masters wird ausgewählt:

- **Lokal / im selben Netz**
- **Entfernt / über WireGuard**

Der ESP muss für die Ersteinrichtung lokal erreichbar sein. Danach soll dieselbe Firmware die von Home Assistant gespeicherte Konfiguration übernehmen und der Master kann an einen entfernten Standort gebracht werden.

### WireGuard-Import

Für einen entfernten Master zeigt Home Assistant einen nativen Datei-Upload an. Erwartet wird eine normale WireGuard-Clientkonfiguration mit genau einem `[Interface]` und einem `[Peer]`.

Ausgelesen/validiert werden:

- `Address`
- `PrivateKey`
- Peer-`PublicKey`
- optional `PresharedKey`
- `Endpoint` inkl. Host/Port
- `AllowedIPs`
- optional `PersistentKeepalive`

Die Upload-Datei selbst wird nicht dauerhaft aufbewahrt. Die geparsten Werte werden im Master-Subentry als Sollkonfiguration gespeichert, damit die spätere ESP-Firmware sie beim Provisionieren abrufen kann.

> Der Private Key wird in v0.10.1 noch als Teil der Home-Assistant-Konfiguration gespeichert, weil die Firmware zur Laufzeit noch nicht existiert. Eine spätere Verbesserung kann den Schlüssel direkt auf dem ESP erzeugen und HA nur den Public Key geben.

## Sollkonfiguration für die spätere Firmware

Neuer authentifizierter Endpunkt:

`POST /api/lueftungsberater/hardware/config`

Request:

```json
{
  "entry_id": "<Lüftungsassistent-ConfigEntry>",
  "hardware_id": "<Stations-ID>"
}
```

Antwort enthält – abhängig von der Rolle – unter anderem:

- `protocol`
- `hardware_id`
- `station_subentry_id`
- `role`
- `transport`
- `room_id`
- `room_name`
- für `node`: den von HA ausgewählten Master
- für `master`: die HA-Teilnehmerliste
- für entfernte `master`: das WireGuard-Profil

Damit muss die spätere Firmware keine Rolle erraten und keine eigene dauerhafte Teilnehmerverwaltung als Quelle der Wahrheit erfinden. Sie kann HA-Sollzustand abrufen/übernehmen und die Funk-/Displayaufgabe ausführen.

## Direkte Einzelstation / eigener Master-Sensor

Ein lokaler ESP kann weiterhin als normales ESPHome-Gerät eingebunden werden:

`SCD41 -> ESPHome -> Home Assistant -> Lüftungsassistent`

Home Assistant erkennt genau je einen CO₂-, Temperatur- und Luftfeuchtesensor. Diese Original-Entities bleiben Eigentum von ESPHome; der Lüftungsassistent erzeugt keine doppelten Rohwert-Entities.

Dieselbe direkte Verbindung wird in v0.10.1 auch für die **eigenen** SCD41-Werte eines Masters genutzt. Seine zusätzlichen ESP-NOW-Aufgaben kommen später mit der gemeinsamen Firmware hinzu.

## Topologie- und Report-Hardening

Für neue v0.10.1-Nodes ist die **Master-Subentry-ID** die dauerhafte Quelle der Wahrheit. Die zusätzlich gespeicherte Master-Hardware-ID dient nur noch dem Funkprotokoll und der Rückwärtskompatibilität.

Beim `POST /api/lueftungsberater/hardware/report` gilt deshalb:

- Node und konfigurierter Master vorhanden + `master_id` passt → Report wird angenommen.
- `master_id` gehört zu einem anderen Master → `409 Conflict`, Messwerte werden nicht gespeichert.
- die explizit verknüpfte Master-Subentry wurde gelöscht → `409 Conflict`, kein Fallback auf eine alte Hardware-ID.

Die Displayantwort wird danach **direkt aus dem aktuellen RoomCoordinator/RoomSnapshot** aufgebaut. Die sichtbare Advisor-Sensorentity ist kein Bestandteil der Firmware-Kommunikationsstrecke.

Wird ein physisches Master-Gerät im Reconfigure ersetzt, bleibt die Node-Beziehung wegen der stabilen Subentry-ID bestehen. Es müssen keine Node-Subentries kaskadierend aktualisiert werden. Wird der Master dagegen gelöscht, bleiben die Nodes absichtlich sichtbar, tragen `configuration_error = master_missing`, ihre Messwerte gelten sofort als nicht mehr verwendbar und sie müssen einem neuen Master zugeordnet werden.

Dasselbe gilt für die Raumbeziehung: Wird ein verknüpfter Raum gelöscht, bleibt die Hardwarestation sichtbar, trägt `configuration_error = room_missing`, ihre Werte werden sofort aus Entscheidungen ausgeschlossen und Hardware-Reports werden mit `409 Conflict` abgewiesen, bis ein gültiger Raum neu zugeordnet wurde. Ein Master liefert solche verwaisten Nodes nicht in seiner Teilnehmerliste aus.

### Master-Reconfigure und WireGuard

- `lokal → remote`: neuer WireGuard-Import ist Pflicht.
- `remote → remote`: vorhandenes Profil kann unverändert bleiben oder durch eine neue Datei ersetzt werden.
- `remote → lokal`: gespeicherte WireGuard-Schlüssel/Peer-Daten werden aus der Stationskonfiguration entfernt.

### Direkte ESPHome-Sensorzuordnung

Genau ein CO₂-/Temperatur-/Feuchtesensor wird weiterhin automatisch gewählt. Gibt es bereits beim ersten Setup mehrere passende Sensoren (z. B. SCD41 + DS18B20), bleibt das Gerät auswählbar und Home Assistant fragt einmal explizit nach den drei Quellen. Die gespeicherte Auswahl wird anschließend auch bei weiteren gleichartigen Sensoren beibehalten.

## ESP-NOW-Node / Hardware-API

Master-gebundene Nodes bleiben über die vorhandene Hardware-API angebunden:

- `POST /api/lueftungsberater/hardware/discover`
- `POST /api/lueftungsberater/hardware/report`
- `POST /api/lueftungsberater/hardware/config`

Ein Stationsreport gilt 180 Sekunden als frisch. Danach werden alte Rohwerte für Entscheidungen gesperrt und die Hardware-Entities `unavailable`, die Kopplung bleibt aber bestehen. Eine ungültige HA-Topologie (`room_missing` oder bei neuen Nodes `master_missing`) sperrt die Werte sofort, unabhängig vom 180-Sekunden-TTL.

`report` spiegelt `round_id` und `request_id` zurück. Diese IDs sind Transportkorrelation; die endgültige Retry-/Altrundenlogik wird zusammen mit der Master-Firmware festgelegt.

## Geplanter ESP-NOW-Ablauf

Der von HA konfigurierte Master verwaltet die Runde:

`REQUEST -> SENSOR_DATA -> HA-Auswertung -> DISPLAY_RESULT -> ACK -> nächste Station`

Home Assistant bleibt die einzige Entscheidungsinstanz. Der ESP berechnet keine zweite Lüftungslogik.

## Gleiche Firmware / spätere Provisionierung

Das Ziel für den nächsten Schritt ist eine gemeinsame Firmware mit persistentem Gerätespeicher für ungefähr:

- Geräte-/Hardware-ID,
- HA-Sollrolle,
- Raum-/Masterbeziehung,
- WLAN-Profile,
- WireGuard-Profil,
- ESP-NOW-Peers/Teilnehmercache,
- zuletzt angewandte Konfigurationsrevision.

Rolle, Raum und Master kommen aus Home Assistant. Gerätespezifische Geheimnisse/Netzwerkdaten liegen persistent auf dem jeweiligen ESP, nachdem sie einmal lokal provisioniert wurden.

## Noch bewusst nicht Teil von v0.10.1

- fertige ESP-NOW-Firmware,
- dynamisches Anwenden der WireGuard-Konfiguration auf einem ESP,
- WLAN-Provisionierung für entfernte Standorte,
- Ersatzmaster-/Election-Logik,
- Mehrhop-Routing und Route-Recovery,
- endgültige ACK-/Retry-/Timeout-Parameter.

Diese Punkte werden **nach** der HA-Seite gegen den jetzt festgelegten v0.10.1-Vertrag implementiert.
