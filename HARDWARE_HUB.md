# Hardware-Hub / ESP-NOW – Architektur v0.11.0

> Home Assistant bleibt die Quelle der Wahrheit für Stationsrolle, Raum, Master-Zuordnung und Netzwerk-/WireGuard-Konfiguration. v0.11.0 ergänzt den bestehenden Laufzeitvertrag um die vollständige Erst-/Neu-Provisionierung der einheitlichen Firmware direkt aus dem normalen Stationsdialog.

> **Sicherheit:** Der HTTP-Provisioning-Endpunkt bleibt nur für Home-Assistant-Administratoren freigegeben, weil ein importiertes Remote-Master-Profil auch den WireGuard-Private-Key enthalten kann. Der neue Laufzeit-Reportweg verwendet dagegen die bereits authentifizierte ESPHome-Native-API und erfordert in der ESPHome-Integration eine ausdrückliche Freigabe für Home-Assistant-Aktionen.

## Grundprinzip: eine Firmware, Rollen aus Home Assistant

Alle Lüftungsstationen sollen später dasselbe ESP-Programm erhalten. Die Hardware muss beim Flashen nicht in „Master“ und „Slave“ getrennt werden.

Home Assistant speichert stattdessen pro Station eine Rolle:

- **`standalone` – Einzelstation:** eigener SCD41 + Display, direkte Verbindung zu Home Assistant/ESPHome, kein ESP-NOW-Master nötig.
- **`master` – ESP-NOW-Master:** Gateway für weitere Stationen und optional selbst eine direkte Raumstation mit eigenen Sensoren/Display. Ein reiner Gateway-Master benötigt keinen eigenen Display-Rückkanal.
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

- Node und konfigurierter Master vorhanden + `master_id` **und `master_secret`** passen → Report wird angenommen.
- `master_id` gehört zu einem anderen Master → `409 Conflict`, Messwerte werden nicht gespeichert.
- `master_secret` fehlt oder ist falsch → Report wird abgewiesen, Messwerte werden nicht gespeichert.
- die explizit verknüpfte Master-Subentry wurde gelöscht → `409 Conflict`, kein Fallback auf eine alte Hardware-ID.

Der HTTP-Kompatibilitätspfad verwendet damit denselben Anwendungsschutz wie die ESPHome-Native-API-Aktion; eine normale authentifizierte HA-HTTP-Anfrage allein ersetzt das Master-Credential nicht.

Die Displayantwort wird danach **direkt aus dem aktuellen RoomCoordinator/RoomSnapshot** aufgebaut. Die sichtbare Assistent-Sensorentity ist kein Bestandteil der Firmware-Kommunikationsstrecke.

Wird ein physisches Master-Gerät im Reconfigure ersetzt, bleibt die Node-Beziehung wegen der stabilen Subentry-ID bestehen. Es müssen keine Node-Subentries kaskadierend aktualisiert werden. Wird der Master dagegen gelöscht, bleiben die Nodes absichtlich sichtbar, tragen `configuration_error = master_missing`, ihre Messwerte gelten sofort als nicht mehr verwendbar und sie müssen einem neuen Master zugeordnet werden.

Dasselbe gilt für die Raumbeziehung: Wird ein verknüpfter Raum gelöscht, bleibt die Hardwarestation sichtbar, trägt `configuration_error = room_missing`, ihre Werte werden sofort aus Entscheidungen ausgeschlossen und Hardware-Reports werden mit `409 Conflict` abgewiesen, bis ein gültiger Raum neu zugeordnet wurde. Ein Master liefert solche verwaisten Nodes nicht in seiner Teilnehmerliste aus.

### Master-Reconfigure und WireGuard

- `lokal → remote`: neuer WireGuard-Import ist Pflicht.
- `remote → remote`: vorhandenes Profil kann unverändert bleiben oder durch eine neue Datei ersetzt werden.
- `remote → lokal`: gespeicherte WireGuard-Schlüssel/Peer-Daten werden aus der Stationskonfiguration entfernt.

### Direkte ESPHome-Sensorzuordnung

