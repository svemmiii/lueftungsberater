# Changelog

## v0.9.0

### Letzte Schwellen- und Konfliktregressionen geschlossen
- Der **24-h-Routine-Fallback bleibt ein Fallback**, verliert seinen bereits vorhandenen positiven Lüftungsnutzen aber nicht mehr exakt beim Sprung **999 → 1000 ppm**. Wenn die Routine unter denselben Außenbedingungen sinnvoll grün wäre und der erste CO₂-Bereich nur wegen begrenztem Außen-CO₂-Nutzen eine Abwägung erzeugt, bleibt CO₂ der Entscheidungstreiber und die Empfehlung wird als grünes Lüften **mit Nachteil** fortgeführt. Die Routine wird dafür nicht wieder als normaler Peer in den Merger aufgenommen.
- An der **59,9 → 60,0-%-Feuchtegrenze** kann ein neu aktiver Feuchtebedarf eine bereits grüne Empfehlung nicht mehr allein wegen **mäßiger** Außenluftqualität auf Gelb abschwächen, wenn die Außenluft die Feuchte tatsächlich verbessert und keine zusätzliche NINA-/Wetter-/Außen-CO₂-Warnung dagegen spricht. `poor`/`very_poor` bleiben unverändert restriktiver.
- Ein `co2_warten` wegen **höherem gemessenem Außen-CO₂** übernimmt für den Konfliktvergleich nicht mehr künstlich die Dringlichkeit des gerade aktiven 1000-/1400-/2000-ppm-Innenbands. Der Außen-CO₂-Nachteil behält damit bei unveränderten Außenwerten dieselbe Konfliktstärke; ein zusätzlicher gelber Komfortgrund wird über die normale Prioritätslogik bewertet statt durch einen pauschalen CO₂-Sonderweg.
- Drei neue Regressionstests sichern genau diese Übergänge ab. Die bestehenden Monotonie-/Warnungs-/Mehrfachgründe-Tests bleiben unverändert aktiv.

### Zusammenführung und Entscheidungs-Memory stabilisiert
- Der Konflikt-Merger löst den **vollständigen Kandidatensatz in einem Schritt** auf: stärkster Öffnungsgrund gegen stärksten Gegengrund, jeweils nach Dringlichkeit und bei Gleichstand nach Schutzstufe. Ein dritter schwächerer Grund kann dadurch nicht mehr zufällig bestimmen, welche anderen Kandidaten überhaupt miteinander verglichen werden.
- `beneficial` und echte `tradeoff`-Kandidaten werden **immer mit derselben Dringlichkeitslogik** ausgewählt – unabhängig davon, ob gleichzeitig ein orangefarbener Gegengrund existiert. Dadurch kann ein zusätzlicher schwacher Kandidat nicht mehr den Auswahlalgorithmus wechseln; z. B. bleibt eine dringlichere Feuchte-Abwägung gegenüber einem schwächeren grünen CO₂-Grund auch an der 24-h-Grenze gelb.
- Die **24-h-Routine ist jetzt tatsächlich ein Fallback**: Sie wird nur als eigener Bedarf aktiviert, wenn kein konkreter CO₂-/Feuchte-/Schimmel-/Temperaturgrund vorliegt. Damit kann „seit 24 Stunden nicht gelüftet“ eine bereits laufende echte Entscheidung weder verschärfen noch abschwächen.
- Kritisches CO₂ gegen ungewöhnlich sehr schlechte Außenluft bleibt stabil eine echte Abwägung, auch wenn ein schwacher Zusatzgrund an einer Schwelle hinzukommt (z. B. 23,9 → 24,0 h oder 59,9 → 60,0 % rF).
- Der Merger trennt echte **Hard Safety Locks** (NINA-/Wetter-`danger`, weiterhin außerhalb des normalen Mergers) von stark schädlichen gemessenen Außenbedingungen. Ungewöhnlich **sehr schlechte Außenluft** bleibt ein starker roter Gegengrund, ist aber kein absoluter Lock: kritisches CO₂ mit höherer Dringlichkeit kann weiterhin eine echte gelbe Abwägung ergeben.
- Außenwarnungen/AQ werden als **globale Gegenseite** einmal in den Kandidatensatz eingebracht und hängen nicht mehr davon ab, ob zufällig noch Routine, Temperatur oder Feuchte als zweiter Bedarf aktiv wird. Dadurch kann z. B. das Erreichen von 24,0 h eine CO₂-/AQ-Entscheidung nicht allein durch das Auftauchen eines neuen Kandidaten umstufen.
- Bei gleich dringlichen Gegengründen wird die Schutzbedeutung stabil berücksichtigt: Oberflächen-/Schimmelrisiko hat Vorrang vor gleich starken Komfortgründen, während CO₂ und normale Feuchte weiterhin eine echte gelbe Abwägung bilden können.
- Der Mehrfachgründe-Merger unterscheidet intern jetzt **beneficial / tradeoff / neutral / harmful / strong_harmful** statt gelbe oder rote Zustände allein nach ihrer Farbe gleichzusetzen. Ein neutraler Zusatzgrund wie `feuchte_neutral` kann dadurch keine bereits vorhandene Empfehlung „besser geschlossen“ mehr aufweichen; `strong_harmful` bleibt zugleich klar von einem echten Safety-Lock getrennt.
- Zusätzliche NINA-/Wetter-Vorsicht wird monoton angewendet: Eine neue Außenwarnung darf eine bestehende restriktivere Entscheidung nicht öffnungsfreundlicher machen. Insbesondere bleiben Fälle wie **1500 ppm innen / 1800 ppm außen** bei `co2_warten`, auch wenn zusätzlich eine Vorsichtsmeldung hinzukommt.
- `primary_need` bleibt der stärkste Innenraum-/Anzeigegrund. Neu getrennt davon wird `decision_need` als tatsächlicher Entscheidungstreiber geführt und für die Zustands-Memory verwendet. Dadurch behält z. B. eine laufende Temperaturentscheidung ihre eigene Hysterese, auch wenn Feuchte gleichzeitig der stärkere UI-Grund ist.
- Die gespeicherte Decision-Memory liest ältere v0.9.0-Vorab-Builds mit `primary_need` einmalig als Fallback, speichert danach aber den getrennten `decision_need`.
- Die 24-h-Routinelüftung beendet sich bei vorhandenem Fensterkontakt nicht mehr unmittelbar nach dem Öffnen. Sie bleibt bis **mindestens fünf reale Offen-Minuten** aktiv und passt damit zur bereits bestehenden Bestätigungsschwelle des Airing-Trackers.
- Neue Regression-/Invariantentests sichern ab, dass zusätzliche weiche Außenwarnungen die Öffnungsempfehlung niemals verbessern und dass die Routinelüftung sowie die getrennte Temperatur-Hysterese stabil bleiben.
- Die **Schwere der Außenluftqualität bleibt im Mehrfachgründe-Pfad erhalten**: `poor`/`very_poor` werden nicht mehr zu einem generischen Luftqualitäts-Hinweis zusammengefaltet und anschließend fälschlich als `luftqualitaet_maessig` oder bloße gelbe Abwägung ausgegeben.
- Konflikte zwischen gleichzeitig nützlichen und schädlichen Lüftungsgründen berücksichtigen jetzt deren Dringlichkeit. Ein niedriger priorisierter Komfortgrund kann damit z. B. einen **persistenten Schimmel-Gegengrund** nicht mehr blind mit Grün überstimmen. Die bestehende CO₂-Monotonie bleibt als ausdrückliche Ausnahme erhalten: eine höhere CO₂-Stufe darf eine unabhängig sichere Lüftungsmöglichkeit nicht schwächen.
- `erwaermen` verwendet beim Start dieselbe physikalische Obergrenze wie bei einer laufenden Lüftung: Außenluft darf höchstens **Solltemperatur + 4 K** betragen. Damit kann die Karte bei unveränderten Sensorwerten nicht mehr erst „zum Erwärmen öffnen“ und unmittelbar nach dem Öffnen „fertig“ melden; auch die `weiter_lueften`-Begründung nutzt dieselbe Bedingung.

### Mehrere Lüftungsgründe werden gemeinsam bewertet
- Die Engine ermittelt weiterhin einen nachvollziehbaren Hauptgrund für Anzeige und Dringlichkeit, vergisst aber **gleichzeitig aktive Nebengründe nicht mehr**. CO₂, Feuchte/Oberflächenfeuchte und Temperatur werden jeweils gegen dieselben Außenbedingungen geprüft und die Ergebnisse anschließend zusammengeführt. Die 24-h-Routine bleibt davon getrennt ein reiner Fallback, wenn kein konkreter Innenraumgrund aktiv ist.
- Dadurch kann ein zusätzlicher Innenraumfehler eine unabhängig sinnvolle Lüftungsmöglichkeit nicht mehr allein durch einen Prioritätswechsel verschwinden lassen. Reproduzierte Grenzfälle wie **1800 ppm + 64,9 → 65,0 % rF** sowie ein Sprung an der 60-%-Feuchtegrenze bleiben handlungslogisch stabil.
- CO₂ bleibt bei einer tatsächlich CO₂-relevanten Lüftung bewusst der Sitzungs-/Hysterese-Treiber, auch wenn ein zweiter Innenraumgrund das Öffnen zusätzlich rechtfertigt. Die bestehende Mindestlüftung und Wiedereinschaltlogik gehen dadurch bei Mehrfachgründen nicht verloren.
- Regressionstests sichern zusätzlich die Invariante ab, dass **1399 → 1400 ppm bei ansonsten identischen Bedingungen und Regen** die Empfehlung nicht mehr abschwächen darf.

