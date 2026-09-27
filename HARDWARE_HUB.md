# Hardware-Hub / ESP-NOW – Architektur v0.10.2

> Home Assistant bleibt die Quelle der Wahrheit für Stationsrolle, Raum, Master-Zuordnung und Netzwerk-/WireGuard-Konfiguration. v0.10.2 ergänzt den bereits in v0.10.1 vorbereiteten Vertrag um einen response-fähigen ESPHome-Native-API-Rückkanal für laufende Messrunden.

> **Sicherheit:** Der HTTP-Provisioning-Endpunkt bleibt nur für Home-Assistant-Administratoren freigegeben, weil ein importiertes Remote-Master-Profil auch den WireGuard-Private-Key enthalten kann. Der neue Laufzeit-Reportweg verwendet dagegen die bereits authentifizierte ESPHome-Native-API und erfordert in der ESPHome-Integration eine ausdrückliche Freigabe für Home-Assistant-Aktionen.

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

> Der Private Key wird weiterhin als Teil der Home-Assistant-Sollkonfiguration gespeichert, damit ein remote vorgesehener Master lokal provisioniert werden kann. Eine spätere Härtung kann den Schlüssel direkt auf dem ESP erzeugen und HA nur den Public Key geben.

## Sollkonfiguration für die einheitliche Firmware

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

Damit muss die einheitliche Firmware keine Rolle erraten und keine eigene dauerhafte Teilnehmerverwaltung als Quelle der Wahrheit erfinden. Sie kann den HA-Sollzustand übernehmen und die Funk-/Displayaufgabe ausführen.

## Direkte Einzelstation / eigener Master-Sensor

Ein lokaler ESP kann weiterhin als normales ESPHome-Gerät eingebunden werden:

`SCD41 -> ESPHome -> Home Assistant -> Lüftungsassistent`

Home Assistant erkennt genau je einen CO₂-, Temperatur- und Luftfeuchtesensor. Diese Original-Entities bleiben Eigentum von ESPHome; der Lüftungsassistent erzeugt keine doppelten Rohwert-Entities.

Dieselbe direkte Verbindung wird auch für die **eigenen** SCD41-Werte eines Masters genutzt. Seine zusätzlichen ESP-NOW-Aufgaben übernimmt dieselbe gemeinsame Stationsfirmware abhängig von der durch HA gesetzten Rolle.

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

## Native-API-Rückkanal ab v0.10.2

Für den normalen Laufzeitpfad eines ESP-NOW-Masters existiert die Home-Assistant-Aktion `lueftungsberater.hardware_report`. Sie ist **kein zweiter Entscheidungsweg**: Nach der Stationsauflösung verwendet sie denselben internen Report-/RoomCoordinator-/Displaypfad wie `POST /api/lueftungsberater/hardware/report`.

Der Master übergibt mindestens:

- `hardware_id` des Nodes,
- `master_id` des meldenden Masters,
- `master_secret` des provisionierten Masters,
- `round_id` und `request_id`,
- vorhandene Rohwerte (`co2`, `temperature`, `humidity`) und optional Funkdiagnose/Firmware.

Home Assistant prüft die gespeicherte Node→Master-Beziehung **vor** der Messwertübernahme. `master_id` muss zum konfigurierten Master passen und `master_secret` muss dessen von HA provisioniertem Credential entsprechen. Erst danach werden Rohwerte übernommen. Anschließend liefert die Action-Response unter anderem `status`, `recommendation`, `recommendation_key`, `display_mode`, `safety_lock`, `room_name`, `round_id`, `request_id` und `master_location_mode`.

ESPHome erhält diese Serviceantwort über `capture_response`; Home Assistants ESPHome-Bridge kapselt die eigentliche Serviceantwort dabei unter `response`, die Firmware liest also die Nutzdaten aus dem inneren Response-Objekt.

**Mindestversion:** Für `homeassistant.action` mit `capture_response`/Response-Verarbeitung wird **ESPHome >= 2025.10** vorausgesetzt.

### Lokal vs. entfernt

Der Reportvertrag ist in beiden Fällen identisch:

- `local`: ESPHome Native API direkt über das lokale Netz.
- `remote`: dieselbe ESPHome Native API über den von HA provisionierten WireGuard-Tunnel.

`master_location_mode` wird ausschließlich aus dem konfigurierten Master-Subentry abgeleitet. Weder IP-Bereich noch Latenz noch das Vorhandensein einer VPN-Adresse dürfen den Standortmodus automatisch ändern. Dadurch bleibt ein entfernter Master auch dann eindeutig `remote`, wenn seine Tunneladresse technisch wie ein internes Netz aussieht.

Der Native-API-Weg setzt voraus, dass für den betreffenden ESPHome-Master in Home Assistant ausdrücklich das Ausführen von Home-Assistant-Aktionen erlaubt wurde. Remote wird der ESPHome-API-Port ausschließlich innerhalb des WireGuard-Tunnels genutzt und nicht öffentlich freigegeben.

