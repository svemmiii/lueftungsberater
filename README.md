<p align="center">
  <img src="custom_components/lueftungsberater/brand/icon@2x.png" width="180" alt="Lüftungsassistent">
</p>

# Lüftungsassistent

**Alpha-Integration für Home Assistant · aktueller Stand: v0.7.7**

Lüftungsassistent bewertet Innen- und Außenbedingungen gemeinsam und gibt für jeden Raum eine verständliche Lüftungsempfehlung aus. Je nach vorhandener Hardware können Temperatur, Luftfeuchtigkeit, CO₂, Fenster-/Türkontakte, Thermostate, Wetterdaten, Luftqualität und Warnmeldungen berücksichtigt werden.

> **Status:** Alpha. Die Integration wird im Alltag eingesetzt, aber weiterhin aktiv getestet und weiterentwickelt. Sie ist ein Beratungswerkzeug und ersetzt keine medizinische, bauphysikalische oder amtliche Bewertung.

## Funktionen

- Eigene Lüftungsempfehlung pro Raum mit kurzer Begründung und empfohlener Dauer
- Zwei wählbare Ansichten derselben Entscheidungsengine:
  - **Lüftungsbedarf (Standard):** Grün = aktuell kein relevanter Lüftungsgrund, Gelb/Orange = zunehmender Bedarf, Rot = jetzt lüften
  - **Lüftungsampel:** Grün = Lüften sinnvoll, Gelb = Abwägung/Übergang, Orange = eher geschlossen lassen, Rot = Lüften deutlich nachteilig
- Separater **🔒 Sperrzustand** für echte Schutzlagen und amtliche Schließanweisungen
- Absolute Feuchtigkeit innen und außen sowie Differenz in g/m³
- Optionaler CO₂-Sensor pro Raum mit Hysterese, Kurzzeit-Failsafe und stabilen Lüftungssitzungen
- Automatischer Lüftungsverlauf mit Fenster-/Türkontakt
- Bestätigte Lüftung ab 5 Minuten; bei einer tatsächlich gestarteten CO₂-Lüftung wird diese Mindestzeit gezielt stabilisiert
- Wetterdaten über normale Home-Assistant-`weather.*`-Entities
- Optionale Warnquelle mit erweiterter Unterstützung für DWD und NINA
- Plausibilitätsgeprüfte Außenluftqualität über Ozon, PM2.5, PM10, NO₂ und SO₂, ergänzt um lokalen Verlauf und Trend
- Optionaler eigener Außen-CO₂-Sensor
- Optionaler Feuchte-/Schimmelschutz mit realem Oberflächentemperatursensor und zeitlichem Kontext
- Forecastbasierte Nachtlüftungsstrategie mit einstellbarem Zeitfenster
- Detaillierte Raumkarte und kompakte Mehrraumübersicht direkt im Home-Assistant-Kartenpicker
- Oberfläche und Empfehlungen auf Deutsch, Englisch und Türkisch
- Dashboard-Texte folgen der Sprache des aktuell angemeldeten Home-Assistant-Benutzers
- Unterstützung für Celsius- und Fahrenheit-Setups
- Assistentenweite Warn-/Entwarnungsbenachrichtigungen und pro Raum aktivierbare Lüftungsstatus-Meldungen über eine normale Home-Assistant-`notify`-Entity
- Tailscale-Remote für ausgewählte Räume anderer Home-Assistant-Installationen, ohne gespiegelte Remote-Messentities
- Recorder-schonende Speicherung; Lüftungsassistent-Entities werden gezielt auf maximal 20 Tage Recorder-Verlauf begrenzt, sofern die globale Recorder-Konfiguration nicht bereits weniger behält

## Voraussetzungen

- Home Assistant **2026.6.0 oder neuer**
- HACS für die empfohlene Installation
- Pro Raum mindestens:
  - Innentemperatur
  - relative Luftfeuchtigkeit innen
- Eine `weather.*`-Entity mit Außentemperatur und Außenluftfeuchtigkeit

Optional:

- CO₂-Sensor
- Fenster-/Türkontakte
- Climate-/Thermostat-Entity
- Temperatursensor an einer kalten/kritischen Oberfläche
- Warnintegration wie NINA oder DWD Weather Warnings
- `notify`-Entity für Benachrichtigungen
- eigener CO₂-Außensensor