Genau ein CO₂-/Temperatur-/Feuchtesensor wird weiterhin automatisch gewählt. Gibt es bereits beim ersten Setup mehrere passende Sensoren (z. B. SCD41 + DS18B20), bleibt das Gerät auswählbar und Home Assistant fragt einmal explizit nach den drei Quellen. Die gespeicherte Auswahl wird anschließend auch bei weiteren gleichartigen Sensoren beibehalten.


## Automatische HA→ESPHome-Provisionierung ab v0.11.0

Beim bewussten Anlegen oder Reconfigure einer Station markiert HA genau diesen Stations-Subentry als zu provisionieren. Nach dem Speichern wird die Sollkonfiguration über die vom gemeinsamen Firmware-Build registrierten ESPHome-Native-API-Aktionen übertragen:

- `lueftungsstation_apply_station_config` für Rolle, Entry-/Stations-/Raumbezug, Master-MAC und Standortmodus,
- `lueftungsstation_apply_master_credential` ausschließlich für einen echten Master,
- `lueftungsstation_apply_wireguard` bzw. `lueftungsstation_clear_wireguard` entsprechend der Master-Konfiguration,
- `lueftungsstation_apply_participants` als zusätzlicher Master-Topologievertrag, sobald die eingesetzte Unified-Firmware diese Action unterstützt.

Die Teilnehmer-Action arbeitet absichtlich als **vollständiger Replace**, nicht als `ADD_NODE`/`REMOVE_NODE`: HA übergibt parallel `hardware_ids`, `station_subentry_ids`, `room_ids` und einen SHA-256-`topology_hash`. Die Firmware muss gleiche Arraylängen validieren und den kompletten Peer-/Teilnehmercache atomar ersetzen. Dadurch ist ein Master nach Ausfall/Neustart nicht davon abhängig, dass jede historische Einzeländerung angekommen ist. Ein leerer Payload bedeutet entsprechend: keine Nodes.

Die Zieladresse wird **nicht** über feste IPs oder Namen im Lüftungsassistent-Code ermittelt. HA nimmt das vom Benutzer ausgewählte ESPHome-Gerät, liest dessen `CONNECTION_NETWORK_MAC` aus der Device Registry und verwendet die von ESPHome selbst registrierten Native-API-Aktionen. Direkte Stations-IDs werden als `DIRECT:<MAC>` gespeichert; ESP-NOW-Protokoll-IDs verwenden die rohe MAC. Eine interne HA-Device-ID ist niemals physische Hardware-ID.

Ein Master-Secret entsteht nur beim tatsächlichen Anlegen eines Master-Subentries. Normale Rekonfiguration desselben physischen Masters behält **denselben HA-Wert**; ein Wechsel auf eine andere Master-MAC erzeugt ein neues Secret. Während einer bewussten Master-Neuprovisionierung wird der gespeicherte HA-Wert trotzdem erneut an die Firmware gesendet und frisch bestätigt. So wird auch ein seltener Drift nach manuellem Flash/Restore korrigiert, ohne das Secret zu rotieren oder als Diagnosewert offenzulegen. Migration 1.13 korrigiert vorhandene Stationen auf die echte Netzwerk-MAC, **setzt aber absichtlich kein Provisionierungsflag und erzeugt kein Master-Secret für Standalone-/Node-Geräte**.

Die Unified-Firmware speichert die übergebenen Werte persistent. HA behandelt ein altes `on` ausdrücklich **nicht** als Bestätigung eines neuen Pushs: Die erforderlichen Diagnose-Entities müssen nach der jeweiligen ESPHome-Aktion frisch gemeldet werden. Rolle, Raum-ID, Master-MAC und Standortmodus werden zusätzlich gegen den HA-Sollzustand geprüft.

