<p align="center">
  <img src="custom_components/lueftungsberater/brand/icon@2x.png" width="180" alt="Lüftungsassistent">
</p>

# Lüftungsassistent

**Alpha-Version für Home Assistant.**

Lüftungsassistent bewertet Innen- und Außenbedingungen und gibt für jeden Raum eine verständliche Lüftungsempfehlung aus. Je nach vorhandener Hardware können Temperatur, Luftfeuchtigkeit, CO₂, Fenster-/Türkontakte, Thermostate, Wetterdaten und Warnmeldungen berücksichtigt werden.

> **Status:** frühe Alpha. Die Integration läuft bereits im Alltag, wird aber noch aktiv getestet und weiterentwickelt.

## Funktionen

- Eigene Lüftungsempfehlung pro Raum
- Vierstufige, konfigurierbare Ampeldarstellung mit kurzer Begründung
  - **Lüftungsbedarf (Standard):** dieselbe vollständige Gesamtbewertung aus Sicht des aktuellen Lüftungsbedarfs im Raum. Grün = aktuell kein Lüftungsgrund, Gelb/Orange = zunehmender Bedarf, Rot = jetzt lüften.
  - **Lüftungsampel (optional):** dieselbe Gesamtbewertung aus Sicht der aktuellen Lüftungs-/Außenbedingungen. Grün = Lüften sinnvoll, Gelb = Abwägung/Übergang, Orange = eher geschlossen lassen, Rot = Lüften deutlich nachteilig.
  - Beide Ansichten nutzen dieselbe Entscheidungsengine; es werden keine Sensoren je nach Darstellung ein- oder ausgeschaltet. Nur Farbe, kurze Empfehlung und Begründung werden aus der gewählten Perspektive formuliert.
  - Echte Schutzlagen liegen außerhalb der normalen Ampel und werden eindeutig mit **🔒 Fenster geschlossen halten** dargestellt.
- Absolute Feuchtigkeit innen/außen
- Optionaler CO₂-Sensor pro Raum
- Automatischer Lüftungsverlauf mit Fenster-/Türkontakt
- Erkennung einer bestätigten Lüftung ab 5 Minuten
- Wetterdienst über eine normale Home-Assistant-`weather.*`-Entity
- Optionale Warn-App / Warndienst
- Erweiterte Unterstützung für DWD und NINA
- Kurzzeit-Failsafe bei CO₂-Sensorausfällen
- Detaillierte Raumkarte
- Kompakte Mehrraumübersicht
- Karten erscheinen im Home-Assistant-Kartenpicker
- Natürliche Oberfläche und Empfehlungen auf Deutsch, Englisch und Türkisch
- Dashboard-Karten folgen der Sprache des aktuell angemeldeten Home-Assistant-Benutzers
- Unterstützung für Celsius- und Fahrenheit-Setups
- Ruhigere Empfehlungen durch Hysterese an normalen CO₂-/Feuchte-/Temperaturgrenzen
- Optionaler Feuchte-/Schimmelschutz über einen realen kalten/kritischen Oberflächentemperatursensor mit zeitlichem Kontext
- Plausibilitätsgeprüfte Außenluftqualität über passende Ozon-, PM2.5-, PM10-, NO₂- und SO₂-Sensoren des Wetter-Providers, ergänzt um lokalen Verlauf und Trend
- Optionaler eigener Außen-CO₂-Sensor für die lokale Lüftungsbewertung
- Optionale, forecastbasierte Nachtlüftungsstrategie mit einstellbarer Anzeigezeit
- Assistentenweite Warn-/Entwarnungsbenachrichtigungen plus bewusst pro Raum aktivierbare Lüftungsstatus-Meldungen über eine normale Home-Assistant-`notify`-Entity
- Recorder-schonende Entity-Historie; Lüftungsassistent-Entities werden gezielt auf maximal 20 Tage Recorder-Verlauf begrenzt (die globale Recorder-Konfiguration kann weniger behalten)


## Bekannte Home-Assistant-Einschränkung bei „Raum hinzufügen“

Remote-/Tailscale-Verbindungen unterstützen keine lokalen Räume und werden vom Backend strikt abgewiesen. Der globale Home-Assistant-Dialog zum Hinzufügen eines Subentries listet derzeit jedoch alle ConfigEntries derselben Integration als mögliche Eltern auf, ohne die unterstützten Subentry-Typen jedes einzelnen Entries zu filtern. Deshalb kann ein Remote-Hub dort sichtbar bleiben; ein tatsächlicher Raum kann ihm nicht hinzugefügt werden.

## Voraussetzungen