## Installation über HACS – Custom Repository

1. HACS öffnen.
2. Oben rechts **⋮ → Custom repositories** auswählen.
3. Repository eintragen:

   `https://github.com/svemmiii/lueftungsberater`

4. Typ **Integration** auswählen.
5. Repository hinzufügen und **Lüftungsassistent** installieren.
6. Home Assistant neu starten.
7. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Lüftungsassistent** öffnen.

## Einrichtung

### 1. Gemeinsame Außendaten

Beim ersten Einrichten wählst du:

- einen **Wetterdienst**
- optional eine **Warn-App / einen Warndienst**
- die gewünschte **Ampeldarstellung**
- optional eigene Außensensoren, darunter auch **CO₂ außen**
- optional ein **Benachrichtigungsziel** und die gewünschten Assistenten-Ereignisse

Eigene Außensensoren können in den erweiterten Optionen verwendet werden. Sind konfigurierte Außentemperatur- oder Außenfeuchtesensoren vorübergehend `unavailable` oder `unknown`, fällt Lüftungsassistent für den jeweils betroffenen Wert automatisch auf die konfigurierte `weather.*`-Entity zurück, sofern dort ein gültiger Wert vorhanden ist. Die Raumkarte kennzeichnet diesen Fallback mit **Wetterdienst**.

### 2. Räume hinzufügen

Für jeden Raum können konfiguriert werden:

- Temperatur
- Luftfeuchtigkeit
- optional CO₂
- optional Fenster-/Türkontakte
- optional Thermostat / Climate
- optional Temperatur einer kalten/kritischen Oberfläche
- Solltemperatur
- Nachtlüftungs-Zeitfenster **von–bis** (Standard **22:00–07:00**)
- optional raumbezogene Lüftungsstatus-Benachrichtigungen

Die Einstellungen sind in **Raumklima**, **Nachtlüftung**, **Zusatzsensoren** und **Fenster & Türen** gegliedert. Die Sensor-Auswahl wird nach passenden Home-Assistant-Geräteklassen gefiltert.

Ohne Fensterkontakt arbeitet ein Raum rein beobachtend. Mit Fensterkontakt erkennt Lüftungsassistent automatisch laufende und bestätigte Lüftungen. Eine laufende Lüftung sowie die letzte bestätigte Lüftung überstehen einen Home-Assistant-Neustart; ein beim Start kurz `unknown` oder `unavailable` meldender Kontakt beendet die Sitzung nicht fälschlich.

## Wie die Empfehlung entsteht

Lüftungsassistent bewertet den **Gesamtnutzen** des Lüftens. Ein einzelner Grenzwert gewinnt nicht automatisch gegen alle anderen Bedingungen. Sicherheit und Gesundheit haben Vorrang; anschließend werden Innenraumluft, Feuchte und Oberflächenrisiko, persönliches Temperatursoll, Komfort sowie Außenbedingungen gemeinsam eingeordnet.

Die wählbare Ampeldarstellung ändert diese Hintergrundentscheidung nicht. Sie bestimmt nur die Perspektive der sichtbaren Farbe, Empfehlung und Kurzbegründung:

- **Lüftungsbedarf:** Wie stark gibt es im Raum aktuell einen Grund zu lüften?
- **Lüftungsampel:** Wie geeignet sind die Bedingungen aktuell zum Lüften?

Echte Schutzlagen liegen außerhalb beider normalen Farbskalen und werden eindeutig als **🔒 Fenster geschlossen halten** dargestellt.

### Feuchte

Ob Lüften trocknet, richtet sich nach der **absoluten Feuchtedifferenz** zwischen innen und außen. Um **±0,5 g/m³** liegt eine technische Neutralzone gegen Messrauschen und praktisch sehr kleine Unterschiede. Sie ist kein Gesundheits- oder Normgrenzwert.

Positive Differenzen bedeuten trockenere Außenluft, negative Differenzen feuchtere Außenluft. Die Stärke der Differenz wird zusammen mit Raumfeuchte, Temperatur, CO₂ und optionalen Zusatzdaten bewertet. Eine laufende sinnvolle Feuchtelüftung erhält eine kleine Hysterese, damit die Empfehlung nicht bei jedem kleinen Sensorschritt umspringt.