Bei einem neu erzeugten bzw. nach physischem Mastertausch rotierten Credential nutzt HA den vorhandenen Firmwarevertrag für einen eindeutigen Reset-Handshake: zunächst wird die Station bewusst kurz als Nicht-Master provisioniert und `Master-Credential konfiguriert = off` frisch bestätigt; danach folgen endgültige Masterrolle und neues Secret mit einer frischen `on`-Bestätigung. Eine normale Rekonfiguration desselben physischen Masters behält das Secret und überspringt nur den Reset; der identische HA-Wert wird dennoch erneut angewendet und seine frische `on`-Meldung abgewartet.

Ein neues Remote-WireGuard-Profil wird ebenfalls zuerst bewusst gelöscht (`off` frisch bestätigt) und anschließend angewendet (`on` frisch bestätigt). Das bestätigt, dass genau der neue Apply-Vorgang nach dem Reset erfolgreich war, ohne Schlüsselmaterial als Diagnosewert auszugeben.

Ist das Gerät während des Speicherns offline, wird nur diese ausdrücklich offene Provisionierung erneut versucht. Die Warteabstände steigen pro Station 1 → 2 → 5 → 10 Minuten an; erfolgreiche Bestätigung entfernt den Pending-Zustand. Normale Boots führen keinen Config-Abruf aus.

### HA-owned Master-Teilnehmerliste

Die Node→Master-Beziehung bleibt vollständig in Home Assistant. Für jeden Master bildet HA aus allen gültigen Node-Subentries die komplette Soll-Liste. Diese Berechnung wird auch vom authentifizierten `/hardware/config`-Endpoint verwendet, sodass HTTP-Konfiguration und Native-API-Provisionierung nicht auseinanderlaufen können.

Jede Config-Entry-Änderung führt beim Reload zu einem neuen Topologie-Digest. Damit werden insbesondere automatisch erkannt:

- Node neu angelegt,
- Node gelöscht,
- Node von Master A auf Master B umgehängt,
- Node einem anderen Raum zugeordnet,
- Node durch fehlenden Raum/Master ungültig.

Besitzt die Firmware `lueftungsstation_apply_participants`, sendet HA den **kompletten aktuellen Sollzustand**. Der Firmwarevertrag verlangt gleichzeitig die Diagnose `Lüftungsstation Topologie-Hash`: Nach dem atomaren Replace speichert der Master den übergebenen SHA-256-Hash persistent und meldet exakt diesen Wert an Home Assistant zurück. **Nur der vom Master gemeldete Hash bestätigt den Sync.** Ein HA-seitig gespeicherter alter Hash oder der reine Zähler `Lüftungsstation Gekoppelte Nodes` genügt ausdrücklich nicht, weil beides einen falschen/geleerten Cache nach Reflash oder Restore nicht beweisen kann.

Die heute bereits eingesetzte Unified-Firmware besitzt diesen Vertrag möglicherweise noch nicht. Das ist absichtlich rückwärtskompatibel: Rolle, Credential, WireGuard und normaler Messbetrieb bleiben nutzbar; nur die HA-owned Teilnehmerlisten-Synchronisierung bleibt ausstehend. Sobald Action **und** Topologie-Hash-Diagnose vorhanden sind, gleicht HA den Gerätehash mit dem aktuellen Soll-Hash ab. Abweichung, `unknown` oder `unavailable` bleibt automatisch pending. Zusätzlich zum Service-Registry-Event läuft ein begrenzter Retry mit 1→2→5→10 Minuten Backoff, sodass auch ein während der Änderung ausgeschalteter Master oder ein später zurückgesetzter Cache selbstständig wieder den vollständigen HA-Sollzustand erhält.

## Direkter Display-Rückkanal für Standalone und lokalen Master

`lueftungsberater.hardware_report` bleibt absichtlich **node-only**. Standalone-Geräte melden ihre SCD41-Werte weiterhin als normale ESPHome-Sensor-Entities; ein Master mit eigener lokaler Sensorstation tut dasselbe für seinen eigenen Raum. Für deren lokales Display existiert separat der HA→ESPHome-Vertrag:

`lueftungsstation_apply_display_result`

Parameter:

- `station_subentry_id: string`
- `room_id: string`
- `room_name: string`
- `status: string` (`green`, `yellow`, `orange`, `red`, `locked`)
- `recommendation: string`
- `recommendation_key: string`
- `display_mode: string`
- `safety_lock: bool`