- Home Assistant **2026.6.0 oder neuer**
- HACS für die empfohlene Installation
- Mindestens pro Raum:
  - Innentemperatur
  - relative Luftfeuchtigkeit innen
- Ein Wetterdienst mit Außentemperatur und Außenluftfeuchtigkeit

Optional:
- CO₂-Sensor
- Fenster-/Türkontakte
- Climate-/Thermostat-Entity
- Temperatur-Sensor an einer kalten/kritischen Oberfläche für zusätzlichen Schimmelschutz
- Warnintegration wie NINA oder DWD Weather Warnings
- `notify`-Entity für Benachrichtigungen
- eigener CO₂-Außensensor

## Installation über HACS – Custom Repository

1. HACS öffnen.
2. Oben rechts auf **⋮ → Custom repositories**.
3. Repository eintragen:

   `https://github.com/svemmiii/lueftungsberater`

4. Typ **Integration** auswählen.
5. Repository hinzufügen und **Lüftungsassistent** installieren.
6. Home Assistant neu starten.
7. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Lüftungsassistent**.

## Einrichtung

### 1. Gemeinsame Außendaten

Beim ersten Einrichten wählst du:

- **Wetterdienst**
- optional **Warn-App / Warndienst**
- die gewünschte **Ampeldarstellung**
- optional eigene Außensensoren, darunter auch **CO₂ außen**
- optional ein **Benachrichtigungsziel** und die Ereignisse, über die du informiert werden möchtest

Standardmäßig lösen weiterhin nur **ernste Außenluftgefahren** (z. B. Brandrauch/Gefahrstoffe) und **schwere Wettergefahren** eine Benachrichtigung aus, wenn tatsächlich ein konfiguriertes Fenster oder eine Tür offen ist. Zusätzlich kannst du vorsorgliche Luft-/Wetterhinweise sowie zwei reine Lüftungsstatus-Hinweise aktivieren: **„Lüften ist wieder sinnvoll“** und **„Lüften kann beendet werden“**. Eine rote Empfehlung allein ist ausdrücklich kein Benachrichtigungsauslöser.

Benachrichtigungen verwenden ab v0.6.20 ausschließlich den aktuellen Home-Assistant-Weg über eine ausgewählte `notify`-Entity und `notify.send_message`. Titel und Nachricht kommen vom Lüftungsassistent; Ton, Vibration, Priorität und weitere gerätespezifische Eigenschaften bestimmt das gewählte Notify-Ziel. Der frühere separate `notify.mobile_app_*`-Companion-Weg mit eigenen Vibrations-/Critical-Einstellungen wurde entfernt, damit es nur noch einen klaren Benachrichtigungsweg gibt. Bestehende alte Companion-Optionen werden beim Update verworfen; ein bereits gesetztes normales Notify-Ziel bleibt erhalten.

Die beiden Lüftungsstatus-Hinweise bleiben zustandswechselbasiert: Sie werden nicht bei jedem Sensorupdate und nicht direkt nach einem Home-Assistant-Neustart erneut gesendet.

Eigene Außensensoren können bei Bedarf unter den erweiterten Optionen verwendet werden. Werden konfigurierte Außensensoren vorübergehend `unavailable` oder `unknown`, fällt Lüftungsassistent für Temperatur und Luftfeuchtigkeit unabhängig voneinander automatisch auf die aktuelle `weather.*`-Entity zurück, sofern der jeweilige Wert dort verfügbar ist. Die Raumkarte kennzeichnet einen solchen aktiven Fallback direkt am betroffenen Außenwert mit **Wetterdienst**.

### 2. Räume hinzufügen

Für jeden Raum können konfiguriert werden:

- Temperatur
- Luftfeuchtigkeit
- optional CO₂
- optional Fenster-/Türkontakte
- optional Thermostat / Climate
- optional Temperatur einer kalten/kritischen Oberfläche
- Solltemperatur
- Uhrzeit, ab der eine mögliche Nachtlüftungsstrategie angezeigt werden darf (Standard 22 Uhr)

Die Raum-Einstellungen sind dafür in klare Bereiche aufgeteilt: **Raumklima**, **Nachtlüftung**, **Zusatzsensoren** und **Fenster & Türen**. Die Nachtzeit verwendet einen echten Uhrzeit-Selector, damit z. B. 21:00 nicht wie eine 21-°C-Temperaturvorgabe wirkt.

Ohne Fensterkontakt arbeitet der Raum rein beobachtend. Mit Fensterkontakt erkennt Lüftungsassistent automatisch, wann tatsächlich gelüftet wurde. Laufende Lüftungen und die letzte bestätigte Lüftung werden kompakt gespeichert und überstehen einen Home-Assistant-Neustart. Ein beim Start kurz `unknown`/`unavailable` gemeldeter Fensterkontakt beendet eine laufende Lüftung nicht fälschlich.

