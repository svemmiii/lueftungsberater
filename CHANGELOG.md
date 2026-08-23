## 0.6.16 - Alpha

- Begründungstexte unter **„Warum diese Empfehlung?“** sind jetzt reine Texte und nicht mehr anklickbar oder unterstrichen.
- Ein Klick auf den Begründungstext öffnet weder die Lüftungsberater-Entity noch eine Warn-/Wetter-Entity.
- Anklickbare Verläufe bleiben auf echte Mess- und Statuswerte beschränkt.
- Keine Änderung an Entscheidungslogik, Warnlogik oder Schwellenwerten.

## 0.6.15 - Alpha

### Warnquellen-Hotfix

- Warn-App / Warndienst ist weiterhin vollständig optional; ohne Auswahl wird wie bisher `Kein Warndienst` verwendet.
- NINA, DWD Weather Warnings und erkannte weitere Warnanbieter erscheinen wieder im Einrichtungs-Dropdown.
- Fehler behoben, bei dem der Select-Selector einen String (`none`) mit beschrifteten Optionsobjekten gemischt hat und dadurch auf die Fallback-Auswahl ohne Warnanbieter zurückfiel.
- Neue Regressionstests prüfen gleichzeitig `Kein Warndienst`, NINA und DWD sowie den optionalen Default.
- Keine Änderung an Pflichtsensoren, Lüftungslogik, Warnbewertung, Remote-Protokoll oder Dashboard-Verhalten.

## 0.6.14 - Alpha

### Tests und Einrichtungsdialog

- NINA-Warnauswertung funktioniert jetzt auch dann weiter, wenn das Entity Registry in einem leichten Test-/Startup-Kontext noch nicht verfügbar ist; Legacy-Warnattribute bleiben vollständig nutzbar.
- Remote-Erfolgs- und Reconfigure-Bestätigungsseiten werden jetzt als echte Home-Assistant-Bestätigungsdialoge markiert und nicht automatisch übersprungen.
- GitHub-Pytest-Workflow korrigiert: Home-Assistant-Version wird über `importlib.metadata` ausgelesen, der fehlerhafte `homeassistant.__version__`-Zugriff wurde entfernt.
- Pytest läuft ausführlich mit `-v`; unnötiges pip-Cache-Setup ohne Requirements-Datei wurde entfernt.
- Keine Änderung an Lüftungslogik, Schwellenwerten, Tailscale-Remote-Protokoll oder vorhandenen Entities.

# Changelog

## 0.6.13 - Alpha

Bugfix-Release für die Einrichtungsflüsse aus v0.6.12.

- Erfolgreiche Tailscale-Remote-Verbindungen können wieder abgeschlossen und gespeichert werden; ein Fehler im Progress-/Bestätigungsübergang wurde behoben.
- Remote-Protokoll bleibt Version 1 und damit kompatibel zu entfernten Lüftungsberater-Installationen ab v0.6.10.
- Lokale Lüftungsberater verwenden keine zufällig erzeugte `ConfigEntry.unique_id` mehr; mehrere manuell angelegte lokale Installationen bleiben voneinander unabhängig.
- Die kurzfristig in v0.6.12 erzeugten `local:...`-Unique-IDs werden beim Update automatisch entfernt.
- Der Aufbau der lokalen Einrichtung ist gegen fehlerhafte/ungewöhnliche Warnanbieter-Einträge abgesichert, damit ein einzelner Registry-Eintrag nicht den ganzen Config Flow mit „Fehler“ beendet.
- Zusätzliche Config-Flow-Regressionstests decken erfolgreiche Remote-Einrichtung und mehrere lokale Installationen ab.
- Der GitHub-Workflow führt Pytest nun ausdrücklich mit aus.

## 0.6.12 - Alpha