### CO₂-Ziele und Außen-CO₂ korrigiert
- Kritisches CO₂ mit nur einem weichen Außenhinweis (z. B. mäßiger Luftqualität) behält bei weiterhin grüner `co2_kritisch`-Entscheidung das passende Sitzungziel. Ein unsichtbarer Sprung von **850 auf 1850 ppm** nur durch einen weichen Hinweis ist entfernt.
- Der 1700+-CO₂-Zweig verwendet für starke Feuchtenachteile kontinuierliche absolute Feuchtedifferenzen statt eines zusätzlichen harten 65-%-Sprungs.
- Ein gemessener Außen-CO₂-Wert, der deutlich schlechter als innen ist, wird als **allgemeiner weicher Außenluft-Nachteil** berücksichtigt. Das gilt nun auch für Kühlung, Feuchtelüftung, Routine und die längere Nachtlüftungsstrategie sowie für Situationen ohne aktuellen Innenraum-Lüftungsgrund.
- Ein CO₂-Sitzungsziel wird bei vorhandenem Außen-CO₂ nicht mehr physikalisch unerreichbar unter einen ungünstig hohen Außenwert gelegt; wenn Außenluft den Innenwert trotzdem verbessern kann, wird das Ziel vorsichtig oberhalb des gemessenen Außenwerts begrenzt.

### Einheiten und Forecast robuster
- Wind wird über Home Assistants `SpeedConverter` normalisiert. **Beaufort und ft/s** werden damit korrekt unterstützt; unbekannte Einheiten werden verworfen statt stillschweigend als km/h interpretiert.
- Forecast-Niederschlagsmengen werden auf **Millimeter** normalisiert, sodass Weather-Entities mit `in` nicht mehr gegen mm-Schwellen verglichen werden.
- Die README beschreibt die tatsächlich verwendete Windstufe jetzt konsistent mit den Codegrenzen.

### Sensor-Ausfälle erfinden keine Zeit mehr
- Ein laufender Fensterkontakt darf kurz `unknown`/`unavailable` sein, aber nur innerhalb einer **2-Minuten-Grace**. Danach endet die bestätigte Offenzeit am letzten sicher bekannten Zeitpunkt; unbekannte Minuten können dadurch keine 5-Minuten-Lüftung vortäuschen.
- Beim optionalen Oberflächenfeuchte-Tracking werden fehlende Messwerte höchstens kurz toleriert. Nach **10 Minuten ohne gültigen Wert** wird eine kritische Phase am letzten bestätigten Messpunkt pausiert, statt Sensor-Downtime als gemessene Expositionszeit weiterzuzählen.

### Tests / CI / Release
- Neue Regressionstests decken Mehrfachgründe, CO₂-Monotonie, das kritische 850/1850-Ziel, Außen-CO₂ bei Kühlung/Nachtlüftung, Beaufort/ft/s, Inch-Niederschlag sowie lange `unknown`-/`unavailable`-Phasen ab.
- GitHub Actions prüft das Frontend-JavaScript jetzt zusätzlich mit `node --check`, bevor der Python-Teststack läuft.
- Versionsangaben in Manifest und Python-Konstanten stehen gemeinsam auf **0.9.0**.

## v0.8.1

### Lüftungsbedarf-Ampel ruhiger und eindeutiger
- Die Standardansicht **„Lüftungsbedarf“** bleibt dieselbe vollständige Gesamtbewertung, wird vorne aber konsequenter als Handlungsampel dargestellt: **Grün = aktuell nichts zu tun**, **Gelb = beobachten**, **Orange = Lüften ist sinnvoll**, **Rot = jetzt lüften**.
- Leichte Abweichungen wie knapp erhöhte Raumfeuchte, leicht erhöhtes CO₂ oder eine kleine Temperaturabweichung dürfen deshalb bewusst noch Grün bleiben, solange daraus im Gesamtsystem kein sinnvoller Handlungsdruck entsteht. Grün bedeutet dabei nicht „jeder Messwert ist perfekt“, sondern „du musst aktuell nichts unternehmen“.
- Der 24-Stunden-Routine-Fallback bleibt bewusst sichtbar und wird nicht in der ruhigeren Grünzone versteckt.
- Die optionale **„Grün = Lüften“**-Ansicht behält ihre eigene Bedeutung: Grün = gute Lüftungsgelegenheit, Gelb = neutral/Abwägung, Orange/Rot = zunehmend ungeeignete Außenbedingungen. Die beiden Ansichten werden nicht künstlich spiegelverkehrt eingefärbt.
- Die eigentliche Entscheidungsengine, Sensorbeteiligung und Safety-Lock-Priorität bleiben gemeinsam; geändert wurde die Darstellungsschwere der Bedarfsperspektive, nicht die grundlegende Physik der Lüftungsentscheidung.

### Kurzer Wetter-Vorlauf für die normale Karte
- Die normale Live-Beratung kann jetzt zusätzlich die **nächsten bis zu 60 Minuten** der stündlichen Wettervorhersage als vorsichtigen Vorlauf berücksichtigen.
- Kommendes schlechteres Wetter beeinflusst die Empfehlung nur, wenn es die erwartete Lüftungsdauer realistisch treffen kann. Ein Gewitterpunkt weit nach einer kurzen Stoßlüftung blockiert deshalb nicht unnötig die aktuelle Gelegenheit.
- Der Blick funktioniert auch in die andere Richtung: Soll sich eine aktuell ungünstige Wetterlage innerhalb der nächsten Stunde beruhigen, kann die Karte auf die voraussichtlich bessere Gelegenheit hinweisen.
- Forecast-Daten sind ausschließlich eine **weiche Planungshilfe**. Ein künftiger Forecast erzeugt niemals allein einen harten Safety-Lock; aktuelle Wettergefahr, Radar und amtliche Schutzanweisungen behalten Vorrang.
- Der gemeinsame Wetter-Forecast wird pro Lüftungsassistent zwischengespeichert und höchstens etwa alle **15 Minuten** aktualisiert. Dadurch erhalten alle Räume denselben kurzen Ausblick, ohne pro Raum zusätzliche Forecast-Abfragen zu erzeugen.
- Neue Diagnoseattribute zeigen die erkannte kurzfristige Änderung, deren Art und den zeitlichen Abstand zum relevanten Forecastpunkt.

### Kartentexte verständlicher
- Nutzertexte in **Deutsch, Englisch und Türkisch** wurden nochmals auf eine möglichst direkte Aussage geprüft: zuerst was zu tun ist, danach kurz warum.
- Der unklare Satz **„Die aktuelle Außen- oder Wetterlage spricht zusätzlich für Vorsicht“** wurde entfernt. Wenn bekannt, nennt die Karte nun konkret den Grund – z. B. Gewitter, Regen, starken Wind oder ungünstige Außenbedingungen.
- Bei einer erwarteten Wetteränderung werden bewusst Formulierungen wie **„in Kürze“** oder **„innerhalb der nächsten Stunde“** verwendet. Ein stündlicher Forecastpunkt wird nicht fälschlich als minutengenauer Beginn oder minutengenaues Ende eines Ereignisses dargestellt.
- Leicht erhöhte Innenwerte in einer grünen Bedarfskarte werden offen benannt, gleichzeitig aber klar eingeordnet: Die Karte sagt ausdrücklich, wenn daraus aktuell noch kein Lüften nötig ist.
- Aktuelle harte Wetterlagen bleiben eindeutig formuliert; eine erwartete Besserung darf als Zusatz genannt werden, hebt die aktuelle Sperre aber nicht vorzeitig auf.

### Tests / Release
- Neue Regressionstests für die ruhigere Bedarfskarte, den 24-Stunden-Fallback sowie bevorstehende und abklingende Kurzzeit-Wetterlagen ergänzt.
- CO₂-Mindestlüftung berücksichtigt eine neu auftretende, unmittelbar relevante Forecast-Verschlechterung weiterhin als echten neuen Außenfaktor; bereits bekannte Bedingungen verursachen kein unnötiges Hin-und-her.
- Release-Struktur bleibt auf das bestehende Repository-Layout beschränkt; keine Cache-, `__pycache__`-, `.pyc`- oder Arbeitsdateien werden in das Archiv aufgenommen.

## v0.8.0

### NINA / MoWaS sicherer und praxisnäher ausgewertet
- Vollständige Entwarnungen werden jetzt von bloßen Teil-/bedingten Entwarnungen sauber getrennt. Eine eindeutige Aufhebung wie **„Die Warnung ist aufgehoben“** darf eine alte, im Entwarnungsdatensatz noch mitgeführte Schutzanweisung überstimmen: Die harte Sperre fällt, die normale Lüftungsbewertung läuft wieder und der bestehende Entwarnungshinweis bleibt sichtbar.
- **Teilentwarnung**, bedingte/teilweise Entwarnung und Entwarnung mit Einschränkungen bleiben defensiv: Ist weiterhin eine amtliche Schließanweisung vorhanden, bleibt die harte Sperre aktiv.
- Fenster-/Lüftungsanweisungen werden nicht mehr nur über einzelne starre Vollsätze erkannt. Zusätzlich gibt es einen konservativen, satzgebundenen Matcher für reale MoWaS-Varianten wie „alle Fenster und Türen schließen“, „Fenster geschlossen halten“ oder „Belüftung ausschalten“. Freigabeformulierungen wie „Fenster können wieder geöffnet werden“ werden ausdrücklich ausgenommen.
- Bei mehreren gleichzeitigen Warnslots gewinnt jede noch aktive lüftungsrelevante Gefahr über eine Entwarnung eines anderen Slots. Dadurch können harte Sperre und globaler Entwarnungshinweis nicht mehr gleichzeitig erscheinen.
- Nur tatsächlich lüftungsrelevante Warnungen fließen noch in den Warn-Fingerprint ein. Eine parallele, für die Lüftung irrelevante Meldung (z. B. Gewässer-/Ölwarnung) kann dadurch keine identische Rauchwarnung erneut benachrichtigen.
- NINA-Details aus `nina.get_details` werden weiterhin gecacht, aber spätestens nach fünf Minuten neu geladen. Änderungen an einer laufenden Warnung bleiben dadurch nicht wegen einer unveränderten Warnungs-ID dauerhaft im Cache hängen.
- Diagnoseattribute merken sich jetzt die tatsächlich entscheidende NINA-/DWD-Quellentität statt eines zufälligen Elements aus einer Menge.

