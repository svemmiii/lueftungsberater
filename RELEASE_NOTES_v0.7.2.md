# v0.7.2 – Benachrichtigungen, Verlauf und Recorder

## Benachrichtigungen

Benachrichtigungen sind jetzt zweistufig konfiguriert. Globale Warnereignisse gehören zum Assistenten; normale Lüftungsübergänge werden pro Raum aktiviert. So erzeugen zwei Räume nicht automatisch zwei „jetzt lüften“-Meldungen, außer dies wurde für beide Räume bewusst eingeschaltet.

Der Warn-Fingerprint basiert auf stabilen Warnungs-IDs und semantischen Warnzuständen. Rohwertänderungen und redaktionelle Textänderungen derselben Warnung lösen keine neue Benachrichtigung mehr aus.

## 40-MiB-Raumhistorie

Jeder lokale Raum besitzt nun eine eigene, sprachneutrale Verlaufshistorie mit zwei Grenzen:

- maximal 30 Tage
- maximal 40 MiB pro Raum

Neue Samples werden immer gespeichert. Wird das Budget überschritten, werden nur die ältesten entbehrlichen Verlaufspunkte entfernt, bis wieder ungefähr 38 MiB erreicht sind. Kritische Betriebsdaten wie Konfiguration, Hysteresezustand, Warnstatus und aktuelle Zustände liegen außerhalb dieses Verlaufs und sind von der Bereinigung nicht betroffen.

Die Home-Assistant-Hilfsentities wurden zusätzlich recorderfreundlicher gemacht; laufend wechselnde Diagnoseattribute werden nicht unnötig historisiert.

## Remote / Raum hinzufügen

Remote-Einträge bleiben read-only. Der globale Home-Assistant-Dialog „Raum hinzufügen“ kann einen Remote-Eintrag trotzdem anzeigen, weil das aktuelle HA-Frontend die Parent-Liste nicht pro Entry nach `supported_subentry_types` filtert. Der Backend-Flow verweigert Remote-Räume zuverlässig; ein vollständiges visuelles Entfernen aus diesem nativen Picker ist integrationseitig derzeit nicht sauber möglich.