Die Sensor-Auswahl wird nach Home-Assistant-Geräteklassen gefiltert: Temperatur, Luftfeuchtigkeit und CO₂ werden nur in den jeweils passenden Sensorfeldern angeboten; bei Fenster-/Türkontakten erscheinen passende Öffnungs-, Fenster-, Tür- und Garagentor-Binary-Sensoren.

### Optionaler Feuchte-/Schimmelschutz

Die normale Feuchtebewertung funktioniert vollständig ohne zusätzliche Hardware. Optional kann pro Raum die Temperatur einer besonders kalten bzw. kritischen Oberfläche angegeben werden, zum Beispiel an einer bekannten Wärmebrücke. Nur wenn dieser **reale Oberflächentemperatursensor** vorhanden ist, berechnet Lüftungsassistent aus Raumtemperatur, Raumfeuchte und gemessener Oberflächentemperatur die relative Feuchte direkt an dieser Stelle. Ohne Sensor werden keine Oberflächenwerte geschätzt oder erfunden.

Ab ungefähr **80 % relativer Oberflächenfeuchte** wird die Situation im Hintergrund stärker berücksichtigt. Zusätzlich merkt sich Lüftungsassistent lokal, wie lange und wie wiederholt dieser Bereich tatsächlich anliegt. Ein kurzer Peak wird dadurch anders bewertet als eine länger anhaltende Belastung. Die zeitliche Bewertung ist eine vorsichtige Beratungsheuristik und ausdrücklich **keine Schimmeldiagnose oder DIN-Grenze**. Erst wenn die Belastung relevant anhält, wird sie deutlicher in Ampel und Begründung aufgenommen.

### Wetterwarnungen, Regen, Wind und Außenluftqualität

Regen ist kein Ersatz für eine Feuchtebewertung: Ob Lüften trocknet, entscheidet die absolute Feuchtedifferenz innen/außen. Aktueller bzw. unmittelbar bevorstehender Niederschlag wird nur als praktischer Nachteil für ein geöffnetes Fenster gewertet. Ein Radarereignis beeinflusst die Empfehlung nur noch dann, wenn es während der erwarteten Lüftungsdauer beziehungsweise kurz danach beginnen kann; ein Niederschlag in deutlich späterer Zukunft blockiert keine kurze Lüftung.

Starker Wind wird als Fenstersicherheits-/Komfortfaktor behandelt, nicht als angebliche amtliche DWD-Warnfarbe. Ab ungefähr Bft 6 wird vorsichtiger bewertet; ab etwa **50 km/h anhaltendem Wind** oder **65 km/h Böen** kann Lüften insgesamt nachteilig und damit Orange sein. Deutlich extremere Bedingungen können in der normalen Lüftungsampel Rot werden; echte Warnlagen mit klarem Schutzgrund werden zusätzlich eindeutig mit dem separaten **🔒-Sperrzustand** dargestellt. Offizielle DWD-Warnungen werden weiterhin separat nach ihrer konkreten Warnstufe und Handlungsempfehlung berücksichtigt.

### Nachtlüftung

Pro Raum lässt sich ein eigenes Nachtfenster **von–bis** festlegen (Standard **22:00–07:00**). Beide Zeiten sind reine Anzeigegrenzen und keine Aufforderung, genau dann ein Fenster zu öffnen oder zu schließen. Zeiträume über Mitternacht und ungewöhnliche Schichtzeiten werden unterstützt. Die Nachtkarte ist bewusst eine einfache Einschätzung vor dem Schlafengehen: Wenn ein längeres Lüften in der Nacht voraussichtlich sinnvoll ist, nennt sie den passenden Zeitraum; wenn eine grundsätzlich interessante Nachtlage nur mit Abwägung sinnvoll ist, sagt sie das kurz dazu. Ergibt längeres Nachtlüften praktisch keinen Nutzen, bleibt der Zusatz komplett verborgen.

Dafür wird – sofern der ausgewählte Wetterdienst sie unterstützt – die stündliche Home-Assistant-Wettervorhersage ausgewertet. Persönliche Solltemperatur sowie vorhandene Prognosen für Feuchte, Regen und Wind und aktuelle Warn-/Luftqualitätslagen können die Empfehlung beeinflussen. Ein Forecastpunkt gilt für den **längeren, weitgehend unbeaufsichtigten** Nachthinweis nur dann als plausibel, wenn seine Außentemperatur höchstens **9 K** von der aktuellen Raumtemperatur entfernt liegt. Diese 9-K-Grenze gilt ausdrücklich nicht für die normale Live-Lüftungsberatung.

