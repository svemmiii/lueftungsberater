# Dashboard-Karten

[← Zur Übersicht](../README.md)

Nach der Installation und einem Neustart erscheinen die Karten im Home-Assistant-Kartenpicker. Du musst dafür keine zusätzlichen Fremd-Karten installieren.

## Lüftungsassistent – Raum

Die Raumkarte zeigt im normalen, kompakten Modus den Raumnamen, die Statusfarbe und die aktuelle Empfehlung. Über das Informationssymbol kannst du Gründe, die vorgeschlagene Dauer, Messwerte und weitere Hinweise ausklappen.

Deine Entscheidung für kompakte oder ausgeklappte Ansicht wird **pro Browser beziehungsweise Endgerät** gespeichert. Sie bleibt nach dem Neuladen oder einem Home-Assistant-Neustart erhalten.

Sicherheitsrelevante Informationen sollen dabei nicht verschwinden: **Aktive harte Fenstersperren** mit Sperrgrund und vorhandene Nachtlüftungshinweise bleiben auch im Kompaktmodus sichtbar. Eine reine Entwarnung erscheint nur in der Detailansicht.

Bei lokalen Räumen kannst du echte Messsensoren öffnen, um Home Assistants More-Info- und Verlaufsansicht zu sehen. Erklärungstexte selbst sind keine anklickbaren Messsensoren.

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