- Mehrere lokale Lüftungsberater-Installationen explizit unterstützt und neue lokale Config Entries mit eigener Unique-ID versehen.
- Remote-Einrichtung nutzt jetzt Home Assistants nativen Fortschrittsdialog und zeigt anschließend Berater und gefundene Räume übersichtlicher an.
- Remote-Topologie erscheint ohne Remote-Entities im Geräte-Register als Remote Home Assistant → Lüftungsberater → Räume.
- Remote-Raumnamen bleiben auch bei fehlender oder noch nicht geladener Sensorik erhalten.
- CO₂-Bewertung in der Raumkarte ist anklickbar und öffnet den Verlauf des CO₂-Statussensors.
- Neuer Sensor für die absolute Feuchtedifferenz (Δ g/m³); der Delta-Wert ist dadurch ebenfalls anklickbar und historisierbar.
- NINA-Auswertung liest Headline und Severity zusätzlich aus den neuen separaten NINA-Sensoren und bleibt damit auf die angekündigte Entfernung der alten Warning-Attribute vorbereitet.
- Keine Änderung an Lüftungsschwellen, Farblogik, Tailscale-Sicherheitsmodell oder Remote-Historienprinzip.

## 0.6.11
- Remote-Einrichtung und Remote-Rekonfiguration besitzen jetzt einen eigenen Verbindungstest mit sichtbarer Erfolgsbestätigung, bevor die Zugangsdaten gespeichert werden. Die Bestätigung zeigt zusätzlich, wie viele Lüftungsberater-Instanzen und Räume gefunden wurden.
- Der visuelle Editor der Übersicht zeigt jetzt lokale und Tailscale-Remote-Installationen gemeinsam an. Ganze Installationen sowie einzelne Räume können ein- oder ausgeblendet werden.
- Installationen und Räume lassen sich direkt im Editor mit Pfeiltasten in die gewünschte Reihenfolge bringen; neue Räume werden weiterhin automatisch aufgenommen, solange sie nicht gezielt ausgeblendet wurden.
- Der Editor rendert strukturelle Remote-Änderungen nicht mehr mitten während einer Texteingabe neu und schützt damit den Eingabefokus zusätzlich vor späten Remote-Updates.
- Der Raumdialog der Übersicht wurde grundlegend überarbeitet: Er wird erst beim Öffnen erzeugt und beim Schließen oder Verlassen der Dashboard-Ansicht vollständig zerstört. Dadurch können keine unsichtbaren modalen Dialoge im Hintergrund hängen bleiben.
- Raumdialoge sind rein browserlokal. Das Schließen auf Handy, Tablet oder PC verändert keinen gemeinsamen Home-Assistant-Zustand und kann damit kein anderes Gerät gezielt schließen.
- Während der bestehenden 3-Minuten-Remote-Karenz bleibt ein bereits geöffneter Remote-Raum erhalten. Erst wenn die Remote-Instanz vom Backend wirklich als nicht erreichbar markiert wird, wird die Detailansicht beendet.
- Fehlende Pflicht-Sensordaten führen jetzt zu einem klaren gelben Zustand **„Aktuell keine zuverlässige Empfehlung möglich“** statt des sichtbaren internen Schlüssels `recommendation.unknown`. Eine natürliche Erklärung wird auf Deutsch, Englisch und Türkisch angezeigt.
- Der Hauptsensor behält bei unvollständigen Sensordaten seine Raum-/Instanz-Metadaten. Dadurch bleibt der Raum in lokalen und entfernten Übersichten eindeutig erkennbar, auch wenn gerade keine vollständige Berechnung möglich ist.
- Remote-Snapshots enthalten zusätzlich eine stabile Raumkennung und den Raumnamen als Metadaten; es werden weiterhin keine fremden Entity-IDs oder Recorder-Historien übertragen.
- Keine Änderung an Lüftungs-Schwellenwerten oder der Grün/Gelb/Rot-Entscheidungslogik.