Intern darf die Nachtplanung bis zu **eine Stunde hinter die konfigurierte Endzeit** in den Forecast schauen, um einen Abschnitt am Ende noch belastbar beurteilen zu können. Die sichtbare Nachtzeit wird dadurch niemals verlängert: Ist z. B. 06:00 Uhr als Ende eingestellt, verschwindet der Hinweis um 06:00 Uhr. In der letzten Stunde werden aus einer dünner werdenden Forecastbasis keine neuen positiven Strategien mehr erfunden. Stattdessen bleibt der letzte belastbare Basisstatus erhalten; eine Verschlechterung darf die Empfehlung weiterhin vorsichtiger machen und ein harter Safety-Lock übersteuert sie jederzeit. Nach einer späten Entwarnung kann dadurch auf den vorherigen Basisplan zurückgefallen werden, statt kurz vor Ende eine völlig neue Nachtstrategie zu starten. Der gehaltene Basisstatus ist neustartsicher.

Fehlende Forecast-Felder werden nicht geschätzt. Die Nachtbewertung bleibt eine Zusatzinformation und verändert die normale aktuelle Ampel nicht.

### Außenluftqualität und lokaler Kontext

Wenn der ausgewählte Wetter-Provider passende Ozon-, PM2.5-, PM10-, NO₂- oder SO₂-Sensoren bereitstellt, nutzt Lüftungsassistent plausible und aktuelle Einzelwerte nach den Klassen des Umweltbundesamt-Luftqualitätsindex. Der jeweils schlechteste verfügbare gültige Schadstoff bestimmt die absolute Außenluftbewertung. Fehlende Schadstoffe sind erlaubt; `unknown`, `unavailable`, veraltete, negative oder offensichtlich unplausible Providerwerte werden ignoriert. Fehlende Daten werden niemals als gute Luft interpretiert.

Zusätzlich kann Lüftungsassistent pro Standort einen rollierenden typischen Bereich und den jüngsten Trend aufbauen. Dieser Verlauf dient ausschließlich als Kontext: dauerhaft schlechte Luft bleibt schlecht, der Berater erkennt aber zusätzlich, ob die aktuelle Belastung für den Standort üblich oder außergewöhnlich hoch ist. Bei einem deutlichen Standortwechsel wird ein anderer Verlaufsbereich verwendet. Die lokale Statistik ist bewusst größenbegrenzt und speichert keine zweite 30-Tage-Rohdatenbank. Ein optionaler eigener Außen-CO₂-Sensor ergänzt diese Bewertung für den konkreten Luftaustausch am Gebäude; er ersetzt keine Schadstoffmessung und wird nicht mit regionalen CO₂-Werten gemittelt.

## Wie die Empfehlung entschieden und stabil gehalten wird

Lüftungsassistent bewertet den **Gesamtnutzen** des Lüftens. Ein einzelner Grenzwert gewinnt nicht automatisch gegen alle anderen Messwerte. Gesundheit und Sicherheit haben Vorrang; danach werden Innenraumluft, Feuchte-/Oberflächenrisiko, persönliches Temperatursoll, erwartete Komfortänderung sowie Außenbedingungen gemeinsam eingeordnet. Der persönliche Sollwert bleibt der Maßstab für thermische Behaglichkeit, während sehr hohe und länger anhaltende Raumtemperaturen zusätzlich als gesundheitlicher Hitzefaktor berücksichtigt werden. Die wählbare Ampeldarstellung verändert diese Hintergrundentscheidung nicht: Sie bestimmt nur, ob die kurze Vorderseite stärker den **Lüftungsbedarf im Raum** oder die **aktuelle Eignung der Außen-/Lüftungsbedingungen** erklärt. Lüftungsassistent bleibt dabei ein Berater und gibt kein medizinisches oder bauphysikalisches Gutachten ab.

Für die absolute Feuchtedifferenz wird um **±0,5 g/m³** eine kleine technische Neutralzone verwendet. Diese Zahl ist kein Gesundheits- oder Normgrenzwert, sondern verhindert, dass Messrauschen und praktisch sehr kleine Unterschiede eine starke Empfehlung auslösen. Positive Differenzen bedeuten trocknere Außenluft; negative Differenzen bedeuten feuchtere Außenluft. Die Stärke dieser Abweichung wird zusammen mit CO₂, Raumfeuchte, Temperatur und optionalen Zusatzdaten abgewogen. Eine laufende sinnvolle Feuchtelüftung erhält zusätzlich eine kleine Hysterese.