### CO₂ und Mindestlüftung

CO₂ wird nicht pauschal allein anhand eines einzelnen ppm-Werts bewertet, sondern gegen die übrigen Innen- und Außenbedingungen abgewogen. Normale Schwellen besitzen Hysteresen, damit die Empfehlung stabil bleibt.

Wird aufgrund der Gesamtbewertung tatsächlich zum Lüften wegen CO₂ geraten und anschließend ein überwachtes Fenster geöffnet, erhält diese gestartete CO₂-Lüftung **mindestens 5 Minuten** Zeit. Ein schneller CO₂-Abfall beendet die Empfehlung in dieser Mindestphase nicht sofort.

- Die Mindestzeit beginnt mit der tatsächlichen Fensteröffnung.
- War das Fenster beim Entstehen des Lüftungsgrunds bereits offen, wird die vergangene Öffnungszeit berücksichtigt.
- Wird ein Fenster entgegen einer aktuellen Empfehlung wie „noch warten“ geöffnet, entsteht daraus keine künstliche 5-Minuten-Sitzung.
- Bereits beim Start bekannte und bewusst akzeptierte Außennachteile lösen während der kurzen Mindestphase kein ständiges Hin-und-her aus.
- Neue relevante Verschlechterungen sowie harte Safety-Locks und amtliche Schließanweisungen dürfen die Mindestzeit jederzeit übersteuern.
- Nach der Mindestzeit greift wieder die normale CO₂-Abschlusshysterese: 850–900 ppm gilt als Zielnähe; beendet wird nach mindestens 2 stabilen Minuten bei höchstens 850 ppm.

Der 60-Sekunden-Failsafe für einen kurz ausfallenden CO₂-Sensor sowie die relevanten CO₂-Hysterese-Zeitpunkte sind neustartsicher. Abgelaufene Werte werden nicht als aktuelle Messwerte wiederhergestellt.

### Temperatur

Die Temperaturberatung orientiert sich am persönlichen Sollwert und an der **Richtung**, in die Außenluft den Raum bewegt. Außenluft muss nicht selbst näher am Sollwert liegen, um einen zu warmen oder zu kalten Raum sinnvoll in Richtung Soll zu verändern. Sehr hohe und länger anhaltende Raumtemperaturen können zusätzlich als Hitzefaktor berücksichtigt werden.

### Feuchte-/Schimmelschutz

Die normale Feuchtebewertung funktioniert vollständig ohne Zusatzhardware. Optional kann pro Raum ein realer Temperatursensor an einer besonders kalten oder kritischen Oberfläche angegeben werden, zum Beispiel an einer bekannten Wärmebrücke.

Nur mit diesem Sensor berechnet Lüftungsassistent die relative Feuchte direkt an der gemessenen Oberfläche. Ohne Sensor werden keine Oberflächenwerte geschätzt. Ab ungefähr **80 % relativer Oberflächenfeuchte** wird die Lage stärker berücksichtigt; ein kompakter zeitlicher Kontext unterscheidet kurze Peaks von länger oder wiederholt anhaltender Belastung.

Diese Bewertung ist eine vorsichtige Beratungsheuristik und ausdrücklich **keine Schimmeldiagnose oder DIN-Grenze**.

## Wetter, Warnungen und Außenluft

### Regen und Wind

Regen ersetzt keine Feuchtebewertung. Aktueller oder unmittelbar bevorstehender Niederschlag wird als praktischer Nachteil eines geöffneten Fensters berücksichtigt. Ein späteres Regenereignis blockiert keine kurze Lüftung, wenn es außerhalb der erwarteten Lüftungsdauer plus kleiner Reserve liegt.

Starker Wind wird als Fenster-Sicherheits- und Komfortfaktor behandelt, nicht als erfundene amtliche Warnfarbe. Ab ungefähr Bft 6 wird vorsichtiger bewertet; etwa **50 km/h anhaltender Wind** oder **65 km/h Böen** können Lüften als deutlichen Nachteil in den orangefarbenen Bereich verschieben. Extreme Rohwerte können stärker wirken. Offizielle Warnlagen mit konkreter Schutzanweisung werden getrennt als Sperrzustand behandelt.

