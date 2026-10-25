"""Independent audit inputs and event/quantity-specific headline context."""
from datetime import datetime, timedelta
import json

import pytest

from test_v0119_warning_scopes_pure import NOW, assess, policy, warning


AUDIT_CASES = [
    ('Böen 65 km/h bei starker Brise.', False, 60, {}),
    ('Böen 65 km/h bei kräftigem Wind.', False, 60, {}),
    ('Böen 65 km/h bei milden Temperaturen.', False, 60, {}),
    ('Böen 65 km/h bei langanhaltendem Regen.', False, 60, {}),
    ('Böen 65 km/h bei kräftigen Regenschauern.', False, 60, {}),
    ('Böen 65 km/h bei gefrierendem Sprühregen.', False, 60, {}),
    ('Böen 65 km/h bei extrem hoher Luftfeuchtigkeit.', False, 60, {}),
    ('Böen 65 km/h bei stark bewölktem Himmel.', False, 60, {}),
    ('Böen 65 km/h bei einer herannahenden Kaltfront.', False, 60, {}),
    ('Böen 65 km/h bei absinkendem Luftdruck.', False, 60, {}),
    ('Böen 65 km/h mit kräftigen Gewittern.', False, 60, {}),
    ('Böen 65 km/h mit gleichzeitigem Hagel.', False, 60, {}),
    ('Böen 65 km/h ohne kräftige Regenfälle.', False, 60, {}),
    ('Böen 65 km/h und Schneefall ist möglich.', False, 60, {}),
    ('Böen 65 km/h und Starkregen ist möglich.', False, 60, {}),
    ('Böen 65 km/h während eines kräftigen Gewitters.', False, 60, {}),
    ('Böen 65 km/h bei trockenem und mildem Wetter.', False, 60, {}),
    ('Böen 65 km/h bei leichtem Schnee und starkem Regen.', False, 60, {}),
    ('Böen 65 km/h in Verbindung mit Schneeschauern.', False, 60, {}),
    ('Böen 65 km/h während anhaltender Niederschläge.', False, 60, {}),
    ('Böen 65 km/h bei Schneematsch.', False, 60, {}),
    ('Böen 65 km/h bei Gewittern mit Hagel.', False, 60, {}),
    ('Böen 65 km/h mit Nebel und Frost.', False, 60, {}),
    ('Böen 65 km/h bei anhaltendem Dauerregen.', False, 60, {}),
    ('Böen 65 km/h unter unbeständigen Wetterverhältnissen.', False, 60, {}),
    ('Böen 89 km/h bei starker Brise.', False, 60, {}),
    ('Böen 89 km/h bei kräftigem Wind.', False, 60, {}),
    ('Böen 89 km/h bei milden Temperaturen.', False, 60, {}),
    ('Böen 89 km/h bei langanhaltendem Regen.', False, 60, {}),
    ('Böen 89 km/h bei kräftigen Regenschauern.', False, 60, {}),
    ('Böen 89 km/h bei gefrierendem Sprühregen.', False, 60, {}),
    ('Böen 89 km/h bei extrem hoher Luftfeuchtigkeit.', False, 60, {}),
    ('Böen 89 km/h bei stark bewölktem Himmel.', False, 60, {}),
    ('Böen 89 km/h bei einer herannahenden Kaltfront.', False, 60, {}),
    ('Böen 89 km/h bei absinkendem Luftdruck.', False, 60, {}),
    ('Böen 89 km/h mit kräftigen Gewittern.', False, 60, {}),
    ('Böen 89 km/h mit gleichzeitigem Hagel.', False, 60, {}),
    ('Böen 89 km/h ohne kräftige Regenfälle.', False, 60, {}),
    ('Böen 89 km/h und Schneefall ist möglich.', False, 60, {}),
    ('Böen 89 km/h und Starkregen ist möglich.', False, 60, {}),
    ('Böen 89 km/h während eines kräftigen Gewitters.', False, 60, {}),
    ('Böen 89 km/h bei trockenem und mildem Wetter.', False, 60, {}),
    ('Böen 89 km/h bei leichtem Schnee und starkem Regen.', False, 60, {}),
    ('Böen 89 km/h in Verbindung mit Schneeschauern.', False, 60, {}),
    ('Böen 89 km/h während anhaltender Niederschläge.', False, 60, {}),
    ('Böen 89 km/h bei Schneematsch.', False, 60, {}),
    ('Böen 89 km/h bei Gewittern mit Hagel.', False, 60, {}),
    ('Böen 89 km/h mit Nebel und Frost.', False, 60, {}),
    ('Böen 89 km/h bei anhaltendem Dauerregen.', False, 60, {}),
    ('Böen 89 km/h unter unbeständigen Wetterverhältnissen.', False, 60, {}),
    ('Böen 90 km/h bei starker Brise.', True, 60, {}),
    ('Böen 90 km/h bei kräftigem Wind.', True, 60, {}),
    ('Böen 90 km/h bei milden Temperaturen.', True, 60, {}),
    ('Böen 90 km/h bei langanhaltendem Regen.', True, 60, {}),
    ('Böen 90 km/h bei kräftigen Regenschauern.', True, 60, {}),
    ('Böen 90 km/h bei gefrierendem Sprühregen.', True, 60, {}),
    ('Böen 90 km/h bei extrem hoher Luftfeuchtigkeit.', True, 60, {}),
    ('Böen 90 km/h bei stark bewölktem Himmel.', True, 60, {}),
    ('Böen 90 km/h bei einer herannahenden Kaltfront.', True, 60, {}),
    ('Böen 90 km/h bei absinkendem Luftdruck.', True, 60, {}),
    ('Böen 90 km/h mit kräftigen Gewittern.', True, 60, {}),
    ('Böen 90 km/h mit gleichzeitigem Hagel.', True, 60, {}),
    ('Böen 90 km/h ohne kräftige Regenfälle.', True, 60, {}),
    ('Böen 90 km/h und Schneefall ist möglich.', True, 60, {}),
    ('Böen 90 km/h und Starkregen ist möglich.', True, 60, {}),
    ('Böen 90 km/h während eines kräftigen Gewitters.', True, 60, {}),
    ('Böen 90 km/h bei trockenem und mildem Wetter.', True, 60, {}),
    ('Böen 90 km/h bei leichtem Schnee und starkem Regen.', True, 60, {}),
    ('Böen 90 km/h in Verbindung mit Schneeschauern.', True, 60, {}),
    ('Böen 90 km/h während anhaltender Niederschläge.', True, 60, {}),
    ('Böen 90 km/h bei Schneematsch.', True, 60, {}),
    ('Böen 90 km/h bei Gewittern mit Hagel.', True, 60, {}),
    ('Böen 90 km/h mit Nebel und Frost.', True, 60, {}),
    ('Böen 90 km/h bei anhaltendem Dauerregen.', True, 60, {}),
    ('Böen 90 km/h unter unbeständigen Wetterverhältnissen.', True, 60, {}),
    ('Böen 110 km/h bei starker Brise.', True, 60, {}),
    ('Böen 110 km/h bei kräftigem Wind.', True, 60, {}),
    ('Böen 110 km/h bei milden Temperaturen.', True, 60, {}),
    ('Böen 110 km/h bei langanhaltendem Regen.', True, 60, {}),
    ('Böen 110 km/h bei kräftigen Regenschauern.', True, 60, {}),
    ('Böen 110 km/h bei gefrierendem Sprühregen.', True, 60, {}),
    ('Böen 110 km/h bei extrem hoher Luftfeuchtigkeit.', True, 60, {}),
    ('Böen 110 km/h bei stark bewölktem Himmel.', True, 60, {}),
    ('Böen 110 km/h bei einer herannahenden Kaltfront.', True, 60, {}),
    ('Böen 110 km/h bei absinkendem Luftdruck.', True, 60, {}),
    ('Böen 110 km/h mit kräftigen Gewittern.', True, 60, {}),
    ('Böen 110 km/h mit gleichzeitigem Hagel.', True, 60, {}),
    ('Böen 110 km/h ohne kräftige Regenfälle.', True, 60, {}),
    ('Böen 110 km/h und Schneefall ist möglich.', True, 60, {}),
    ('Böen 110 km/h und Starkregen ist möglich.', True, 60, {}),
    ('Böen 110 km/h während eines kräftigen Gewitters.', True, 60, {}),
    ('Böen 110 km/h bei trockenem und mildem Wetter.', True, 60, {}),
    ('Böen 110 km/h bei leichtem Schnee und starkem Regen.', True, 60, {}),
    ('Böen 110 km/h in Verbindung mit Schneeschauern.', True, 60, {}),
    ('Böen 110 km/h während anhaltender Niederschläge.', True, 60, {}),
    ('Böen 110 km/h bei Schneematsch.', True, 60, {}),
    ('Böen 110 km/h bei Gewittern mit Hagel.', True, 60, {}),
    ('Böen 110 km/h mit Nebel und Frost.', True, 60, {}),
    ('Böen 110 km/h bei anhaltendem Dauerregen.', True, 60, {}),
    ('Böen 110 km/h unter unbeständigen Wetterverhältnissen.', True, 60, {}),
    ('Böen 145 km/h bei starker Brise.', True, 60, {}),
    ('Böen 145 km/h bei kräftigem Wind.', True, 60, {}),
    ('Böen 145 km/h bei milden Temperaturen.', True, 60, {}),
    ('Böen 145 km/h bei langanhaltendem Regen.', True, 60, {}),
    ('Böen 145 km/h bei kräftigen Regenschauern.', True, 60, {}),
    ('Böen 145 km/h bei gefrierendem Sprühregen.', True, 60, {}),
    ('Böen 145 km/h bei extrem hoher Luftfeuchtigkeit.', True, 60, {}),
    ('Böen 145 km/h bei stark bewölktem Himmel.', True, 60, {}),
    ('Böen 145 km/h bei einer herannahenden Kaltfront.', True, 60, {}),
    ('Böen 145 km/h bei absinkendem Luftdruck.', True, 60, {}),
    ('Böen 145 km/h mit kräftigen Gewittern.', True, 60, {}),
    ('Böen 145 km/h mit gleichzeitigem Hagel.', True, 60, {}),
    ('Böen 145 km/h ohne kräftige Regenfälle.', True, 60, {}),
    ('Böen 145 km/h und Schneefall ist möglich.', True, 60, {}),
    ('Böen 145 km/h und Starkregen ist möglich.', True, 60, {}),
    ('Böen 145 km/h während eines kräftigen Gewitters.', True, 60, {}),
    ('Böen 145 km/h bei trockenem und mildem Wetter.', True, 60, {}),
    ('Böen 145 km/h bei leichtem Schnee und starkem Regen.', True, 60, {}),
    ('Böen 145 km/h in Verbindung mit Schneeschauern.', True, 60, {}),
    ('Böen 145 km/h während anhaltender Niederschläge.', True, 60, {}),
    ('Böen 145 km/h bei Schneematsch.', True, 60, {}),
    ('Böen 145 km/h bei Gewittern mit Hagel.', True, 60, {}),
    ('Böen 145 km/h mit Nebel und Frost.', True, 60, {}),
    ('Böen 145 km/h bei anhaltendem Dauerregen.', True, 60, {}),
    ('Böen 145 km/h unter unbeständigen Wetterverhältnissen.', True, 60, {}),
    ('Böen 70 km/h. Die Sonne scheint.', False, 60, {}),
    ('Böen 70 km/h. Die Temperaturen betragen 5 Grad.', False, 60, {}),
    ('Böen 70 km/h. Bei Hagel besteht zusätzliche Gefahr.', False, 60, {}),
    ('Böen 70 km/h. Der Niederschlag hält an.', False, 60, {}),
    ('Böen 70 km/h. In einzelnen Städten regnet es.', False, 60, {}),
    ('Böen 70 km/h. Die Regenmenge beträgt 110 mm.', False, 60, {}),
    ('Böen 70 km/h. Die Sichtweite sinkt auf 200 m.', False, 60, {}),
    ('Böen 70 km/h. Sturmflut wird nicht erwartet.', False, 60, {}),
    ('Böen 70 km/h. Über den Bergen zieht Regen auf.', False, 60, {}),
    ('Böen 70 km/h. Die Blitzaktivität bleibt gering.', False, 60, {}),
    ('Böen 70 km/h. Glatteis tritt nicht auf.', False, 60, {}),
    ('Böen 70 km/h. Ein hoher Wasserstand von 120 cm ist möglich.', False, 60, {}),
    ('Böen 89 km/h. Die Sonne scheint.', False, 60, {}),
    ('Böen 89 km/h. Die Temperaturen betragen 5 Grad.', False, 60, {}),
    ('Böen 89 km/h. Bei Hagel besteht zusätzliche Gefahr.', False, 60, {}),
    ('Böen 89 km/h. Der Niederschlag hält an.', False, 60, {}),
    ('Böen 89 km/h. In einzelnen Städten regnet es.', False, 60, {}),
    ('Böen 89 km/h. Die Regenmenge beträgt 110 mm.', False, 60, {}),
    ('Böen 89 km/h. Die Sichtweite sinkt auf 200 m.', False, 60, {}),
    ('Böen 89 km/h. Sturmflut wird nicht erwartet.', False, 60, {}),
    ('Böen 89 km/h. Über den Bergen zieht Regen auf.', False, 60, {}),
    ('Böen 89 km/h. Die Blitzaktivität bleibt gering.', False, 60, {}),
    ('Böen 89 km/h. Glatteis tritt nicht auf.', False, 60, {}),
    ('Böen 89 km/h. Ein hoher Wasserstand von 120 cm ist möglich.', False, 60, {}),
    ('Böen 90 km/h. Die Sonne scheint.', True, 60, {}),
    ('Böen 90 km/h. Die Temperaturen betragen 5 Grad.', True, 60, {}),
    ('Böen 90 km/h. Bei Hagel besteht zusätzliche Gefahr.', True, 60, {}),
    ('Böen 90 km/h. Der Niederschlag hält an.', True, 60, {}),
    ('Böen 90 km/h. In einzelnen Städten regnet es.', True, 60, {}),
    ('Böen 90 km/h. Die Regenmenge beträgt 110 mm.', True, 60, {}),
    ('Böen 90 km/h. Die Sichtweite sinkt auf 200 m.', True, 60, {}),
    ('Böen 90 km/h. Sturmflut wird nicht erwartet.', True, 60, {}),
    ('Böen 90 km/h. Über den Bergen zieht Regen auf.', True, 60, {}),
    ('Böen 90 km/h. Die Blitzaktivität bleibt gering.', True, 60, {}),
    ('Böen 90 km/h. Glatteis tritt nicht auf.', True, 60, {}),
    ('Böen 90 km/h. Ein hoher Wasserstand von 120 cm ist möglich.', True, 60, {}),
    ('Böen 110 km/h. Die Sonne scheint.', True, 60, {}),
    ('Böen 110 km/h. Die Temperaturen betragen 5 Grad.', True, 60, {}),
    ('Böen 110 km/h. Bei Hagel besteht zusätzliche Gefahr.', True, 60, {}),
    ('Böen 110 km/h. Der Niederschlag hält an.', True, 60, {}),
    ('Böen 110 km/h. In einzelnen Städten regnet es.', True, 60, {}),
    ('Böen 110 km/h. Die Regenmenge beträgt 110 mm.', True, 60, {}),
    ('Böen 110 km/h. Die Sichtweite sinkt auf 200 m.', True, 60, {}),
    ('Böen 110 km/h. Sturmflut wird nicht erwartet.', True, 60, {}),
    ('Böen 110 km/h. Über den Bergen zieht Regen auf.', True, 60, {}),
    ('Böen 110 km/h. Die Blitzaktivität bleibt gering.', True, 60, {}),
    ('Böen 110 km/h. Glatteis tritt nicht auf.', True, 60, {}),
    ('Böen 110 km/h. Ein hoher Wasserstand von 120 cm ist möglich.', True, 60, {}),
    ('Böen 89 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 60, {}),
    ('Böen 89 km/h werden den Prognosen des Wetterdienstes zufolge nicht auftreten.', False, 60, {}),
    ('Böen 89 km/h werden nach Einschätzung der Behörde nicht erwartet.', False, 60, {}),
    ('Böen 89 km/h sind entgegen älteren Vorhersagen nicht zu erwarten.', False, 60, {}),
    ('Böen 89 km/h bleiben laut amtlichen Berechnungen aus.', False, 60, {}),
    ('Böen 89 km/h sind nach Rückmeldung der Meteorologen nicht wahrscheinlich.', False, 60, {}),
    ('Böen 89 km/h sind laut neuester Modellberechnung ausgeschlossen.', False, 60, {}),
    ('Böen 89 km/h werden morgen nicht eintreten.', False, 60, {}),
    ('Böen 89 km/h kann der Wetterdienst ausschließen.', False, 60, {}),
    ('Böen 89 km/h werden laut DWD keinesfalls eintreten.', False, 60, {}),
    ('Böen 89 km/h werden nach unserem Kenntnisstand nicht vorhergesagt.', False, 60, {}),
    ('Böen 89 km/h treten laut aktuellen Prognosen nicht auf.', False, 60, {}),
    ('Böen 89 km/h sind nach übereinstimmenden Prognosen ausgeschlossen.', False, 60, {}),
    ('Böen 90 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 60, {}),
    ('Böen 90 km/h werden den Prognosen des Wetterdienstes zufolge nicht auftreten.', False, 60, {}),
    ('Böen 90 km/h werden nach Einschätzung der Behörde nicht erwartet.', False, 60, {}),
    ('Böen 90 km/h sind entgegen älteren Vorhersagen nicht zu erwarten.', False, 60, {}),
    ('Böen 90 km/h bleiben laut amtlichen Berechnungen aus.', False, 60, {}),
    ('Böen 90 km/h sind nach Rückmeldung der Meteorologen nicht wahrscheinlich.', False, 60, {}),
    ('Böen 90 km/h sind laut neuester Modellberechnung ausgeschlossen.', False, 60, {}),
    ('Böen 90 km/h werden morgen nicht eintreten.', False, 60, {}),
    ('Böen 90 km/h kann der Wetterdienst ausschließen.', False, 60, {}),
    ('Böen 90 km/h werden laut DWD keinesfalls eintreten.', False, 60, {}),
    ('Böen 90 km/h werden nach unserem Kenntnisstand nicht vorhergesagt.', False, 60, {}),
    ('Böen 90 km/h treten laut aktuellen Prognosen nicht auf.', False, 60, {}),
    ('Böen 90 km/h sind nach übereinstimmenden Prognosen ausgeschlossen.', False, 60, {}),
    ('Böen 110 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 60, {}),
    ('Böen 110 km/h werden den Prognosen des Wetterdienstes zufolge nicht auftreten.', False, 60, {}),
    ('Böen 110 km/h werden nach Einschätzung der Behörde nicht erwartet.', False, 60, {}),
    ('Böen 110 km/h sind entgegen älteren Vorhersagen nicht zu erwarten.', False, 60, {}),
    ('Böen 110 km/h bleiben laut amtlichen Berechnungen aus.', False, 60, {}),
    ('Böen 110 km/h sind nach Rückmeldung der Meteorologen nicht wahrscheinlich.', False, 60, {}),
    ('Böen 110 km/h sind laut neuester Modellberechnung ausgeschlossen.', False, 60, {}),
    ('Böen 110 km/h werden morgen nicht eintreten.', False, 60, {}),
    ('Böen 110 km/h kann der Wetterdienst ausschließen.', False, 60, {}),
    ('Böen 110 km/h werden laut DWD keinesfalls eintreten.', False, 60, {}),
    ('Böen 110 km/h werden nach unserem Kenntnisstand nicht vorhergesagt.', False, 60, {}),
    ('Böen 110 km/h treten laut aktuellen Prognosen nicht auf.', False, 60, {}),
    ('Böen 110 km/h sind nach übereinstimmenden Prognosen ausgeschlossen.', False, 60, {}),
    ('Böen 89 km/h in der Innenstadt.', False, 60, {}),
    ('Böen 89 km/h im Nordwesten des Kreises.', False, 60, {}),
    ('Böen 89 km/h entlang des Rheins.', False, 60, {}),
    ('Böen 89 km/h in den Tälern der Eifel.', False, 60, {}),
    ('Böen 89 km/h auf dem Deich.', False, 60, {}),
    ('Böen 89 km/h am Rand der Stadt.', False, 60, {}),
    ('Böen 89 km/h zwischen Aachen und Düren.', False, 60, {}),
    ('Böen 89 km/h südöstlich von Köln.', False, 60, {}),
    ('Böen 89 km/h im Gebirge.', False, 60, {}),
    ('Böen 89 km/h nur in den offenen Hochlagen.', False, 60, {}),
    ('Böen 89 km/h im Umland von Bonn.', False, 60, {}),
    ('Böen 89 km/h an der Ostsee.', False, 60, {}),
    ('Böen 89 km/h auf dem offenen Meer.', False, 60, {}),
    ('Böen 89 km/h über der Bucht.', False, 60, {}),
    ('Böen 89 km/h über dem Odenwald.', False, 60, {}),
    ('Böen 89 km/h auf den Berggipfeln.', False, 60, {}),
    ('Böen 89 km/h in der Nähe des Flughafens.', False, 60, {}),
    ('Böen 90 km/h in der Innenstadt.', False, 60, {}),
    ('Böen 90 km/h im Nordwesten des Kreises.', False, 60, {}),
    ('Böen 90 km/h entlang des Rheins.', False, 60, {}),
    ('Böen 90 km/h in den Tälern der Eifel.', False, 60, {}),
    ('Böen 90 km/h auf dem Deich.', False, 60, {}),
    ('Böen 90 km/h am Rand der Stadt.', False, 60, {}),
    ('Böen 90 km/h zwischen Aachen und Düren.', False, 60, {}),
    ('Böen 90 km/h südöstlich von Köln.', False, 60, {}),
    ('Böen 90 km/h im Gebirge.', False, 60, {}),
    ('Böen 90 km/h nur in den offenen Hochlagen.', False, 60, {}),
    ('Böen 90 km/h im Umland von Bonn.', False, 60, {}),
    ('Böen 90 km/h an der Ostsee.', False, 60, {}),
    ('Böen 90 km/h auf dem offenen Meer.', False, 60, {}),
    ('Böen 90 km/h über der Bucht.', False, 60, {}),
    ('Böen 90 km/h über dem Odenwald.', False, 60, {}),
    ('Böen 90 km/h auf den Berggipfeln.', False, 60, {}),
    ('Böen 90 km/h in der Nähe des Flughafens.', False, 60, {}),
    ('Böen 110 km/h in der Innenstadt.', False, 60, {}),
    ('Böen 110 km/h im Nordwesten des Kreises.', False, 60, {}),
    ('Böen 110 km/h entlang des Rheins.', False, 60, {}),
    ('Böen 110 km/h in den Tälern der Eifel.', False, 60, {}),
    ('Böen 110 km/h auf dem Deich.', False, 60, {}),
    ('Böen 110 km/h am Rand der Stadt.', False, 60, {}),
    ('Böen 110 km/h zwischen Aachen und Düren.', False, 60, {}),
    ('Böen 110 km/h südöstlich von Köln.', False, 60, {}),
    ('Böen 110 km/h im Gebirge.', False, 60, {}),
    ('Böen 110 km/h nur in den offenen Hochlagen.', False, 60, {}),
    ('Böen 110 km/h im Umland von Bonn.', False, 60, {}),
    ('Böen 110 km/h an der Ostsee.', False, 60, {}),
    ('Böen 110 km/h auf dem offenen Meer.', False, 60, {}),
    ('Böen 110 km/h über der Bucht.', False, 60, {}),
    ('Böen 110 km/h über dem Odenwald.', False, 60, {}),
    ('Böen 110 km/h auf den Berggipfeln.', False, 60, {}),
    ('Böen 110 km/h in der Nähe des Flughafens.', False, 60, {}),
    ('Böen 89 km/h ab 500 Metern Höhe.', False, 60, {}),
    ('Böen 89 km/h ab 500 Metern Höhe.', False, 500, {}),
    ('Böen 89 km/h ab 500 Metern Höhe.', False, 501, {}),
    ('Böen 89 km/h ab 500 Metern Höhe.', False, 1800, {}),
    ('Böen 89 km/h über 500 Metern ü. NN.', False, 60, {}),
    ('Böen 89 km/h über 500 Metern ü. NN.', False, 500, {}),
    ('Böen 89 km/h über 500 Metern ü. NN.', False, 501, {}),
    ('Böen 89 km/h über 500 Metern ü. NN.', False, 1800, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 500 Metern.', False, 60, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 500 Metern.', False, 500, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 500 Metern.', False, 501, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 500 Metern.', False, 1800, {}),
    ('Böen 89 km/h oberhalb 500 m.', False, 60, {}),
    ('Böen 89 km/h oberhalb 500 m.', False, 500, {}),
    ('Böen 89 km/h oberhalb 500 m.', False, 501, {}),
    ('Böen 89 km/h oberhalb 500 m.', False, 1800, {}),
    ('Böen 89 km/h ab 1000 Metern Höhe.', False, 60, {}),
    ('Böen 89 km/h ab 1000 Metern Höhe.', False, 1000, {}),
    ('Böen 89 km/h ab 1000 Metern Höhe.', False, 1001, {}),
    ('Böen 89 km/h ab 1000 Metern Höhe.', False, 1800, {}),
    ('Böen 89 km/h über 1000 Metern ü. NN.', False, 60, {}),
    ('Böen 89 km/h über 1000 Metern ü. NN.', False, 1000, {}),
    ('Böen 89 km/h über 1000 Metern ü. NN.', False, 1001, {}),
    ('Böen 89 km/h über 1000 Metern ü. NN.', False, 1800, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, 60, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, 1000, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, 1001, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, 1800, {}),
    ('Böen 89 km/h oberhalb 1.000 m.', False, 60, {}),
    ('Böen 89 km/h oberhalb 1.000 m.', False, 1000, {}),
    ('Böen 89 km/h oberhalb 1.000 m.', False, 1001, {}),
    ('Böen 89 km/h oberhalb 1.000 m.', False, 1800, {}),
    ('Böen 89 km/h ab 1200 Metern Höhe.', False, 60, {}),
    ('Böen 89 km/h ab 1200 Metern Höhe.', False, 1200, {}),
    ('Böen 89 km/h ab 1200 Metern Höhe.', False, 1201, {}),
    ('Böen 89 km/h ab 1200 Metern Höhe.', False, 1800, {}),
    ('Böen 89 km/h über 1200 Metern ü. NN.', False, 60, {}),
    ('Böen 89 km/h über 1200 Metern ü. NN.', False, 1200, {}),
    ('Böen 89 km/h über 1200 Metern ü. NN.', False, 1201, {}),
    ('Böen 89 km/h über 1200 Metern ü. NN.', False, 1800, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1200 Metern.', False, 60, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1200 Metern.', False, 1200, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1200 Metern.', False, 1201, {}),
    ('Böen 89 km/h oberhalb einer Meereshöhe von 1200 Metern.', False, 1800, {}),
    ('Böen 89 km/h oberhalb 1.200 m.', False, 60, {}),
    ('Böen 89 km/h oberhalb 1.200 m.', False, 1200, {}),
    ('Böen 89 km/h oberhalb 1.200 m.', False, 1201, {}),
    ('Böen 89 km/h oberhalb 1.200 m.', False, 1800, {}),
    ('Böen 90 km/h ab 500 Metern Höhe.', False, 60, {}),
    ('Böen 90 km/h ab 500 Metern Höhe.', True, 500, {}),
    ('Böen 90 km/h ab 500 Metern Höhe.', True, 501, {}),
    ('Böen 90 km/h ab 500 Metern Höhe.', True, 1800, {}),
    ('Böen 90 km/h über 500 Metern ü. NN.', False, 60, {}),
    ('Böen 90 km/h über 500 Metern ü. NN.', False, 500, {}),
    ('Böen 90 km/h über 500 Metern ü. NN.', True, 501, {}),
    ('Böen 90 km/h über 500 Metern ü. NN.', True, 1800, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 500 Metern.', False, 60, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 500 Metern.', False, 500, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 500 Metern.', True, 501, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 500 Metern.', True, 1800, {}),
    ('Böen 90 km/h oberhalb 500 m.', False, 60, {}),
    ('Böen 90 km/h oberhalb 500 m.', False, 500, {}),
    ('Böen 90 km/h oberhalb 500 m.', True, 501, {}),
    ('Böen 90 km/h oberhalb 500 m.', True, 1800, {}),
    ('Böen 90 km/h ab 1000 Metern Höhe.', False, 60, {}),
    ('Böen 90 km/h ab 1000 Metern Höhe.', True, 1000, {}),
    ('Böen 90 km/h ab 1000 Metern Höhe.', True, 1001, {}),
    ('Böen 90 km/h ab 1000 Metern Höhe.', True, 1800, {}),
    ('Böen 90 km/h über 1000 Metern ü. NN.', False, 60, {}),
    ('Böen 90 km/h über 1000 Metern ü. NN.', False, 1000, {}),
    ('Böen 90 km/h über 1000 Metern ü. NN.', True, 1001, {}),
    ('Böen 90 km/h über 1000 Metern ü. NN.', True, 1800, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, 60, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, 1000, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1000 Metern.', True, 1001, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1000 Metern.', True, 1800, {}),
    ('Böen 90 km/h oberhalb 1.000 m.', False, 60, {}),
    ('Böen 90 km/h oberhalb 1.000 m.', False, 1000, {}),
    ('Böen 90 km/h oberhalb 1.000 m.', True, 1001, {}),
    ('Böen 90 km/h oberhalb 1.000 m.', True, 1800, {}),
    ('Böen 90 km/h ab 1200 Metern Höhe.', False, 60, {}),
    ('Böen 90 km/h ab 1200 Metern Höhe.', True, 1200, {}),
    ('Böen 90 km/h ab 1200 Metern Höhe.', True, 1201, {}),
    ('Böen 90 km/h ab 1200 Metern Höhe.', True, 1800, {}),
    ('Böen 90 km/h über 1200 Metern ü. NN.', False, 60, {}),
    ('Böen 90 km/h über 1200 Metern ü. NN.', False, 1200, {}),
    ('Böen 90 km/h über 1200 Metern ü. NN.', True, 1201, {}),
    ('Böen 90 km/h über 1200 Metern ü. NN.', True, 1800, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1200 Metern.', False, 60, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1200 Metern.', False, 1200, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1200 Metern.', True, 1201, {}),
    ('Böen 90 km/h oberhalb einer Meereshöhe von 1200 Metern.', True, 1800, {}),
    ('Böen 90 km/h oberhalb 1.200 m.', False, 60, {}),
    ('Böen 90 km/h oberhalb 1.200 m.', False, 1200, {}),
    ('Böen 90 km/h oberhalb 1.200 m.', True, 1201, {}),
    ('Böen 90 km/h oberhalb 1.200 m.', True, 1800, {}),
    ('Böen 110 km/h ab 500 Metern Höhe.', False, 60, {}),
    ('Böen 110 km/h ab 500 Metern Höhe.', True, 500, {}),
    ('Böen 110 km/h ab 500 Metern Höhe.', True, 501, {}),
    ('Böen 110 km/h ab 500 Metern Höhe.', True, 1800, {}),
    ('Böen 110 km/h über 500 Metern ü. NN.', False, 60, {}),
    ('Böen 110 km/h über 500 Metern ü. NN.', False, 500, {}),
    ('Böen 110 km/h über 500 Metern ü. NN.', True, 501, {}),
    ('Böen 110 km/h über 500 Metern ü. NN.', True, 1800, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 500 Metern.', False, 60, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 500 Metern.', False, 500, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 500 Metern.', True, 501, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 500 Metern.', True, 1800, {}),
    ('Böen 110 km/h oberhalb 500 m.', False, 60, {}),
    ('Böen 110 km/h oberhalb 500 m.', False, 500, {}),
    ('Böen 110 km/h oberhalb 500 m.', True, 501, {}),
    ('Böen 110 km/h oberhalb 500 m.', True, 1800, {}),
    ('Böen 110 km/h ab 1000 Metern Höhe.', False, 60, {}),
    ('Böen 110 km/h ab 1000 Metern Höhe.', True, 1000, {}),
    ('Böen 110 km/h ab 1000 Metern Höhe.', True, 1001, {}),
    ('Böen 110 km/h ab 1000 Metern Höhe.', True, 1800, {}),
    ('Böen 110 km/h über 1000 Metern ü. NN.', False, 60, {}),
    ('Böen 110 km/h über 1000 Metern ü. NN.', False, 1000, {}),
    ('Böen 110 km/h über 1000 Metern ü. NN.', True, 1001, {}),
    ('Böen 110 km/h über 1000 Metern ü. NN.', True, 1800, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, 60, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern.', False, 1000, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern.', True, 1001, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1000 Metern.', True, 1800, {}),
    ('Böen 110 km/h oberhalb 1.000 m.', False, 60, {}),
    ('Böen 110 km/h oberhalb 1.000 m.', False, 1000, {}),
    ('Böen 110 km/h oberhalb 1.000 m.', True, 1001, {}),
    ('Böen 110 km/h oberhalb 1.000 m.', True, 1800, {}),
    ('Böen 110 km/h ab 1200 Metern Höhe.', False, 60, {}),
    ('Böen 110 km/h ab 1200 Metern Höhe.', True, 1200, {}),
    ('Böen 110 km/h ab 1200 Metern Höhe.', True, 1201, {}),
    ('Böen 110 km/h ab 1200 Metern Höhe.', True, 1800, {}),
    ('Böen 110 km/h über 1200 Metern ü. NN.', False, 60, {}),
    ('Böen 110 km/h über 1200 Metern ü. NN.', False, 1200, {}),
    ('Böen 110 km/h über 1200 Metern ü. NN.', True, 1201, {}),
    ('Böen 110 km/h über 1200 Metern ü. NN.', True, 1800, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1200 Metern.', False, 60, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1200 Metern.', False, 1200, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1200 Metern.', True, 1201, {}),
    ('Böen 110 km/h oberhalb einer Meereshöhe von 1200 Metern.', True, 1800, {}),
    ('Böen 110 km/h oberhalb 1.200 m.', False, 60, {}),
    ('Böen 110 km/h oberhalb 1.200 m.', False, 1200, {}),
    ('Böen 110 km/h oberhalb 1.200 m.', True, 1201, {}),
    ('Böen 110 km/h oberhalb 1.200 m.', True, 1800, {}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 70 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MEZ.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 89 km/h ab 18 Uhr MESZ.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', True, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', True, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 90 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:15:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:29:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', True, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:30:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', True, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:31:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr UTC.', False, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MEZ.', True, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 110 km/h ab 18 Uhr MESZ.', True, 60, {'now': '2026-10-24 17:00:00+00:00'}),
    ('Böen 90 km/h allgemein; Böen 50 km/h in der Innenstadt.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 80 km/h in der Innenstadt.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 50 km/h im Nordwesten des Kreises.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 80 km/h im Nordwesten des Kreises.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 50 km/h entlang des Rheins.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 80 km/h entlang des Rheins.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 50 km/h in den Tälern der Eifel.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 80 km/h in den Tälern der Eifel.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 50 km/h auf dem Deich.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 80 km/h auf dem Deich.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 50 km/h am Rand der Stadt.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 80 km/h am Rand der Stadt.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 50 km/h zwischen Aachen und Düren.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 80 km/h zwischen Aachen und Düren.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 50 km/h südöstlich von Köln.', True, 60, {}),
    ('Böen 90 km/h allgemein; Böen 80 km/h südöstlich von Köln.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 50 km/h in der Innenstadt.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 80 km/h in der Innenstadt.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 50 km/h im Nordwesten des Kreises.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 80 km/h im Nordwesten des Kreises.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 50 km/h entlang des Rheins.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 80 km/h entlang des Rheins.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 50 km/h in den Tälern der Eifel.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 80 km/h in den Tälern der Eifel.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 50 km/h auf dem Deich.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 80 km/h auf dem Deich.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 50 km/h am Rand der Stadt.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 80 km/h am Rand der Stadt.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 50 km/h zwischen Aachen und Düren.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 80 km/h zwischen Aachen und Düren.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 50 km/h südöstlich von Köln.', True, 60, {}),
    ('Böen 110 km/h allgemein; Böen 80 km/h südöstlich von Köln.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 50 km/h in der Innenstadt.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 80 km/h in der Innenstadt.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 50 km/h im Nordwesten des Kreises.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 80 km/h im Nordwesten des Kreises.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 50 km/h entlang des Rheins.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 80 km/h entlang des Rheins.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 50 km/h in den Tälern der Eifel.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 80 km/h in den Tälern der Eifel.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 50 km/h auf dem Deich.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 80 km/h auf dem Deich.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 50 km/h am Rand der Stadt.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 80 km/h am Rand der Stadt.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 50 km/h zwischen Aachen und Düren.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 80 km/h zwischen Aachen und Düren.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 50 km/h südöstlich von Köln.', True, 60, {}),
    ('Böen 145 km/h allgemein; Böen 80 km/h südöstlich von Köln.', True, 60, {}),
    ('Böen 30 km/h.', False, 60, {}),
    ('Böen 30 km/h ausgeschlossen.', False, 60, {}),
    ('Böen 30 km/h nur in den Bergen.', False, 60, {}),
    ('Böen 70 km/h.', False, 60, {}),
    ('Böen 70 km/h ausgeschlossen.', False, 60, {}),
    ('Böen 70 km/h nur in den Bergen.', False, 60, {}),
    ('Böen 89 km/h.', False, 60, {}),
    ('Böen 89 km/h ausgeschlossen.', False, 60, {}),
    ('Böen 89 km/h nur in den Bergen.', False, 60, {}),
    ('Böen 90 km/h.', True, 60, {}),
    ('Böen 90 km/h ausgeschlossen.', False, 60, {}),
    ('Böen 90 km/h nur in den Bergen.', False, 60, {}),
    ('Böen 110 km/h.', True, 60, {}),
    ('Böen 110 km/h ausgeschlossen.', False, 60, {}),
    ('Böen 110 km/h nur in den Bergen.', False, 60, {}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Hagel nur auf Inseln.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Starkregen nur in der Eifel.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Gewitter nur auf Gipfeln.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Schneefall nur an der Küste.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Regen nur im Harz.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Schnee ausschließlich in den Bergen.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Windböen 70 km/h nur auf den Gipfeln.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Allgemeine Wetterwarnung.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Windböen allgemein.'}),
    ('Böen 70 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Gewitter und Böen.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Hagel nur auf Inseln.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Starkregen nur in der Eifel.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Gewitter nur auf Gipfeln.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Schneefall nur an der Küste.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Regen nur im Harz.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Schnee ausschließlich in den Bergen.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Windböen 70 km/h nur auf den Gipfeln.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Allgemeine Wetterwarnung.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Windböen allgemein.'}),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60, {'headline': 'Gewitter und Böen.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Hagel nur auf Inseln.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Starkregen nur in der Eifel.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Gewitter nur auf Gipfeln.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Schneefall nur an der Küste.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Regen nur im Harz.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Schnee ausschließlich in den Bergen.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Windböen 70 km/h nur auf den Gipfeln.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Allgemeine Wetterwarnung.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Windböen allgemein.'}),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Gewitter und Böen.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Hagel nur auf Inseln.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Starkregen nur in der Eifel.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Gewitter nur auf Gipfeln.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Schneefall nur an der Küste.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Regen nur im Harz.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Schnee ausschließlich in den Bergen.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Windböen 70 km/h nur auf den Gipfeln.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Allgemeine Wetterwarnung.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Windböen allgemein.'}),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Gewitter und Böen.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Hagel nur auf Inseln.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Starkregen nur in der Eifel.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Gewitter nur auf Gipfeln.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Schneefall nur an der Küste.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Regen nur im Harz.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Schnee ausschließlich in den Bergen.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Windböen 70 km/h nur auf den Gipfeln.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Allgemeine Wetterwarnung.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Windböen allgemein.'}),
    ('Böen 145 km/h im gesamten Warngebiet.', True, 60, {'headline': 'Gewitter und Böen.'}),
]


@pytest.mark.parametrize("text,expected,elevation,kwargs", AUDIT_CASES)
def test_independent_592_case_audit(text, expected, elevation, kwargs):
    kwargs = dict(kwargs)
    if "now" in kwargs:
        kwargs["now"] = datetime.fromisoformat(kwargs["now"])
    assert assess(text, elevation=elevation, **kwargs)["hard_lock"] is expected


@pytest.mark.parametrize("condition", ["bei Schneematsch", "bei nassem Schneematsch", "bei starker Brise", "bei starken Brisen"])
@pytest.mark.parametrize("speed", [89, 90, 110])
@pytest.mark.parametrize("field", ["description", "headline", "event", "parameter"])
def test_complete_condition_heads_do_not_replace_the_explicit_gust_quantity(condition, speed, field):
    text = f"Böen {speed} km/h {condition}."
    changes = {field: text} if field in {"headline", "event"} else {}
    params = {"gusts": text} if field == "parameter" else {}
    result = assess(text if field == "description" else "", params, **changes)
    assert result["gust_max_kmh"] == speed
    assert result["hard_lock"] is (speed >= 90)


@pytest.mark.parametrize("place", ["bei Schneematschtal", "bei Brisenheim", "bei starker Brise im Harz"])
def test_condition_morphology_keeps_real_names_and_added_places_unverified(place):
    result = assess(f"Böen 110 km/h {place}.", {"gusts": "110 km/h"})
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("text", ["Starke Brise bei 110 km/h.", "Brise 110 km/h."])
def test_a_qualitative_wind_condition_is_not_itself_a_gust_value(text):
    result = assess(text, headline="Amtliche Meldung", event="Wetter")
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


SOURCES = ["nach Ansicht der Meteorologen", "den Prognosen des Wetterdienstes zufolge",
           "entgegen älteren Vorhersagen", "nach Rückmeldung der Meteorologen", "nach unserem Kenntnisstand"]


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h sind {source} auszuschließen.", False),
    ("Böen 110 km/h sind {source} nicht auszuschließen.", True),
    ("Böen 110 km/h werden {source} nicht auftreten.", False),
    ("Böen 110 km/h sind {source} nicht wahrscheinlich.", False),
    ("Böen 110 km/h werden {source} erwartet.", True),
    ("Böen 110 km/h, Schäden werden {source} nicht erwartet.", True),
])
@pytest.mark.parametrize("field", ["description", "headline", "event", "parameter"])
def test_reported_predictions_keep_polarity_and_subject_in_every_field(source, frame, locked, field):
    text = frame.format(source=source)
    changes = {field: text} if field in {"headline", "event"} else {}
    params = {"gusts": text} if field == "parameter" else {}
    assert assess(text if field == "description" else "", params, **changes)["hard_lock"] is locked


@pytest.mark.parametrize("source", ["den Prognosen des Deutschen Wetterdienstes zufolge",
                                    "den Prognosen der Wetterbehörden zufolge", "den Prognosen der Meteorologen zufolge"])
def test_genitive_source_complements_do_not_hide_the_following_forecast_negation(source):
    result = assess(f"Böen 110 km/h treten {source} nicht auf.")
    assert not result["hard_lock"] and all(item["denied"] for item in result["gust_evidence"])


FOREIGN_HEADS = ["Hagel nur auf Inseln.", "Starkregen nur in der Eifel.", "Gewitter nur auf Gipfeln.",
                 "Schneefall nur an der Küste.", "Regen nur im Harz.", "Schnee ausschließlich in den Bergen.",
                 "Sturmflut nur an der Küste.", "Rauch nur im Harz.", "Hitzewarnung nur auf Inseln."]


@pytest.mark.parametrize("title", FOREIGN_HEADS)
@pytest.mark.parametrize("field", ["headline", "event"])
@pytest.mark.parametrize("scope", ["", " im gesamten Warngebiet"])
@pytest.mark.parametrize("params", [{}, {"gusts": "110 km/h"}])
def test_a_different_event_cannot_donate_its_region_to_wind(title, field, scope, params):
    result = assess(f"Böen 110 km/h{scope}.", params, **{field: title})
    assert result["hard_lock"] and result["gust_max_kmh"] == 110
    assert result["area_verified"] and not result["gust_scope_uncertain"]
    assert all(not item.get("scope_from_header") for item in result["gust_evidence"])


@pytest.mark.parametrize("title", ["Windböen im Harz.", "Sturmwarnung nur auf Inseln.", "Nur auf den Gipfeln."])
@pytest.mark.parametrize("field", ["headline", "event"])
def test_generic_wind_and_pure_location_headings_still_require_window_membership(title, field):
    result = assess("Böen 110 km/h.", {"gusts": "110 km/h"}, **{field: title})
    assert not result["hard_lock"] and not result["area_verified"]
    assert result["gust_scope_uncertain"]


@pytest.mark.parametrize("title,locked", [
    ("Hagel nur im Harz, Windböen im gesamten Warngebiet.", True),
    ("Windböen nur im Harz, Hagel im gesamten Warngebiet.", False),
    ("Rauch im Harz bei Wind.", True),
    ("Hagel nur im Harz, Windwarnung allgemein.", True),
    ("Windwarnung nur im Harz, Hagel allgemein.", False),
    ("Hagel nur im Harz, Sturmwarnung allgemein.", True),
    ("Sturmwarnung nur im Harz, Hagel allgemein.", False),
])
def test_mixed_headers_use_the_wind_subjects_own_context(title, locked):
    assert assess("Böen 110 km/h.", headline=title)["hard_lock"] is locked


@pytest.mark.parametrize("title", ["Hagel ab 18 Uhr UTC.", "Starkregen ab Montag.",
                                    "Hagel ab 18 Uhr UTC, Windböen allgemein.",
                                    "Hagel ab 18 Uhr UTC, Windwarnung allgemein.",
                                    "Hagel ab 18 Uhr UTC, Sturmwarnung allgemein."])
def test_another_events_time_cannot_postpone_the_wind_start(title):
    result = assess("Böen 110 km/h im gesamten Warngebiet.", headline=title)
    assert result["hard_lock"] and not result["gust_time_uncertain"] and not result["gust_time_conflict"]


@pytest.mark.parametrize("prefix", ["Rauch nur im Harz", "Hochwasser ab 18 Uhr UTC",
                                     "Erdrutsch nur in der Eifel", "Schäden im gesamten Warngebiet"])
@pytest.mark.parametrize("field", ["headline", "event", "description"])
@pytest.mark.parametrize("params", [{}, {"gusts": "110 km/h"}])
def test_independent_unknown_subjects_cannot_become_pending_wind_context(prefix, field, params):
    text = f"{prefix}, {'Böen 110 km/h' if field == 'description' else 'Windwarnung'} allgemein."
    changes = {field: text} if field != "description" else {}
    result = assess(text if field == "description" else "Böen 110 km/h im gesamten Warngebiet.", params, **changes)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110
    assert not result["gust_scope_uncertain"] and not result["gust_time_uncertain"]


@pytest.mark.parametrize("description,locked", [
    ("Im Harz, Böen 110 km/h.", False), ("Laut DWD, Böen 110 km/h.", True),
    ("Nicht erwartet: Böen 110 km/h.", False), ("Ab 18 Uhr UTC, Böen 110 km/h.", False),
    ("Allgemein, Böen 110 km/h.", True),
])
def test_true_adjuncts_and_preposed_predicates_still_complete_the_wind_claim(description, locked):
    assert assess(description)["hard_lock"] is locked


@pytest.mark.parametrize("minute,locked", [(17 * 60 + 29, False), (17 * 60 + 30, True), (18 * 60, True)])
@pytest.mark.parametrize("subject", ["Windböen", "Windwarnung", "Sturmwarnung"])
def test_a_generic_wind_time_keeps_its_own_thirty_minute_lead_in_a_combined_headline(minute, locked, subject):
    now = NOW.replace(hour=0, minute=0) + timedelta(minutes=minute)
    result = assess("Böen 110 km/h.", headline=f"Hagel nur im Harz, {subject} ab 18 Uhr UTC.", now=now)
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("field", ["headline", "event"])
@pytest.mark.parametrize("scope,locked", [("", False), (" allgemein", True), (" im gesamten Warngebiet", True)])
@pytest.mark.parametrize("params", [{}, {"gusts": "70 km/h"}, {"gusts": "110 km/h"}])
def test_a_numeric_local_header_does_not_overwrite_an_independent_general_forecast(field, scope, locked, params):
    result = assess(f"Böen 110 km/h{scope}.", params, **{field: "Windböen 70 km/h nur auf den Gipfeln."})
    assert result["hard_lock"] is locked
    if locked:
        assert result["gust_max_kmh"] == 110
        assert any(item["max"] == 110 and item["location_verified"] for item in result["gust_evidence"])
    assert any(item["max"] == 70 and not item["location_verified"] for item in result["gust_evidence"])
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("field", ["headline", "event"])
@pytest.mark.parametrize("scope,locked", [("", False), (" allgemein", True), (" im gesamten Warngebiet", True)])
def test_a_matching_header_only_supplies_missing_spatial_context(field, scope, locked):
    result = assess(f"Böen 110 km/h{scope}.", **{field: "Böen 110 km/h nur im Harz."})
    assert result["hard_lock"] is locked
    assert result["gust_scope_uncertain"]


@pytest.mark.parametrize("description,locked", [
    ("Böen 110 km/h mit Schäden im gesamten Warngebiet.", False),
    ("Böen 110 km/h mit Schäden allgemein.", False),
    ("Böen 110 km/h ohne Niederschlag im gesamten Warngebiet.", False),
    ("Böen 110 km/h im gesamten Warngebiet mit Schäden.", True),
    ("Böen 110 km/h allgemein mit Schäden.", True),
])
@pytest.mark.parametrize("params", [{}, {"gusts": "110 km/h"}])
def test_general_coverage_of_a_consequence_cannot_supply_the_gusts_missing_scope(description, locked, params):
    result = assess(description, params, headline="Böen 110 km/h nur im Harz.")
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("height,locked", [(60, False), (1200, True)])
def test_numeric_height_scope_is_shared_only_with_the_same_unqualified_wind_quantity(height, locked):
    result = assess(parameters={"gusts": "110 km/h"}, headline="Böen 110 km/h oberhalb 1000 m.", elevation=height)
    assert result["hard_lock"] is locked
    param = next(item for item in result["gust_evidence"] if item["source"] == "parameter")
    assert param["location_explicit"] and param["location_verified"] is locked


def test_unknown_shared_cap_area_cannot_be_overridden_by_event_separation():
    result = assess("Böen 110 km/h im gesamten Warngebiet.", headline="Hagel nur auf Inseln.", area_restriction_unknown=True)
    assert not result["hard_lock"] and not result["area_verified"]


def test_other_hazards_do_not_clear_a_wind_polarity_conflict_between_fields():
    result = assess("Böen 110 km/h ausgeschlossen.", headline="Hagel nur im Harz; Böen 110 km/h erwartet.")
    assert result["gust_polarity_conflict"] and result["gust_conflict"]


def test_explicit_closing_instructions_keep_their_existing_message_area_check():
    result = policy.assess_official_warning(warning(headline="Rauch nur im Harz.", description="Fenster schließen."),
                                            NOW, explicit_close=True, elevation=60)
    assert not result["hard_lock"] and not result["area_verified"]