### Entscheidungsengine konsistenter
- Ein zusätzlicher CO₂-Lüftungsgrund kann eine bereits unabhängig sinnvolle grüne Lüftung nicht mehr abschwächen. Grenzfälle wie **1399 → 1400 ppm** oder **1999 → 2001 ppm** bleiben deshalb mindestens so handlungsstark, wenn Feuchte, Temperatur oder Schimmelschutz unter denselben Außenbedingungen ohnehin bereits klar zum Lüften raten.
- Harte amtliche Schutzsperren und echte Außenwarnungen behalten dabei unverändert höchste Priorität. Die Änderung verhindert nur widersprüchliche Abschwächungen innerhalb gleichzeitig vorhandener Innenraumgründe.

### Robustheit / Home Assistant
- Nicht-endliche Messwerte (`NaN`, `+/-inf`) werden in Provider- und CO₂-Pfaden verworfen. Gespeicherte CO₂-Gnadenwerte werden ebenfalls validiert.
- Unbekannte Temperatureinheiten werden nicht mehr stillschweigend als °C interpretiert. Ein nicht konvertierbarer Wert gilt stattdessen als nicht verwendbar; dabei wird auch der von aktuellen Home-Assistant-Konvertern verwendete `HomeAssistantError` sauber abgefangen.
- Raum-Benachrichtigungen werden pro Raum serialisiert, damit nahezu gleichzeitige Sensorupdates denselben Zustandsübergang nicht doppelt melden können.
- Der gemeinsame Outside-Coordinator beobachtet Änderungen der Home-Assistant-Entity-Registry und zieht seine Provider-Quellen dynamisch nach. Später erzeugte oder umbenannte Wetter-/Warnentitäten benötigen dadurch keinen Lüftungsberater-Reload mehr.
- Der notwendige Home-Assistant-Kompatibilitätsworkaround für den privaten Subentry-Capability-Cache ist in `compat.py` isoliert und greift nur, solange die betreffende interne HA-Struktur existiert.
- Python-seitige Versionsangaben verwenden eine gemeinsame `INTEGRATION_VERSION`; Manifest, Frontend-Cache-Buster und Geräteanzeige stehen für dieses Release auf **0.8.0**.
- `nina_status` ist im Datenmodell explizit als `none | caution | danger | clear` typisiert; nicht verwendete Warnparameter und kleine doppelte/mehrdeutige Stellen wurden bereinigt.
- Der tägliche GitHub-Pytest-Job installiert nicht mehr dauerhaft einen alten festgepinnten Home-Assistant-Teststack, sondern aktualisiert auf die jeweils aktuelle `pytest-homeassistant-custom-component`-Version und protokolliert die verwendeten Versionen.

### Tests / Qualität
- Neue Regressionstests decken reale Voll-Entwarnungen mit alten Schließtexten, Teilentwarnungen mit weiterhin gültiger Schutzanweisung, flexible MoWaS-Formulierungen, parallele Warn-/Entwarnungsslots, irrelevante Warn-IDs sowie `NaN`/`inf` und die CO₂-Grenzsprünge der Engine ab.
- Die bestehende Sicherheitsarchitektur bleibt erhalten: amtliche harte Sperren können weiterhin nicht durch CO₂, Feuchte, Temperatur oder Komfortgründe überstimmt werden.

## v0.7.9

### CO₂-Wiedereinschaltung nach abgeschlossener Lüftung stabilisiert
- Nach einer erfolgreich abgeschlossenen CO₂-Lüftung wird die auslösende CO₂-Stufe jetzt als **Wiedereinschaltgrenze** gespeichert. Dadurch kann der Assistent nach dem Schließen nicht sofort aufgrund inzwischen besserer Außenbedingungen dieselbe Lüftung erneut verlangen.
- Beispiel: Wurde eine Sitzung erst in der **1400-ppm-Stufe** sinnvoll und bei etwa **1250 ppm** erfolgreich beendet, bleibt CO₂ anschließend zwischen 1000 und 1399 ppm für diesen Zyklus ruhig. Erst ein erneutes Erreichen von 1400 ppm darf diese Stufe wieder als Lüftungsgrund freigeben.
- Niedrigere CO₂-Stufen können sich wieder freischalten, sobald der Raum nachweislich deutlich besser geworden ist. Dafür gilt eine **50-ppm-Deadband plus 2 Minuten Stabilität**: Aus einer 1400er-Sperre wird die 1000er-Stufe erst wieder freigegeben, wenn CO₂ höchstens 950 ppm für 2 Minuten stabil erreicht.
- Dasselbe Prinzip gilt stufenweise für die höheren Bereiche: 2000 → 1700, 1700 → 1400 und 1400 → 1000. Fällt CO₂ bereits deutlich weiter, kann nach derselben stabilen Deadband direkt die niedrigste tatsächlich erreichte Stufe freigegeben werden.
- Messwertflattern wie **999 → 1000 ppm** reicht damit ausdrücklich nicht aus, um direkt nach einer beendeten höheren Sitzung erneut „Lüften“ auszulösen.
- Die Wiedereinschaltgrenze bleibt neustartsicher gespeichert. Der kurze 2-Minuten-Deadband-Timer wird nur aus frischem Entscheidungs-Memory fortgesetzt; die eigentliche Sperrstufe bleibt auch über längere Neustarts erhalten.
- Die bestehende 5-Minuten-Mindestlüftung, die situationsabhängigen 850/1250/1550/1850-ppm-Ziele und die normale Gesamtbewertung aus Innen- und Außenwerten bleiben unverändert erhalten.

### Entwarnungs-Erkennung defensiver gemacht
- Formulierungen wie **„Teilentwarnung“**, **„bedingte Entwarnung“**, **„teilweise Entwarnung“** oder **„Entwarnung mit Einschränkungen“** werden nicht mehr allein wegen des enthaltenen Wortes „Entwarnung“ als vollständiges `clear` gewertet. Sie bleiben normale Meldungstexte und werden anschließend weiter ausgewertet.
- Diese Begriffe erzeugen bewusst **keinen neuen Warnzustand und keine neue Ampelfarbe**; sie dienen ausschließlich als Schutz vor einer falschen Voll-Entwarnung durch Substring-Erkennung.
- Eine explizite amtliche Anweisung wie **„Fenster und Türen geschlossen halten“** hat jetzt auch dann Vorrang, wenn dieselbe Meldung gleichzeitig das Wort „Entwarnung“ enthält. Harte Schutzanweisungen können dadurch nicht versehentlich durch einen widersprüchlichen Entwarnungstext aufgehoben werden.
- Zusätzliche Formulierungsvarianten wie „Fenster und Türen weiterhin geschlossen halten“ werden als amtliche Schließanweisung erkannt.

### Tests / Release
- Neue Regressionstests decken die CO₂-Wiedereinschaltung, die 50-ppm-/2-Minuten-Deadband, direkte Rückkehr in eine niedrigere CO₂-Stufe, Neustart-Memory sowie qualifizierte Entwarnungsformulierungen und widersprüchliche Schutzanweisungen ab.

## v0.7.8

### CO₂-Lüftungssitzung repariert und situationsabhängig beendet
- Behebt einen Praxisfehler, bei dem eine laufende CO₂-Lüftung ihren Sitzungskontext verlieren konnte, sobald der Messwert z. B. von über 1400 ppm wieder knapp unter 1400 ppm fiel. Eine einmal tatsächlich gestartete CO₂-Lüftung bleibt jetzt als eigene Sitzung erhalten und hängt nicht mehr davon ab, welcher Grund oder Modus beim nächsten Sensorupdate vorne liegt.
- Die 5-Minuten-Mindestlüftung bleibt unverändert bestehen. Sie ist weiterhin nur eine zusätzliche Mindestdauer und ersetzt nicht die anschließende CO₂-Abschlusshysterese. Harte Safety-Locks und neu deutlich schlechtere Außenbedingungen dürfen weiterhin sofort übersteuern.
- Das CO₂-Abschlussziel ist jetzt **situationsabhängig** statt für jede Sitzung pauschal 850 ppm. Entscheidend ist die CO₂-Stufe, ab der die aktuelle Gesamtbewertung das Lüften tatsächlich sinnvoll bzw. vertretbar gemacht hat.
- Bei guten Außenbedingungen bleibt der normale Zielbereich erhalten: Wenn der Assistent bereits ab etwa 1000 ppm zum Lüften geraten hätte, liegt das Sitzungsziel weiterhin bei **850 ppm** – auch wenn der Nutzer das Fenster erst bei einem deutlich höheren Wert öffnet.
- Wird Lüften wegen ungünstiger Außenbedingungen erst in einer höheren CO₂-Stufe sinnvoll, gilt derselbe 150-ppm-Hysteresepuffer situationsabhängig: typischerweise **1400 → 1250 ppm**, beim stärkeren **1700-ppm-Override → 1550 ppm** und bei einer nur noch im kritischen Bereich vertretbaren Lüftung **2000 → 1850 ppm**.
- Das jeweilige Ziel muss weiterhin **2 Minuten stabil** erreicht bzw. unterschritten sein, bevor die Lüftung als beendet gilt. Die letzten 50 ppm oberhalb des Sitzungsziels werden als gelbe Zielnähe dargestellt.
- Kartentexte nennen bei einer laufenden CO₂-Sitzung jetzt bei Bedarf das konkrete Ziel dieser Lüftung. Die frühere pauschale Dauerangabe „bis unter etwa 1000 ppm“ wurde entfernt, weil sie bei situationsabhängigen Zielwerten irreführend wäre. Deutsch, Englisch und Türkisch wurden gemeinsam angepasst.
- Der explizite Sitzungskontext einschließlich Zielwert wird mit dem vorhandenen kleinen Entscheidungs-Memory gespeichert und kann einen Home-Assistant-Neustart überstehen.

