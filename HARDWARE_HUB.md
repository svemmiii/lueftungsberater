# Hardware-Hub / ESP-NOW – Zielarchitektur

> v0.10.0 enthält die **Home-Assistant-Seite** der Hardware-Erweiterung mit zwei Transportwegen: Eine einzelne Station kann direkt als vorhandenes ESPHome-Gerät einem Raum zugeordnet werden, während mehrere Knoten über einen Master/ESP-NOW laufen können. In beiden Fällen bleibt die Lüftungslogik ausschließlich in Home Assistant. Das eigentliche ESP-NOW-/Mehrhop-Protokoll läuft weiterhin erst in der noch zu erstellenden ESP-Firmware.

## Rollen

- **Home Assistant / Lüftungsassistent:** einzige Entscheidungsinstanz. Erhält Rohwerte, führt Wetter-/Warn-/Sessionlogik aus und liefert Farbe + kurze Empfehlung zurück.
- **Standalone-/Direkt-Station:** ESP32 + SCD41 + Display, bereits als normales ESPHome-Gerät in Home Assistant eingebunden. Sie braucht keinen zusätzlichen Master; Home Assistant liest ihre drei Rohsensoren direkt.
- **Master-ESP:** WLAN/WireGuard nach Home Assistant, ESP-NOW zu weiteren Raumstationen, Pairing, Teilnehmerliste, Routing, Retries, Diagnosen. Er darf selbst zugleich eine direkt angebundene Raumstation sein. Keine eigene Lüftungsentscheidung.
- **ESP-NOW-Raumstation:** SCD41 + Display. Misst CO₂/Temperatur/rF, relayed bei Bedarf ESP-NOW-Pakete und zeigt exakt den von Home Assistant gelieferten Status/Text.

## Direkte Einzelstation ohne Master

Für einen einzelnen ESP ist kein Hub nötig:

`SCD41 -> ESPHome -> WLAN/WireGuard -> Home Assistant -> Lüftungsassistent -> Status/Text zurück per ESPHome-API`

Im Lüftungsassistenten wird bei **Lüftungsstation hinzufügen** zuerst die Verbindungsart gewählt. Bei **Direkt über ESPHome / Home Assistant** werden nur ESPHome-Geräte angeboten, bei denen eindeutig genau ein CO₂-, ein Temperatur- und ein Luftfeuchtesensor erkannt wird. Danach wird nur noch der gewünschte Lüftungsassistent-Raum gewählt. Die drei Entities werden intern gemeinsam gespeichert/aufgelöst und müssen nicht noch einmal einzeln im Raum ausgewählt werden.

Das physische ESPHome-Gerät bleibt in Home Assistant Eigentum der ESPHome-Integration; der Lüftungsassistent speichert lediglich die Stations-/Raumzuordnung und benutzt dessen Entities. Das vermeidet doppelte Geräte und doppelte Recorder-Historien. Entity-ID-Umbenennungen werden über die Gerätezuordnung erneut aufgelöst, solange das Sensor-Set weiterhin eindeutig ist.

Ein Direkt-Setup erzeugt kein leeres Master-Gerät. Sobald Master-Stationen verwendet oder vom Master Discovery-Meldungen empfangen werden, wird die Hub-Topologie angelegt.

## Pairing / Raumzuordnung

1. Pairing wird aus einem vorhandenen Lüftungsassistent-Raum gestartet.
2. Der Master öffnet kurz den Pairingmodus.
3. Eine ungekoppelte Station sendet `JOIN_REQUEST` mit stabiler Hardware-ID und Fähigkeiten.
4. Home Assistant zeigt die gefundene Station im selben Lüftungsassistenten an.
5. Die Station wird dem bereits gewählten Raum und optional dessen HA-Bereich zugeordnet; Temperatur, Feuchte und CO₂ müssen nicht einzeln erneut ausgewählt werden.
6. Master und Station speichern die Kopplung persistent.

Stationen bleiben bei Funk-/Stromausfall registriert und werden in jeder neuen Runde erneut versucht. Nur explizites Entfernen löscht die Zuordnung.

Auf der Home-Assistant-Seite gilt ein Stationsreport **180 Sekunden** als frisch. Nach drei Minuten ohne neuen Report wird die Station automatisch als offline markiert; die alten SCD41-Rohwerte werden für die Entscheidungs-Engine gesperrt und die Hardware-Entities werden unavailable. Die Registrierung/Pairing-Zuordnung bleibt dabei vollständig erhalten und ein späterer gültiger Report aktiviert die Station sofort wieder.

## Abfragerunde

Ungefähr einmal pro Minute führt der Master die bekannte Teilnehmerliste sequenziell durch:

`REQUEST -> SENSOR_DATA -> HA-Auswertung -> DISPLAY_RESULT -> ACK -> ~100 ms -> nächste Station`

Für eine einzelne Station gelten kurze Retries/Timeouts; ein globaler Rundewatchdog verhindert, dass eine defekte Station den gesamten Zyklus blockiert.

