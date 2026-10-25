# So arbeitet der Lüftungsassistent

[← Zur Übersicht](../README.md)

Lüften ist nicht allein eine Frage der Raumtemperatur. Der Lüftungsassistent betrachtet mehrere Gründe zusammen und prüft, ob die aktuellen Außenbedingungen tatsächlich helfen oder eher schaden würden.

## Die wichtigsten Eingangsdaten

| Bereich | Verwendete Daten |
| --- | --- |
| Raumklima | Temperatur und relative Luftfeuchte, daraus auch absolute Feuchte |
| Luftqualität innen | Optional CO₂, Feinstaub, VOC, NO₂/NOx, Formaldehyd und andere unterstützte Sensoren |
| Außenbedingungen | Temperatur, Feuchte, Wind, Böen, Regen, Luftqualität und aktuelle Wetterentwicklung |
| Raumstatus | Optional Fenster-/Türkontakt, Thermostat, Solltemperatur und Oberflächensensor |
| Planung | Optional stündliche Wetterprognose und ein einstellbares Nachtzeitfenster |
| Schutz | Amtliche Warnungen und passende Anweisungen; Details unter [Warnungen](WARNUNGEN.md) |

### Feuchte und Temperatur

Für eine Feuchtelüftung ist die **absolute Feuchte** entscheidender als der bloße Vergleich zweier relativer Prozentwerte. Eine kleine Neutralzone von rund **±0,5 g/m³** verhindert, dass Messrauschen zu ständig wechselnden Empfehlungen führt. Das ist keine medizinische oder bauliche Normgrenze.

Eine Temperatur-Empfehlung berücksichtigt nicht nur den Sollwert, sondern auch, ob sich der Raum durch Lüften überhaupt noch sinnvoll in Richtung dieses Werts verändern lässt.

Ohne Fensterkontakt reagiert die reine Temperaturberatung bewusst zurückhaltender: Ein neuer rein thermischer Lüftungsgrund startet erst bei etwa **4 K** Abstand zum Sollwert und endet bei einer bereits laufenden thermischen Empfehlung unter etwa **3 K**. Andere Lüftungsgründe wie CO₂ oder Feuchte behalten ihre eigenen Regeln.

### CO₂ und weitere Sensoren

Ein hoher CO₂-Wert kann ein eigenständiger Grund zum Lüften sein. Feuchteregeln oder bereits abgeschlossene Feuchte-Sitzungen dürfen einen neuen, dringlichen CO₂-Bedarf nicht einfach blockieren. Sensorfehler werden zeitlich begrenzt behandelt, statt dauerhaft einen alten Wert als aktuell auszugeben.

Bei einem vorhandenen Sensor an einer kalten Oberfläche kann die lokale Oberflächenfeuchte zusätzlich beobachtet werden. Eine länger anhaltende hohe Belastung wiegt schwerer als ein kurzer Messpeak; fehlende Oberflächenwerte werden nicht als gemessene Belastungszeit weitergezählt. **Das ist keine Schimmeldiagnose.**

## Zwei Ampelperspektiven

- **Lüftungsbedarf:** Wie wichtig ist frische Luft für diesen Raum gerade? In dieser Ansicht bedeutet Rot hohen Handlungsbedarf.
- **Lüftungsampel:** Wie gut sind die aktuellen Bedingungen zum Lüften? Hier kann Rot bedeuten, dass Lüften deutlich nachteilig ist.

Das ist **dieselbe Auswertung mit einer anderen Darstellung**. Eine harte Sicherheitssperre erscheint in beiden Fällen getrennt mit einem Schlosssymbol.

## Laufende Lüftung und Fensterkontakte

Mit einem Fensterkontakt erkennt die Integration tatsächliche Offen- und Schließphasen. Eine sicher beobachtete Lüftung von **mindestens fünf Minuten** kann für Routineentscheidungen bereits ausreichen; der Zeitpunkt der **letzten bestätigten Lüftung** wird jedoch erst beim beobachteten Schließen gesetzt.

Kurze Kontakt-Ausfälle führen nicht sofort zu einer erfundenen Schließung. Bleibt ein Kontakt länger unbekannt, wird eine laufende Sitzung konservativ beendet, ohne einen nicht beobachteten Zeitpunkt als bestätigte Lüftung auszugeben.

Normale Grenzen besitzen Hysteresen. Das verhindert, dass Empfehlungen bei jedem kleinen Sensorschritt umspringen. **Neue Sicherheitsgefahren haben Vorrang** und müssen nicht auf das Ende einer laufenden Routine-Lüftung warten.

## Wetter und kurzer Ausblick

Regen wird als möglicher praktischer Nachteil bewertet, nicht automatisch als Zeichen, dass Außenluft zu feucht zum Lüften sei. Starker Wind kann zum Geschlossenhalten raten; er ist jedoch nicht dasselbe wie eine amtliche absolute Fenstersperre.

Wenn der Wetterdienst einen stündlichen Forecast liefert, prüft die normale Beratung vorsichtig die **nächsten bis zu 60 Minuten**. Nur absehbare Änderungen, die eine gerade geplante Lüftung betreffen könnten, werden einbezogen. Der Forecast ist weder eine minutengenaue Gewitterprognose noch automatisch ein Hardlock.

## Nachtlüftung

Pro Raum kannst du ein Nachtzeitfenster festlegen, standardmäßig **22:00–07:00 Uhr**. Die Nachtanzeige zeigt mögliche längere Lüftungsgelegenheiten auf Grundlage der vorhandenen Vorhersage – sie fordert nicht dazu auf, ein Fenster unbeaufsichtigt offen zu lassen.

Die Planung achtet darauf, dass das Lüften für den jeweiligen Grund tatsächlich sinnvoll wäre und nicht einen anderen wichtigen Raumluftbedarf verschlechtert. Ein später gutes Nachtfenster darf die aktuell angezeigte Sicherheitsentscheidung nicht überstimmen. Fehlen verlässliche Prognosedaten, erfindet die Anzeige keine positiven Zeitfenster.

## Datenqualität und Ressourcen

Die automatischen Wetter-, Luft- und Warnquellen werden pro lokaler Installation gemeinsam genutzt. Messwerte behalten ihre eigenen Beobachtungs- und Abrufzeitpunkte. Alte oder unplausible Werte werden nach den jeweiligen Quellenregeln verworfen; fehlende einzelne Größen können aus verfügbaren Ersatzquellen ergänzt werden.

Die Integration vermeidet unnötige fortlaufende Komplettberechnungen und begrenzt Recorder-Verläufe bestimmter Hilfs-Entities. Mehr zu sichtbaren Verläufen steht unter [Historie](HISTORIE.md).

[← Zur Übersicht](../README.md)