Auch an normalen CO₂-/Feuchte-/Temperaturgrenzen werden Hysteresen verwendet, damit die Karte nicht bei jedem kleinen Sensorschritt umspringt. Wird eine vom Assistenten tatsächlich empfohlene CO₂-Lüftung durch das Öffnen eines überwachten Fensters gestartet, erhält dieser Luftaustausch mindestens **5 Minuten** Zeit, bevor ein bereits stark gefallener CO₂-Wert die Sitzung beenden kann. Bereits bekannte und beim Start akzeptierte Außen-Nachteile lösen in dieser kurzen Mindestzeit kein Hin-und-her aus; neue relevante Verschlechterungen sowie harte Safety-Locks werden weiterhin sofort berücksichtigt. Danach greift wieder die bestehende CO₂-Abschlusshysterese. Kritisches CO₂ sowie echte Außenluft- und Unwettergefahren wirken dagegen unmittelbar. Die Routinelüftung nach 24 Stunden bleibt bewusst nur ein Fallback für Situationen ohne früheren echten Lüftungsgrund.

Der Hauptsensor bleibt bewusst die zentrale Automation-Schnittstelle. Eine zusätzliche Binary-Entity „Lüften empfohlen“ wird nicht erzeugt, weil die Zustände des Hauptsensors (`open_now`, `keep_open`, `close_now`, `wait` usw.) bereits gezieltere Automationen erlauben.

## Neustartsicherheit und Ressourcen

Lüftungsassistent hält sein internes Gedächtnis bewusst klein. Gespeichert werden nur Zustände, die sich nach einem Neustart nicht zuverlässig aus den aktuellen Home-Assistant-Entities rekonstruieren lassen: laufende bzw. letzte bestätigte Lüftung, die kurzen CO₂-Hysterese-Zeitpunkte einschließlich einer noch laufenden 5-Minuten-Mindestlüftung, der noch gültige 60-Sekunden-CO₂-Ausfallpuffer, ein belastbarer Nacht-Basisstatus bis zu dessen Endzeit, kompakter Oberflächen-Feuchtekontext und eine begrenzte lokale Außenluft-Statistik. Temperatur-, Feuchte- und CO₂-Rohverläufe werden nicht zusätzlich zum Home-Assistant-Recorder dupliziert. Persistierte CO₂-Rohwerte dienen ausschließlich dem sehr kurzen Ausfallpuffer und werden nach Ablauf dieser Grace-Periode nicht als aktueller Messwert wiederverwendet.

Im Leerlauf laufen keine minutenweisen Komplettauswertungen pro Raum nur für den 24-Stunden-Fallback. Der Minutentakt für „Fenster geöffnet seit“ ist nur während einer tatsächlichen Lüftung aktiv; der 24-Stunden-Fallback wird gezielt terminiert. Wetter, Warnungen und Außenluft werden einmal pro lokalem Lüftungsassistent aufbereitet und von den Räumen gemeinsam genutzt. Große Kartenattribute bleiben für die Oberfläche verfügbar, werden aber nicht unnötig als eigener Recorder-Verlauf gespeichert.

## Sprache und Einheiten

Lüftungsassistent unterstützt aktuell **Deutsch, Englisch und Türkisch**. Empfehlungen werden nicht als kurze technische Meldungen oder wortwörtliche Maschinenübersetzungen erzeugt, sondern für jede Sprache natürlich formuliert. Ab v0.7.1 trägt die Raum-Entity nicht mehr alle Sprachvarianten gleichzeitig als `localized_texts` mit sich. Die Dashboard-Karten lassen Empfehlung, Grund, Dauer und Nachttext bei Bedarf über die Integration in der Sprache des jeweils angemeldeten Home-Assistant-Benutzers rendern und cachen das Ergebnis. Die aktuell in den Zustandsattributen vorhandenen Einzeltexte bleiben als sofortiger Fallback in der Home-Assistant-Systemsprache erhalten. Nicht unterstützte Sprachen fallen auf Englisch zurück.

Amtliche Warnquellen werden handlungsorientiert ausgewertet: Der Lüftungsassistent versucht nicht selbst zu entscheiden, *wie gefährlich* ein Ereignis ist. Gibt eine offizielle Warnquelle ausdrücklich vor, Fenster/Türen geschlossen zu halten, Lüftung/Klima abzuschalten oder Außenluftzufuhr zu vermeiden, gilt diese Schutzmaßnahme unmittelbar als harte Sperre. Warnungen ohne lüftungsrelevante Handlungsanweisung beeinflussen diesen Pfad nicht. DWD behält daneben seine eigene Wetterwarnungsbewertung. Vollständige Entwarnungen heben eine amtliche Sperre auf, bleiben solange der Warneintrag vorhanden ist als Hinweis sichtbar und setzen selbst keine Farbe; danach übernimmt wieder vollständig die normale Engine. Teil-/bedingte Entwarnungen werden dagegen nicht als Vollfreigabe behandelt, solange weiterhin eine Schutzanweisung gilt. Reale MoWaS-Entwarnungen dürfen alte, noch mitgeführte Handlungsempfehlungen enthalten; eindeutige Aufhebungstexte werden deshalb bewusst von weiterhin gültigen Teilwarnungen unterschieden.