## Paketkopf / Dubletten

Geplanter logischer Header:

- `network_id`
- `origin_id`
- `target_id`
- `round_id` (`uint16`)
- `packet_id` (`uint8`, 0…255, danach Wrap)
- `type`
- `ttl` (`uint8`)
- Flags / Payload

Ein Paket wird über `origin_id + round_id + packet_id` identifiziert. Jeder Knoten hält nur einen kleinen Ringpuffer zuletzt gesehener Kennungen. Ein bereits bekanntes Paket wird weder erneut verarbeitet noch erneut weitergeleitet. `ttl` begrenzt zusätzlich die maximale Hopzahl.

## Mehrhop / Routing

- Jeder gekoppelte Raumknoten kann zugleich Relay sein.
- Die räumliche/Etagenzuordnung in Home Assistant bestimmt **nicht** den Funkweg.
- Bei unbekannter/defekter Route wird kontrolliert gesucht; funktionierende Wege können anschließend bevorzugt werden.
- Fällt ein Zwischenknoten aus, wird – sofern physisch erreichbar – ein alternativer Weg verwendet.
- Master und Raumstationen müssen denselben ESP-NOW/WLAN-Kanal verwenden; ungekoppelte bzw. getrennte Nodes sollen den Masterkanal automatisch suchen und danach speichern.

## Entfernen

Normales Entfernen ist zweiphasig und erst nach bestätigtem Reset abgeschlossen:

`UNPAIR_PREPARE -> UNPAIR_READY -> UNPAIR_COMMIT -> Neustart ungekoppelt -> UNPAIRED_CONFIRM`

Erst nach `UNPAIRED_CONFIRM` darf das HA-Gerät normal verschwinden.

**Erzwungen entfernen** versucht bei erreichbarer Station trotzdem zuerst denselben sauberen Ablauf. Antwortet die Station nicht, darf HA sie dennoch entfernen; der Master behält einen kleinen `FORCED_REMOVED`-Tombstone. Taucht dieselbe Hardware später mit alter Kopplung auf, wird sie zurückgesetzt und wieder koppelbar gemacht.

Ein lokaler Hardware-Fallback an der Station (z. B. langer BOOT-Tastendruck) soll Pairingdaten ebenfalls löschen können.

## Home-Assistant-Modell

Es bleibt **eine** Integration: `lueftungsberater`.

Direkte Stationen referenzieren ihr bereits vorhandenes ESPHome-Gerät und dessen normale Recorder-Entities; es wird kein zweites physisches Gerät gespiegelt. Für ESP-NOW-Stationen wird der Master als Hub-Gerät registriert und die Stationen werden als eigene physische Geräte mit `via_device_id` zum Master geführt. Die Raumzuweisung erfolgt in beiden Fällen im Lüftungsassistenten. Die Transportimplementierung darf keine zweite Lüftungslogik und keine zweite manuelle Sensorzuordnung erzeugen.

## In v0.10.0 bereits aktiv

- Subentry-Typ **Lüftungsstation** in derselben `lueftungsberater`-Integration.
- Auswahl **Direkt über ESPHome / Home Assistant** oder **Über Master / ESP-NOW** beim Hinzufügen.
- Direkte ESPHome-Geräte werden automatisch nur dann angeboten, wenn genau je ein CO₂-, Temperatur- und Luftfeuchtesensor erkannt wird; anschließend genügt die einmalige Raumzuordnung.
- Zuordnung einer Station zu genau einem vorhandenen Raum; ein Raum kann höchstens eine Hardwarestation besitzen.
- Räume dürfen ohne separat ausgewählte Temperatur-/Feuchtesensoren angelegt werden und werden nach der Stationszuordnung automatisch aus den SCD41-Rohwerten versorgt.
- Ein Direkt-Setup erzeugt kein Master-Gerät. Master-/Hub-Gerät plus `via_device_id`-Stationsgeräte werden nur für den ESP-NOW-Weg verwendet.
- Master-/ESP-NOW-Stationen erhalten eigene Entities für CO₂, Temperatur, Luftfeuchte und Online sowie optionale Diagnosen (RSSI, Hops, Antwortzeit, Retries). Direkte Stationen verwenden stattdessen ihre vorhandenen ESPHome-Entities.
- `POST /api/lueftungsberater/hardware/discover`: merkt einen JOIN-Kandidaten (`entry_id`, `hardware_id`, `master_id`, Name/Fähigkeiten).
- `POST /api/lueftungsberater/hardware/report`: akzeptiert nur bereits zugeordnete Hardware, aktualisiert Rohwerte und gibt `room_name`, `status`, `recommendation`, `recommendation_key`, `display_mode` und `safety_lock` zurück.

Beide Endpunkte verwenden die normale Home-Assistant-Authentifizierung. Ein unbekanntes Gerät wird bei `report` **nicht** als Messquelle akzeptiert, sondern nur als Pairing-Kandidat vorgemerkt.