### Amtliche Warnungen

Amtliche Warnquellen werden handlungsorientiert ausgewertet. Fordert eine Warnung ausdrücklich dazu auf, Fenster oder Türen geschlossen zu halten, Lüftung/Klima abzuschalten oder Außenluftzufuhr zu vermeiden, gilt diese Schutzmaßnahme unmittelbar als harte Sperre. Eine Warnung ohne lüftungsrelevante Handlungsanweisung blockiert diesen Pfad nicht automatisch.

Entwarnungen heben eine amtliche Sperre auf. Externe Warntexte von DWD, NINA oder anderen Anbietern werden nicht automatisch übersetzt; Lüftungsassistent erzeugt eine eigene lokalisierte Begründung und bewahrt den Originaltext zusätzlich als Attribut auf.

### Außenluftqualität

Stellt der gewählte Wetter-Provider passende Ozon-, PM2.5-, PM10-, NO₂- oder SO₂-Sensoren bereit, werden plausible und aktuelle Werte nach den Klassen des Umweltbundesamt-Luftqualitätsindex bewertet. Der schlechteste verfügbare gültige Schadstoff bestimmt die absolute Außenluftbewertung.

`unknown`, `unavailable`, veraltete, negative oder offensichtlich unplausible Werte werden ignoriert. Fehlende Daten werden niemals als gute Luft interpretiert.

Zusätzlich kann Lüftungsassistent pro Standort einen größenbegrenzten typischen Bereich und den jüngsten Trend aufbauen. Dieser Kontext macht dauerhaft schlechte Luft nicht „gut“, hilft aber ungewöhnliche oder steigende Belastungen am jeweiligen Standort zu erkennen. Ein eigener Außen-CO₂-Sensor ergänzt die lokale Lüftungsbewertung, ersetzt aber keine Schadstoffmessung.

## Nachtlüftung

Pro Raum lässt sich ein eigenes Nachtfenster **von–bis** einstellen. Zeiträume über Mitternacht und ungewöhnliche Schichtzeiten werden unterstützt. Die Uhrzeiten sind reine Anzeigegrenzen und keine Aufforderung, genau dann ein Fenster zu öffnen oder zu schließen.

Sofern der Wetterdienst einen stündlichen Forecast bereitstellt, sucht Lüftungsassistent innerhalb des Nachtfensters nach einem plausiblen längeren Lüftungszeitraum. Dabei können Solltemperatur, Temperatur, Feuchte, Regen, Wind sowie aktuelle Warn- und Luftqualitätslagen berücksichtigt werden. Fehlende Forecast-Felder werden nicht geschätzt.

Für den längeren, weitgehend unbeaufsichtigten Nachthinweis werden Forecastpunkte mit mehr als **9 K** Abstand zur aktuellen Raumtemperatur verworfen. Diese Grenze gilt **nicht** für die normale Live-Lüftungsberatung.

Zur belastbaren Bewertung des letzten Abschnitts darf die Engine intern bis zu **eine Stunde hinter die konfigurierte Endzeit** in den Forecast schauen. Sichtbar verlängert wird das Nachtfenster dadurch nie. In der letzten Stunde wird bei dünner Forecastbasis kein neuer positiver Plan erfunden; ein bereits belastbarer Basisstatus kann gehalten werden, während Verschlechterungen und harte Schutzlagen weiterhin sofort wirken.

Die Nachtberatung ist immer nur eine Zusatzinformation und verändert die aktuelle Hauptampel nicht. Gibt es nachts nichts Sinnvolles zu empfehlen, bleibt der Zusatz verborgen.

## Benachrichtigungen

Benachrichtigungen laufen ausschließlich über eine ausgewählte Home-Assistant-`notify`-Entity und `notify.send_message`. Titel und Nachricht kommen vom Lüftungsassistent; Ton, Vibration, Priorität und andere gerätespezifische Eigenschaften bestimmt das gewählte Notify-Ziel.

Assistentenweite Ereignisse und Raum-Ereignisse sind getrennt:

- Warnungen, optionale Vorsichtshinweise und Entwarnungen werden einmal pro Lüftungsassistent verarbeitet.
- **„Lüften ist wieder sinnvoll“** und **„Lüften kann beendet werden“** werden bewusst pro Raum aktiviert.
- Lüftungsstatus-Hinweise sind zustandswechselbasiert und werden nicht bei jedem Sensorupdate oder direkt nach einem Neustart erneut gesendet.
- Eine rote Empfehlung allein ist kein automatischer Benachrichtigungsauslöser.

Warn-Fingerprints orientieren sich an der tatsächlich aktiven Quelle und stabilen Warnzuständen. Kleine Rohwertänderungen oder redaktionelle Änderungen derselben Warnung sollen dadurch keine identische Meldung erneut auslösen.

## Dashboard und Entities

Nach dem Neustart stehen im Kartenpicker zwei Karten zur Verfügung:

### Lüftungsassistent – Raum

Detaillierte Ansicht eines Raums mit Empfehlung, Begründung, Messwerten, Lüftungsdauer und optionaler Nachtinformation.

### Lüftungsassistent – Übersicht

Kompakte Mehrraumansicht mit Name, Empfehlung, Statusfarbe und bei Bedarf einem **offen**-Badge. Ein Tipp auf einen Raum öffnet dessen vollständige Detailkarte erst in diesem Moment in einem Dialog; es laufen keine unsichtbaren Detailkarten im Hintergrund.

Bei mehreren lokalen oder Remote-Instanzen kann die Übersicht gruppieren. Im visuellen Editor lassen sich sichtbare Installationen und Räume auswählen und sortieren.

Lokale Mess- und Statuswerte verlinken auf Home Assistants More-Info-/Verlaufsansicht. Der farbige Kopf-/Statusbereich öffnet die Lüftungsassistent-Hauptentity; Erklärungstexte und Lüftungsdauer bleiben reine Texte.

Der Hauptsensor ist bewusst die zentrale Automation-Schnittstelle und verwendet Zustände wie `open_now`, `keep_open`, `close_now`, `keep_closed` und `wait`. Eine zusätzliche Binary-Entity „Lüften empfohlen“ wird nicht erzeugt. Wenn eine passende Warnquelle vorhanden ist, steht pro Raum zusätzlich ein Safety-Binary-Sensor für eine **kritische Gefahr / Schutzsperre** zur Verfügung.

## Mehrere Instanzen und Tailscale-Remote

Mehrere lokale Lüftungsassistent-Instanzen können parallel eingerichtet werden, zum Beispiel für unterschiedliche Wohnungen oder Standorte.

Zusätzlich kann eine andere Home-Assistant-Installation über **Tailscale-Remote** eingebunden werden. Dafür muss die entfernte Instanz über eine Tailscale-IP oder einen MagicDNS-Namen erreichbar sein und einen gültigen Home-Assistant-Long-Lived-Access-Token erhalten.

Die Quellinstallation entscheidet pro Raum, ob Remote-Abfragen erlaubt sind. Auf der empfangenden Installation werden anschließend ausdrücklich nur die gewünschten Assistenten und Räume ausgewählt. Neue Räume werden nicht automatisch übernommen.

Remote bleibt absichtlich read-only und flüchtig:

- keine gespiegelten Remote-Messentities
- keine lokale Recorder-Historie der Remote-Messwerte
- keine dauerhafte Messwertkopie
- aktuelle Snapshots ausschließlich im Arbeitsspeicher
- Remote-Abfrage alle 30 Sekunden
- ungefähr 3 Minuten Offline-Karenz bei kurzen Verbindungsabbrüchen

Remote-Verbindungen sind auf Tailscale beschränkt. Sowohl Zielauflösung als auch Quelladresse des Snapshot-Zugriffs werden entsprechend geprüft. Für zusätzliche Netztrennung empfiehlt sich eine Tailscale-Grant/ACL-Regel, die dem abfragenden Home Assistant nur TCP-Port 8123 am entfernten Home Assistant erlaubt.

### Bekannte Home-Assistant-Einschränkung bei „Raum hinzufügen“

Remote-/Tailscale-Verbindungen unterstützen keine lokalen Räume und werden vom Backend abgewiesen. Der globale Home-Assistant-Dialog zum Hinzufügen eines Subentries kann derzeit trotzdem alle ConfigEntries derselben Integration als mögliche Eltern anzeigen, ohne die unterstützten Subentry-Typen jedes einzelnen Entries vollständig zu filtern. Dadurch kann ein Remote-Hub in diesem Dialog sichtbar bleiben; ein Raum lässt sich ihm tatsächlich nicht hinzufügen.