Texte von externen Warnanbietern wie DWD oder NINA werden nicht automatisch übersetzt. Lüftungsassistent erzeugt daraus eine eigene lokalisierte Begründung und bewahrt den Originaltext zusätzlich im Attribut `original_warning_text` auf.

Temperaturwerte werden intern einheitlich in °C verarbeitet. Anzeige und Eingabe der Fallback-Solltemperatur folgen dem in Home Assistant eingestellten Einheitensystem, sodass auch Fahrenheit-Setups korrekt funktionieren.

## Dashboard

Nach dem Neustart stehen im Kartenpicker zwei Karten zur Verfügung:

### Lüftungsassistent – Raum

Detaillierte Ansicht für einen Raum mit Empfehlung, Grund und Messwerten.

### Lüftungsassistent – Übersicht

Die Übersicht ist bewusst sehr kompakt: Pro Raum werden nur Name, aktuelle Empfehlung, Statusfarbe und – falls zutreffend – ein kleines **offen**-Badge gezeigt. Ein Tipp auf einen Raum erzeugt erst in diesem Moment eine vollständige Raumkarte in einem Dialog; eine separat eingerichtete Raumkarte ist dafür nicht erforderlich und es laufen keine unsichtbaren Raumkarten im Hintergrund. Der Dialog wird beim Schließen oder beim Verlassen der Dashboard-Ansicht vollständig entfernt, sodass Handy, Tablet und PC jeweils einen rein lokalen Dialogzustand besitzen.

Sind mehrere Lüftungsassistent-Instanzen vorhanden, gruppiert dieselbe Übersicht die Räume automatisch nach Instanz. Bei nur einer sichtbaren Instanz wird diese Zwischenebene übersprungen. Im visuellen Karteneditor lassen sich lokale und Tailscale-Remote-Installationen sowie einzelne Räume ein-/ausblenden und per Pfeiltasten sortieren.

Lokale Raumkarten verlinken echte Mess- und Statuswerte weiterhin auf Home Assistants More-Info-/Verlaufsansicht. Ab v0.6.12 gilt das auch für die **CO₂-Bewertung** sowie die **absolute Feuchtedifferenz Δ g/m³**, die dafür einen eigenen Sensor erhält. Ab v0.6.17 öffnet ausschließlich der **farbige Kopf-/Statusbereich** die Lüftungsassistent-Hauptentity; Erklärungstexte und die empfohlene Lüftungsdauer sind reine Texte und lösen keine Navigation aus.

Die Dashboard-Ressource wird bei normalen Home-Assistant-Dashboards automatisch registriert.


## Mehrere Instanzen und Tailscale-Remote

Mehrere lokale Lüftungsassistent-Instanzen können parallel eingerichtet werden, zum Beispiel für mehrere Wohnungen. Jede Installation verwendet Home Assistants eigene Config-Entry-ID; eine künstliche `unique_id` wird bewusst nicht vergeben, weil lokale Berater manuell wiederholbare Konfigurationen und keine einzelne physische Hardware sind. Die gemeinsame Übersicht gruppiert die Installationen unabhängig voneinander und öffnet die Räume erst nach Auswahl der jeweiligen Instanz.

Zusätzlich kann eine andere Home-Assistant-Installation als **Tailscale-Remote** eingebunden werden. Dafür muss das entfernte Home Assistant Lüftungsassistent v0.6.10 oder neuer ausführen und über seine Tailscale-IP oder einen MagicDNS-Namen erreichbar sein. Die Einrichtung verlangt zusätzlich einen gültigen Home-Assistant-Long-Lived-Access-Token. Ab v0.7.0 entscheidet die Quellinstallation pro Raum, ob Remote-Abfragen erlaubt sind; die empfangende Installation wählt anschließend ausdrücklich nur die Assistenten/Räume aus, die sie sehen möchte. Neue Räume werden nicht automatisch übernommen, sondern erscheinen lediglich als zusätzliche Auswahl. Remote-Messwerte bleiben flüchtig und erzeugen auf der empfangenden Instanz weiterhin keine gespiegelten Entities oder Recorder-Historien. Auf der Quellseite kennzeichnet die Übersicht aktiv remote abgefragte Räume und weist auf Assistenten-Ebene darauf hin, wenn mindestens ein Raum gerade von einer anderen Instanz genutzt wird. Ab v0.7.1 erscheint bei einer aktiven Abfrage zusätzlich in der detaillierten lokalen Raumkarte ein kleines Remote-Symbol. `remote_shared` bedeutet nur Freigabe; eine tatsächliche laufende Abfrage wird getrennt als `remote_access_active` geführt.