`station_subentry_id` und `room_id` sind Schutz-/Korrelationswerte und keine Displaytexte. Eine spätere Firmware kann damit einen verspäteten Push nach einer Rekonfiguration verwerfen. Der sichtbare Inhalt wird aus **demselben gemeinsamen Display-Payload-Builder** erzeugt wie die Response von `lueftungsberater.hardware_report`; es gibt keine zweite Lüftungsentscheidung und keine abweichende Karten-/Displaylogik.

Der Push hängt an neuen RoomCoordinator-Snapshots und reagiert daher nicht nur auf neue CO₂-/Temperatur-/Feuchtewerte, sondern ebenso auf Wetter, amtliche Warnungen/Hard-Locks, Fensterzustände, Session-/Hystereselogik, Außendaten und andere neu berechnete Raumentscheidungen.

Direkt beliefert werden nur:

- `standalone`,
- `master` **mit eigener direkter Raum-Sensorik**.

Ein `node` erhält niemals `lueftungsstation_apply_display_result`; sein Displaypfad bleibt `Node → ESP-NOW → Master → lueftungsberater.hardware_report → Master → derselbe Node`. Ein reiner Gateway-Master ohne eigene lokale Sensorstation erhält ebenfalls keinen eigenen Raum-Display-Push. Der direkte Master-Push ist damit eine eigene lokale Anzeigeaktion und darf firmwareseitig niemals als aktuell bearbeitete Node-Antwort/`DISPLAY_RESULT` interpretiert oder in deren Korrelation eingemischt werden.

Die aktuell installierte DEV-0.7-Firmware darf die Action noch nicht besitzen. Das ist kein Setup- oder Auswertungsfehler: HA hält nur die neueste Payload in Memory als deferred/pending. Sobald ESPHome die Action später registriert, wird der aktuelle Zustand automatisch einmal nachgesendet. Ist die Action registriert, das Gerät aber offline, laufen leichte Retries mit 1→2→5→10 Minuten Backoff. Identische bereits erfolgreich gesendete Payloads werden pro Stations-Subentry im laufenden HA-Prozess dedupliziert; nach einem HA-Neustart wird der aktuelle Zustand einmal erneut übertragen. Eine inhaltlich neue Payload – besonders ein geänderter `safety_lock` – wartet nicht hinter dem Retry-Timer der alten Payload, sondern wird sofort einmal versucht.

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

`report` spiegelt `round_id` und `request_id` zurück. Diese IDs sind Transportkorrelation. HA verwirft aktuell bewusst **nicht** anhand einer bloßen Rundennummer, weil ein Masterneustart dieselbe Nummer wiederverwenden kann. Für eine später vollständig HA-seitige Replay-/Altrundenabwehr wäre zusätzlich eine vom Master gelieferte `boot_id`/`session_id` nötig; bis dahin muss die gemeinsame Firmware höchstens eine HA-Anfrage gleichzeitig führen und verspätete Antworten anhand ihrer Korrelation verwerfen.

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
- zuletzt angewandten lokalen Provisionierungszustand.

Rolle, Raum und Master kommen aus Home Assistant. Gerätespezifische Geheimnisse/Netzwerkdaten liegen persistent auf dem jeweiligen ESP, nachdem sie einmal lokal provisioniert wurden.

**Wichtig:** `/api/lueftungsberater/hardware/config` ist kein Laufzeit-Polling-Endpunkt für jeden Boot. Er dient der bewussten Erst-/Neu-Provisionierung (beziehungsweise einer später explizit angestoßenen Konfigurationsaktualisierung). Der ESP speichert die erhaltene Sollkonfiguration einschließlich `master_secret` und – bei `remote` – WireGuard-Profil persistent. Ein normaler Neustart benutzt diesen lokalen Zustand weiter und benötigt weder einen HA-Admin-Token noch einen erneuten `/hardware/config`-Abruf.

## Noch bewusst nicht Teil von v0.11.0

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