## v0.7.7

### CO₂-Lüftungssitzungen stabilisiert
- Wenn der Lüftungsassistent aufgrund seiner Gesamtbewertung tatsächlich zum Lüften wegen CO₂ auffordert und anschließend ein Fenster geöffnet wird, erhält diese gestartete CO₂-Lüftung jetzt **mindestens 5 Minuten** Zeit. Ein sehr schneller CO₂-Abfall kann die Empfehlung in dieser Mindestzeit nicht sofort wieder auf „fertig“ umschalten.
- Die Mindestzeit beginnt mit der tatsächlichen Fensteröffnung. War das Fenster beim Entstehen des CO₂-Lüftungsgrunds bereits geöffnet, wird die bereits vergangene Öffnungszeit berücksichtigt.
- Öffnet der Nutzer ein Fenster entgegen einer aktuellen CO₂-Empfehlung wie „noch warten“, wird daraus bewusst **keine** künstliche 5-Minuten-Sitzung erzeugt.
- Bereits beim Start bekannte und von der Gesamtentscheidung akzeptierte Nachteile draußen werden während der kurzen Mindestzeit nicht sekündlich neu gegen den inzwischen fallenden CO₂-Wert ausgespielt. Neue relevante Verschlechterungen der Außenlage dürfen die Mindestzeit dagegen aufheben; harte Safety-Locks und amtliche Schließanweisungen übersteuern weiterhin sofort.
- War die ursprüngliche CO₂-Empfehlung wegen ungünstiger Außenbedingungen nur **Gelb / kurz und beobachten**, bleibt auch die Mindestphase bewusst vorsichtig und wird nicht künstlich auf Grün hochgestuft.
- Nach Ablauf der 5 Minuten gilt unverändert die vorhandene CO₂-Abschlusshysterese: Zielnähe zwischen 850 und 900 ppm sowie Abschluss erst nach mindestens 2 stabilen Minuten bei höchstens 850 ppm.
- Startzeit und kleiner Sitzungskontext werden mit dem vorhandenen Entscheidungs-Memory gespeichert, damit ein kurzer Home-Assistant-Neustart die Mindestlüftung nicht künstlich verkürzt.
- Neue kurze Kartentexte für die Mindestlüftung wurden in Deutsch, Englisch und Türkisch ergänzt.

### Texte und Formulierungen überarbeitet
- Alle nutzerseitigen Empfehlungstexte der Hauptkarte wurden auf Verständlichkeit, Satzbau und Bezug zur tatsächlichen Entscheidungslogik geprüft. Die zugrunde liegende Lüftungsentscheidung bleibt unverändert.
- Die Bedarfsperspektive verwendet jetzt den klareren Begriff **„Lüftungsgrund“** statt „Lüftungsdruck“. Grün bedeutet damit verständlich: aktuell besteht kein relevanter Grund zu lüften.
- Mehrere Kurzbegründungen wurden sprachlich geglättet, insbesondere für CO₂, Feuchte, Oberflächenfeuchte, Temperatur, Routine-Lüftung, Wind, Regen und Zielkonflikte mit ungünstigen Außenbedingungen.
- Die Nachttexte wurden vereinfacht: bedingte Nachtlüftung spricht jetzt von **Einschränkungen** statt der schwerer verständlichen Formulierung „nicht ohne Abwägung“.
- Benachrichtigungen und Karten-Hinweise wurden an denselben kurzen, direkten Sprachstil angepasst.
- Deutsche Konfigurations- und Editor-Texte wurden grammatikalisch bereinigt; unter anderem „Lüftungsassistenten“, Nacht-Zeitfenster, Remote-Hinweise und einzelne UI-Beschriftungen.
- Englische und türkische Texte wurden inhaltlich entsprechend angeglichen; mehrere wörtlich oder technisch klingende Formulierungen wurden natürlicher formuliert.
- Keine Grenzwerte, Prioritäten, Hysteresen, Warnlogiken oder Nachtentscheidungen wurden durch dieses Text-Update verändert.

## v0.7.6

### Zwei Ampelperspektiven sauber getrennt
- Die eigentliche Lüftungsentscheidung bleibt dieselbe vollständige Gesamtabwägung aus Innen- und Außenwerten. v0.7.6 baut **keine zweite Entscheidungsengine** und verändert die bestehenden CO₂-/Feuchte-/Temperatur-Schwellen nicht.
- Die Standardansicht `room_air` wird als **Lüftungsbedarf-/Handlungsdruck-Perspektive** sauber ausgewertet: leichte Innenabweichungen bleiben bei deutlich ungeeigneter Außenluft bewusst ruhig, stärkere Gründe steigen schrittweise über Gelb/Orange bis Rot an.
- Regression für den v0.7.5-Doppel-Orange-Fall: Bei ansonsten guten Innenwerten, nur leicht erhöhter Raumfeuchte und noch feuchterer Außenluft kann die Lüftungsampel weiterhin Orange sein, während die Bedarfsperspektive korrekt Grün zeigt.
- `room_air` tauscht nicht mehr nur die Farbe aus. Empfehlung und Kurzbegründung werden jetzt ebenfalls aus der Raum-/Bedarfsperspektive formuliert; Safety-Locks behalten immer den eindeutigen amtlichen Schutztext.
- Akzeptiert ein starker Innenbedarf bewusst einen ungünstigen Außenfaktor, benennt die Bedarfsperspektive diesen Zielkonflikt jetzt korrekt in Deutsch, Englisch und Türkisch, statt die Außenbedingungen fälschlich als passend zu bezeichnen.
- Kartenlayout, Messwertdarstellung und Bedienung bleiben unverändert.

### Nachtlüftung ruhiger und plausibler
- Für einen längeren, weitgehend unbeaufsichtigten Nachthinweis werden Forecastpunkte mit mehr als **9 K** Abstand zur aktuellen Raumtemperatur verworfen. Die normale Live-Lüftungslogik ist davon nicht betroffen.
- Die Forecastauswertung darf intern bis zu **eine Stunde hinter die konfigurierte Nacht-Endzeit** schauen, um den letzten Abschnitt belastbar zu bestätigen; angezeigt wird weiterhin niemals über die vom Nutzer eingestellte Endzeit hinaus.
- In der letzten Stunde wird bei dünner Forecastbasis der letzte belastbare Nacht-Basisstatus gehalten statt eine neue positive Strategie zu erfinden. Verschlechterungen dürfen die Aussage weiterhin vorsichtiger machen; harte NINA-/DWD-Schutzsperren übersteuern jederzeit.
- Nach einer späten Entwarnung kann auf den vorherigen Basisplan zurückgefallen werden. Ist der eigentliche Nacht-Lüftungsgrund inzwischen weggefallen oder der aktuelle Temperaturabstand unplausibel groß, wird kein alter Plan künstlich festgehalten.
- Der gehaltene Nacht-Basisstatus wird kompakt gespeichert und nach einem Home-Assistant-Neustart innerhalb desselben Nachtfensters wiederhergestellt.

### Neustartsicherheit
- Die Zeitpunkte der 3-Minuten-CO₂-Rücklaufhysterese und der 2-Minuten-Abschlussstabilisierung werden kompakt mit dem bestehenden Entscheidungs-Memory gespeichert und nach einem Neustart weiterverwendet, sofern der Live-Kontext noch passt.
- Der vorhandene 60-Sekunden-Failsafe für einen kurz ausfallenden CO₂-Sensor übersteht nun ebenfalls einen Neustart, ohne die Grace-Zeit neu zu starten. Ein abgelaufener Wert wird nicht als aktueller Messwert wiederhergestellt.
- Es wird weiterhin **keine zusätzliche CO₂-/Temperatur-/Feuchte-Rohhistorie** angelegt. Gespeichert werden nur kleine Zustandsautomaten und Zeitpunkte, die nach einem Neustart nicht sicher aus Live-Entities rekonstruierbar sind.

### Tests / Release
- Neue Regressionstests für beide Ampelperspektiven, den 9-K-Nachtfilter, den +1-h-Forecastpuffer, den Final-Hour-Hold, Safety-Override/Entwarnung sowie restartfähige CO₂-Zustände ergänzt.
- Release-Archiv bleibt auf das normale Repository-Layout beschränkt; keine Root-Manifeste, Caches, `__pycache__`, `.pyc` oder Arbeitsdateien.

## v0.7.5