## 0.6.10
- Mehrere lokale Lüftungsberater-Instanzen werden jetzt unterstützt und in der gemeinsamen Übersicht automatisch nach Instanz gruppiert. Bei nur einer Instanz wird die Gruppenebene übersprungen.
- Die Gesamtansicht wurde bewusst verkürzt: Pro Raum erscheinen nur Fenster-Symbol, Raumname, aktuelle Empfehlung, Statusfarbe und bei geöffnetem Fenster/Tür das kleine `offen`-Badge.
- Ein Tipp auf einen Raum öffnet jetzt eine temporär erzeugte vollständige Raumkarte im Dialog statt der More-Info-Ansicht des Hauptsensors. Eine separat konfigurierte Raumkarte ist dafür nicht nötig; nach dem Schließen wird die temporäre Karte wieder entfernt.
- Editor-Fokusfehler behoben: laufende Sensorupdates rendern den visuellen Karteneditor nicht mehr vollständig neu und werfen den Cursor dadurch nicht mehr aus Textfeldern.
- Lange offene Lüftungen werden lesbar formatiert: bis einschließlich 60 Minuten in Minuten, danach natürlich als Stunden und Minuten (z. B. `13 Stunden und 20 Minuten`).
- Eigener Sensor für die absolute Außenfeuchte ergänzt. Dadurch ist der Außenwert in `g/m³` auf lokalen Raumkarten anklickbar und besitzt einen eigenen Recorder-Verlauf.
- Türkisch als dritte vollständig unterstützte Sprache ergänzt. Deutsche, englische und türkische Empfehlungen bleiben eigenständig und natürlich formuliert.
- Englische Formulierungen weiter geglättet, u. a. `while your target is` und `opening the windows` statt technisch klingender Formulierungen.
- Tailscale-Remote hinzugefügt: Andere Home-Assistant-Installationen mit Lüftungsberater können über eine Tailscale-IP bzw. einen auf Tailscale auflösenden MagicDNS-Namen und einen Home-Assistant-Access-Token eingebunden werden.
- Remote überträgt ausschließlich aktuelle Lüftungsberater-Raum-Snapshots. Es werden keine fremden Sensor-Entities und keine Recorder-Historien auf der empfangenden Instanz angelegt.
- Remote-Snapshots liegen nur flüchtig im RAM und werden durch neue Werte ersetzt. Abruf alle 30 Sekunden; kurze Aussetzer werden toleriert und erst nach rund 3 Minuten ohne erfolgreichen Abruf wird `Nicht erreichbar` angezeigt.
- Remote-Raumdetails verwenden dieselbe vollständige Darstellung, bleiben aber bewusst read-only; lokale Karten behalten ihre anklickbaren Messwerte und Verläufe.
- Tailscale wird beidseitig erzwungen: Zieladressen werden bei Einrichtung und jedem Abruf geprüft; zusätzlich lehnt der Snapshot-Endpunkt Anfragen ab, deren Quell-IP nicht aus einem Tailscale-Adressbereich stammt.
- Keine Änderung an den eigentlichen Lüftungs-Schwellenwerten oder der Grün/Gelb/Rot-Entscheidungslogik.

## 0.6.9
- Messwert und Einheit werden in Karten und natürlich formulierten Begründungen als untrennbare Einheit dargestellt. Dadurch kann z. B. `69,8 °F` nicht mehr so umbrechen, dass `°F` alleine in der nächsten Zeile steht.
- Dafür wird ein schmaler geschützter Abstand zwischen Zahl und Einheit verwendet; bei Platzmangel wandern Zahl und Einheit gemeinsam in die nächste Zeile.
- Gilt neben °C/°F auch für %, ppm und g/m³.
- Keine Änderung an Lüftungs-, Warn-, Schwellen- oder Farblogik.