Tailscale-Remote-Verbindungen erzeugen auf der empfangenden Home-Assistant-Instanz weiterhin **keine Remote-Entities und keine Messwert-Historien**. Für die Geräteansicht wird lediglich eine leichte Raumkarte pro Remote-Raum registriert; die früheren unnötigen Zwischenebenen **Remote Home Assistant → Lüftungsassistent** entfallen. Die Raumkarten enthalten keine Messentities. Alle aktuellen Remote-Werte bleiben ausschließlich flüchtige Snapshots im Arbeitsspeicher.

Remote-Verbindungen sind absichtlich auf Tailscale beschränkt. Beim laufenden Abruf wird erneut geprüft, dass das Ziel ausschließlich auf Tailscale-Adressen auflöst. Zusätzlich akzeptiert der Snapshot-Endpunkt selbst nur Anfragen, deren Quell-IP aus einem Tailscale-Adressbereich stammt. Ein gültiger Home-Assistant-Token allein reicht außerhalb des Tailnets daher nicht aus. Übertragen werden nur die aktuellen Lüftungsassistent-Hauptzustände und deren aktuelle Detailwerte – keine Recorder-Historie und keine fremden Sensor-Entities werden im empfangenden Home Assistant angelegt.

Die entfernten Snapshots werden nur im Arbeitsspeicher gehalten und bei neuen Daten ersetzt. Die Remote-Verbindung prüft alle 30 Sekunden. Kurze LTE-/Tailscale-Aussetzer werden toleriert; erst nach ungefähr 3 Minuten ohne erfolgreichen Abruf wird die Instanz als **Nicht erreichbar** angezeigt. Während dieser Karenz bleibt auch eine bereits geöffnete Remote-Raumansicht bestehen. Sobald die Verbindung wieder steht, wird wieder ein aktueller Snapshot geladen. Fehlen dagegen nur notwendige Temperatur-/Feuchtewerte auf der erreichbaren Remote-Instanz, bleibt der Raum sichtbar und zeigt gelb **„Aktuell keine zuverlässige Empfehlung möglich“** statt als offline zu gelten.

In der Remote-Detailansicht sind Messwerte reine Anzeige und nicht anklickbar. Lokale Raumkarten bleiben unverändert: Dort funktionieren More-Info und Recorder-Verlauf weiterhin.

Für eine möglichst enge Netzfreigabe empfiehlt sich zusätzlich eine Tailscale-Grant/ACL-Regel, die vom abfragenden Home-Assistant-Gerät nur TCP-Port 8123 des entfernten Home Assistants erlaubt.

## Unterstützte Wetter- und Warndienste

Grundsätzlich kann jede passende Home-Assistant-`weather.*`-Entity verwendet werden, sofern die benötigten Werte vorhanden sind.

Besonders berücksichtigt werden aktuell:

- DWD Weather
- DWD Weather Warnings
- NINA

Andere Anbieter können über die standardisierten Home-Assistant-Wetterdaten bzw. generische Warnstrukturen teilweise ebenfalls funktionieren.

## Hinweise zur Alpha

Bitte beachte:

- Nicht jede Kombination aus Wetter- und Warnintegration ist bereits getestet.
- Die Entscheidungslogik wird aktuell weiter geprüft.
- Bei ungewöhnlichen Zuständen bitte ein GitHub-Issue mit Home-Assistant-Version, Lüftungsassistent-Version und den betroffenen Entity-Zuständen anlegen.

## Datenschutz

Ohne konfigurierte Remote-Verbindung verarbeitet Lüftungsassistent die vorhandenen Entities ausschließlich lokal. Wird Tailscale-Remote verwendet, stellt die entfernte Lüftungsassistent-Installation nur über eine authentifizierte, auf Tailscale-Quell- und Zieladressen beschränkte Home-Assistant-API aktuelle Raum-Snapshots bereit. Eine Recorder-Historie wird dabei nicht übertragen oder auf der empfangenden Instanz angelegt. Externe Wetter-/Warndienste können unabhängig davon eigene Cloud-Verbindungen verwenden.