- CO₂-Empfehlungen starten weiterhin bei 1000 ppm, werden bei geschlossenem Fenster aber erst nach 3 stabilen Minuten unter 900 ppm zurückgenommen.
- Eine bereits gestartete CO₂-Lüftung wird als Sitzung behandelt: oberhalb 900 ppm weiterlüften, 850–900 ppm gelbe Zielnähe, Abschluss erst nach 2 stabilen Minuten bei höchstens 850 ppm.
- Steigt CO₂ während der Stabilitätsphase wieder über die jeweilige Rückfallgrenze, beginnt die Stabilitätszeit neu.
- Die sichtbaren CO₂-Klassen (<800 / 800–999 / 1000–1399 / 1400–2000 / >2000 ppm) bleiben unverändert.

## v0.7.4

- Trennt den Benachrichtigungs-Fingerprint jetzt strikt nach der tatsächlich aktiven Quelle (`nina_*`, `luftqualitaet_*`, `wetter*`).
- Änderungen der normalen Luftqualität können dadurch eine unveränderte NINA-Warnung nicht mehr erneut benachrichtigen.
- Umgekehrt ändern NINA-/DWD-Daten nicht mehr die Identität einer reinen Luftqualitätswarnung.
- Wetterwarnungen verwenden ausschließlich ihre Warnungs-ID/Reason-/Schutzanweisungs-Identität und ignorieren parallele Luftqualitätsänderungen.
- Rohwerte und mutable Beschreibungstexte bleiben weiterhin aus dem Fingerprint ausgeschlossen.

## v0.7.3

- Entfernt die experimentelle, integrationseigene 30-Tage/40-MiB-`RoomHistory`. Sie duplizierte Recorder-Daten, wurde von keiner Beratungsfunktion ausgewertet und konnte unnötig RAM/Storage belegen.
- Bestehende v0.7.2-`lueftungsberater.history.*`-Stores werden beim ersten lokalen Setup automatisch entfernt.
- Die bereits eingeführten Recorder-Optimierungen bleiben erhalten: große/dynamische Advisor-Attribute, Warntexte, CO₂-Rohwertattribute und Lüftungs-Debugattribute werden nicht unnötig historisiert.
- Neue gezielte Recorder-Aufbewahrung: Lüftungsassistent-Entities werden einmal täglich auf **maximal 20 Tage** State-Historie begrenzt. Andere Integrationen bleiben unberührt. Eine global kürzere Recorder-Aufbewahrung bleibt maßgeblich.
- Der Purge verwendet die exakten aktuell registrierten Entity-IDs der Lüftungsassistent-ConfigEntries; umbenannte Entities werden dadurch ebenfalls korrekt erfasst.
- Behebt den veralteten Config-Flow-Test, der `MINOR_VERSION == 7` verlangte, obwohl v0.7.2 korrekt Minor-Version 8 verwendet.
- Bereinigt den Release von den alten kaputten `reference`-YAML-Dateien.

## v0.7.2

### Benachrichtigungen
- Benachrichtigungen sind jetzt sauber in **Assistenten-Ereignisse** und **Raum-Ereignisse** getrennt. Amtliche Warnungen, Wetter-/Außenluftgefahren, optionale Warnungen bei bereits geschlossenen Fenstern und Entwarnungen werden einmal pro Assistent verarbeitet.
- **„Lüften jetzt sinnvoll“** und **„Lüftung beendet“** werden pro Raum konfiguriert. Beim Upgrade werden diese Raum-Meldungen bewusst nicht automatisch für alle Räume aktiviert.
- Warn-Fingerprints verwenden stabile Warnungs-IDs und semantische Zustände statt veränderlicher Beschreibungstexte oder Rohmesswerte. Änderungen wie AQ 160 → 161 oder redaktionelle Textänderungen derselben Warnung erzwingen dadurch keine neue Nachricht.
- Eine neue Warnungs-ID bzw. eine echte neue Warnlage kann weiterhin neu benachrichtigen. Werden während derselben Gefahr alle Fenster geschlossen und später erneut geöffnet, darf erneut gewarnt werden.

### Verlauf / Recorder
- Neue, integrationseigene **rollierende Raumhistorie**: maximal **30 Tage und 40 MiB pro Raum**. Neue Daten werden immer angenommen; bei Überschreitung werden ausschließlich die ältesten entbehrlichen Verlaufssamples bis ca. 38 MiB zurückgeschnitten.
- Konfiguration, aktuelle Zustände, Hysterese-/Warnspeicher, letzte bestätigte Lüftung und andere betriebsnotwendige Daten liegen außerhalb dieses Budgets und werden niemals durch das 40-MiB-Limit gelöscht.
- Die Verlaufssamples sind sprachneutral und speichern Mess-/Statusdaten statt gerenderter Texte oder Entity-Quellnamen.
- Zusätzliche HA-Recorder-Entlastung: häufig wechselnde Hilfsattribute werden als `unrecorded` markiert; der Stunden-seit-Lüftung-Sensor wird nur noch mit der ohnehin dargestellten Zehntelstunden-Auflösung aufgezeichnet.
- Die Hauptkarte zeigt Diagnosewerte für Größe, Limit, Sample-Anzahl und ältesten Verlaufspunkt der eigenen Raumhistorie.

### Räume / Remote
- Remote-Entries bleiben backendseitig strikt read-only; ein direkter Subentry-Flow gegen einen Remote-Hub wird weiterhin abgewiesen.
- **Bekannte Home-Assistant-Frontend-Einschränkung:** Der globale HA-Dialog „Raum hinzufügen“ listet derzeit alle ConfigEntries derselben Integration und filtert den einzelnen Parent nicht nach seinen `supported_subentry_types`. Dadurch kann ein Remote-/Tailscale-Eintrag dort weiterhin sichtbar sein, obwohl Home Assistant/Core und Lüftungsassistent das tatsächliche Hinzufügen anschließend ablehnen. Das lässt sich nicht sauber aus einer HACS-Custom-Integration heraus aus dem nativen Picker entfernen.

### Tests / Release
- Regressionstests für stabile Warn-Fingerprints, getrennte Assistent-/Raum-Benachrichtigungsoptionen und den kompakten Historien-Snapshot ergänzt.

## v0.7.1

### Bugfixes
- Doppelte Einträge für **amtliche Schutzwarnung bei geschlossenen Fenstern** und **Entwarnung** aus der Benachrichtigungsauswahl entfernt.
- Warn- und Entwarnungsbenachrichtigungen werden jetzt **einmal pro Lüftungsassistent** statt einmal pro Raum geführt. Normale Lüftungsstatus-Meldungen bleiben weiterhin raumbezogen.
- Die Nachtlüftung verwendet jetzt an allen Stellen die konfigurierte Endzeit. Der gemeinsame Außen-/Forecast-Pfad berücksichtigt nicht mehr fest 07:00 Uhr.
- Jeder Raum erhält zusätzlich einen Timer auf das Ende seines Nachtfensters, damit der Nachthinweis exakt zur eingestellten Bis-Zeit verschwindet.
- `display_mode` wird wieder im Remote-Snapshot übertragen, damit entfernte Karten dieselbe Ampelinterpretation wie die Quellinstanz verwenden.
- Bestehende Remote-/Tailscale-Einträge werden beim Update erneut mit **keinen unterstützten Raum-Subentries** veröffentlicht. Die Config-Flow-Minor-Version wurde dafür korrekt auf 7 angehoben, damit die Migration von v0.7.0 tatsächlich ausgeführt wird.
- CI bereinigt keine versehentlichen Root-Dateien mehr vor Hassfest/Pytest. Ein falsches Repository-Layout schlägt dadurch künftig sichtbar fehl statt im Workflow verdeckt zu werden.

### Karten / Remote
- Beim weißen Safety-Lock wird in der detaillierten Raumkarte nur noch der farbige Statuskopf weiß dargestellt; der restliche Kartenkörper behält das Home-Assistant-Theme.
- Lokal remote abgefragte Räume zeigen in der detaillierten Raumkarte ein kleines `lan-connect`-Symbol. Die Übersicht behält zusätzlich den Hinweis auf Assistenten-Ebene und das Badge am betroffenen Raum.
- `remote_access_*`-Attribute werden nur noch gesetzt, solange tatsächlich eine Remote-Instanz den Raum aktiv abfragt; `remote_shared` bleibt davon getrennt und bedeutet lediglich, dass der Raum freigegeben ist.

### Zustandsattribute / Sprache
- Das vollständige `localized_texts`-Paket mit Deutsch, Englisch und Türkisch wird nicht mehr in jeder Raum-Entity mitgeführt.
- Die Karte lässt Empfehlung, Grund, Dauer und Nachttext bei Bedarf über einen kleinen WebSocket-Befehl in der Sprache des aktuell angemeldeten Home-Assistant-Benutzers rendern und cached das Ergebnis. Nicht unterstützte Sprachen fallen weiterhin auf Englisch zurück.
- Die bisherigen aktuell gerenderten Texte bleiben als sofortiger Fallback erhalten; die sichtbare Kartenfunktion geht dadurch nicht verloren.
- Seltene Warn-/Remote-Metadaten werden nur noch als Attribute ergänzt, wenn sie tatsächlich aktiv bzw. vorhanden sind.

### Tests
- Regressionstests für doppelte Benachrichtigungsoptionen, Nacht-Endzeit, Remote-`display_mode`, v0.7.1-Migrationsversion und raumunabhängige Warn-Fingerprints ergänzt.

## v0.7.0

### Lüftungsassistent / Fresh Air Assistant
- Sichtbarer deutscher Produktname von **Lüftungsberater** auf **Lüftungsassistent** umgestellt. Die technische Domain `lueftungsberater` und bestehende Entity-/Config-IDs bleiben unverändert.
- Englische und internationale Oberfläche verwendet **Fresh Air Assistant**; nicht unterstützte UI-Sprachen fallen weiterhin auf Englisch zurück.

