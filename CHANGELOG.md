# Änderungen

Hier stehen die **zusammengefassten Änderungen pro Version**, nicht einzelne interne Testläufe oder unfertige Zwischenstände. Für ältere tatsächlich veröffentlichte Fassungen ist die [GitHub-Releaseübersicht](https://github.com/svemmiii/lueftungsberater/releases) die maßgebliche Quelle.

## v0.12.0 – Alpha (5. November 2026)

- Anzeige-Randfälle: Ein eingerichteter, aber zeitweise ausgefallener Fensterkontakt erhält auch in der klassischen und individuell gestalteten Detailansicht einen gelben Hinweis. Insbesondere behauptet das Feld „Zuletzt gelüftet“ während `grace`, `unknown` oder `unavailable` keine weiterhin bestätigte Fensteröffnung. Der letzte bekannte Zustand wird intern nicht verändert; der Raum bewertet verfügbare Messwerte weiter. `unknown` und `unavailable` verändern nicht allein die Hauptampel.
- Ältere Remote-Snapshots der zwischenzeitlichen v0.12.0 mit vereinheitlichten Farben verwenden in der Lüftungsperspektive wieder den ursprünglichen nativen Empfehlungstext. Die damals gespeicherte, raumbezogene Begründung wird dort nicht zusätzlich angezeigt, wenn ihre Herkunft nicht zur Lüftungsperspektive passt; offizielle Sicherheitshinweise bleiben sichtbar. Aktuelle Remote-Versionen bleiben unverändert.

### Perspektivengetrennte Raum-Handlungsampel und Lüftungseignung (05.11.2026)
- **Grün heißt Fenster schließen oder geschlossen lassen**, auch wenn Innenwerte noch erhöht sind und weiteres Lüften wegen Außenluft oder fehlendem Fortschritt nicht sinnvoll ist. Gelb/Orange/Rot fordern niemals gleichzeitig zum Schließen auf; die interne Lüftungseignung bleibt als Diagnose erhalten.
- **Zwei Perspektiven bleiben getrennt:** `room_air` zeigt die sinnvolle Fensteraktion; `ventilation` bewertet die Eignung der Außenbedingungen (Grün bedeutet dort weiterhin zum Lüften geeignet). Raumkarte, Übersicht und Remote-Daten berücksichtigen den gewählten Modus.
- Bestehende Sensorattribute `ventilation_status` und `ventilation_recommendation_key` behalten ihre native Bedeutung. Der historische Entscheidungssensor speichert weiterhin die beim jeweiligen Modus gewählte Empfehlung; alte Recorder-Farben werden nicht nachträglich als neue Handlungsfarben ausgelegt. Der native Hauptsensorzustand für Automationen bleibt unverändert.
- Ein zeitweise nicht verfügbarer optionaler Fensterkontakt erscheint weiterhin als gelber Hinweis, überschreibt aber keine anhand der übrigen Sensoren ermittelte Raum-Handlungsfarbe.
- Fünf-Minuten-Schutz und 15-%-Ausnahme bleiben erhalten; wetterbedingte Schließentscheidungen werden auch während der Mindestzeit sichtbar. **Grün darf keinen Lüftungserfolg vortäuschen:** Die Erfolgsbestätigung prüft Sitzungs- und Messwerte separat.
- Historische Tests und aktualisierte Handlungsinvarianten für Engine, Transport, Lifetime-Tests und Frontend ergänzt.

### CI-Korrekturen (GitHub Actions, 05.11.2026)
- Veralteten DWD-Retry-Test auf höchstens einen Versuch pro Station und Abruf sowie Wiederaufnahme im nächsten Abruf angepasst.
- Unvollständige Lifecycle-/Speicher-Test-Attrappen um die bereits vorhandenen Zustandsfelder und den Ablauf-Timer ergänzt.
- Manifest um die gültige HACS-Kategorie `climate.fans_ventilation` ergänzt.


### Verlässlichere Fenster- und Feuchtebewertung

- Ein Fensterkontaktwechsel allein lässt die Raumampel nicht zwischen Grün und Nicht-Grün springen. Tatsächliche Messwertverschlechterungen und Sicherheitswarnungen können die Anzeige jederzeit verschärfen.
- Fünf Minuten Öffnungsdauer sind eine Mindestzeit, **kein Erfolgsnachweis**. Kürzere Lüftungen werden als Abbruch behandelt; ausschließlich bei mindestens 15 % Sicherheitsreserve innerhalb aller relevanten Gutbereiche kann eine vorzeitige Grünfreigabe erfolgen.
- Feuchtelüftungen behalten ungelösten Bedarf nach Abbruch, nach mindestens fünf Minuten ohne Verbesserung und nach wirkungslosen Langzeitversuchen. Die nun **grüne Handlungsampel** bei einer Schließempfehlung bedeutet trotzdem keinen behobenen Feuchtewert und keinen nachgewiesenen Lüftungserfolg.
- Bestätigte, erfolgreiche und abgebrochene Sitzungen werden getrennt geführt. Anzeige- und Sitzungszustände bleiben bei regelmäßigen Aktualisierungen und Neustarts konsistent.
- Begründungstexte erklären die aktuellen Lüftungsgründe und die sinnvollste Fensteraktion, ohne störende Zehntelminuten-Angaben; Deutsch, Englisch und Türkisch bleiben unterstützt.

### Individuelle Luftbeobachtung

- Optionale Raumeinstellung für **passive Belüftung** sowie begrenzte Beobachtung von CO₂-, Feuchte-, Temperatur- und verfügbaren Luftqualitätswerten; sie funktioniert auch ohne CO₂-Sensor mit eingeschränkter Aussagekraft.
- Ohne Fensterkontakt wird möglicher Luftaustausch nur **vermutet**, nicht als bestätigte Fensterlüftung gespeichert. Veraltete Vermutungen verschwinden nach 60 Minuten auch ohne weitere Sensoränderung.
- Die 24-Stunden-Routine kann bei nachweislich stabil guter Luft zurücktreten; große CO₂-Schwankungen, Messlücken und eigenständige Feuchte-, Schimmel- oder Schadstoffgründe bleiben relevant.

### Ressourcen, Datenquellen und Sicherheit

- Länder- und Warnregionsgeometrien werden über eine indexierte SQLite-Datenbank bedarfsgerecht geladen. Der bisherige vollständige JSON-RAM-Aufbau entfällt; Warnregions- und Länderdaten bleiben enthalten.
- Die 15-Minuten-Feuchtespitzenhistorie ist auf **180 Messwerte pro Raum** begrenzt. Bei sehr schnellen Sensorupdates werden Originalwerte und Zeitstempel nach schmalen Feuchtebereichen zusammengefasst. Die maximale Abweichung des gleitenden Minimums beträgt für gültige 0–100 % unter **0,625 Prozentpunkten**; Grenzfälle unmittelbar an der Sechs-Punkte-Spitzenschwelle können verzögert reagieren.
- Die bestehende gemeinsame, zeitversetzte Außenabfrageplanung bleibt erhalten. **DWD- und UBA-Stationskandidaten werden innerhalb eines Abrufs höchstens einmal angefragt.** Geeignete Ersatzstationen werden weiter geprüft; fehlende Messgrößen dürfen weiterhin aus dem bestehenden Modell-Fallback stammen.
- Doppelte Snapshot-Berechnungen und unnötige Messverlaufs-Schreibvorgänge wurden vermindert. Strukturierte amtliche Warnungen und ihre Sicherheitssperren bleiben vorrangig.

### Dashboard und Remote-Übersicht

- Die Raumkarte erlaubt eine individuell einstellbare Hintergrunddeckkraft von **0–100 %**; ohne Einstellung gilt weiterhin das aktive Theme. Texte und Ampelfarben werden nicht mit transparent.
- Die Gesamtansicht und ihr visueller Editor laden Remote-Gruppen beim Aufruf. **Ohne eingerichtete Remote-Instanzen läuft anschließend kein 30-Sekunden-Remote-Polling mehr.** Ein Home-Assistant-Konfigurationsereignis erkennt nachträglich hinzugefügte Verbindungen. Bei vorhandenen Remote-Instanzen werden die bestehenden 30-Sekunden-Aktualisierungen beibehalten; bei Entfernung und beim Abbau der Karte werden Timer und Abonnements freigegeben.

### Qualitätsstatus

- Ergänzte Regressionstests für Sitzungs- und Ampelfarben, Feuchte-Spitzen, Stationsausfälle und Remote-Gesamtansichten sowie bestehende Frontend- und Geodaten-Gegenproben.
- **Alpha / Pre-release:** Nach der Änderung der Handlungsampel stehen ein neuer vollständiger GitHub-Validate-Lauf und Update-/UI-Smoke-Tests auf einer echten HA-Instanz aus. Vor dem Update ein vollständiges Backup erstellen.

## v0.11.10

### Standort und Verfügbarkeit

- Feste Home-Assistant-Zonen wie `zone.home` werden bei unveränderten Koordinaten nicht mehr nach fünf Minuten fälschlich als neuer Standort gewertet. Geänderte Koordinaten oder relevante Höhenänderungen lösen weiterhin einen Standortwechsel aus.
- Normale Aktualisierungen behalten bereits verfügbare Wetter-, Prognose- und Warnungsdaten bis zur jeweils vorgesehenen Gültigkeitsgrenze. Ein unnötiger Neustart der automatischen Datenquellen entfällt.
- Bei tatsächlichen Standortwechseln oder nicht mehr gültigen mobilen Positionen werden ortsgebundene Daten weiterhin von neuen Warngebieten getrennt. Ein Ausfall wird nicht als Entwarnung behandelt.

### Luftqualität und Anbieterformate

- Die langfristige lokale Luftqualitäts-Basislinie orientiert sich am tatsächlich akzeptierten Außenstandort statt an einer eventuell abweichenden Wetter-Entity. Die bestehende Speicherung und bereits gelernte Werte bleiben erhalten; neue Standorte verwenden getrennte Ortsbereiche.
- Der Parser für UBA-Schadstoff-Metadaten akzeptiert zusätzlich indizierte JSON-Objekte und Einträge ohne wiederholte Komponenten-ID. Unbekannte Metadaten werden weiterhin nicht als Messwerte interpretiert.
- Regressionstests für unbewegte Zonen, echte Standortänderungen, mobile Positionen, Luftqualitäts-Ortsbindung und UBA-Metadaten ergänzt.

**Hinweis:** Die Änderungen wurden mit gezielten isolierten Tests und Syntaxprüfungen überprüft. Ein vollständiger Home-Assistant-Integrationstest mit echten Anbieterantworten bleibt für die Alpha-Version erforderlich.

## v0.11.9

### Automatische Datenquellen und weniger unnötige Abrufe

- Gemeinsame, verteilte HTTP-Abrufe für Wetter, Luftqualität und Warnungen mit begrenzter Parallelität.
- Standortbezogene Stationsauswahl: verfügbare, frische DWD- und UBA-Messwerte werden je Messgröße bevorzugt; fehlende Daten können aus geeigneten Modellen ergänzt werden.
- Dringliche Warnungsabrufe werden bei freier Kapazität bevorzugt, ohne das übrige Abrufsystem grundsätzlich zu umgehen.

### Amtliche Warnungen und Sicherheit

- Mehrsprachige CAP-Informationsblöcke bleiben mit ihren eigenen Zeit-, Gebiets- und Herkunftsangaben erhalten.
- Strukturierte Böenwerte unterstützter Anbieter werden unabhängig davon geprüft, ob der begleitende Freitext sprachlich erkannt wird.
- Für eindeutig zugeordnete amtliche Böen ab **90 km/h** kann eine Fenstersperre **30 Minuten vor dem erwarteten Beginn** greifen.
- Angaben zu Einheiten, strikt offenen Geschwindigkeitsgrenzen, Orten, Höhen und einzelnen Zeitfenstern werden differenzierter behandelt; verneinte oder widersprüchliche Aussagen werden nicht einfach gleichgesetzt.
- Die Warntextverarbeitung besitzt getrennte Spracheinstiege für Deutsch, Englisch und Türkisch; weitere unterstützte Textsprachen werden separat verwaltet.
- Bestätigte Schutzsperren werden bei bloßen Provider-Ausfällen nicht automatisch als entwarnt behandelt.

### Home Assistant und Darstellung

- Zeitzonenauflösung in asynchronen Abläufen so angepasst, dass neue Zeitzonen nicht direkt auf dem Event-Loop-Thread von der Festplatte geladen werden müssen.
- Vorhandene Raumkonfigurationen und Sensorzuordnungen werden bei einem normalen Update weiterverwendet; die Oberfläche und der HTTP-Planer bleiben in ihren bisherigen Aufgabenbereichen erhalten.
- Zusätzliche Regressionstests für Warnungen, Zeitangaben und die Zusammenarbeit mit der Sicherheitslogik.

### Wichtige Grenzen

- Es handelt sich weiterhin um eine **Alpha-Version**. Nicht jeder Standort besitzt automatische amtliche Warnabdeckung.
- Sehr starke **gemessene** Böen ohne passende amtliche Warnung sind nicht automatisch derselbe Hardlock wie eine amtliche Windwarnung.
- Für ein produktives Update empfiehlt sich ein Home-Assistant-Backup.

Ausführliche aktuelle Bedien- und Sicherheitshinweise stehen unter [Dokumentation](README.md#dokumentation).

---

**Frühere Veröffentlichungen:** [GitHub Releases](https://github.com/svemmiii/lueftungsberater/releases). Die früheren, nicht veröffentlichten internen Testzwischenstände werden hier bewusst nicht als eigene Versionen aufgeführt.
