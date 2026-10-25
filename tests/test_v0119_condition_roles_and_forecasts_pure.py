"""Warning constituents: conditions, dimensions, agents and forecast polarity.

The independent audit's 393 inputs and expectations are retained verbatim.
Additional counterpairs test the meaning across fields and combinations; these
are deliberate regression scenarios, not a real-world error-rate estimate.
"""
from datetime import timedelta
import json
import operator

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


AUDIT_CASES = [
    ('Böen 40 km/h bei feuchten Straßen.', False, 60),
    ('Böen 40 km/h bei winterlichen Bedingungen.', False, 60),
    ('Böen 40 km/h bei Temperaturen um den Gefrierpunkt.', False, 60),
    ('Böen 40 km/h bei gefrorenem Boden.', False, 60),
    ('Böen 40 km/h bei starker Bewölkung.', False, 60),
    ('Böen 40 km/h bei anhaltender Trockenheit.', False, 60),
    ('Böen 40 km/h bei extremer Hitze.', False, 60),
    ('Böen 40 km/h bei gefährlicher Glätte.', False, 60),
    ('Böen 40 km/h bei klarem Himmel.', False, 60),
    ('Böen 40 km/h bei wolkigem Wetter.', False, 60),
    ('Böen 40 km/h bei starkem Regen.', False, 60),
    ('Böen 40 km/h bei Sturm und Regen.', False, 60),
    ('Böen 40 km/h bei geschlossener Wolkendecke.', False, 60),
    ('Böen 40 km/h bei wechselhaften Bedingungen.', False, 60),
    ('Böen 40 km/h bei erhöhten Temperaturen.', False, 60),
    ('Böen 40 km/h bei frostiger Witterung.', False, 60),
    ('Böen 69 km/h bei feuchten Straßen.', False, 60),
    ('Böen 69 km/h bei winterlichen Bedingungen.', False, 60),
    ('Böen 69 km/h bei Temperaturen um den Gefrierpunkt.', False, 60),
    ('Böen 69 km/h bei gefrorenem Boden.', False, 60),
    ('Böen 69 km/h bei starker Bewölkung.', False, 60),
    ('Böen 69 km/h bei anhaltender Trockenheit.', False, 60),
    ('Böen 69 km/h bei extremer Hitze.', False, 60),
    ('Böen 69 km/h bei gefährlicher Glätte.', False, 60),
    ('Böen 69 km/h bei klarem Himmel.', False, 60),
    ('Böen 69 km/h bei wolkigem Wetter.', False, 60),
    ('Böen 69 km/h bei starkem Regen.', False, 60),
    ('Böen 69 km/h bei Sturm und Regen.', False, 60),
    ('Böen 69 km/h bei geschlossener Wolkendecke.', False, 60),
    ('Böen 69 km/h bei wechselhaften Bedingungen.', False, 60),
    ('Böen 69 km/h bei erhöhten Temperaturen.', False, 60),
    ('Böen 69 km/h bei frostiger Witterung.', False, 60),
    ('Böen 89 km/h bei feuchten Straßen.', False, 60),
    ('Böen 89 km/h bei winterlichen Bedingungen.', False, 60),
    ('Böen 89 km/h bei Temperaturen um den Gefrierpunkt.', False, 60),
    ('Böen 89 km/h bei gefrorenem Boden.', False, 60),
    ('Böen 89 km/h bei starker Bewölkung.', False, 60),
    ('Böen 89 km/h bei anhaltender Trockenheit.', False, 60),
    ('Böen 89 km/h bei extremer Hitze.', False, 60),
    ('Böen 89 km/h bei gefährlicher Glätte.', False, 60),
    ('Böen 89 km/h bei klarem Himmel.', False, 60),
    ('Böen 89 km/h bei wolkigem Wetter.', False, 60),
    ('Böen 89 km/h bei starkem Regen.', False, 60),
    ('Böen 89 km/h bei Sturm und Regen.', False, 60),
    ('Böen 89 km/h bei geschlossener Wolkendecke.', False, 60),
    ('Böen 89 km/h bei wechselhaften Bedingungen.', False, 60),
    ('Böen 89 km/h bei erhöhten Temperaturen.', False, 60),
    ('Böen 89 km/h bei frostiger Witterung.', False, 60),
    ('Böen 90 km/h bei feuchten Straßen.', True, 60),
    ('Böen 90 km/h bei winterlichen Bedingungen.', True, 60),
    ('Böen 90 km/h bei Temperaturen um den Gefrierpunkt.', True, 60),
    ('Böen 90 km/h bei gefrorenem Boden.', True, 60),
    ('Böen 90 km/h bei starker Bewölkung.', True, 60),
    ('Böen 90 km/h bei anhaltender Trockenheit.', True, 60),
    ('Böen 90 km/h bei extremer Hitze.', True, 60),
    ('Böen 90 km/h bei gefährlicher Glätte.', True, 60),
    ('Böen 90 km/h bei klarem Himmel.', True, 60),
    ('Böen 90 km/h bei wolkigem Wetter.', True, 60),
    ('Böen 90 km/h bei starkem Regen.', True, 60),
    ('Böen 90 km/h bei Sturm und Regen.', True, 60),
    ('Böen 90 km/h bei geschlossener Wolkendecke.', True, 60),
    ('Böen 90 km/h bei wechselhaften Bedingungen.', True, 60),
    ('Böen 90 km/h bei erhöhten Temperaturen.', True, 60),
    ('Böen 90 km/h bei frostiger Witterung.', True, 60),
    ('Böen 91 km/h bei feuchten Straßen.', True, 60),
    ('Böen 91 km/h bei winterlichen Bedingungen.', True, 60),
    ('Böen 91 km/h bei Temperaturen um den Gefrierpunkt.', True, 60),
    ('Böen 91 km/h bei gefrorenem Boden.', True, 60),
    ('Böen 91 km/h bei starker Bewölkung.', True, 60),
    ('Böen 91 km/h bei anhaltender Trockenheit.', True, 60),
    ('Böen 91 km/h bei extremer Hitze.', True, 60),
    ('Böen 91 km/h bei gefährlicher Glätte.', True, 60),
    ('Böen 91 km/h bei klarem Himmel.', True, 60),
    ('Böen 91 km/h bei wolkigem Wetter.', True, 60),
    ('Böen 91 km/h bei starkem Regen.', True, 60),
    ('Böen 91 km/h bei Sturm und Regen.', True, 60),
    ('Böen 91 km/h bei geschlossener Wolkendecke.', True, 60),
    ('Böen 91 km/h bei wechselhaften Bedingungen.', True, 60),
    ('Böen 91 km/h bei erhöhten Temperaturen.', True, 60),
    ('Böen 91 km/h bei frostiger Witterung.', True, 60),
    ('Böen 110 km/h bei feuchten Straßen.', True, 60),
    ('Böen 110 km/h bei winterlichen Bedingungen.', True, 60),
    ('Böen 110 km/h bei Temperaturen um den Gefrierpunkt.', True, 60),
    ('Böen 110 km/h bei gefrorenem Boden.', True, 60),
    ('Böen 110 km/h bei starker Bewölkung.', True, 60),
    ('Böen 110 km/h bei anhaltender Trockenheit.', True, 60),
    ('Böen 110 km/h bei extremer Hitze.', True, 60),
    ('Böen 110 km/h bei gefährlicher Glätte.', True, 60),
    ('Böen 110 km/h bei klarem Himmel.', True, 60),
    ('Böen 110 km/h bei wolkigem Wetter.', True, 60),
    ('Böen 110 km/h bei starkem Regen.', True, 60),
    ('Böen 110 km/h bei Sturm und Regen.', True, 60),
    ('Böen 110 km/h bei geschlossener Wolkendecke.', True, 60),
    ('Böen 110 km/h bei wechselhaften Bedingungen.', True, 60),
    ('Böen 110 km/h bei erhöhten Temperaturen.', True, 60),
    ('Böen 110 km/h bei frostiger Witterung.', True, 60),
    ('Böen 135 km/h bei feuchten Straßen.', True, 60),
    ('Böen 135 km/h bei winterlichen Bedingungen.', True, 60),
    ('Böen 135 km/h bei Temperaturen um den Gefrierpunkt.', True, 60),
    ('Böen 135 km/h bei gefrorenem Boden.', True, 60),
    ('Böen 135 km/h bei starker Bewölkung.', True, 60),
    ('Böen 135 km/h bei anhaltender Trockenheit.', True, 60),
    ('Böen 135 km/h bei extremer Hitze.', True, 60),
    ('Böen 135 km/h bei gefährlicher Glätte.', True, 60),
    ('Böen 135 km/h bei klarem Himmel.', True, 60),
    ('Böen 135 km/h bei wolkigem Wetter.', True, 60),
    ('Böen 135 km/h bei starkem Regen.', True, 60),
    ('Böen 135 km/h bei Sturm und Regen.', True, 60),
    ('Böen 135 km/h bei geschlossener Wolkendecke.', True, 60),
    ('Böen 135 km/h bei wechselhaften Bedingungen.', True, 60),
    ('Böen 135 km/h bei erhöhten Temperaturen.', True, 60),
    ('Böen 135 km/h bei frostiger Witterung.', True, 60),
    ('Böen 40 km/h im gesamten Warngebiet.', False, 60),
    ('Böen 40 km/h im gesamten amtlichen Warngebiet.', False, 60),
    ('Böen 40 km/h überall in diesem Warngebiet.', False, 60),
    ('Böen 40 km/h überall im Warngebiet.', False, 60),
    ('Böen 40 km/h im kompletten Warngebiet.', False, 60),
    ('Böen 40 km/h im ganzen offiziellen Warngebiet.', False, 60),
    ('Böen 40 km/h in jedem Teil des betroffenen Warngebiets.', False, 60),
    ('Böen 40 km/h in allen Teilen des Warngebiets.', False, 60),
    ('Böen 89 km/h im gesamten Warngebiet.', False, 60),
    ('Böen 89 km/h im gesamten amtlichen Warngebiet.', False, 60),
    ('Böen 89 km/h überall in diesem Warngebiet.', False, 60),
    ('Böen 89 km/h überall im Warngebiet.', False, 60),
    ('Böen 89 km/h im kompletten Warngebiet.', False, 60),
    ('Böen 89 km/h im ganzen offiziellen Warngebiet.', False, 60),
    ('Böen 89 km/h in jedem Teil des betroffenen Warngebiets.', False, 60),
    ('Böen 89 km/h in allen Teilen des Warngebiets.', False, 60),
    ('Böen 90 km/h im gesamten Warngebiet.', True, 60),
    ('Böen 90 km/h im gesamten amtlichen Warngebiet.', True, 60),
    ('Böen 90 km/h überall in diesem Warngebiet.', True, 60),
    ('Böen 90 km/h überall im Warngebiet.', True, 60),
    ('Böen 90 km/h im kompletten Warngebiet.', True, 60),
    ('Böen 90 km/h im ganzen offiziellen Warngebiet.', True, 60),
    ('Böen 90 km/h in jedem Teil des betroffenen Warngebiets.', True, 60),
    ('Böen 90 km/h in allen Teilen des Warngebiets.', True, 60),
    ('Böen 110 km/h im gesamten Warngebiet.', True, 60),
    ('Böen 110 km/h im gesamten amtlichen Warngebiet.', True, 60),
    ('Böen 110 km/h überall in diesem Warngebiet.', True, 60),
    ('Böen 110 km/h überall im Warngebiet.', True, 60),
    ('Böen 110 km/h im kompletten Warngebiet.', True, 60),
    ('Böen 110 km/h im ganzen offiziellen Warngebiet.', True, 60),
    ('Böen 110 km/h in jedem Teil des betroffenen Warngebiets.', True, 60),
    ('Böen 110 km/h in allen Teilen des Warngebiets.', True, 60),
    ('Böen 135 km/h im gesamten Warngebiet.', True, 60),
    ('Böen 135 km/h im gesamten amtlichen Warngebiet.', True, 60),
    ('Böen 135 km/h überall in diesem Warngebiet.', True, 60),
    ('Böen 135 km/h überall im Warngebiet.', True, 60),
    ('Böen 135 km/h im kompletten Warngebiet.', True, 60),
    ('Böen 135 km/h im ganzen offiziellen Warngebiet.', True, 60),
    ('Böen 135 km/h in jedem Teil des betroffenen Warngebiets.', True, 60),
    ('Böen 135 km/h in allen Teilen des Warngebiets.', True, 60),
    ('Böen 90 km/h zwischen Bonn und Köln.', False, 60),
    ('Böen 90 km/h von Köln bis Bonn.', False, 60),
    ('Böen 90 km/h nur im Norden.', False, 60),
    ('Böen 90 km/h am östlichen Stadtrand.', False, 60),
    ('Böen 90 km/h nahe der belgischen Grenze.', False, 60),
    ('Böen 90 km/h rund um Köln.', False, 60),
    ('Böen 90 km/h auf den Anhöhen der Eifel.', False, 60),
    ('Böen 90 km/h im gesamten Warngebiet außer in Tallagen.', False, 60),
    ('Böen 110 km/h zwischen Bonn und Köln.', False, 60),
    ('Böen 110 km/h von Köln bis Bonn.', False, 60),
    ('Böen 110 km/h nur im Norden.', False, 60),
    ('Böen 110 km/h am östlichen Stadtrand.', False, 60),
    ('Böen 110 km/h nahe der belgischen Grenze.', False, 60),
    ('Böen 110 km/h rund um Köln.', False, 60),
    ('Böen 110 km/h auf den Anhöhen der Eifel.', False, 60),
    ('Böen 110 km/h im gesamten Warngebiet außer in Tallagen.', False, 60),
    ('Böen 135 km/h zwischen Bonn und Köln.', False, 60),
    ('Böen 135 km/h von Köln bis Bonn.', False, 60),
    ('Böen 135 km/h nur im Norden.', False, 60),
    ('Böen 135 km/h am östlichen Stadtrand.', False, 60),
    ('Böen 135 km/h nahe der belgischen Grenze.', False, 60),
    ('Böen 135 km/h rund um Köln.', False, 60),
    ('Böen 135 km/h auf den Anhöhen der Eifel.', False, 60),
    ('Böen 135 km/h im gesamten Warngebiet außer in Tallagen.', False, 60),
    ('Böen 70 km/h werden auf keinen Fall erwartet.', False, 60),
    ('Böen 70 km/h treten unter keinen Umständen auf.', False, 60),
    ('Böen 70 km/h sind nicht mehr zu erwarten.', False, 60),
    ('Böen 70 km/h werden keineswegs eintreten.', False, 60),
    ('Böen 70 km/h sind mit Sicherheit nicht zu erwarten.', False, 60),
    ('Böen 70 km/h sind laut aktuellen Meldungen nicht zu erwarten.', False, 60),
    ('Böen 70 km/h werden durch den Wetterdienst ausgeschlossen.', False, 60),
    ('Böen 70 km/h fallen nach derzeitigem Stand aus.', False, 60),
    ('Böen 70 km/h werden ausdrücklich ausgeschlossen.', False, 60),
    ('Böen 89 km/h werden auf keinen Fall erwartet.', False, 60),
    ('Böen 89 km/h treten unter keinen Umständen auf.', False, 60),
    ('Böen 89 km/h sind nicht mehr zu erwarten.', False, 60),
    ('Böen 89 km/h werden keineswegs eintreten.', False, 60),
    ('Böen 89 km/h sind mit Sicherheit nicht zu erwarten.', False, 60),
    ('Böen 89 km/h sind laut aktuellen Meldungen nicht zu erwarten.', False, 60),
    ('Böen 89 km/h werden durch den Wetterdienst ausgeschlossen.', False, 60),
    ('Böen 89 km/h fallen nach derzeitigem Stand aus.', False, 60),
    ('Böen 89 km/h werden ausdrücklich ausgeschlossen.', False, 60),
    ('Böen 90 km/h werden auf keinen Fall erwartet.', False, 60),
    ('Böen 90 km/h treten unter keinen Umständen auf.', False, 60),
    ('Böen 90 km/h sind nicht mehr zu erwarten.', False, 60),
    ('Böen 90 km/h werden keineswegs eintreten.', False, 60),
    ('Böen 90 km/h sind mit Sicherheit nicht zu erwarten.', False, 60),
    ('Böen 90 km/h sind laut aktuellen Meldungen nicht zu erwarten.', False, 60),
    ('Böen 90 km/h werden durch den Wetterdienst ausgeschlossen.', False, 60),
    ('Böen 90 km/h fallen nach derzeitigem Stand aus.', False, 60),
    ('Böen 90 km/h werden ausdrücklich ausgeschlossen.', False, 60),
    ('Böen 110 km/h werden auf keinen Fall erwartet.', False, 60),
    ('Böen 110 km/h treten unter keinen Umständen auf.', False, 60),
    ('Böen 110 km/h sind nicht mehr zu erwarten.', False, 60),
    ('Böen 110 km/h werden keineswegs eintreten.', False, 60),
    ('Böen 110 km/h sind mit Sicherheit nicht zu erwarten.', False, 60),
    ('Böen 110 km/h sind laut aktuellen Meldungen nicht zu erwarten.', False, 60),
    ('Böen 110 km/h werden durch den Wetterdienst ausgeschlossen.', False, 60),
    ('Böen 110 km/h fallen nach derzeitigem Stand aus.', False, 60),
    ('Böen 110 km/h werden ausdrücklich ausgeschlossen.', False, 60),
    ('Böen 140 km/h werden auf keinen Fall erwartet.', False, 60),
    ('Böen 140 km/h treten unter keinen Umständen auf.', False, 60),
    ('Böen 140 km/h sind nicht mehr zu erwarten.', False, 60),
    ('Böen 140 km/h werden keineswegs eintreten.', False, 60),
    ('Böen 140 km/h sind mit Sicherheit nicht zu erwarten.', False, 60),
    ('Böen 140 km/h sind laut aktuellen Meldungen nicht zu erwarten.', False, 60),
    ('Böen 140 km/h werden durch den Wetterdienst ausgeschlossen.', False, 60),
    ('Böen 140 km/h fallen nach derzeitigem Stand aus.', False, 60),
    ('Böen 140 km/h werden ausdrücklich ausgeschlossen.', False, 60),
    ('Non si prevedono raffiche di vento di 90 km/h.', False, 60),
    ('Gusts of 90 km/h are not expected.', False, 60),
    ('No se esperan rachas de viento de 90 km/h.', False, 60),
    ('Rafales de vent à 90 km/h ne sont pas attendues.', False, 60),
    ('Non si prevedono raffiche di vento di 110 km/h.', False, 60),
    ('Gusts of 110 km/h are not expected.', False, 60),
    ('No se esperan rachas de viento de 110 km/h.', False, 60),
    ('Rafales de vent à 110 km/h ne sont pas attendues.', False, 60),
    ('Non si prevedono raffiche di vento di 135 km/h.', False, 60),
    ('Gusts of 135 km/h are not expected.', False, 60),
    ('No se esperan rachas de viento de 135 km/h.', False, 60),
    ('Rafales de vent à 135 km/h ne sont pas attendues.', False, 60),
    ('Windböen bis zu 50 Stundenkilometern.', False, 60),
    ('Windböen bis zu 50 km/h.', False, 60),
    ('Windböen bis zu 50 Kilometer je Stunde.', False, 60),
    ('Windböen von 50 km/h.', False, 60),
    ('Windböen bis zu 89 Stundenkilometern.', False, 60),
    ('Windböen bis zu 89 km/h.', False, 60),
    ('Windböen bis zu 89 Kilometer je Stunde.', False, 60),
    ('Windböen von 89 km/h.', False, 60),
    ('Windböen bis zu 90 Stundenkilometern.', True, 60),
    ('Windböen bis zu 90 km/h.', True, 60),
    ('Windböen bis zu 90 Kilometer je Stunde.', True, 60),
    ('Windböen von 90 km/h.', True, 60),
    ('Windböen bis zu 110 Stundenkilometern.', True, 60),
    ('Windböen bis zu 110 km/h.', True, 60),
    ('Windböen bis zu 110 Kilometer je Stunde.', True, 60),
    ('Windböen von 110 km/h.', True, 60),
    ('Windböen bis zu 140 Stundenkilometern.', True, 60),
    ('Windböen bis zu 140 km/h.', True, 60),
    ('Windböen bis zu 140 Kilometer je Stunde.', True, 60),
    ('Windböen von 140 km/h.', True, 60),
    ('Böen 70 km/h oberhalb von 1200 m.', False, 60),
    ('Böen 70 km/h oberhalb von 1200 m.', False, 1000),
    ('Böen 70 km/h oberhalb von 1200 m.', False, 1500),
    ('Böen 70 km/h ab einer Höhenlage von 1200 Metern.', False, 60),
    ('Böen 70 km/h ab einer Höhenlage von 1200 Metern.', False, 1000),
    ('Böen 70 km/h ab einer Höhenlage von 1200 Metern.', False, 1500),
    ('Böen 70 km/h über 1.200 m über NN.', False, 60),
    ('Böen 70 km/h über 1.200 m über NN.', False, 1000),
    ('Böen 70 km/h über 1.200 m über NN.', False, 1500),
    ('Böen 70 km/h nur oberhalb 1.200 m ü. NN.', False, 60),
    ('Böen 70 km/h nur oberhalb 1.200 m ü. NN.', False, 1000),
    ('Böen 70 km/h nur oberhalb 1.200 m ü. NN.', False, 1500),
    ('Böen 70 km/h über 1 200 Metern.', False, 60),
    ('Böen 70 km/h über 1 200 Metern.', False, 1000),
    ('Böen 70 km/h über 1 200 Metern.', False, 1500),
    ('Böen 70 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 60),
    ('Böen 70 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 1000),
    ('Böen 70 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 1500),
    ('Böen 70 km/h ab 1.200 m Höhe.', False, 60),
    ('Böen 70 km/h ab 1.200 m Höhe.', False, 1000),
    ('Böen 70 km/h ab 1.200 m Höhe.', False, 1500),
    ('Böen 70 km/h nur in Lagen ab 1200 Metern.', False, 60),
    ('Böen 70 km/h nur in Lagen ab 1200 Metern.', False, 1000),
    ('Böen 70 km/h nur in Lagen ab 1200 Metern.', False, 1500),
    ('Böen 89 km/h oberhalb von 1200 m.', False, 60),
    ('Böen 89 km/h oberhalb von 1200 m.', False, 1000),
    ('Böen 89 km/h oberhalb von 1200 m.', False, 1500),
    ('Böen 89 km/h ab einer Höhenlage von 1200 Metern.', False, 60),
    ('Böen 89 km/h ab einer Höhenlage von 1200 Metern.', False, 1000),
    ('Böen 89 km/h ab einer Höhenlage von 1200 Metern.', False, 1500),
    ('Böen 89 km/h über 1.200 m über NN.', False, 60),
    ('Böen 89 km/h über 1.200 m über NN.', False, 1000),
    ('Böen 89 km/h über 1.200 m über NN.', False, 1500),
    ('Böen 89 km/h nur oberhalb 1.200 m ü. NN.', False, 60),
    ('Böen 89 km/h nur oberhalb 1.200 m ü. NN.', False, 1000),
    ('Böen 89 km/h nur oberhalb 1.200 m ü. NN.', False, 1500),
    ('Böen 89 km/h über 1 200 Metern.', False, 60),
    ('Böen 89 km/h über 1 200 Metern.', False, 1000),
    ('Böen 89 km/h über 1 200 Metern.', False, 1500),
    ('Böen 89 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 60),
    ('Böen 89 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 1000),
    ('Böen 89 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 1500),
    ('Böen 89 km/h ab 1.200 m Höhe.', False, 60),
    ('Böen 89 km/h ab 1.200 m Höhe.', False, 1000),
    ('Böen 89 km/h ab 1.200 m Höhe.', False, 1500),
    ('Böen 89 km/h nur in Lagen ab 1200 Metern.', False, 60),
    ('Böen 89 km/h nur in Lagen ab 1200 Metern.', False, 1000),
    ('Böen 89 km/h nur in Lagen ab 1200 Metern.', False, 1500),
    ('Böen 90 km/h oberhalb von 1200 m.', False, 60),
    ('Böen 90 km/h oberhalb von 1200 m.', False, 1000),
    ('Böen 90 km/h oberhalb von 1200 m.', True, 1500),
    ('Böen 90 km/h ab einer Höhenlage von 1200 Metern.', False, 60),
    ('Böen 90 km/h ab einer Höhenlage von 1200 Metern.', False, 1000),
    ('Böen 90 km/h ab einer Höhenlage von 1200 Metern.', True, 1500),
    ('Böen 90 km/h über 1.200 m über NN.', False, 60),
    ('Böen 90 km/h über 1.200 m über NN.', False, 1000),
    ('Böen 90 km/h über 1.200 m über NN.', True, 1500),
    ('Böen 90 km/h nur oberhalb 1.200 m ü. NN.', False, 60),
    ('Böen 90 km/h nur oberhalb 1.200 m ü. NN.', False, 1000),
    ('Böen 90 km/h nur oberhalb 1.200 m ü. NN.', True, 1500),
    ('Böen 90 km/h über 1 200 Metern.', False, 60),
    ('Böen 90 km/h über 1 200 Metern.', False, 1000),
    ('Böen 90 km/h über 1 200 Metern.', True, 1500),
    ('Böen 90 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 60),
    ('Böen 90 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 1000),
    ('Böen 90 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', True, 1500),
    ('Böen 90 km/h ab 1.200 m Höhe.', False, 60),
    ('Böen 90 km/h ab 1.200 m Höhe.', False, 1000),
    ('Böen 90 km/h ab 1.200 m Höhe.', True, 1500),
    ('Böen 90 km/h nur in Lagen ab 1200 Metern.', False, 60),
    ('Böen 90 km/h nur in Lagen ab 1200 Metern.', False, 1000),
    ('Böen 90 km/h nur in Lagen ab 1200 Metern.', True, 1500),
    ('Böen 110 km/h oberhalb von 1200 m.', False, 60),
    ('Böen 110 km/h oberhalb von 1200 m.', False, 1000),
    ('Böen 110 km/h oberhalb von 1200 m.', True, 1500),
    ('Böen 110 km/h ab einer Höhenlage von 1200 Metern.', False, 60),
    ('Böen 110 km/h ab einer Höhenlage von 1200 Metern.', False, 1000),
    ('Böen 110 km/h ab einer Höhenlage von 1200 Metern.', True, 1500),
    ('Böen 110 km/h über 1.200 m über NN.', False, 60),
    ('Böen 110 km/h über 1.200 m über NN.', False, 1000),
    ('Böen 110 km/h über 1.200 m über NN.', True, 1500),
    ('Böen 110 km/h nur oberhalb 1.200 m ü. NN.', False, 60),
    ('Böen 110 km/h nur oberhalb 1.200 m ü. NN.', False, 1000),
    ('Böen 110 km/h nur oberhalb 1.200 m ü. NN.', True, 1500),
    ('Böen 110 km/h über 1 200 Metern.', False, 60),
    ('Böen 110 km/h über 1 200 Metern.', False, 1000),
    ('Böen 110 km/h über 1 200 Metern.', True, 1500),
    ('Böen 110 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 60),
    ('Böen 110 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 1000),
    ('Böen 110 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', True, 1500),
    ('Böen 110 km/h ab 1.200 m Höhe.', False, 60),
    ('Böen 110 km/h ab 1.200 m Höhe.', False, 1000),
    ('Böen 110 km/h ab 1.200 m Höhe.', True, 1500),
    ('Böen 110 km/h nur in Lagen ab 1200 Metern.', False, 60),
    ('Böen 110 km/h nur in Lagen ab 1200 Metern.', False, 1000),
    ('Böen 110 km/h nur in Lagen ab 1200 Metern.', True, 1500),
    ('Böen 135 km/h oberhalb von 1200 m.', False, 60),
    ('Böen 135 km/h oberhalb von 1200 m.', False, 1000),
    ('Böen 135 km/h oberhalb von 1200 m.', True, 1500),
    ('Böen 135 km/h ab einer Höhenlage von 1200 Metern.', False, 60),
    ('Böen 135 km/h ab einer Höhenlage von 1200 Metern.', False, 1000),
    ('Böen 135 km/h ab einer Höhenlage von 1200 Metern.', True, 1500),
    ('Böen 135 km/h über 1.200 m über NN.', False, 60),
    ('Böen 135 km/h über 1.200 m über NN.', False, 1000),
    ('Böen 135 km/h über 1.200 m über NN.', True, 1500),
    ('Böen 135 km/h nur oberhalb 1.200 m ü. NN.', False, 60),
    ('Böen 135 km/h nur oberhalb 1.200 m ü. NN.', False, 1000),
    ('Böen 135 km/h nur oberhalb 1.200 m ü. NN.', True, 1500),
    ('Böen 135 km/h über 1 200 Metern.', False, 60),
    ('Böen 135 km/h über 1 200 Metern.', False, 1000),
    ('Böen 135 km/h über 1 200 Metern.', True, 1500),
    ('Böen 135 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 60),
    ('Böen 135 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', False, 1000),
    ('Böen 135 km/h oberhalb einer Höhe von 1.200 m über dem Meeresspiegel.', True, 1500),
    ('Böen 135 km/h ab 1.200 m Höhe.', False, 60),
    ('Böen 135 km/h ab 1.200 m Höhe.', False, 1000),
    ('Böen 135 km/h ab 1.200 m Höhe.', True, 1500),
    ('Böen 135 km/h nur in Lagen ab 1200 Metern.', False, 60),
    ('Böen 135 km/h nur in Lagen ab 1200 Metern.', False, 1000),
    ('Böen 135 km/h nur in Lagen ab 1200 Metern.', True, 1500),
    ('Böen 40 km/h ohne Hagel.', False, 60),
    ('Böen 40 km/h sind nicht auszuschließen.', False, 60),
    ('Böen 40 km/h bei Regen.', False, 60),
    ('Mittelwind 40 km/h, Böen 70 km/h.', False, 60),
    ('Böen 89 km/h ohne Hagel.', False, 60),
    ('Böen 89 km/h sind nicht auszuschließen.', False, 60),
    ('Böen 89 km/h bei Regen.', False, 60),
    ('Mittelwind 89 km/h, Böen 70 km/h.', False, 60),
    ('Böen 90 km/h ohne Hagel.', True, 60),
    ('Böen 90 km/h sind nicht auszuschließen.', True, 60),
    ('Böen 90 km/h bei Regen.', True, 60),
    ('Mittelwind 90 km/h, Böen 70 km/h.', False, 60),
    ('Böen 110 km/h ohne Hagel.', True, 60),
    ('Böen 110 km/h sind nicht auszuschließen.', True, 60),
    ('Böen 110 km/h bei Regen.', True, 60),
    ('Mittelwind 110 km/h, Böen 70 km/h.', False, 60),
    ('Böen 135 km/h ohne Hagel.', True, 60),
    ('Böen 135 km/h sind nicht auszuschließen.', True, 60),
    ('Böen 135 km/h bei Regen.', True, 60),
    ('Mittelwind 135 km/h, Böen 70 km/h.', False, 60),
]


@pytest.mark.parametrize("text,expected,elevation", AUDIT_CASES)
def test_independent_393_case_audit(text, expected, elevation):
    assert assess(text, elevation=elevation)["hard_lock"] is expected


CONDITIONS = [
    "bei winterlichen Bedingungen", "bei wechselhaften Bedingungen",
    "bei feuchten Straßen", "bei gefrorenem Boden", "bei starker Bewölkung",
    "bei anhaltender Trockenheit", "bei extremer Hitze", "bei gefährlicher Glätte",
    "bei geschlossener Wolkendecke", "bei Temperaturen um den Gefrierpunkt",
    "bei Sturm und Regen", "bei Eisregen und Glatteis",
]


@pytest.mark.parametrize("condition", CONDITIONS)
@pytest.mark.parametrize("separator", [" ", ", "])
@pytest.mark.parametrize("tail,locked", [
    (" werden erwartet.", True), (" sind nicht zu erwarten.", False),
    (" sind nicht ausgeschlossen.", True), (", Schäden sind nicht zu erwarten.", True),
])
def test_a_complete_weather_constituent_keeps_the_gust_predicate(condition, separator, tail, locked):
    result = assess(f"Böen 110 km/h{separator}{condition}{tail}")
    assert result["hard_lock"] is locked
    assert any(condition in item["weather_conditions"] for item in result["gust_evidence"])
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("condition", CONDITIONS)
@pytest.mark.parametrize("place", ["in der Eifel", "bei Neudorf", "zwischen Köln und Bonn"])
@pytest.mark.parametrize("separator", [" ", ", "])
def test_a_weather_condition_cannot_erase_an_added_place(condition, place, separator):
    result = assess(f"Böen 110 km/h{separator}{condition} {place}.", {"gusts": "110 km/h"})
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("place", [
    "bei Winterlingen", "bei Bedingungenstadt", "bei Regenwaldstadt",
    "bei Hitzehausen", "bei Boden", "bei Straßen", "bei Glättebach",
])
def test_unknown_names_and_bare_terrain_are_not_guessed_to_be_conditions(place):
    result = assess(f"Böen 110 km/h {place}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("field", ["description", "headline", "event", "parameter"])
@pytest.mark.parametrize("text,locked", [
    ("Böen 110 km/h bei winterlichen Bedingungen.", True),
    ("Böen 110 km/h überall in diesem Warngebiet.", True),
    ("Böen 110 km/h werden durch den Wetterdienst ausgeschlossen.", False),
    ("Non si prevedono raffiche di vento di 110 km/h.", False),
    ("Windböen bis zu 110 Stundenkilometern.", True),
])
def test_shared_meaning_is_used_in_every_warning_field(field, text, locked):
    changes = {field: text} if field in {"headline", "event"} else {}
    parameters = {"gusts": text} if field == "parameter" else {}
    result = assess(text if field == "description" else "", parameters, **changes)
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("area", [
    "überall in diesem Warngebiet", "überall innerhalb dieses Warngebiets",
    "in allen Teilen dieses Warngebiets", "im gesamten betroffenen Warngebiet",
])
@pytest.mark.parametrize("suffix,locked", [
    ("", True), (" mit Ausnahme der Tallagen", False),
    (" außer im Norden", False), (" nur nicht in der Eifel", False),
])
def test_demonstrative_whole_area_coverage_retains_its_exceptions(area, suffix, locked):
    result = assess(f"Böen 110 km/h {area}{suffix}.")
    assert result["hard_lock"] is locked
    assert result["gust_scope_uncertain"] is (not locked)


@pytest.mark.parametrize("area", [
    "nicht überall in diesem Warngebiet", "fast überall in diesem Warngebiet",
    "überall in diesem Warngebiet der Eifel", "in diesem Warngebiet nur im Norden",
])
def test_partial_negated_or_named_area_is_not_confirmed(area):
    result = assess(f"Böen 110 km/h {area}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("noun", ["Höhe", "Höhenlage"])
@pytest.mark.parametrize("relation,compare", [("ab", operator.ge), ("oberhalb", operator.gt),
                                             ("bis", operator.le), ("unterhalb", operator.lt)])
@pytest.mark.parametrize("height", [60, 1199.99, 1200, 1200.01, 1500, None])
def test_dimensional_height_constituents_resolve_before_temporal_words(noun, relation, compare, height):
    result = assess(f"Böen 110 km/h {relation} einer {noun} von 1.200 Metern über NN.", elevation=height)
    assert result["hard_lock"] is (height is not None and compare(height, 1200))
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("phrase", ["in Höhenlagen ab 1200 Metern", "in einer Höhenlage ab 1200 Metern",
                                    "auf Höhenlagen oberhalb von 1200 Metern"])
@pytest.mark.parametrize("height", [60, 1500])
def test_fronted_height_nouns_have_the_same_dimensional_role(phrase, height):
    result = assess(f"Böen 110 km/h {phrase}.", elevation=height)
    assert result["hard_lock"] is (height > 1200)
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("minute,locked", [(17 * 60 + 29, False), (17 * 60 + 30, True), (18 * 60, True)])
def test_height_and_explicit_clock_are_separate_conditions(minute, locked):
    now = NOW.replace(hour=0, minute=0) + timedelta(minutes=minute)
    text = "Böen 110 Stundenkilometer ab einer Höhenlage von 1200 Metern über NN ab 18.00 Uhr UTC."
    result = assess(text, now=now, elevation=1500)
    assert result["hard_lock"] is locked
    assert not result["gust_time_uncertain"]
    assert not assess(text, now=now, elevation=60)["hard_lock"]


@pytest.mark.parametrize("datum", ["über Grund", "AGL", "WGS84"])
def test_new_height_nouns_do_not_turn_relative_heights_into_sea_level(datum):
    result = assess(f"Böen 110 km/h ab einer Höhenlage von 1200 Metern {datum}.", elevation=1500)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("agent", ["durch den Wetterdienst", "durch die Meteorologen", "vom DWD", "von der Wetterbehörde"])
@pytest.mark.parametrize("prediction,locked", [
    ("ausgeschlossen", False), ("nicht ausgeschlossen", True),
    ("erwartet", True), ("nicht erwartet", False),
])
def test_passive_agent_belongs_to_the_gust_forecast(agent, prediction, locked):
    assert assess(f"Böen 110 km/h werden {agent} {prediction}.")["hard_lock"] is locked


@pytest.mark.parametrize("source", ["nach derzeitigem Stand", "nach aktuellem Stand", "nach Angaben des DWD"])
@pytest.mark.parametrize("negation,locked", [("", False), ("nicht ", True)])
def test_separable_absence_verb_retains_its_particle_and_negation(source, negation, locked):
    assert assess(f"Böen 110 km/h fallen {source} {negation}aus.")["hard_lock"] is locked


@pytest.mark.parametrize("text", [
    "Böen 110 km/h, Schäden werden durch den Wetterdienst ausgeschlossen.",
    "Böen 110 km/h mit Schäden, die durch den Wetterdienst ausgeschlossen werden.",
    "Böen 110 km/h, Schäden fallen nach derzeitigem Stand aus.",
])
def test_another_subjects_absence_or_reporting_agent_does_not_deny_gusts(text):
    assert assess(text)["hard_lock"]


@pytest.mark.parametrize("text,locked", [
    ("Non si prevedono raffiche di vento di 110 km/h.", False),
    ("Si prevedono raffiche di vento di 110 km/h.", True),
    ("Non si possono escludere raffiche di vento di 110 km/h.", True),
    ("Si escludono raffiche di vento di 110 km/h.", False),
    ("Raffiche di vento di 110 km/h non sono attese.", False),
    ("Raffiche di vento di 110 km/h non possono essere escluse.", True),
    ("Non si prevedono danni con raffiche di vento di 110 km/h.", True),
    ("Con raffiche di vento di 110 km/h non si prevedono danni.", True),
    ("Durante raffiche di vento di 110 km/h non si prevedono danni.", True),
    ("In presenza di raffiche di vento di 110 km/h non si prevedono danni.", True),
])
def test_italian_forecast_and_exclusion_have_opposite_negation_semantics(text, locked):
    assert assess(text)["hard_lock"] is locked


def test_a_combined_height_and_weather_adjunct_keeps_the_negative_wind_predicate():
    text = "Böen 110 km/h ab einer Höhenlage von 1200 Metern über NN, bei Sturm und Regen sind nicht zu erwarten."
    result = assess(text, elevation=1500)
    assert not result["hard_lock"] and any(item["denied"] for item in result["gust_evidence"])


@pytest.mark.parametrize("unit", ["Stundenkilometer", "Stundenkilometern", "Stundenkilometers"])
@pytest.mark.parametrize("value", [89, 90, 110])
def test_complete_speed_units_keep_the_inclusive_threshold(unit, value):
    result = assess(f"Windböen bis zu {value} {unit}.")
    assert result["gust_max_kmh"] == value
    assert result["hard_lock"] is (value >= 90)


@pytest.mark.parametrize("text", [
    "Böen 110 Stunden.", "Böen 110 Kilometer.", "Böen 110 Stundenkilometerhausen.",
    "Mittelwind 110 Stundenkilometer, Böen 70 km/h.",
])
def test_unknown_units_and_separate_mean_wind_do_not_become_high_gusts(text):
    assert not assess(text)["hard_lock"]


def test_flat_parameter_retains_the_description_condition_and_original_evidence():
    result = assess("Böen 110 km/h bei winterlichen Bedingungen.", {"gusts": "110 km/h"})
    assert result["hard_lock"]
    assert all(item["weather_conditions"] == ["bei winterlichen Bedingungen"] for item in result["gust_evidence"])


def test_an_independent_positive_field_keeps_a_polarity_conflict_visible():
    result = assess("Böen 110 km/h erwartet.", headline="Böen 110 km/h werden durch den Wetterdienst ausgeschlossen.")
    assert result["gust_conflict"]
    assert any(item.get("polarity_conflict") for item in result["gust_evidence"])