Die Freigabe gilt für Home-Assistant-Aktionen dieses ESPHome-Geräts allgemein. Home Assistants ESPHome-Service-Bridge übergibt dem aufgerufenen Integrations-Service weiterhin keine separate kryptografische Caller-Geräte-ID. Diese Lücke wird deshalb auf Anwendungsebene geschlossen: `master_id` identifiziert den konfigurierten Master, `master_secret` weist den Besitz seiner HA-Provisionierung nach. Ein anderes freigegebenes ESPHome-Gerät kann damit nicht allein durch Nachahmen der Master-MAC gültige Node-Reports erzeugen.

## ESP-NOW-Node / Hardware-API

Master-gebundene Nodes bleiben über die vorhandene Hardware-API angebunden:

- `POST /api/lueftungsberater/hardware/discover`
- `POST /api/lueftungsberater/hardware/report`
- `POST /api/lueftungsberater/hardware/config`

Ein Stationsreport gilt 180 Sekunden als frisch. Danach werden alte Rohwerte für Entscheidungen gesperrt und die Hardware-Entities `unavailable`, die Kopplung bleibt aber bestehen. Eine ungültige HA-Topologie (`room_missing` oder bei neuen Nodes `master_missing`) sperrt die Werte sofort, unabhängig vom 180-Sekunden-TTL.

`report` spiegelt `round_id` und `request_id` zurück. Diese IDs sind Transportkorrelation; die endgültige Retry-/Altrundenlogik wird zusammen mit der Master-Firmware festgelegt.

## ESP-NOW-Ablauf

Der von HA konfigurierte Master verwaltet die Runde:

`REQUEST -> SENSOR_DATA -> lueftungsberater.hardware_report -> HA-Auswertung -> DISPLAY_RESULT -> ACK -> nächste Station`

`round_id` und `request_id` begleiten die Runde bis zur HA-Antwort zurück. Home Assistant bleibt die einzige Entscheidungsinstanz; der ESP berechnet keine zweite Lüftungslogik.

## Gleiche Firmware / Provisionierung

Die gemeinsame Firmware verwendet persistenten Gerätespeicher für ungefähr:

- Geräte-/Hardware-ID,
- HA-Sollrolle,
- Raum-/Masterbeziehung,
- WLAN-Profile,
- WireGuard-Profil,
- ESP-NOW-Peers/Teilnehmercache,
- zuletzt angewandte Konfigurationsrevision.

Rolle, Raum und Master kommen aus Home Assistant. Gerätespezifische Geheimnisse/Netzwerkdaten liegen persistent auf dem jeweiligen ESP, nachdem sie einmal lokal provisioniert wurden.

**Wichtig:** `/api/lueftungsberater/hardware/config` ist kein Laufzeit-Polling-Endpunkt für jeden Boot. Er dient der bewussten Erst-/Neu-Provisionierung (beziehungsweise einer später explizit angestoßenen Konfigurationsaktualisierung). Der ESP speichert die erhaltene Sollkonfiguration einschließlich `master_secret` und – bei `remote` – WireGuard-Profil persistent. Ein normaler Neustart benutzt diesen lokalen Zustand weiter und benötigt weder einen HA-Admin-Token noch einen erneuten `/hardware/config`-Abruf.

## Noch bewusst nicht Teil von v0.10.2

- produktionsreife ESP-NOW-Firmware,
- dynamisches Anwenden der WireGuard-Konfiguration auf einem ESP,
- WLAN-Provisionierung für entfernte Standorte,
- Ersatzmaster-/Election-Logik,
- Mehrhop-Routing und Route-Recovery,
- endgültige ACK-/Retry-/Timeout-Parameter.

Diese Punkte liegen weiterhin auf der Firmware-/Netzwerkseite und ändern den v0.10.2-HA-Vertrag nicht.

## Native-API Master-Credential (v0.10.2)

Jeder Master besitzt ein eigenes zufälliges 256-Bit-Credential. Home Assistant
speichert es im Master-Subentry und liefert es ausschließlich über den
authentifizierten/admin-geschützten Hardware-Konfigurationspfad an die
Provisionierung der Firmware.

Für `lueftungsberater.hardware_report` gilt:

1. `hardware_id` löst den Node auf.
2. Die stabile Node→Master-Subentry-Beziehung bestimmt den erlaubten Master.
3. `master_id` muss zur Hardware-ID dieses Masters passen.
4. `master_secret` muss mit dessen gespeichertem Credential übereinstimmen.
5. Erst danach werden Messwerte gespeichert und die Raumentscheidung berechnet.

Das Secret wird unmittelbar vor dem gemeinsamen Report-Pfad aus dem
Service-Payload entfernt. Es erscheint weder in `StationRuntime.extra`, noch in
Entities/Diagnoseattributen oder in der Service-Response.

`local`/`remote` ändert diesen Authentifizierungsvertrag nicht. Ein Remote-Master
benutzt dasselbe Credential über seine ESPHome-Native-API-Verbindung durch
WireGuard; Home Assistant errät den Standort weiterhin nicht anhand des
Netzwerkwegs.

