"""Independent audit and counterpairs for complete warning constituents."""
from datetime import datetime, timedelta
import json
import operator

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


AUDIT_CASES = [
    ('Böen 70 km/h bei heftigem Gewitterregen.', False, {}),
    ('Böen 70 km/h bei extremer Schneeglätte.', False, {}),
    ('Böen 70 km/h bei teils gefrierenden Niederschlägen.', False, {}),
    ('Böen 70 km/h bei frühwinterlichem Frost.', False, {}),
    ('Böen 70 km/h bei kräftigem Nebel.', False, {}),
    ('Böen 70 km/h bei Unwetterlage.', False, {}),
    ('Böen 70 km/h bei klirrender Kälte.', False, {}),
    ('Böen 70 km/h bei eisigen Windbedingungen.', False, {}),
    ('Böen 70 km/h bei frostig kaltem Wetter.', False, {}),
    ('Böen 70 km/h bei hohen Temperaturen.', False, {}),
    ('Böen 70 km/h bei Schauerwetter.', False, {}),
    ('Böen 70 km/h bei einsetzenden Graupelschauern.', False, {}),
    ('Böen 70 km/h bei Schneeverwehungen.', False, {}),
    ('Böen 70 km/h bei starkem Tauwetter.', False, {}),
    ('Böen 70 km/h bei Starkfrost.', False, {}),
    ('Böen 70 km/h bei Föhnwetter.', False, {}),
    ('Böen 70 km/h bei aufgelockerter Bewölkung.', False, {}),
    ('Böen 70 km/h bei einer Gewitterfront.', False, {}),
    ('Böen 70 km/h bei teils sonnigen Abschnitten.', False, {}),
    ('Böen 70 km/h bei hoher Luftfeuchte.', False, {}),
    ('Böen 70 km/h bei sehr niedrigem Luftdruck.', False, {}),
    ('Böen 70 km/h bei stark fallendem Luftdruck.', False, {}),
    ('Böen 70 km/h bei einer heranziehenden Kaltfront.', False, {}),
    ('Böen 70 km/h bei einer Tiefdruckzone.', False, {}),
    ('Böen 70 km/h bei kräftigem Dauerregen.', False, {}),
    ('Böen 70 km/h bei Nachtfrost.', False, {}),
    ('Böen 70 km/h bei weiter sinkenden Temperaturen.', False, {}),
    ('Böen 89 km/h bei heftigem Gewitterregen.', False, {}),
    ('Böen 89 km/h bei extremer Schneeglätte.', False, {}),
    ('Böen 89 km/h bei teils gefrierenden Niederschlägen.', False, {}),
    ('Böen 89 km/h bei frühwinterlichem Frost.', False, {}),
    ('Böen 89 km/h bei kräftigem Nebel.', False, {}),
    ('Böen 89 km/h bei Unwetterlage.', False, {}),
    ('Böen 89 km/h bei klirrender Kälte.', False, {}),
    ('Böen 89 km/h bei eisigen Windbedingungen.', False, {}),
    ('Böen 89 km/h bei frostig kaltem Wetter.', False, {}),
    ('Böen 89 km/h bei hohen Temperaturen.', False, {}),
    ('Böen 89 km/h bei Schauerwetter.', False, {}),
    ('Böen 89 km/h bei einsetzenden Graupelschauern.', False, {}),
    ('Böen 89 km/h bei Schneeverwehungen.', False, {}),
    ('Böen 89 km/h bei starkem Tauwetter.', False, {}),
    ('Böen 89 km/h bei Starkfrost.', False, {}),
    ('Böen 89 km/h bei Föhnwetter.', False, {}),
    ('Böen 89 km/h bei aufgelockerter Bewölkung.', False, {}),
    ('Böen 89 km/h bei einer Gewitterfront.', False, {}),
    ('Böen 89 km/h bei teils sonnigen Abschnitten.', False, {}),
    ('Böen 89 km/h bei hoher Luftfeuchte.', False, {}),
    ('Böen 89 km/h bei sehr niedrigem Luftdruck.', False, {}),
    ('Böen 89 km/h bei stark fallendem Luftdruck.', False, {}),
    ('Böen 89 km/h bei einer heranziehenden Kaltfront.', False, {}),
    ('Böen 89 km/h bei einer Tiefdruckzone.', False, {}),
    ('Böen 89 km/h bei kräftigem Dauerregen.', False, {}),
    ('Böen 89 km/h bei Nachtfrost.', False, {}),
    ('Böen 89 km/h bei weiter sinkenden Temperaturen.', False, {}),
    ('Böen 90 km/h bei heftigem Gewitterregen.', True, {}),
    ('Böen 90 km/h bei extremer Schneeglätte.', True, {}),
    ('Böen 90 km/h bei teils gefrierenden Niederschlägen.', True, {}),
    ('Böen 90 km/h bei frühwinterlichem Frost.', True, {}),
    ('Böen 90 km/h bei kräftigem Nebel.', True, {}),
    ('Böen 90 km/h bei Unwetterlage.', True, {}),
    ('Böen 90 km/h bei klirrender Kälte.', True, {}),
    ('Böen 90 km/h bei eisigen Windbedingungen.', True, {}),
    ('Böen 90 km/h bei frostig kaltem Wetter.', True, {}),
    ('Böen 90 km/h bei hohen Temperaturen.', True, {}),
    ('Böen 90 km/h bei Schauerwetter.', True, {}),
    ('Böen 90 km/h bei einsetzenden Graupelschauern.', True, {}),
    ('Böen 90 km/h bei Schneeverwehungen.', True, {}),
    ('Böen 90 km/h bei starkem Tauwetter.', True, {}),
    ('Böen 90 km/h bei Starkfrost.', True, {}),
    ('Böen 90 km/h bei Föhnwetter.', True, {}),
    ('Böen 90 km/h bei aufgelockerter Bewölkung.', True, {}),
    ('Böen 90 km/h bei einer Gewitterfront.', True, {}),
    ('Böen 90 km/h bei teils sonnigen Abschnitten.', True, {}),
    ('Böen 90 km/h bei hoher Luftfeuchte.', True, {}),
    ('Böen 90 km/h bei sehr niedrigem Luftdruck.', True, {}),
    ('Böen 90 km/h bei stark fallendem Luftdruck.', True, {}),
    ('Böen 90 km/h bei einer heranziehenden Kaltfront.', True, {}),
    ('Böen 90 km/h bei einer Tiefdruckzone.', True, {}),
    ('Böen 90 km/h bei kräftigem Dauerregen.', True, {}),
    ('Böen 90 km/h bei Nachtfrost.', True, {}),
    ('Böen 90 km/h bei weiter sinkenden Temperaturen.', True, {}),
    ('Böen 110 km/h bei heftigem Gewitterregen.', True, {}),
    ('Böen 110 km/h bei extremer Schneeglätte.', True, {}),
    ('Böen 110 km/h bei teils gefrierenden Niederschlägen.', True, {}),
    ('Böen 110 km/h bei frühwinterlichem Frost.', True, {}),
    ('Böen 110 km/h bei kräftigem Nebel.', True, {}),
    ('Böen 110 km/h bei Unwetterlage.', True, {}),
    ('Böen 110 km/h bei klirrender Kälte.', True, {}),
    ('Böen 110 km/h bei eisigen Windbedingungen.', True, {}),
    ('Böen 110 km/h bei frostig kaltem Wetter.', True, {}),
    ('Böen 110 km/h bei hohen Temperaturen.', True, {}),
    ('Böen 110 km/h bei Schauerwetter.', True, {}),
    ('Böen 110 km/h bei einsetzenden Graupelschauern.', True, {}),
    ('Böen 110 km/h bei Schneeverwehungen.', True, {}),
    ('Böen 110 km/h bei starkem Tauwetter.', True, {}),
    ('Böen 110 km/h bei Starkfrost.', True, {}),
    ('Böen 110 km/h bei Föhnwetter.', True, {}),
    ('Böen 110 km/h bei aufgelockerter Bewölkung.', True, {}),
    ('Böen 110 km/h bei einer Gewitterfront.', True, {}),
    ('Böen 110 km/h bei teils sonnigen Abschnitten.', True, {}),
    ('Böen 110 km/h bei hoher Luftfeuchte.', True, {}),
    ('Böen 110 km/h bei sehr niedrigem Luftdruck.', True, {}),
    ('Böen 110 km/h bei stark fallendem Luftdruck.', True, {}),
    ('Böen 110 km/h bei einer heranziehenden Kaltfront.', True, {}),
    ('Böen 110 km/h bei einer Tiefdruckzone.', True, {}),
    ('Böen 110 km/h bei kräftigem Dauerregen.', True, {}),
    ('Böen 110 km/h bei Nachtfrost.', True, {}),
    ('Böen 110 km/h bei weiter sinkenden Temperaturen.', True, {}),
    ('Böen 145 km/h bei heftigem Gewitterregen.', True, {}),
    ('Böen 145 km/h bei extremer Schneeglätte.', True, {}),
    ('Böen 145 km/h bei teils gefrierenden Niederschlägen.', True, {}),
    ('Böen 145 km/h bei frühwinterlichem Frost.', True, {}),
    ('Böen 145 km/h bei kräftigem Nebel.', True, {}),
    ('Böen 145 km/h bei Unwetterlage.', True, {}),
    ('Böen 145 km/h bei klirrender Kälte.', True, {}),
    ('Böen 145 km/h bei eisigen Windbedingungen.', True, {}),
    ('Böen 145 km/h bei frostig kaltem Wetter.', True, {}),
    ('Böen 145 km/h bei hohen Temperaturen.', True, {}),
    ('Böen 145 km/h bei Schauerwetter.', True, {}),
    ('Böen 145 km/h bei einsetzenden Graupelschauern.', True, {}),
    ('Böen 145 km/h bei Schneeverwehungen.', True, {}),
    ('Böen 145 km/h bei starkem Tauwetter.', True, {}),
    ('Böen 145 km/h bei Starkfrost.', True, {}),
    ('Böen 145 km/h bei Föhnwetter.', True, {}),
    ('Böen 145 km/h bei aufgelockerter Bewölkung.', True, {}),
    ('Böen 145 km/h bei einer Gewitterfront.', True, {}),
    ('Böen 145 km/h bei teils sonnigen Abschnitten.', True, {}),
    ('Böen 145 km/h bei hoher Luftfeuchte.', True, {}),
    ('Böen 145 km/h bei sehr niedrigem Luftdruck.', True, {}),
    ('Böen 145 km/h bei stark fallendem Luftdruck.', True, {}),
    ('Böen 145 km/h bei einer heranziehenden Kaltfront.', True, {}),
    ('Böen 145 km/h bei einer Tiefdruckzone.', True, {}),
    ('Böen 145 km/h bei kräftigem Dauerregen.', True, {}),
    ('Böen 145 km/h bei Nachtfrost.', True, {}),
    ('Böen 145 km/h bei weiter sinkenden Temperaturen.', True, {}),
    ('Böen 90 km/h bleiben nach heutigen Berechnungen aus.', False, {}),
    ('Böen 90 km/h werden nach Einschätzung der Meteorologen nicht eintreten.', False, {}),
    ('Böen 90 km/h sind laut Wetterzentrale keinesfalls zu erwarten.', False, {}),
    ('Böen 90 km/h werden nach aktueller Prognose nicht auftreten.', False, {}),
    ('Böen 90 km/h treten den Messmodellen zufolge nicht auf.', False, {}),
    ('Böen 90 km/h sind nach dem neuesten Stand ausgeschlossen.', False, {}),
    ('Böen 90 km/h werden durch unsere Vorhersage ausdrücklich ausgeschlossen.', False, {}),
    ('Böen 90 km/h sind laut dem heutigen Bericht nicht zu erwarten.', False, {}),
    ('Böen 90 km/h bleiben laut Warnzentrale aus.', False, {}),
    ('Böen 90 km/h sind auch nach der jüngsten Modellrechnung ausgeschlossen.', False, {}),
    ('Böen 110 km/h bleiben nach heutigen Berechnungen aus.', False, {}),
    ('Böen 110 km/h werden nach Einschätzung der Meteorologen nicht eintreten.', False, {}),
    ('Böen 110 km/h sind laut Wetterzentrale keinesfalls zu erwarten.', False, {}),
    ('Böen 110 km/h werden nach aktueller Prognose nicht auftreten.', False, {}),
    ('Böen 110 km/h treten den Messmodellen zufolge nicht auf.', False, {}),
    ('Böen 110 km/h sind nach dem neuesten Stand ausgeschlossen.', False, {}),
    ('Böen 110 km/h werden durch unsere Vorhersage ausdrücklich ausgeschlossen.', False, {}),
    ('Böen 110 km/h sind laut dem heutigen Bericht nicht zu erwarten.', False, {}),
    ('Böen 110 km/h bleiben laut Warnzentrale aus.', False, {}),
    ('Böen 110 km/h sind auch nach der jüngsten Modellrechnung ausgeschlossen.', False, {}),
    ('Böen 145 km/h bleiben nach heutigen Berechnungen aus.', False, {}),
    ('Böen 145 km/h werden nach Einschätzung der Meteorologen nicht eintreten.', False, {}),
    ('Böen 145 km/h sind laut Wetterzentrale keinesfalls zu erwarten.', False, {}),
    ('Böen 145 km/h werden nach aktueller Prognose nicht auftreten.', False, {}),
    ('Böen 145 km/h treten den Messmodellen zufolge nicht auf.', False, {}),
    ('Böen 145 km/h sind nach dem neuesten Stand ausgeschlossen.', False, {}),
    ('Böen 145 km/h werden durch unsere Vorhersage ausdrücklich ausgeschlossen.', False, {}),
    ('Böen 145 km/h sind laut dem heutigen Bericht nicht zu erwarten.', False, {}),
    ('Böen 145 km/h bleiben laut Warnzentrale aus.', False, {}),
    ('Böen 145 km/h sind auch nach der jüngsten Modellrechnung ausgeschlossen.', False, {}),
    ('Böen 89 km/h im südlichen Umland von Köln.', False, {}),
    ('Böen 89 km/h nur in Randbereichen der Eifel.', False, {}),
    ('Böen 89 km/h entlang der Rheinschiene.', False, {}),
    ('Böen 89 km/h auf den Inseln vor der Küste.', False, {}),
    ('Böen 89 km/h im Kölner Stadtgebiet.', False, {}),
    ('Böen 89 km/h rund um den Flughafen.', False, {}),
    ('Böen 89 km/h zwischen Aachen und Düren.', False, {}),
    ('Böen 89 km/h in den nördlichen Landesteilen.', False, {}),
    ('Böen 89 km/h nur in höheren Gipfellagen.', False, {}),
    ('Böen 89 km/h bei Bonn und Umgebung.', False, {}),
    ('Böen 90 km/h im südlichen Umland von Köln.', False, {}),
    ('Böen 90 km/h nur in Randbereichen der Eifel.', False, {}),
    ('Böen 90 km/h entlang der Rheinschiene.', False, {}),
    ('Böen 90 km/h auf den Inseln vor der Küste.', False, {}),
    ('Böen 90 km/h im Kölner Stadtgebiet.', False, {}),
    ('Böen 90 km/h rund um den Flughafen.', False, {}),
    ('Böen 90 km/h zwischen Aachen und Düren.', False, {}),
    ('Böen 90 km/h in den nördlichen Landesteilen.', False, {}),
    ('Böen 90 km/h nur in höheren Gipfellagen.', False, {}),
    ('Böen 90 km/h bei Bonn und Umgebung.', False, {}),
    ('Böen 110 km/h im südlichen Umland von Köln.', False, {}),
    ('Böen 110 km/h nur in Randbereichen der Eifel.', False, {}),
    ('Böen 110 km/h entlang der Rheinschiene.', False, {}),
    ('Böen 110 km/h auf den Inseln vor der Küste.', False, {}),
    ('Böen 110 km/h im Kölner Stadtgebiet.', False, {}),
    ('Böen 110 km/h rund um den Flughafen.', False, {}),
    ('Böen 110 km/h zwischen Aachen und Düren.', False, {}),
    ('Böen 110 km/h in den nördlichen Landesteilen.', False, {}),
    ('Böen 110 km/h nur in höheren Gipfellagen.', False, {}),
    ('Böen 110 km/h bei Bonn und Umgebung.', False, {}),
    ('Böen 70 km/h im ganzen amtlich betroffenen Gebiet.', False, {}),
    ('Böen 70 km/h im gesamten ausgegebenen Warngebiet.', False, {}),
    ('Böen 70 km/h in jedem Teil des offiziellen Warngebiets.', False, {}),
    ('Böen 70 km/h über das Warngebiet hinweg flächendeckend.', False, {}),
    ('Böen 70 km/h im gesamten Geltungsbereich der Warnung.', False, {}),
    ('Böen 89 km/h im ganzen amtlich betroffenen Gebiet.', False, {}),
    ('Böen 89 km/h im gesamten ausgegebenen Warngebiet.', False, {}),
    ('Böen 89 km/h in jedem Teil des offiziellen Warngebiets.', False, {}),
    ('Böen 89 km/h über das Warngebiet hinweg flächendeckend.', False, {}),
    ('Böen 89 km/h im gesamten Geltungsbereich der Warnung.', False, {}),
    ('Böen 90 km/h im ganzen amtlich betroffenen Gebiet.', True, {}),
    ('Böen 90 km/h im gesamten ausgegebenen Warngebiet.', True, {}),
    ('Böen 90 km/h in jedem Teil des offiziellen Warngebiets.', True, {}),
    ('Böen 90 km/h über das Warngebiet hinweg flächendeckend.', True, {}),
    ('Böen 90 km/h im gesamten Geltungsbereich der Warnung.', True, {}),
    ('Böen 110 km/h im ganzen amtlich betroffenen Gebiet.', True, {}),
    ('Böen 110 km/h im gesamten ausgegebenen Warngebiet.', True, {}),
    ('Böen 110 km/h in jedem Teil des offiziellen Warngebiets.', True, {}),
    ('Böen 110 km/h über das Warngebiet hinweg flächendeckend.', True, {}),
    ('Böen 110 km/h im gesamten Geltungsbereich der Warnung.', True, {}),
    ('Böen 145 km/h im ganzen amtlich betroffenen Gebiet.', True, {}),
    ('Böen 145 km/h im gesamten ausgegebenen Warngebiet.', True, {}),
    ('Böen 145 km/h in jedem Teil des offiziellen Warngebiets.', True, {}),
    ('Böen 145 km/h über das Warngebiet hinweg flächendeckend.', True, {}),
    ('Böen 145 km/h im gesamten Geltungsbereich der Warnung.', True, {}),
    ('Böen 70 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 50}),
    ('Böen 70 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 900}),
    ('Böen 70 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 1200}),
    ('Böen 70 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 50}),
    ('Böen 70 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 900}),
    ('Böen 70 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 1200}),
    ('Böen 70 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 50}),
    ('Böen 70 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 900}),
    ('Böen 70 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 1200}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 50}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 900}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 1200}),
    ('Böen 89 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 50}),
    ('Böen 89 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 900}),
    ('Böen 89 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 1200}),
    ('Böen 89 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 50}),
    ('Böen 89 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 900}),
    ('Böen 89 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 1200}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 50}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 900}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1000 Metern.', True, {'elevation': 1200}),
    ('Böen 90 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 50}),
    ('Böen 90 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 900}),
    ('Böen 90 km/h ab 1000 m über dem Meeresspiegel.', True, {'elevation': 1200}),
    ('Böen 90 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 50}),
    ('Böen 90 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 900}),
    ('Böen 90 km/h oberhalb 1.000 m ü. NN.', True, {'elevation': 1200}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 50}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 900}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern.', True, {'elevation': 1200}),
    ('Böen 110 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 50}),
    ('Böen 110 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 900}),
    ('Böen 110 km/h ab 1000 m über dem Meeresspiegel.', True, {'elevation': 1200}),
    ('Böen 110 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 50}),
    ('Böen 110 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 900}),
    ('Böen 110 km/h oberhalb 1.000 m ü. NN.', True, {'elevation': 1200}),
    ('Böen 145 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 50}),
    ('Böen 145 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, {'elevation': 900}),
    ('Böen 145 km/h oberhalb einer Meereshöhe von 1000 Metern.', True, {'elevation': 1200}),
    ('Böen 145 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 50}),
    ('Böen 145 km/h ab 1000 m über dem Meeresspiegel.', False, {'elevation': 900}),
    ('Böen 145 km/h ab 1000 m über dem Meeresspiegel.', True, {'elevation': 1200}),
    ('Böen 145 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 50}),
    ('Böen 145 km/h oberhalb 1.000 m ü. NN.', False, {'elevation': 900}),
    ('Böen 145 km/h oberhalb 1.000 m ü. NN.', True, {'elevation': 1200}),
    ('Böen 70 km/h, in exponierten Lagen bis 150 km/h.', False, {}),
    ('In exponierten Lagen 150 km/h, sonst Böen 70 km/h.', False, {}),
    ('Böen 70 km/h allgemein, lokal bis zu 150 km/h auf Berggipfeln.', False, {}),
    ('Böen 89 km/h, in exponierten Lagen bis 150 km/h.', False, {}),
    ('In exponierten Lagen 150 km/h, sonst Böen 89 km/h.', False, {}),
    ('Böen 89 km/h allgemein, lokal bis zu 150 km/h auf Berggipfeln.', False, {}),
    ('Böen 90 km/h, in exponierten Lagen bis 150 km/h.', True, {}),
    ('In exponierten Lagen 150 km/h, sonst Böen 90 km/h.', True, {}),
    ('Böen 90 km/h allgemein, lokal bis zu 150 km/h auf Berggipfeln.', True, {}),
    ('Böen 110 km/h, in exponierten Lagen bis 150 km/h.', True, {}),
    ('In exponierten Lagen 150 km/h, sonst Böen 110 km/h.', True, {}),
    ('Böen 110 km/h allgemein, lokal bis zu 150 km/h auf Berggipfeln.', True, {}),
    ('Böen 145 km/h, in exponierten Lagen bis 150 km/h.', True, {}),
    ('In exponierten Lagen 150 km/h, sonst Böen 145 km/h.', True, {}),
    ('Böen 145 km/h allgemein, lokal bis zu 150 km/h auf Berggipfeln.', True, {}),
    ('Böen 70 km/h. Schäden mit 150 km/h sind ausgeschlossen.', False, {}),
    ('Böen 70 km/h, Gewitter nicht ausgeschlossen.', False, {}),
    ('Böen 70 km/h. Es gibt keine Hagelgefahr.', False, {}),
    ('Böen 89 km/h. Schäden mit 150 km/h sind ausgeschlossen.', False, {}),
    ('Böen 89 km/h, Gewitter nicht ausgeschlossen.', False, {}),
    ('Böen 89 km/h. Es gibt keine Hagelgefahr.', False, {}),
    ('Böen 90 km/h. Schäden mit 150 km/h sind ausgeschlossen.', True, {}),
    ('Böen 90 km/h, Gewitter nicht ausgeschlossen.', True, {}),
    ('Böen 90 km/h. Es gibt keine Hagelgefahr.', True, {}),
    ('Böen 110 km/h. Schäden mit 150 km/h sind ausgeschlossen.', True, {}),
    ('Böen 110 km/h, Gewitter nicht ausgeschlossen.', True, {}),
    ('Böen 110 km/h. Es gibt keine Hagelgefahr.', True, {}),
    ('Böen 145 km/h. Schäden mit 150 km/h sind ausgeschlossen.', True, {}),
    ('Böen 145 km/h, Gewitter nicht ausgeschlossen.', True, {}),
    ('Böen 145 km/h. Es gibt keine Hagelgefahr.', True, {}),
    ('Mittelwind 140 km/h, Böen 70 km/h.', False, {}),
    ('Böen 70 km/h. 140 km/h gelten nur für das Schnellfahrzeug.', False, {}),
    ('Böen 70 km/h, die Temperatur liegt bei 140 Grad Fahrenheit.', False, {}),
    ('Mittelwind 140 km/h, Böen 89 km/h.', False, {}),
    ('Böen 89 km/h. 140 km/h gelten nur für das Schnellfahrzeug.', False, {}),
    ('Böen 89 km/h, die Temperatur liegt bei 140 Grad Fahrenheit.', False, {}),
    ('Mittelwind 140 km/h, Böen 90 km/h.', True, {}),
    ('Böen 90 km/h. 140 km/h gelten nur für das Schnellfahrzeug.', True, {}),
    ('Böen 90 km/h, die Temperatur liegt bei 140 Grad Fahrenheit.', True, {}),
    ('Mittelwind 140 km/h, Böen 110 km/h.', True, {}),
    ('Böen 110 km/h. 140 km/h gelten nur für das Schnellfahrzeug.', True, {}),
    ('Böen 110 km/h, die Temperatur liegt bei 140 Grad Fahrenheit.', True, {}),
    ('Mittelwind 140 km/h, Böen 145 km/h.', True, {}),
    ('Böen 145 km/h. 140 km/h gelten nur für das Schnellfahrzeug.', True, {}),
    ('Böen 145 km/h, die Temperatur liegt bei 140 Grad Fahrenheit.', True, {}),
    ('Böen 70 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 70 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 70 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 70 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 70 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 70 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 89 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 89 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 89 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 89 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 89 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 89 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 90 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 90 km/h ab 18:00 UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 90 km/h ab 18:00 UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 90 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 90 km/h ab 18.00 Uhr UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 90 km/h ab 18.00 Uhr UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 110 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 110 km/h ab 18:00 UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 110 km/h ab 18:00 UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 110 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 110 km/h ab 18.00 Uhr UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 110 km/h ab 18.00 Uhr UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 145 km/h ab 18:00 UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 145 km/h ab 18:00 UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 145 km/h ab 18:00 UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 145 km/h ab 18 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 145 km/h ab 18 Uhr UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 145 km/h ab 18 Uhr UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 145 km/h ab 18.00 Uhr UTC.', False, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 145 km/h ab 18.00 Uhr UTC.', True, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 145 km/h ab 18.00 Uhr UTC.', True, {'now': '2026-10-24 18:00:00+00:00'}),
    ('Böen 70 km/h.', False, {'parameters': {'gusts': '70 km/h'}}),
    ('Böen 70 km/h.', True, {'parameters': {'gusts': '110 km/h'}}),
    ('Böen 90 km/h.', True, {'parameters': {'gusts': '70 km/h'}}),
    ('Böen 90 km/h.', True, {'parameters': {'gusts': '110 km/h'}}),
    ('Böen 110 km/h.', True, {'parameters': {'gusts': '70 km/h'}}),
    ('Böen 110 km/h.', True, {'parameters': {'gusts': '110 km/h'}}),
]


@pytest.mark.parametrize("text,expected,kwargs", AUDIT_CASES)
def test_independent_361_case_audit(text, expected, kwargs):
    kwargs = dict(kwargs)
    if "now" in kwargs:
        kwargs["now"] = datetime.fromisoformat(kwargs["now"])
    assert assess(text, **kwargs)["hard_lock"] is expected


CONDITIONS = [
    "bei heftigem Gewitterregen", "bei extremer Schneeglätte",
    "bei teils gefrierenden Niederschlägen", "bei Unwetterlage",
    "bei eisigen Windbedingungen", "bei frostig kaltem Wetter", "bei Schauerwetter",
    "bei Schneeverwehungen", "bei starkem Tauwetter", "bei Starkfrost", "bei Föhnwetter",
    "bei einer Gewitterfront", "bei teils sonnigen Abschnitten", "bei meist sonnigen Abschnitten",
    "bei plötzlich kaltem Wetter", "bei überraschend starkem Regen",
    "bei sehr niedrigem Luftdruck", "bei stark fallendem Luftdruck", "bei einer Tiefdruckzone",
]


@pytest.mark.parametrize("condition", CONDITIONS)
@pytest.mark.parametrize("tail,locked", [
    (" werden erwartet.", True), (" sind nicht zu erwarten.", False),
    (" sind nicht ausgeschlossen.", True), (", Schäden sind nicht zu erwarten.", True),
])
def test_weather_constituents_keep_forecast_polarity_and_other_subjects_separate(condition, tail, locked):
    result = assess(f"Böen 110 km/h {condition}{tail}")
    assert result["hard_lock"] is locked
    assert any(condition in item["weather_conditions"] for item in result["gust_evidence"])
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("condition", CONDITIONS)
@pytest.mark.parametrize("place", ["in der Eifel", "zwischen Bonn und Köln"])
def test_meteorological_constituents_do_not_erase_added_geographic_restrictions(condition, place):
    result = assess(f"Böen 110 km/h {condition} {place}.", {"gusts": "110 km/h"})
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("place", [
    "bei Gewitterregenhausen", "bei Unwetterlagenstadt", "bei Tiefdruckzonendorf",
    "bei Schneeglätteberg", "bei Starkfrosttal", "bei Föhnwetterort",
    "bei nördlichen Abschnitten", "in südlichen Windgebieten",
])
def test_names_and_spatial_sections_are_not_weather_condition_heads(place):
    result = assess(f"Böen 110 km/h {place}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


AREAS = ["im gesamten ausgegebenen Warngebiet", "im ganzen amtlich betroffenen Gebiet",
         "über das Warngebiet hinweg flächendeckend", "flächendeckend über das Warngebiet",
         "im gesamten Geltungsbereich der Warnung"]


@pytest.mark.parametrize("area", AREAS)
@pytest.mark.parametrize("suffix,locked", [
    ("", True), (" mit Ausnahme der Tallagen", False), (" nur auf den Gipfeln", False),
])
@pytest.mark.parametrize("field", ["description", "headline", "event", "parameter"])
def test_universal_area_claims_preserve_real_exceptions_in_all_fields(area, suffix, locked, field):
    text = f"Böen 110 km/h {area}{suffix}."
    changes = {field: text} if field in {"headline", "event"} else {}
    parameters = {"gusts": text} if field == "parameter" else {}
    result = assess(text if field == "description" else "", parameters, **changes)
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("area", [
    "nicht im gesamten ausgegebenen Warngebiet", "fast im gesamten ausgegebenen Warngebiet",
    "im gesamten südlichen Warngebiet", "im ganzen nördlichen Gebiet",
    "im gesamten ausgegebenen Warngebiet der Eifel",
    "über das Warngebiet hinweg nicht flächendeckend",
    "über das Warngebiet hinweg fast flächendeckend",
])
def test_nonuniversal_or_named_regions_do_not_confirm_the_windows_membership(area):
    result = assess(f"Böen 110 km/h {area}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


SOURCES = ["den Messmodellen zufolge", "den neuesten Messmodellen des DWD zufolge",
           "den Vorhersagemodellen nach", "dem Wetterdienst zufolge", "den Prognosen zufolge"]


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h treten {source} nicht auf.", False),
    ("Böen 110 km/h treten {source} auf.", True),
    ("Böen 110 km/h bleiben {source} aus.", False),
    ("Böen 110 km/h sind {source} nicht ausgeschlossen.", True),
    ("Böen 110 km/h, Schäden treten {source} nicht auf.", True),
])
@pytest.mark.parametrize("field", ["description", "headline", "event", "parameter"])
def test_postposed_reporting_np_neither_consumes_the_verb_nor_denies_another_subject(source, frame, locked, field):
    text = frame.format(source=source)
    changes = {field: text} if field in {"headline", "event"} else {}
    parameters = {"gusts": text} if field == "parameter" else {}
    result = assess(text if field == "description" else "", parameters, **changes)
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("agent", ["durch unsere Vorhersage", "durch diese jüngste Modellrechnung",
                                     "von unseren Wettermodellen", "vom DWD"])
@pytest.mark.parametrize("predicate,locked", [("ausgeschlossen", False), ("nicht ausgeschlossen", True),
                                             ("nicht erwartet", False), ("erwartet", True)])
def test_shared_reporting_entities_have_their_own_predicate_role(agent, predicate, locked):
    assert assess(f"Böen 110 km/h werden {agent} ausdrücklich {predicate}.")["hard_lock"] is locked


@pytest.mark.parametrize("description", [
    "Böen 110 km/h, Schäden werden durch unsere Vorhersage ausgeschlossen.",
    "Böen 110 km/h mit Schäden, die durch unsere Vorhersage ausgeschlossen werden.",
    "Böen 110 km/h mit Schäden, die den Messmodellen zufolge nicht auftreten.",
])
def test_reporting_the_absence_of_damage_does_not_deny_the_wind_event(description):
    assert assess(description)["hard_lock"]


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h, die {source} nicht auftreten.", False),
    ("Böen 110 km/h, die {source} auftreten.", True),
    ("Böen 110 km/h, die {source} nicht ausgeschlossen sind.", True),
    ("Böen 110 km/h, Schäden, die {source} nicht auftreten.", True),
])
def test_reported_relative_predicates_keep_their_own_subject(source, frame, locked):
    assert assess(frame.format(source=source))["hard_lock"] is locked


@pytest.mark.parametrize("verb,particle,denies", [
    ("treten", "auf", False), ("traten", "auf", False), ("kommen", "vor", False), ("kamen", "vor", False),
    ("bestehen", "", False), ("existieren", "", False), ("bleiben", "aus", True), ("fallen", "aus", True),
])
@pytest.mark.parametrize("source", ["Modellrechnungen zufolge", "Messmodellen zufolge"])
@pytest.mark.parametrize("negative", [False, True])
def test_articleless_sources_cannot_consume_any_supported_finite_forecast_stem(verb, particle, denies, source, negative):
    text = f"Böen 110 km/h {verb} {source} {'nicht ' if negative else ''}{particle}."
    result = assess(text)
    assert result["hard_lock"] is (negative == denies)


@pytest.mark.parametrize("noun", ["Meereshöhe", "Meereshoehe", "Höhe", "Höhenlage"])
@pytest.mark.parametrize("relation,compare", [("oberhalb", operator.gt), ("unterhalb", operator.lt),
                                             ("ab", operator.ge), ("bis", operator.le)])
@pytest.mark.parametrize("height", [50, 999.99, 1000, 1000.01, 1200, None])
def test_height_nouns_share_exact_dimensional_bounds_and_require_known_elevation(noun, relation, compare, height):
    result = assess(f"Böen 110 km/h {relation} einer {noun} von 1.000 Metern.", elevation=height)
    assert result["hard_lock"] is (height is not None and compare(height, 1000))
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("datum", ["über Grund", "AGL", "WGS84"])
def test_a_relative_height_reference_cannot_be_overridden_by_the_noun_meereshoehe(datum):
    result = assess(f"Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern {datum}.", elevation=1200)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("minute,locked", [(17 * 60 + 29, False), (17 * 60 + 30, True), (18 * 60, True)])
def test_reporting_source_height_and_true_onset_stay_separate(minute, locked):
    now = NOW.replace(hour=0, minute=0) + timedelta(minutes=minute)
    text = "Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern ab 18 Uhr UTC sind den Messmodellen zufolge nicht ausgeschlossen."
    result = assess(text, now=now, elevation=1200)
    assert result["hard_lock"] is locked
    assert not assess(text, now=now, elevation=900)["hard_lock"]


def test_new_source_forms_keep_opposite_field_claims_visible_as_conflicting():
    result = assess("Böen 110 km/h treten den Messmodellen zufolge nicht auf.", headline="Böen 110 km/h erwartet.")
    assert result["gust_conflict"]
    assert any(item.get("polarity_conflict") for item in result["gust_evidence"])
