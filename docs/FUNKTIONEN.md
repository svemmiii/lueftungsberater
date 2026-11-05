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

- **Raumluft-Ampel (`room_air`):** Grün = Fenster schließen oder geschlossen lassen; Gelb = Lüftung möglich beziehungsweise Messwerte beobachten; Orange = Fensterlüftung empfohlen; Rot = dringend lüften, sofern sicher.
- **Lüftungsampel (`ventilation`):** Grün = Außenbedingungen zum Lüften günstig; Gelb = eingeschränkt; Orange = eher ungünstig; Rot = sehr ungünstig.

Beide Ansichten verwenden dieselbe intelligente Engine, **aber bewusst unterschiedliche Farbperspektiven**. Der native Hauptsensorzustand und die bestehenden Attribute für Lüftungseignung werden nicht als Raum-Handlungsfarbe umgedeutet. Fehlende Sensorwerte sind gelb markierte Hinweise, kein eigenständiger Grund, eine zuvor erkannte Raumdringlichkeit zu überschreiben. Eine echte Sicherheitssperre hat in beiden Perspektiven Vorrang und erscheint als Schloss.

## Laufende Lüftung und Fensterkontakte

Mit einem Fensterkontakt erkennt die Integration tatsächliche Offen- und Schließphasen. Eine sicher beobachtete Lüftung von **mindestens fünf Minuten** kann für Routineentscheidungen bereits ausreichen; der Zeitpunkt der **letzten bestätigten Lüftung** wird jedoch erst beim beobachteten Schließen gesetzt.

**Neu in v0.12.0:** Das reine Öffnen oder Schließen verändert bei der **Raumluft-Ampel** nicht unmittelbar Grün zu Nicht-Grün oder zurück. Solange ein Fenster weniger als fünf Minuten geöffnet ist, erzeugt die laufende Sitzung allein keine Grün-Freigabe. Tatsächlich gemessene Verschlechterungen und Sicherheitssperren dürfen weiterhin sofort wirksam werden.

Wird das Fenster vor Ablauf der Mindestdauer geschlossen, bleibt die Lüftung **abgebrochen und unbestätigt**. Ausnahmsweise kann die Raumampel bei diesem Schließen Grün freigeben, wenn alle vorhandenen Lüftungsgründe tatsächlich beendet sind und die Messwerte mit mindestens 15 % Abstand innerhalb ihrer jeweiligen Gutbereiche liegen. Dazu gehören bei entsprechender Sensorbestückung unter anderem CO₂ im Bereich bis 910 ppm und die relative Feuchte zwischen 43 und 57 %. Nichtnumerische Gründe, Sperren und bestehende Hysteresen bleiben berücksichtigt. Die Ausnahme bestätigt **keine** Lüftungssitzung. Nach fünf Minuten wird ohne diesen zusätzlichen Puffer normal bewertet.

Eine bestätigte **Dauer** und eine anhand der Raumwerte erfolgreiche Lüftung sind zwei getrennte Sachverhalte. Eine Empfehlung, bei schlechten Außenbedingungen besser zu schließen, ist nicht automatisch eine Bestätigung guter Raumluft.

**Ohne Feuchte-Fortschritt:** Sinkt die absolute Luftfeuchte während eines offenen Fensters über rund 15 Minuten nicht messbar genug, ist weiteres Lüften für **diesen Versuch** nicht mehr sinnvoll. Der Assistent empfiehlt dann das Schließen, markiert die Feuchte jedoch **nicht** als erledigt: Bei weiterhin mindestens 60 % relativer Luftfeuchte bleibt der ungelöste Feuchtegrund **in Sitzungsdaten und Begründung erhalten**. Die sichtbare Handlungsampel wird bei einer Schließempfehlung trotzdem **Grün**. Das ist kein Lüftungserfolg: Erst eine echte Verbesserung darf den Feuchtebedarf zurücksetzen. Andere dringende Gründe wie CO₂ oder Schimmel sowie amtliche Sicherheitssperren bleiben unabhängig davon aktiv.

Kurze Kontakt-Ausfälle führen nicht sofort zu einer erfundenen Schließung. Bleibt ein Kontakt länger unbekannt, wird eine laufende Sitzung konservativ beendet, ohne einen nicht beobachteten Zeitpunkt als bestätigte Lüftung auszugeben.

Normale Grenzen besitzen Hysteresen. Das verhindert, dass Empfehlungen bei jedem kleinen Sensorschritt umspringen. **Neue Sicherheitsgefahren haben Vorrang** und müssen nicht auf das Ende einer laufenden Routine-Lüftung warten.

## Passive Belüftung und beobachteter Luftaustausch

In den Raumeinstellungen lässt sich optional **Passive Belüftung** aktivieren. Die Angabe dient als Hinweis, ist aber kein Nachweis einer geöffneten Fensterfläche. Die Integration beobachtet vorhandene CO₂-, Feuchte- und Temperaturwerte in einer lokalen, auf 64 Stichproben je Raum begrenzten Struktur. Ein auffälliger CO₂-Abfall kann als **vermuteter** Luftaustausch erscheinen; er wird weder als Fensterkontakt-Meldung noch als bestätigte Lüftung gespeichert.

Die Erkennung arbeitet zunächst **nur beobachtend**. Erst bei über längere Zeit belegter stabil guter Luft kann die reine 24-Stunden-Routine zurücktreten. Andere Lüftungs-, Schimmel-, Sicherheits- und Schadstoffgründe bleiben in Kraft. Zusätzliche Internetanfragen werden dafür nicht benötigt.

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