### Amtliche Warnungen und Entwarnungen
- Allgemeine Warnintegrationen werden jetzt **handlungsorientiert** ausgewertet. Der Assistent entscheidet nicht mehr selbst anhand von Ereignisname oder `severity`, wie gefährlich eine Meldung ist.
- Gibt die Behörde ausdrücklich vor, Fenster/Türen geschlossen zu halten, Lüftung/Klima abzuschalten oder Außenluftzufuhr zu vermeiden, wird diese Schutzmaßnahme unmittelbar als harter Safety-Lock übernommen.
- Warnungen ohne lüftungsrelevante Schutzanweisung beeinflussen diesen allgemeinen Warnpfad nicht. DWD behält seine eigenständige Wetterwarnungslogik; eine explizite DWD-Schließanweisung hat unabhängig von der Warnstufe Vorrang.
- Entwarnungen werden als eigener Kontext erkannt. Formulierungen wie **„noch keine Entwarnung“** oder **„Entwarnung liegt nicht vor“** lösen keine Entwarnung aus.
- Eine echte Entwarnung hebt nur die amtliche harte Sperre auf und setzt keine eigene Ampelfarbe. Solange der Warneintrag noch vorhanden ist, bleibt die Entwarnung als Hinweis sichtbar; danach übernimmt wieder vollständig die normale Engine.
- Benachrichtigungen bleiben standardmäßig handlungsbezogen: Gefahr bei offenem Fenster bzw. Öffnen während einer Gefahr. Optional können zusätzlich amtliche Schutzwarnungen bei bereits geschlossenen Fenstern und Entwarnungen aktiviert werden; der Text weist dann ausdrücklich auf den geschlossenen Fensterzustand hin.

### Nachtlüftung
- Nacht-Hinweise besitzen jetzt ein frei konfigurierbares **Von–Bis-Zeitfenster** pro Raum. Standard bleibt **22:00–07:00**.
- Zeitfenster über Mitternacht und ungewöhnliche Schichtzeiten werden unterstützt. Nach Ablauf übernimmt ohne Zwangsaktion wieder die normale Tagesbewertung.
- Bestehende Räume werden migrationssicher mit der bisherigen Endzeit 07:00 ergänzt.

### Stabilere Raumstatus-Hysterese
- Temperaturbedingte Gelb/Grün-Wechsel erhalten eine echte Hysterese: ein Temperaturbedarf beginnt weiterhin erst bei ungefähr 1,0 K Sollabweichung und endet erst unter ungefähr 0,6 K.
- Der Hysteresezustand merkt sich jetzt den **eigentlichen Raumbedarf** getrennt vom Lüftungsmodus. Dadurch bleibt er auch stabil, wenn gleichzeitig z. B. feuchtere Außenluft gegen das Lüften spricht.
- CO₂-, Feuchte- und Oberflächen-Hysteresen bleiben erhalten.

### Tailscale / Remote
- Remote-/Tailscale-Einträge werden backendseitig konsequent read-only gehalten und direkte Raum-Subentry-Flows gegen Remote-Hubs abgewiesen. Der globale Home-Assistant-Parent-Picker kann Remote-Einträge aufgrund seiner eigenen Frontend-Filterlogik trotzdem anzeigen.
- Die Quellinstallation kann jetzt pro Raum festlegen, ob dieser für Remote-Abfragen freigegeben ist. Bestehende v0.6-Räume bleiben beim Upgrade freigegeben, neue v0.7-Räume sind standardmäßig nicht automatisch freigegeben.
- Beim Einrichten oder Rekonfigurieren einer Remote-Verbindung werden nur freigegebene Räume angeboten. Die empfangende Instanz wählt ausdrücklich aus, welche Assistenten/Räume angezeigt werden sollen.
- Später neu angelegte Räume werden **nicht automatisch** übernommen; sie erscheinen lediglich als neue Auswahl.
- Remote-Snapshot-Protokoll auf **v2** erweitert. Protokoll-v1-Gegenstellen bleiben für Rolling Upgrades lesbar; die lokale Auswahl wird auch bei alten Gegenstellen angewendet.
- Remote-Abfragen senden eine stabile Client-Kennung und den Home-Assistant-Standortnamen. Die Quellübersicht kann dadurch anzeigen, wenn mindestens ein Raum aktuell von einer anderen Instanz abgefragt wird; betroffene Räume erhalten ein kleines Remote-Symbol.
- Remote-Messwerte bleiben weiterhin vollständig flüchtig: keine gespiegelten Home-Assistant-Entities und keine Recorder-Historien auf der empfangenden Instanz.

### Datenmodell und Performance
- Der bestehende Kartenumfang bleibt erhalten; v0.7.0 entfernt keine für die aktuelle Darstellung benötigten Attribute.
- Der große Advisor-Attributsatz bleibt über `_unrecorded_attributes = MATCH_ALL` vom Recorder ausgeschlossen. Dadurch werden die sichtbaren Diagnose-/Kartendaten nicht bei jeder Aktualisierung als eigener Attributverlauf gespeichert.
- Remote-Exporte bleiben auf eine explizite Allowlist der tatsächlich für die Karte benötigten aktuellen Werte begrenzt; lokale Entity-IDs und vollständige Originalwarnpayloads werden nicht gespiegelt.
- Mehrsprachige Kartentexte bleiben in v0.7.0 bewusst kompatibel erhalten, damit lokale und Remote-Karten weiterhin dieselben Inhalte in Deutsch, Englisch und Türkisch anzeigen können.

### Tests / Migration
- Config-Entry-Minor-Version auf 6 angehoben und Migrationen für Nacht-Endzeit, Remote-Freigaben und Remote-Client-ID ergänzt.
- Neue Regressionstests für amtliche Schließanweisungen, negierte Entwarnungen, DWD-Schutzanweisungen, Nacht-Endzeiten/Schichtfenster und Temperatur-Hysterese ergänzt.

## 0.6.24 - Alpha

- **Raumluftstatus ist jetzt die Standarddarstellung** für neue lokale Lüftungsberater: Grün = unauffällig, Gelb = leichte Abweichung, Orange = Lüften sinnvoll, Rot = deutlicher Lüftungsbedarf. Die bisherige Lüftungsampel bleibt vollständig auswählbar. Bestehende Installationen behalten ihre bereits gewählte Darstellung.
- Der separate **🔒-Sperrzustand** wurde optisch deutlich hervorgehoben: heller/weißer Kartenbereich mit dunklem Schloss und klarer Kontur statt eines unauffälligen grauen Zustands. Er bleibt außerhalb beider Ampelskalen.
- **Nachtlüftung** wird in der Raumkarte direkt unter „Warum?“ als eigener, breiter Hinweis angezeigt. Die pro Raum einstellbare Startzeit verwendet einen echten Uhrzeit-Selector und bleibt klar von Temperaturwerten getrennt.
- Die Einstellungsdialoge sind übersichtlicher gruppiert: Grundlage/Darstellung, eigene Außensensoren und Benachrichtigungen sowie pro Raum Raumklima, Nachtlüftung, Zusatzsensoren und Fenster/Türen stehen in klar getrennten Abschnitten.
- NINA an die aktuelle Home-Assistant-Schnittstelle angepasst: aktive Warnungen können über `nina.get_details` um Beschreibung und offizielle Handlungsempfehlungen ergänzt werden. Details werden pro Warnungs-ID gecacht und nicht bei jedem Sensorupdate erneut abgefragt.
- Remote-/Tailscale-Einträge werden beim Setup/Migration zusätzlich direkt in Home Assistants gecachtem `supported_subentry_types`-Status als read-only markiert, damit sie nicht als Ziel für „Raum hinzufügen“ angeboten werden. Der eigentliche Remote-Datenweg bleibt unverändert flüchtig und entity-frei.
- Laufende Lüftungen und die letzte bestätigte Lüftung sind robuster **neustartsicher**. `unknown`/`unavailable`-Fensterkontakte direkt nach einem Neustart löschen eine laufende Session nicht mehr.
- Der aktuelle Hysterese-/Entscheidungsmodus wird kompakt und zeitlich begrenzt gespeichert, damit ein normaler Home-Assistant-Neustart eine laufende Beratung nicht unnötig bei null beginnen lässt.
- Oberflächen-/Schimmelkontext bleibt optional und wird kompakt bis etwa sieben Tage gehalten. Eine starre „12 von 24 Stunden“-Schwelle wurde durch eine weichere Bewertung aus langer aktueller Belastung bzw. wiederholten auffälligen Tagen ersetzt.
- Lokaler Außenluft-Kontext wurde von einer wachsenden Rohpunkthistorie auf eine **feste, größenbegrenzte Statistik** umgestellt. Bestehende v0.6.23-Historie wird beim ersten Laden in die kompakte Struktur überführt. Standort-Buckets und Kurzzeitpunkte besitzen feste Obergrenzen.
- Keine zusätzliche Langzeitdatenbank für Raumtemperatur, Raumfeuchte oder CO₂: Home Assistants vorhandene Sensorhistorie wird nicht dupliziert.
- Performance: Der 1-Minuten-Takt des Lüftungstrackers läuft nur noch bei tatsächlich geöffnetem Fenster. Bei geschlossenem Fenster wird der 24-Stunden-Fallback exakt terminiert.
- Performance: Wetter, Warnungen, NINA und Außenluft werden einmal pro Lüftungsberater aufbereitet und von allen Räumen gemeinsam genutzt, statt pro Raum dieselben Providerdaten erneut zu zerlegen.
- Performance: Stunden-Forecasts werden gemeinsam gecacht und nur während eines relevanten Nachtfensters regelmäßig nachgeladen.
- Performance: Lokale Karten rendern nur noch bei für den Lüftungsberater relevanten Entity-Änderungen neu. Remote-Frontend-Polling wurde an den 30-Sekunden-Backend-Takt angepasst.
- Performance: Große dynamische Attribute des Hauptsensors bleiben für die Karte verfügbar, werden aber vom Recorder ausgeschlossen; der eigentliche Empfehlungszustand bleibt historisierbar.
- Performance: Remote-Geräte-Registry wird nur noch bei einer echten Änderung der Remote-Raumtopologie synchronisiert und nicht bei jedem neuen Messwert. Wiederholt benötigte abgeleitete Entity-IDs werden gecacht.
- Sichtbare Texte und Einstellungsbeschreibungen in Deutsch, Englisch und Türkisch weiter auf kurze, natürliche Formulierungen ausgerichtet.