## Fehler melden

Issues:

https://github.com/svemmiii/lueftungsberater/issues

## Lizenz

MIT License

## HACS-Alpha und Releases

Die Software ist weiterhin als Alpha gekennzeichnet, die GitHub-Releases für
HACS-Tester werden aber als normale Releases veröffentlicht. Dadurch nutzt HACS
die Versionsnummer des Releases statt den Commit-Hash des Default-Branches.

## Branding in HACS

Home Assistant verwendet das mitgelieferte lokale Brand-Icon nach der Installation.
Die HACS-Oberfläche kann bei Custom Integrations vor der Installation weiterhin
einen Platzhalter anzeigen, obwohl `brand/icon.png` korrekt enthalten ist.


### Hinweis zu v0.6.20

v0.6.20 überarbeitet die Beratungslogik grundlegend zu einer nachvollziehbaren Gesamtabwägung: absolute Feuchte verwendet eine technische Neutralzone statt einer harten 1,0-g/m³-Hürde, CO₂ wird gegen Außenbedingungen und Komfort abgewogen, Regen nur noch zeitlich passend zur Lüftung berücksichtigt, Wind und Warntexte differenzierter bewertet und plausible Außenluftqualität automatisch einbezogen. Der optionale Oberflächensensor erhält einen lokalen zeitlichen Feuchtekontext, ohne ohne Sensor Werte zu erfinden oder eine Schimmeldiagnose zu behaupten. Benachrichtigungen laufen nur noch über `notify.send_message`; der alte Companion-Sonderweg entfällt. Remote-Tailscale-Werte bleiben vollständig flüchtig und entity-frei, während frühere leere Remote-Geräte-Metadaten aufgeräumt werden. Deutsch, Englisch und Türkisch wurden gemeinsam aktualisiert.

### Hinweis zu v0.6.19

v0.6.19 erweitert die Benachrichtigungen um frei wählbare Lüftungsstatus-Hinweise und optionale Companion-App-Steuerung. Normale Hinweise können still auf dem Handy erscheinen, während Vorsicht und Gefahr getrennte Android-Vibrationsmuster erhalten. Kritische Zustellung bleibt ausdrücklich opt-in. Die Entscheidungslogik und Lüftungsschwellen bleiben unverändert.

### Hinweis zu v0.6.18

v0.6.18 ist ein reiner Test-/CI-Hotfix. Die Lüftungslogik aus v0.6.17 bleibt unverändert. Korrigiert wurde ausschließlich ein Regressionstest, der bei der Prüfung der CO₂-Hysterese unbeabsichtigt gleichzeitig die Kühl-Hysterese aktiviert hatte.

### Hinweis zu v0.6.17

v0.6.17 vereinheitlicht die Klicklogik der Raumkarte, filtert die Sensorauswahl nach passenden Geräteklassen, beruhigt Grenzbereiche mit Hysterese und ergänzt optionalen Schimmelschutz sowie gezielte Warn-Benachrichtigungen bei tatsächlich offenem Fenster/Tür. Die bestehenden Wetter-/Radarwege bleiben bewusst unverändert.

### Hinweis zu v0.6.16

v0.6.16 ist ein kleiner UI-Fix: Die Begründung unter **„Warum diese Empfehlung?“** ist jetzt ausschließlich Text. Sie wird nicht mehr als Verlauf-/More-Info-Link dargestellt und löst beim Antippen keine Navigation aus. Messwerte und echte Statuswerte bleiben weiterhin anklickbar.

### Hinweis zu v0.6.15

v0.6.15 ist ein kleiner Warnquellen-Hotfix. NINA/DWD und andere erkannte Warnanbieter sind im lokalen Einrichtungsdialog wieder auswählbar; der Warndienst bleibt weiterhin optional und `Kein Warndienst` ist der Standard.

### Hinweis zu v0.6.14

v0.6.14 ist ein kleiner Test- und Config-Flow-Hotfix. Er hält die Remote-Erfolgsseite zuverlässig als Bestätigungsdialog offen, macht die NINA-Auswertung robuster gegenüber fehlendem Entity Registry in Test-/Startup-Kontexten und korrigiert den GitHub-Pytest-Workflow.

### Hinweis zu v0.6.13

v0.6.13 behebt einen Fehler im neuen Remote-Fortschrittsdialog von v0.6.12, durch den erfolgreiche Tailscale-Verbindungen nach der Prüfung nicht gespeichert werden konnten. Außerdem wurde der lokale Mehrfach-Setup-Pfad vereinfacht und die automatische Pytest-Prüfung im GitHub-Workflow ausdrücklich aktiviert.
