# Dashboard-Karten

[← Zur Übersicht](../README.md)

Nach der Installation und einem Neustart erscheinen die Karten im Home-Assistant-Kartenpicker. Du musst dafür keine zusätzlichen Fremd-Karten installieren.

## Lüftungsassistent – Raum

Die Raumkarte zeigt im normalen, kompakten Modus den Raumnamen, die Statusfarbe und die aktuelle Empfehlung. Über das Informationssymbol kannst du Gründe, die vorgeschlagene Dauer, Messwerte und weitere Hinweise ausklappen.

Deine Entscheidung für kompakte oder ausgeklappte Ansicht wird **pro Browser beziehungsweise Endgerät** gespeichert. Sie bleibt nach dem Neuladen oder einem Home-Assistant-Neustart erhalten.

Sicherheitsrelevante Informationen sollen dabei nicht verschwinden: **Aktive harte Fenstersperren** mit Sperrgrund und vorhandene Nachtlüftungshinweise bleiben auch im Kompaktmodus sichtbar. Eine reine Entwarnung erscheint nur in der Detailansicht.

Bei lokalen Räumen kannst du echte Messsensoren öffnen, um Home Assistants More-Info- und Verlaufsansicht zu sehen. Erklärungstexte selbst sind keine anklickbaren Messsensoren.

### Hintergrunddeckkraft der Raumkarte

Im visuellen Karteneditor gibt es die Einstellung **Hintergrunddeckkraft**. Standardmäßig wird das Home-Assistant-Theme unverändert verwendet. Wählst du **Manuell**, kannst du den Kartenhintergrund von **0 %** (transparent) bis **100 %** (deckend) einstellen. Nur die jeweilige Raumkarte ist betroffen; Text, Icons und Ampelfarben behalten ihre eigene Deckkraft. Die Einstellung benötigt kein `card-mod`.

## Lüftungsassistent – Übersicht

Die Übersicht zeigt mehrere Räume nebeneinander beziehungsweise untereinander, ohne für jeden Raum dauerhaft eine umfangreiche Detailkarte zu laden. Ein Tipp auf einen Eintrag öffnet dessen vollständige Raumansicht in einem Dialog.

Mehrere lokale oder eingebundene Remote-Installationen können getrennt gruppiert werden. Im Karteneditor legst du fest, welche Instanzen und Räume sichtbar sind und in welcher Reihenfolge sie erscheinen.

## Zwei Ampelansichten

Die **Lüftungsbedarf-Ampel** bewertet, wie dringend frische Luft gebraucht wird. Die optionale **Lüftungsampel** bewertet stattdessen, wie günstig das Lüften unter den gegenwärtigen Bedingungen ist. Gleiche Farben können darum Unterschiedliches bedeuten; beide Darstellungen greifen auf dieselbe Entscheidung zurück.

Eine **harte Sperre** wird in beiden Ansichten zusätzlich und eindeutig mit einem Schloss gekennzeichnet.

## Messwerte und History

Viele abgeleitete Diagnosewerte erscheinen direkt in der Karte, auch wenn ihre eigenen Hilfs-Entities aus Gründen der Recorder-Datenhygiene deaktiviert sind. Sollen solche Entities als eigenständige Sensoren sichtbar sein, kannst du sie gegebenenfalls aktivieren; die Integration begrenzt ihren Recorder-Verlauf trotzdem.

Für eigene Diagramme gibt es außerdem die [Historienkarte](HISTORIE.md).

[← Zur Übersicht](../README.md)

## Zwei Ampelperspektiven ab v0.12.0

**Raumluft (`room_air`)** ist eine **Fenster-Handlungsampel**: Grün = schließen beziehungsweise geschlossen lassen; Gelb = Lüften möglich/Werte beobachten; Orange = Lüften empfohlen; Rot = dringend lüften. Eine Schließempfehlung kann auch bei weiterhin erhöhter Feuchte Grün anzeigen – das ist kein nachgewiesener Lüftungserfolg.

**Lüftungseignung (`ventilation`)** bewertet die Außenbedingungen: Grün = zum Lüften geeignet; Gelb = eingeschränkt; Orange = eher ungünstig; Rot = sehr ungünstig. **Nicht mit den Raum-Handlungsfarben vertauschen.** Der Modus wird bei Raumkarte, Gesamtübersicht, Remote-Räumen und Recorder-Einträgen berücksichtigt; die aufgezeichnete historische Farbe bleibt die aus der damals gewählten Ansicht.

Vorhandene Automationen können weiterhin `ventilation_status` (native Eignungsfarbe) und `ventilation_recommendation_key` (native Empfehlung) verwenden. Daneben geben `room_status` und `room_recommendation_key` die Raum-Handlung wieder. Der native Zustand des Hauptsensors ist unverändert. Nicht verfügbare Messwerte und ein ausgefallener optionaler Fensterkontakt erscheinen als gelbe Datenhinweise, **ohne** allein die aus anderen Sensoren gewonnene Raumampelfarbe zu ändern. Sicherheitsentscheidungen bleiben in beiden Modi gesperrt.