## 0.6.8
- Vollständige natürliche Laufzeit-Lokalisierung für Deutsch und Englisch ergänzt. Empfehlungen und Begründungen werden nicht wortwörtlich maschinell übersetzt, sondern pro Sprache eigenständig formuliert.
- Die Entscheidungsengine liefert jetzt sprachneutrale Bedeutungs-Keys und Messwerte; die Formulierung erfolgt erst in einer eigenen Lokalisierungsschicht.
- Die Raum- und Übersichtskarten richten sich nach der Sprache des aktuell angemeldeten Home-Assistant-Benutzers. Backend-Attribute verwenden die Home-Assistant-Systemsprache.
- Karten, visuelle Editoren, Status-, Messwert-, Fallback- und Hinweistexte vollständig auf Deutsch und Englisch lokalisiert.
- Zahlen werden in der Karte passend zur Sprache formatiert.
- Die Fallback-Solltemperatur im Einrichtungsdialog folgt jetzt dem Home-Assistant-Einheitensystem (°C/°F); intern wird weiterhin einheitlich in °C gerechnet.
- Eigene, natürlich formulierte Warnbegründungen für Starkregen, Dauerregen, Gewitter, Hagel, Sturm/Wind sowie Luft-/Rauchwarnungen ergänzt.
- Originaltexte externer Warnanbieter werden nicht automatisch übersetzt oder verfälscht; sie bleiben separat als `original_warning_text` erhalten.
- Die Lüftungs-, Schwellen- und Farblogik wurde durch die Internationalisierung nicht verändert.

## 0.6.7
- Warnlogik verfeinert: Regen bzw. der Weather-Zustand `pouring` ist nicht mehr automatisch Rot.
- DWD-Wetterwarnungen werden anhand der Stufe der konkreten Einzelwarnung unterschieden: Stufe 1/2 und Vorabinformationen führen zu Gelb/Vorsicht, Stufe 3/4 zu Rot/Vermeiden.
- Generische CAP-/NINA-artige Wetterwarnungen werden bei `Moderate` als Vorsicht und bei `Severe`/`Extreme` als Gefahr bewertet.
- Neuer Engine-Modus `wetter_vorsicht` für relevante, aber nicht rote Wetterwarnungen.
- Fehler behoben, durch den der neue `warning_source`-Selektor die Binary-Entity „Kritische Gefahr“ nicht zuverlässig aktivierte.
- `warning_source: none` wird jetzt korrekt als „kein Warndienst“ behandelt und nicht als konfigurierter Provider.
- Temperaturen aus Sensor-, Weather- und Climate-Entities werden vor der Entscheidungslogik auf °C normalisiert; dadurch funktionieren auch Fahrenheit-Setups korrekt.
- Die Dashboard-Karte zeigt Temperaturen anschließend wieder in der Home-Assistant-Anzeigeeinheit an.
- Bei aktivem Außensensor-Fallback kennzeichnet die Raumkarte den betroffenen Außenwert dezent mit „Wetterdienst“.
- Pro Raum gibt es jetzt einen gemeinsamen eventgesteuerten `DataUpdateCoordinator`; Wetter-, Warn- und Engine-Auswertung werden pro Quelländerung nur einmal berechnet und von allen Raum-Entities gemeinsam verwendet.
- GitHub Actions führt zusätzlich zu HACS und Hassfest jetzt automatisch die Python-Unit-Tests mit `pytest-homeassistant-custom-component` aus.
- Zusätzliche Regressionstests für Wetterwarnstufen, Starkregen/`pouring`, Warn-Vorsicht und Temperaturkonvertierung ergänzt.

## 0.6.6
- Robuster Fallback für eigene Außensensoren ergänzt.
- Außentemperatur und Außenluftfeuchtigkeit fallen unabhängig voneinander auf die aktuelle `weather.*`-Entity zurück, wenn der jeweils konfigurierte lokale Sensor `unknown`, `unavailable` oder anderweitig ungültig ist.
- Sobald ein lokaler Außensensor wieder einen gültigen Wert liefert, wird automatisch wieder auf ihn zurückgeschaltet.
- Neue Diagnoseattribute an der Raum-Hauptentity: `outdoor_temperature_source` und `outdoor_humidity_source` (`local_sensor`, `weather_fallback`, `weather_service` oder `unavailable`).
- Die eigentliche Entscheidungslogik in `engine.py` bleibt unverändert.

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