## Neustartsicherheit und Ressourcen

Lüftungsassistent hält sein internes Gedächtnis bewusst klein. Gespeichert werden nur Zustände, die nach einem Neustart nicht zuverlässig aus den aktuellen Home-Assistant-Entities rekonstruiert werden können, darunter:

- laufende und letzte bestätigte Lüftung
- relevante CO₂-Hysterese-Zeitpunkte und eine laufende 5-Minuten-Mindestlüftung
- der noch gültige 60-Sekunden-CO₂-Ausfallpuffer
- ein belastbarer Nacht-Basisstatus bis zu dessen Endzeit
- kompakter Oberflächen-Feuchtekontext
- begrenzte lokale Außenluft-Statistik

Temperatur-, Feuchte- und CO₂-Rohverläufe werden nicht zusätzlich zum Home-Assistant-Recorder dupliziert.

Im Leerlauf läuft keine minutenweise Komplettauswertung pro Raum nur für den 24-Stunden-Routinelüftungs-Fallback. Der Minutentakt für **Fenster geöffnet seit** ist nur während einer tatsächlichen Lüftung aktiv; der 24-Stunden-Fallback wird gezielt terminiert. Wetter, Warnungen und Außenluft werden einmal pro lokalem Lüftungsassistent aufbereitet und von dessen Räumen gemeinsam genutzt.

Große dynamische Kartenattribute bleiben für die Oberfläche verfügbar, werden aber nicht unnötig historisiert. Die States der Lüftungsassistent-Entities werden einmal täglich gezielt auf maximal **20 Tage** Recorder-Verlauf begrenzt. Eine global kürzere Recorder-Aufbewahrung bleibt maßgeblich; andere Integrationen werden dadurch nicht verändert.

## Sprache und Einheiten

Lüftungsassistent unterstützt **Deutsch, Englisch und Türkisch**. Empfehlung, Grund, Dauer und Nachttext können für die Dashboard-Karten in der Sprache des aktuell angemeldeten Home-Assistant-Benutzers gerendert werden. Nicht unterstützte Sprachen fallen auf Englisch zurück.

Temperaturwerte werden intern in °C verarbeitet. Anzeige und Eingabe des Fallback-Sollwerts folgen dem in Home Assistant eingestellten Einheitensystem, sodass auch Fahrenheit-Setups korrekt funktionieren.

## Unterstützte Wetter- und Warndienste

Grundsätzlich kann jede passende Home-Assistant-`weather.*`-Entity verwendet werden, sofern die benötigten Werte vorhanden sind.

Besonders berücksichtigt werden aktuell:

- DWD Weather
- DWD Weather Warnings
- NINA

Andere Anbieter können über standardisierte Home-Assistant-Wetterdaten und generische Warnstrukturen teilweise ebenfalls funktionieren. Nicht jede Kombination ist bereits getestet.

## Datenschutz

Ohne konfigurierte Remote-Verbindung verarbeitet Lüftungsassistent die verwendeten Home-Assistant-Entities lokal. Bei Tailscale-Remote stellt die entfernte Installation ausschließlich authentifizierte aktuelle Raum-Snapshots über die Home-Assistant-API bereit; Recorder-Historien und fremde Sensor-Entities werden nicht übertragen oder auf der empfangenden Instanz angelegt.

Externe Wetter- und Warndienste können unabhängig davon eigene Cloud-Verbindungen verwenden.

## Hinweise zur Alpha

- Die Entscheidungslogik wird weiterhin geprüft und weiterentwickelt.
- Nicht jede Kombination aus Wetter-, Warn- und Sensorintegration ist bereits getestet.
- Bei ungewöhnlichem Verhalten bitte Home-Assistant-Version, Lüftungsassistent-Version und die betroffenen Entity-Zustände im Issue angeben.

## Änderungen und Fehler melden

- [Changelog](CHANGELOG.md)
- [GitHub Issues](https://github.com/svemmiii/lueftungsberater/issues)

## Lizenz

MIT License