## 0.6.23 - Alpha

- Hauptberatung weiter auf die vierstufige Gesamtabwägung abgestimmt. Die vereinbarten Grenzfälle für CO₂, Temperatur, Feuchte, Regen und Wind sind als Regressionstests festgehalten; starke Innenraumgründe können moderate Außennachteile überwiegen, ohne echte Schutzlagen zu ignorieren.
- Neuer **Sperrzustand** außerhalb der normalen Ampel: konkrete Fenster-schließen-Warnungen und schwere Wettergefahren werden in der Karte mit Schloss dargestellt. Dadurch behält jede normale Ampelfarbe ihre Bedeutung und wird nie für zwei gegensätzliche Handlungen verwendet.
- Neue wählbare **Ampeldarstellung**: Standard bleibt die Lüftungsampel (Grün = Lüften sinnvoll). Alternativ zeigt der Raumluftstatus die Dringlichkeit im Raum (Grün = alles gut, Rot = Lüften dringend sinnvoll). Der Sperrzustand übersteuert beide Darstellungen eindeutig.
- Temperaturbewertung weiter verbessert: Richtung zum persönlichen Sollwert, Stärke der Temperaturwirkung und andere Raum-/Außenwerte werden gemeinsam betrachtet. Große Temperaturunterschiede wirken stärker, lösen aber nicht allein pauschal eine Farbe aus.
- Plausibilitätsfilter absichtlich großzügig gehalten: extreme, aber mögliche Raumwerte bleiben gültig. Offensichtlich unbrauchbare Daten werden ignoriert statt durch erfundene Werte ersetzt. Unplausible Climate-Sollwerte fallen auf den gespeicherten Lüftungsberater-Sollwert zurück.
- CO₂-Lüftungen besitzen eine klarere Rücklaufhysterese: während einer sinnvollen Lüftung bleibt die Empfehlung stabil, geht nahe am Ziel in Gelb über und bewertet erst nach dem Schließen wieder die verbleibenden Außennachteile.
- Optionaler **Außen-CO₂-Sensor** ergänzt. Ein plausibler lokaler Wert zeigt, wie groß das tatsächliche CO₂-Senkungspotenzial durchs Lüften ist; er wird nicht mit regionalen Daten gemittelt und macht hohe Innenwerte niemals künstlich gut.
- Außenluftqualität erhält lokalen Kontext und Trend: Der UBA-LQI bleibt die absolute gesundheitliche Klasse. Zusätzlich merkt sich Lüftungsberater pro Standort einen rollierenden typischen Bereich und erkennt ungewöhnliche bzw. steigende Belastungen, ohne dauerhaft schlechte Luft gesundzurechnen.
- Standortbezogene Luftqualitäts-Historie verhindert, dass ein gelernter Normalbereich blind auf einen deutlich anderen Standort übertragen wird. Ohne brauchbare Standortinformation bleibt nur die absolute Bewertung.
- Nachtlüftung überarbeitet: Die Startzeit der Anzeige ist pro Raum einstellbar (Standard 22 Uhr), aber keine feste Startanweisung. Lüftungsberater sucht in der Stundenprognose nach einem passenden Zeitfenster und kann z. B. „Später lüften – ab etwa 01:00 Uhr wird es draußen deutlich kühler“ anzeigen. Wenn nachts nichts Sinnvolles zu melden ist, bleibt die Zusatzzeile verborgen.
- Nachtbewertung nutzt nur tatsächlich vorhandene Forecastfelder und berücksichtigt soweit verfügbar Temperatur, Feuchte, Regen, Wind, Warnungen und Außenluftqualität. Die aktuelle Hauptampel bleibt davon getrennt.
- Remote-/Tailscale-Einträge werden robuster als read-only erkannt, einschließlich älterer Einträge ohne explizites `entry_kind`. Der gecachte Home-Assistant-Subentry-Status wird beim Setup aktualisiert, damit Remote-Verbindungen nicht mehr als Ziel beim Anlegen lokaler Räume angeboten werden.
- Remote-Messwerte bleiben unverändert flüchtige Snapshots: keine gespiegelten Entities, keine Recorder-Historie und keine dauerhafte Messwertkopie auf dem empfangenden Home Assistant.
- Sichtbare Texte in Karte, Konfiguration und Nachtberatung weiter auf kurze, natürliche Formulierungen umgestellt. Deutsch, Englisch und Türkisch wurden gemeinsam aktualisiert.

## 0.6.22 - Alpha

- Vierstufige Ampel eingeführt: Grün = klar sinnvoll, Gelb = optional/nahe Abwägung, Orange = eher nachteilig bzw. besser geschlossen lassen, Rot = deutlicher Schutz-/Gefahrengrund zum Geschlossenhalten.
- Bisherige harmlose Rot-Fälle wie ungünstige Feuchte, unnötiges Auskühlen, mäßige/schlechte Außenluftqualität oder starker Wind werden soweit passend nach Orange getrennt; echte Außenluftgefahren, sehr schlechte Luftqualität und schwere Wetterlagen bleiben Rot.
- Rohwindwerte neu zur Vierfarbenlogik passend abgestuft: ungefähr 50 km/h anhaltender Wind bzw. 65 km/h Böen sind ein klarer Orange-Nachteil; erst deutlich extremere Rohwerte (ca. 75 km/h Dauerwind bzw. 105 km/h Böen) werden ohne zusätzliche Warnquelle als harter Rot-Fall behandelt.
- Remote-/Tailscale-Lüftungsberater werden nicht mehr als Ziel beim Hinzufügen eines lokalen Raums angeboten. Legacy-Remoteeinträge mit Remote-Host werden ebenfalls erkannt; Remote-Topologie bleibt read-only.
- Neue kompakte Nachtlüftungs-Zusatzempfehlung am späten Abend. Wenn der gewählte Weather-Provider einen stündlichen Forecast unterstützt, werden persönliche Solltemperatur sowie vorhandene Temperatur-, Feuchte-, Regen- und Windprognosen für die kommende Nacht ausgewertet.
- Nachtlüftung bleibt bewusst eine Zusatzinformation und ändert die aktuelle Hauptampel nicht. Fehlende Forecastdaten werden ignoriert statt geschätzt; Provider ohne Stundenforecast zeigen keine Nachtzeile.
- Stündliche Forecasts werden über Home Assistants `weather.get_forecasts` bezogen und pro Lüftungsberater gecacht, damit mehrere Räume denselben Wetterdienst nicht unnötig mehrfach abfragen.
- Deutsch, Englisch und Türkisch sowie Frontend- und Remote-Snapshot-Texte für die neuen Zustände aktualisiert.

## 0.6.21 - Alpha

- Hotfix: Temperaturberatung bewertet kalte bzw. warme Außenluft jetzt nach der **Richtung der Temperaturänderung zum persönlichen Sollwert**. Außenluft muss nicht selbst näher am Sollwert liegen, um einen zu warmen/zu kalten Raum sinnvoll in Richtung Soll zu bewegen.
- Temperatur-Hysterese korrigiert: Eine bereits laufende temperaturbedingte Lüftung bleibt bis auf etwa 0,2 K am Sollwert aktiv, statt beim Annähern plötzlich wegen der weiter entfernten Außentemperatur auf Rot zu springen.
- Tailscale-Geräteansicht korrigiert: Die unnötigen Zwischenkarten für Remote-HA und Remote-Lüftungsberater bleiben entfernt, **Remote-Raumkarten werden wieder angezeigt**. Sie enthalten weiterhin ausschließlich Topologie-Metadaten – Remote-Messwerte bleiben flüchtig, ohne lokale Entities, Recorder-Historie oder Spiegelung.

## 0.6.20 - Alpha

### Kontextabhängige Gesamtbewertung statt starrer Einzelgrenzen

- Entscheidungsengine neu geordnet: Sicherheit/Gesundheit, Innenraumluft, Feuchte-/Oberflächenrisiko, persönliches Temperatursoll, Komfort und Außenbedingungen werden gemeinsam bewertet statt einfach den schlechtesten Einzelwert gewinnen zu lassen.
- Ampelbedeutung geschärft: Grün = klarer Gesamtvorteil, Gelb = optional/nahe Abwägung, Rot = unnötig oder Nachteile überwiegen.
- Absolute Feuchte: harte 1,0-g/m³-Startschwelle entfernt. ±0,5 g/m³ dient nur als technische Neutralzone gegen Messrauschen; laufende Feuchtelüftung besitzt eine kleine Rücklaufhysterese.
- CO₂-Stufen 1000/1400/2000 ppm bleiben erhalten, werden aber kontextabhängig gegen Feuchte, Temperatur, Luftqualität, Wetter und echte Außenluftgefahren abgewogen. Hohes CO₂ kann kleine Nachteile akzeptieren, harte Sicherheitslagen bleiben vorrangig.
- Persönliche Solltemperatur stärker als Komfortreferenz genutzt. Hohe Raumtemperaturen werden zusätzlich separat als Hitzebelastung bewertet, ohne 26 °C pauschal als ungesund zu bezeichnen.
- Optionale Oberflächenfeuchte erweitert: Nur mit realem Oberflächentemperatursensor wird Oberflächen-rF berechnet. Lokaler zeitlicher Kontext unterscheidet kurze Peaks von länger anhaltender kritischer Feuchte; ohne Sensor werden keine Werte geschätzt. Die Anzeige bleibt bewusst beratend und nicht diagnostisch.
- Regenlogik entkoppelt von der Feuchtephysik. Radar-Niederschlag beeinflusst eine Empfehlung nur noch, wenn er die erwartete Lüftungsdauer plus kleine Reserve tatsächlich überlappt; die alte pauschale 2-Stunden-Wirkung entfällt.
- Wind differenzierter bewertet: ungefähr ab Bft 6 Vorsicht; etwa 50 km/h anhaltender Wind bzw. 65 km/h Böen können als realer Nachteil eines offenen Fensters Rot auslösen, ohne dies als amtliche DWD-Rotwarnung darzustellen.
- NINA/CAP- und DWD-Auswertung stärker an konkreten Handlungsempfehlungen ausgerichtet. „Keine Gefahr“ ohne Schutzanweisung blockiert nicht mehr nur wegen Rauch-/Brand-Schlüsselwörtern; explizites Fenster-schließen bzw. schwere Warnlage bleibt vorrangig.
- Außenluftqualität ergänzt: plausible aktuelle Ozon-, PM2.5-, PM10-, NO₂- und SO₂-Sensoren aus dem Wetter-Config-Entry werden nach UBA-LQI-Klassen bewertet; der schlechteste verfügbare gültige Schadstoff zählt. Fehlende, veraltete und unplausible Daten werden ignoriert.
- Lüftungsdauer überarbeitet: warme Außenbedingungen werden nicht mehr pauschal mit nur 5–10 Minuten als ausreichend dargestellt; empfohlene Normalzeiten beginnen bei mindestens 5 Minuten und bleiben mit der Lüftungsbestätigung konsistent.
- 24-Stunden-Routinelüftung bewusst unverändert als letzter Fallback beibehalten.
- Benachrichtigungen vereinheitlicht: nur noch moderne `notify`-Entity via `notify.send_message`. Companion-spezifischer `notify.mobile_app_*`-Pfad, Vibrationsstufen, Critical-Payloads, Channels und Tags entfernt. Alte Optionsschlüssel werden bei der Migration sicher verworfen; ein vorhandenes normales Notify-Ziel bleibt erhalten.
- Tailscale-Remote bleibt vollständig flüchtig: weiterhin keine Remote-Entities, kein lokaler Recorder-Verlauf und keine gespiegelten Messsensoren. Die früher erzeugte leere Remote-Gerätehierarchie wird entfernt/aufgeräumt, sodass keine doppelten „Wohnmobil/Lüftungsberater/Raum“-Gerätekarten mehr entstehen.
- UI-Texte bewusst kurz gehalten; komplexere Abwägungen passieren im Hintergrund und werden mit wenigen relevanten Gründen erklärt.
- Deutsch, Englisch und Türkisch vollständig an neue Zustände und Texte angepasst.

## 0.6.19 - Alpha

### Konfigurierbare Handy-Benachrichtigungen

- Benachrichtigungsauswahl erweitert: Zusätzlich zu Außenluft- und Wetterwarnungen können optional **„Lüften ist wieder sinnvoll“** und **„Lüften kann beendet werden“** aktiviert werden.
- Die beiden Lüftungsstatus-Hinweise sind echte Zustandswechsel-Benachrichtigungen: kein erneutes Senden bei jedem Sensorupdate und kein unnötiger Hinweis direkt nach einem Home-Assistant-Neustart.
- Optionales Companion-App-Ziel (`notify.mobile_app_*`) ergänzt. Ist es ausgewählt, wird es anstelle des normalen `notify`-Ziels verwendet und ermöglicht erweiterte Handy-Payloads ohne doppelte Zustellung.
- Lüftungsstatus-Hinweise werden über die Companion App bewusst still zugestellt: Android nutzt einen Low-Importance-Kanal ohne erzwungene Vibration, iOS eine passive Benachrichtigung ohne Ton.
- Android-Vibration für **Vorsicht** und **Gefahr** getrennt konfigurierbar: Aus, Leicht, Mittel oder Stark. Die Stufen verwenden unterschiedliche Vibrationsmuster; die tatsächliche Motoramplitude bleibt geräteabhängig.
- Android verwendet getrennte Notification Channels je Warnstufe/Vibrationsprofil, weil Importance und Vibrationsmuster ab Android 8 nach der ersten Kanalerstellung vom System gespeichert werden.
- Gefahren werden über die Companion App mit hoher Zustellpriorität (`priority: high`, `ttl: 0`) verschickt.
- Kritische Zustellung ist ein eigener, standardmäßig deaktivierter Opt-in: iOS nutzt einen echten Critical Alert; Android verwendet dafür einen Kanal mit maximaler Importance. Ein DND-Bypass auf Android muss, sofern gewünscht, weiterhin in den Systemeinstellungen des Kanals erlaubt werden.
- Companion-App-Meldungen verwenden stabile Tags pro Raum. Veraltete Lüftungsstatus- und Warnmeldungen werden bei Zustandsende bestmöglich wieder entfernt bzw. durch die aktuelle Meldung ersetzt.
- Bestehende Installationen bleiben kompatibel: Ohne Companion-App-Ziel arbeitet das bisherige generische `notify.send_message` weiter wie zuvor.
- Keine Änderung an Entscheidungslogik, Hysterese-Schwellen, Warnbewertung, Schimmelschutz, Karten oder Remote-Protokoll.

## 0.6.18 - Alpha

### Pytest-/CI-Hotfix für die CO₂-Hysterese

- Regressionstest für die CO₂-Hysterese bei offenem Fenster korrigiert. Der bisherige Test aktivierte mit den Standardwerten `23 °C` innen, `22 °C` Soll und `15 °C` außen gleichzeitig die Kühl-Hysterese und erwartete deshalb fälschlich ein Ende des Lüftens bei `940 ppm`.
- Der Test neutralisiert den Temperatureinfluss jetzt mit `target_temp=23`, sodass ausschließlich die CO₂-Hysterese geprüft wird: Bei `980 ppm` bleibt eine laufende Lüftung aktiv, bei `940 ppm` wird sie beendet.
- Die Abschlussprüfung erwartet nun explizit `lueftung_fertig` statt nur „nicht `weiter_lueften`“ und schützt damit genauer vor zukünftigen Regressionen.
- Keine Änderung an Lüftungslogik, Hysterese-Schwellen, Warnungen, Benachrichtigungen, Karten oder Sensorberechnungen.

## 0.6.17 - Alpha

### Letzter Funktions-/Polish-Schritt vor der öffentlichen HACS-Einreichung

- Raumkarte vereinheitlicht: Nur der farbige Status-/Kopfbereich öffnet bei lokalen Räumen die Hauptentity. Begründung und empfohlene Lüftungsdauer sind reine Texte; echte Mess- und Statuswerte bleiben gezielt anklickbar. Remote-Raumkarten bleiben read-only.
- Sensor-Auswahl im Config Flow eingeschränkt: Temperaturfelder zeigen nur Temperatursensoren, Feuchtefelder nur Luftfeuchtesensoren, CO₂ nur CO₂-Sensoren und Fenster-/Türfelder nur passende binäre Öffnungs-/Tür-/Fensterklassen.
- Hysterese für normale Grenzbereiche ergänzt, damit Empfehlungen bei Sensorwerten direkt an Schwellen nicht unnötig zwischen Zuständen springen. Kritisches CO₂ und echte Warnlagen bleiben sofort wirksam.
- Optionaler Schimmelschutz ergänzt: Wird eine Temperatur-Entity für eine kalte/kritische Oberfläche angegeben, berechnet Lüftungsberater daraus zusammen mit Raumtemperatur und Raumfeuchte die relative Feuchte an dieser Oberfläche. Ab 80 % Oberflächenfeuchte wird das Risiko still in der Empfehlung berücksichtigt; ein eigener Schimmel-Helfer ist nicht nötig. Ohne Oberflächensensor bleibt die bisherige Feuchtelogik unverändert aktiv.
- Optionale Warn-Benachrichtigungen ergänzt. Ein `notify`-Ziel kann direkt beim lokalen Lüftungsberater gewählt werden. Standardmäßig wird nur bei ernster Außenluftgefahr oder schwerer Wettergefahr benachrichtigt, wenn tatsächlich ein konfiguriertes Fenster/eine Tür offen ist. Vorsichtshinweise können optional zusätzlich aktiviert werden.
- Benachrichtigungen sind ereignisbezogen statt farbbezogen: Ein roter Zustand wegen ungünstiger Temperatur löst ausdrücklich keine Gefahrenmeldung aus. Pro Warnereignis/Fenster-Öffnungszyklus wird höchstens einmal benachrichtigt.
- Keine zusätzliche redundante „Lüften empfohlen“-Binary-Entity: Der vorhandene Hauptsensor bleibt die zentrale Automation-Schnittstelle.
- Generische `weather.get_forecasts`-Niederschlagsprognosen werden in diesem Release bewusst noch nicht zusätzlich abgefragt; vorhandenes Wetter-/Radar-Verhalten bleibt unverändert.

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
