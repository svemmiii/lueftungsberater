"""Atomic weather conditions, regional subtraction and height references."""
from datetime import timedelta
import json
import math
import operator

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


# All 276 independent audit inputs, preserving the original expectations.
# Two ab-1200-m cases have an erroneous strict '>' expectation in the audit.
# Their inclusive boundary correction is explicit below, not hidden in data.
AUDIT_CASES = [
    ('Böen 50 km/h bei trockenem Wetter.', False, {}),
    ('Böen 50 km/h bei sonnigem Wetter.', False, {}),
    ('Böen 50 km/h bei feuchtem Wetter.', False, {}),
    ('Böen 50 km/h bei schwülem Wetter.', False, {}),
    ('Böen 50 km/h bei kaltem Wetter.', False, {}),
    ('Böen 50 km/h bei wolkenlosem Himmel.', False, {}),
    ('Böen 50 km/h bei warmer Witterung.', False, {}),
    ('Böen 50 km/h bei mäßigem Wind und Sonne.', False, {}),
    ('Böen 50 km/h bei unangenehmer Kälte.', False, {}),
    ('Böen 50 km/h bei frostigem Wetter.', False, {}),
    ('Böen 50 km/h bei steigenden Temperaturen.', False, {}),
    ('Böen 50 km/h bei böigem Wetter.', False, {}),
    ('Böen 89 km/h bei trockenem Wetter.', False, {}),
    ('Böen 89 km/h bei sonnigem Wetter.', False, {}),
    ('Böen 89 km/h bei feuchtem Wetter.', False, {}),
    ('Böen 89 km/h bei schwülem Wetter.', False, {}),
    ('Böen 89 km/h bei kaltem Wetter.', False, {}),
    ('Böen 89 km/h bei wolkenlosem Himmel.', False, {}),
    ('Böen 89 km/h bei warmer Witterung.', False, {}),
    ('Böen 89 km/h bei mäßigem Wind und Sonne.', False, {}),
    ('Böen 89 km/h bei unangenehmer Kälte.', False, {}),
    ('Böen 89 km/h bei frostigem Wetter.', False, {}),
    ('Böen 89 km/h bei steigenden Temperaturen.', False, {}),
    ('Böen 89 km/h bei böigem Wetter.', False, {}),
    ('Böen 90 km/h bei trockenem Wetter.', True, {}),
    ('Böen 90 km/h bei sonnigem Wetter.', True, {}),
    ('Böen 90 km/h bei feuchtem Wetter.', True, {}),
    ('Böen 90 km/h bei schwülem Wetter.', True, {}),
    ('Böen 90 km/h bei kaltem Wetter.', True, {}),
    ('Böen 90 km/h bei wolkenlosem Himmel.', True, {}),
    ('Böen 90 km/h bei warmer Witterung.', True, {}),
    ('Böen 90 km/h bei mäßigem Wind und Sonne.', True, {}),
    ('Böen 90 km/h bei unangenehmer Kälte.', True, {}),
    ('Böen 90 km/h bei frostigem Wetter.', True, {}),
    ('Böen 90 km/h bei steigenden Temperaturen.', True, {}),
    ('Böen 90 km/h bei böigem Wetter.', True, {}),
    ('Böen 91 km/h bei trockenem Wetter.', True, {}),
    ('Böen 91 km/h bei sonnigem Wetter.', True, {}),
    ('Böen 91 km/h bei feuchtem Wetter.', True, {}),
    ('Böen 91 km/h bei schwülem Wetter.', True, {}),
    ('Böen 91 km/h bei kaltem Wetter.', True, {}),
    ('Böen 91 km/h bei wolkenlosem Himmel.', True, {}),
    ('Böen 91 km/h bei warmer Witterung.', True, {}),
    ('Böen 91 km/h bei mäßigem Wind und Sonne.', True, {}),
    ('Böen 91 km/h bei unangenehmer Kälte.', True, {}),
    ('Böen 91 km/h bei frostigem Wetter.', True, {}),
    ('Böen 91 km/h bei steigenden Temperaturen.', True, {}),
    ('Böen 91 km/h bei böigem Wetter.', True, {}),
    ('Böen 110 km/h bei trockenem Wetter.', True, {}),
    ('Böen 110 km/h bei sonnigem Wetter.', True, {}),
    ('Böen 110 km/h bei feuchtem Wetter.', True, {}),
    ('Böen 110 km/h bei schwülem Wetter.', True, {}),
    ('Böen 110 km/h bei kaltem Wetter.', True, {}),
    ('Böen 110 km/h bei wolkenlosem Himmel.', True, {}),
    ('Böen 110 km/h bei warmer Witterung.', True, {}),
    ('Böen 110 km/h bei mäßigem Wind und Sonne.', True, {}),
    ('Böen 110 km/h bei unangenehmer Kälte.', True, {}),
    ('Böen 110 km/h bei frostigem Wetter.', True, {}),
    ('Böen 110 km/h bei steigenden Temperaturen.', True, {}),
    ('Böen 110 km/h bei böigem Wetter.', True, {}),
    ('Böen 130 km/h bei trockenem Wetter.', True, {}),
    ('Böen 130 km/h bei sonnigem Wetter.', True, {}),
    ('Böen 130 km/h bei feuchtem Wetter.', True, {}),
    ('Böen 130 km/h bei schwülem Wetter.', True, {}),
    ('Böen 130 km/h bei kaltem Wetter.', True, {}),
    ('Böen 130 km/h bei wolkenlosem Himmel.', True, {}),
    ('Böen 130 km/h bei warmer Witterung.', True, {}),
    ('Böen 130 km/h bei mäßigem Wind und Sonne.', True, {}),
    ('Böen 130 km/h bei unangenehmer Kälte.', True, {}),
    ('Böen 130 km/h bei frostigem Wetter.', True, {}),
    ('Böen 130 km/h bei steigenden Temperaturen.', True, {}),
    ('Böen 130 km/h bei böigem Wetter.', True, {}),
    ('Böen 90 km/h im gesamten Warngebiet mit Ausnahme der Tallagen.', False, {'elevation': 60}),
    ('Böen 90 km/h im gesamten Warngebiet mit Ausnahme der Tallagen.', False, {'elevation': 1500}),
    ('Böen 90 km/h im ganzen Warngebiet außer in der Eifel.', False, {'elevation': 60}),
    ('Böen 90 km/h im ganzen Warngebiet außer in der Eifel.', False, {'elevation': 1500}),
    ('Böen 90 km/h im gesamten Warngebiet außer im Norden.', False, {'elevation': 60}),
    ('Böen 90 km/h im gesamten Warngebiet außer im Norden.', False, {'elevation': 1500}),
    ('Böen 90 km/h überall im Warngebiet, nur nicht in den Tälern.', False, {'elevation': 60}),
    ('Böen 90 km/h überall im Warngebiet, nur nicht in den Tälern.', False, {'elevation': 1500}),
    ('Böen 90 km/h im gesamten betroffenen Warngebiet außer an der Küste.', False, {'elevation': 60}),
    ('Böen 90 km/h im gesamten betroffenen Warngebiet außer an der Küste.', False, {'elevation': 1500}),
    ('Böen 90 km/h im gesamten Warngebiet mit Ausnahme der Berglagen.', False, {'elevation': 60}),
    ('Böen 90 km/h im gesamten Warngebiet mit Ausnahme der Berglagen.', False, {'elevation': 1500}),
    ('Böen 90 km/h im gesamten Warngebiet außer rund um Köln.', False, {'elevation': 60}),
    ('Böen 90 km/h im gesamten Warngebiet außer rund um Köln.', False, {'elevation': 1500}),
    ('Böen 90 km/h im ganzen Warnbereich mit Ausnahme der tieferen Lagen.', False, {'elevation': 60}),
    ('Böen 90 km/h im ganzen Warnbereich mit Ausnahme der tieferen Lagen.', False, {'elevation': 1500}),
    ('Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Tallagen.', False, {'elevation': 60}),
    ('Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Tallagen.', False, {'elevation': 1500}),
    ('Böen 110 km/h im ganzen Warngebiet außer in der Eifel.', False, {'elevation': 60}),
    ('Böen 110 km/h im ganzen Warngebiet außer in der Eifel.', False, {'elevation': 1500}),
    ('Böen 110 km/h im gesamten Warngebiet außer im Norden.', False, {'elevation': 60}),
    ('Böen 110 km/h im gesamten Warngebiet außer im Norden.', False, {'elevation': 1500}),
    ('Böen 110 km/h überall im Warngebiet, nur nicht in den Tälern.', False, {'elevation': 60}),
    ('Böen 110 km/h überall im Warngebiet, nur nicht in den Tälern.', False, {'elevation': 1500}),
    ('Böen 110 km/h im gesamten betroffenen Warngebiet außer an der Küste.', False, {'elevation': 60}),
    ('Böen 110 km/h im gesamten betroffenen Warngebiet außer an der Küste.', False, {'elevation': 1500}),
    ('Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Berglagen.', False, {'elevation': 60}),
    ('Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Berglagen.', False, {'elevation': 1500}),
    ('Böen 110 km/h im gesamten Warngebiet außer rund um Köln.', False, {'elevation': 60}),
    ('Böen 110 km/h im gesamten Warngebiet außer rund um Köln.', False, {'elevation': 1500}),
    ('Böen 110 km/h im ganzen Warnbereich mit Ausnahme der tieferen Lagen.', False, {'elevation': 60}),
    ('Böen 110 km/h im ganzen Warnbereich mit Ausnahme der tieferen Lagen.', False, {'elevation': 1500}),
    ('Böen 130 km/h im gesamten Warngebiet mit Ausnahme der Tallagen.', False, {'elevation': 60}),
    ('Böen 130 km/h im gesamten Warngebiet mit Ausnahme der Tallagen.', False, {'elevation': 1500}),
    ('Böen 130 km/h im ganzen Warngebiet außer in der Eifel.', False, {'elevation': 60}),
    ('Böen 130 km/h im ganzen Warngebiet außer in der Eifel.', False, {'elevation': 1500}),
    ('Böen 130 km/h im gesamten Warngebiet außer im Norden.', False, {'elevation': 60}),
    ('Böen 130 km/h im gesamten Warngebiet außer im Norden.', False, {'elevation': 1500}),
    ('Böen 130 km/h überall im Warngebiet, nur nicht in den Tälern.', False, {'elevation': 60}),
    ('Böen 130 km/h überall im Warngebiet, nur nicht in den Tälern.', False, {'elevation': 1500}),
    ('Böen 130 km/h im gesamten betroffenen Warngebiet außer an der Küste.', False, {'elevation': 60}),
    ('Böen 130 km/h im gesamten betroffenen Warngebiet außer an der Küste.', False, {'elevation': 1500}),
    ('Böen 130 km/h im gesamten Warngebiet mit Ausnahme der Berglagen.', False, {'elevation': 60}),
    ('Böen 130 km/h im gesamten Warngebiet mit Ausnahme der Berglagen.', False, {'elevation': 1500}),
    ('Böen 130 km/h im gesamten Warngebiet außer rund um Köln.', False, {'elevation': 60}),
    ('Böen 130 km/h im gesamten Warngebiet außer rund um Köln.', False, {'elevation': 1500}),
    ('Böen 130 km/h im ganzen Warnbereich mit Ausnahme der tieferen Lagen.', False, {'elevation': 60}),
    ('Böen 130 km/h im ganzen Warnbereich mit Ausnahme der tieferen Lagen.', False, {'elevation': 1500}),
    ('Böen 89 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 89 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 89 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 89 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 1300}),
    ('Böen 89 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 1500}),
    ('Böen 89 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 89 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 89 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 89 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 1300}),
    ('Böen 89 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 1500}),
    ('Böen 89 km/h ab 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 89 km/h ab 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 89 km/h ab 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 89 km/h ab 1.200 Metern über NN.', False, {'elevation': 1300}),
    ('Böen 89 km/h ab 1.200 Metern über NN.', False, {'elevation': 1500}),
    ('Böen 89 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 60}),
    ('Böen 89 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 1100}),
    ('Böen 89 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 1200}),
    ('Böen 89 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 1300}),
    ('Böen 89 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 1500}),
    ('Böen 89 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 60}),
    ('Böen 89 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 1100}),
    ('Böen 89 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 1200}),
    ('Böen 89 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 1300}),
    ('Böen 89 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 1500}),
    ('Böen 89 km/h auf Höhen über 1200 m.', False, {'elevation': 60}),
    ('Böen 89 km/h auf Höhen über 1200 m.', False, {'elevation': 1100}),
    ('Böen 89 km/h auf Höhen über 1200 m.', False, {'elevation': 1200}),
    ('Böen 89 km/h auf Höhen über 1200 m.', False, {'elevation': 1300}),
    ('Böen 89 km/h auf Höhen über 1200 m.', False, {'elevation': 1500}),
    ('Böen 89 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 60}),
    ('Böen 89 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 1100}),
    ('Böen 89 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 1200}),
    ('Böen 89 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 1300}),
    ('Böen 89 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 1500}),
    ('Böen 90 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 90 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 90 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 90 km/h oberhalb 1.200 Metern über NN.', True, {'elevation': 1300}),
    ('Böen 90 km/h oberhalb 1.200 Metern über NN.', True, {'elevation': 1500}),
    ('Böen 90 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 90 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 90 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 90 km/h oberhalb von 1.200 Metern über NN.', True, {'elevation': 1300}),
    ('Böen 90 km/h oberhalb von 1.200 Metern über NN.', True, {'elevation': 1500}),
    ('Böen 90 km/h ab 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 90 km/h ab 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 90 km/h ab 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 90 km/h ab 1.200 Metern über NN.', True, {'elevation': 1300}),
    ('Böen 90 km/h ab 1.200 Metern über NN.', True, {'elevation': 1500}),
    ('Böen 90 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 60}),
    ('Böen 90 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 1100}),
    ('Böen 90 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 1200}),
    ('Böen 90 km/h oberhalb 1.200 m ü. NN.', True, {'elevation': 1300}),
    ('Böen 90 km/h oberhalb 1.200 m ü. NN.', True, {'elevation': 1500}),
    ('Böen 90 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 60}),
    ('Böen 90 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 1100}),
    ('Böen 90 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 1200}),
    ('Böen 90 km/h in Höhenlagen oberhalb von 1200 m.', True, {'elevation': 1300}),
    ('Böen 90 km/h in Höhenlagen oberhalb von 1200 m.', True, {'elevation': 1500}),
    ('Böen 90 km/h auf Höhen über 1200 m.', False, {'elevation': 60}),
    ('Böen 90 km/h auf Höhen über 1200 m.', False, {'elevation': 1100}),
    ('Böen 90 km/h auf Höhen über 1200 m.', False, {'elevation': 1200}),
    ('Böen 90 km/h auf Höhen über 1200 m.', True, {'elevation': 1300}),
    ('Böen 90 km/h auf Höhen über 1200 m.', True, {'elevation': 1500}),
    ('Böen 90 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 60}),
    ('Böen 90 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 1100}),
    ('Böen 90 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 1200}),
    ('Böen 90 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', True, {'elevation': 1300}),
    ('Böen 90 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', True, {'elevation': 1500}),
    ('Böen 110 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 110 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 110 km/h oberhalb 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 110 km/h oberhalb 1.200 Metern über NN.', True, {'elevation': 1300}),
    ('Böen 110 km/h oberhalb 1.200 Metern über NN.', True, {'elevation': 1500}),
    ('Böen 110 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 110 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 110 km/h oberhalb von 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 110 km/h oberhalb von 1.200 Metern über NN.', True, {'elevation': 1300}),
    ('Böen 110 km/h oberhalb von 1.200 Metern über NN.', True, {'elevation': 1500}),
    ('Böen 110 km/h ab 1.200 Metern über NN.', False, {'elevation': 60}),
    ('Böen 110 km/h ab 1.200 Metern über NN.', False, {'elevation': 1100}),
    ('Böen 110 km/h ab 1.200 Metern über NN.', False, {'elevation': 1200}),
    ('Böen 110 km/h ab 1.200 Metern über NN.', True, {'elevation': 1300}),
    ('Böen 110 km/h ab 1.200 Metern über NN.', True, {'elevation': 1500}),
    ('Böen 110 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 60}),
    ('Böen 110 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 1100}),
    ('Böen 110 km/h oberhalb 1.200 m ü. NN.', False, {'elevation': 1200}),
    ('Böen 110 km/h oberhalb 1.200 m ü. NN.', True, {'elevation': 1300}),
    ('Böen 110 km/h oberhalb 1.200 m ü. NN.', True, {'elevation': 1500}),
    ('Böen 110 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 60}),
    ('Böen 110 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 1100}),
    ('Böen 110 km/h in Höhenlagen oberhalb von 1200 m.', False, {'elevation': 1200}),
    ('Böen 110 km/h in Höhenlagen oberhalb von 1200 m.', True, {'elevation': 1300}),
    ('Böen 110 km/h in Höhenlagen oberhalb von 1200 m.', True, {'elevation': 1500}),
    ('Böen 110 km/h auf Höhen über 1200 m.', False, {'elevation': 60}),
    ('Böen 110 km/h auf Höhen über 1200 m.', False, {'elevation': 1100}),
    ('Böen 110 km/h auf Höhen über 1200 m.', False, {'elevation': 1200}),
    ('Böen 110 km/h auf Höhen über 1200 m.', True, {'elevation': 1300}),
    ('Böen 110 km/h auf Höhen über 1200 m.', True, {'elevation': 1500}),
    ('Böen 110 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 60}),
    ('Böen 110 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 1100}),
    ('Böen 110 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', False, {'elevation': 1200}),
    ('Böen 110 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', True, {'elevation': 1300}),
    ('Böen 110 km/h oberhalb 1.200 Metern über dem Meeresspiegel.', True, {'elevation': 1500}),
    ('Böen 89 km/h sind nach DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 89 km/h sind laut DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 89 km/h sind laut Angaben des DWD nicht zu erwarten.', False, {}),
    ('Böen 89 km/h sind nach Angaben des DWD nicht zu erwarten.', False, {}),
    ('Böen 89 km/h sind nach jüngsten DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 89 km/h sind nach offiziellen DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 89 km/h treten nach Einschätzung des DWD nicht auf.', False, {}),
    ('Böen 89 km/h werden nach aktuellen Meldungen des DWD nicht auftreten.', False, {}),
    ('Böen 89 km/h sind völlig ausgeschlossen.', False, {}),
    ('Böen 89 km/h sind ausdrücklich ausgeschlossen.', False, {}),
    ('Böen 90 km/h sind nach DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 90 km/h sind laut DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 90 km/h sind laut Angaben des DWD nicht zu erwarten.', False, {}),
    ('Böen 90 km/h sind nach Angaben des DWD nicht zu erwarten.', False, {}),
    ('Böen 90 km/h sind nach jüngsten DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 90 km/h sind nach offiziellen DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 90 km/h treten nach Einschätzung des DWD nicht auf.', False, {}),
    ('Böen 90 km/h werden nach aktuellen Meldungen des DWD nicht auftreten.', False, {}),
    ('Böen 90 km/h sind völlig ausgeschlossen.', False, {}),
    ('Böen 90 km/h sind ausdrücklich ausgeschlossen.', False, {}),
    ('Böen 110 km/h sind nach DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 110 km/h sind laut DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 110 km/h sind laut Angaben des DWD nicht zu erwarten.', False, {}),
    ('Böen 110 km/h sind nach Angaben des DWD nicht zu erwarten.', False, {}),
    ('Böen 110 km/h sind nach jüngsten DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 110 km/h sind nach offiziellen DWD-Angaben nicht zu erwarten.', False, {}),
    ('Böen 110 km/h treten nach Einschätzung des DWD nicht auf.', False, {}),
    ('Böen 110 km/h werden nach aktuellen Meldungen des DWD nicht auftreten.', False, {}),
    ('Böen 110 km/h sind völlig ausgeschlossen.', False, {}),
    ('Böen 110 km/h sind ausdrücklich ausgeschlossen.', False, {}),
    ('Böen 89 km/h sind laut DWD zu erwarten.', False, {}),
    ('Böen 89 km/h sind nach Angaben des DWD wahrscheinlich.', False, {}),
    ('Böen 89 km/h werden erwartet.', False, {}),
    ('Böen 89 km/h sind derzeit möglich.', False, {}),
    ('Böen 89 km/h treten auf.', False, {}),
    ('Böen 89 km/h sind voraussichtlich zu erwarten.', False, {}),
    ('Böen 89 km/h werden nicht ausgeschlossen.', False, {}),
    ('Böen 90 km/h sind laut DWD zu erwarten.', True, {}),
    ('Böen 90 km/h sind nach Angaben des DWD wahrscheinlich.', True, {}),
    ('Böen 90 km/h werden erwartet.', True, {}),
    ('Böen 90 km/h sind derzeit möglich.', True, {}),
    ('Böen 90 km/h treten auf.', True, {}),
    ('Böen 90 km/h sind voraussichtlich zu erwarten.', True, {}),
    ('Böen 90 km/h werden nicht ausgeschlossen.', True, {}),
    ('Böen 110 km/h sind laut DWD zu erwarten.', True, {}),
    ('Böen 110 km/h sind nach Angaben des DWD wahrscheinlich.', True, {}),
    ('Böen 110 km/h werden erwartet.', True, {}),
    ('Böen 110 km/h sind derzeit möglich.', True, {}),
    ('Böen 110 km/h treten auf.', True, {}),
    ('Böen 110 km/h sind voraussichtlich zu erwarten.', True, {}),
    ('Böen 110 km/h werden nicht ausgeschlossen.', True, {}),

]


def _correct_audit_boundary(description, original, options):
    if description in {"Böen 90 km/h ab 1.200 Metern über NN.", "Böen 110 km/h ab 1.200 Metern über NN."} and options == {"elevation": 1200}:
        assert original is False
        return True  # "ab" includes exactly 1200 m, as existing regressions do.
    return original


assert len(AUDIT_CASES) == 276
assert sum(_correct_audit_boundary(d, expected, opts) is not expected for d, expected, opts in AUDIT_CASES) == 2


@pytest.mark.parametrize("description,original,options", AUDIT_CASES)
def test_independent_276_audit_cases_with_two_documented_inclusive_boundary_corrections(description, original, options):
    result = assess(description, **options)
    assert result["hard_lock"] is _correct_audit_boundary(description, original, options)


@pytest.mark.parametrize("condition", ["trockenem Wetter", "sonnigem Wetter", "schwülem Wetter", "wolkenlosem Himmel",
                                       "frostigem Wetter", "warmer Witterung", "unangenehmer Kälte", "böigem Wetter"])
@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h bei {condition}.", True),
    ("Bei {condition} sind Böen 110 km/h möglich.", True),
    ("Böen 110 km/h sind bei {condition} nicht ausgeschlossen.", True),
    ("Böen 110 km/h sind bei {condition} nicht zu erwarten.", False),
])
def test_general_weather_state_descriptors_preserve_their_own_gust_predicate(condition, frame, locked):
    result = assess(frame.format(condition=condition))
    assert result["hard_lock"] is locked and not result["gust_scope_uncertain"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h bei Trockenwetterhausen.", "Böen 110 km/h bei wolkenlosem Himmelstadt.",
    "Böen 110 km/h bei warmer Witterungsburg.", "Böen 110 km/h bei unangenehmer Kälteheim.",
    "Böen 110 km/h bei trockenem Wetter im Harz.", "Bei trockenem Wetter im Harz Böen 110 km/h.",
])
def test_weather_heads_do_not_consume_place_names_or_additional_regions(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


EXCEPTIONS = ["mit Ausnahme der Tallagen", "mit Ausnahme der Berglagen", "mit Ausnahme von Neudorf",
              "außer in der Eifel", "außer im Norden", "nur nicht in den Tälern", "nicht aber in Tallagen",
              "ausgenommen im Harz", "except in the valleys", "excluding Neudorf"]


@pytest.mark.parametrize("exception", EXCEPTIONS)
@pytest.mark.parametrize("separator", [" ", ", "])
@pytest.mark.parametrize("elevation", [60, 1500])
def test_unverified_subtracted_regions_stay_attached_to_their_claim(exception, separator, elevation):
    result = assess(f"Böen 110 km/h im gesamten Warngebiet{separator}{exception}.", elevation=elevation)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]
    assert result["gust_evidence"][0]["location_exclusions"]


@pytest.mark.parametrize("description", [
    "Mit Ausnahme der Tallagen sind Böen 110 km/h im gesamten Warngebiet möglich.",
    "Mit Ausnahme der Tallagen Böen 110 km/h im gesamten Warngebiet.",
    "Böen 110 km/h im gesamten Warngebiet, nur nicht in den Tälern und an der Küste.",
    "Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Tallagen und der Berglagen.",
])
def test_fronted_or_coordinated_exceptions_do_not_fall_out_of_the_assertion(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("field", ["description", "headline", "event", "parameter"])
def test_all_warning_fields_keep_their_excluded_regions(field):
    text = "Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Tallagen."
    changes = {field: text} if field in {"headline", "event"} else {}
    parameters = {"gusts": text} if field == "parameter" else {}
    result = assess(text if field == "description" else "", parameters, **changes)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


def test_a_flat_parameter_cannot_erase_a_description_exception():
    result = assess("Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Tallagen.", {"gusts": "110 km/h"})
    assert not result["hard_lock"] and all(not item["location_verified"] for item in result["gust_evidence"])
    assert all(item["location_exclusions"] for item in result["gust_evidence"])


def test_an_independent_general_forecast_survives_a_different_claims_exception():
    result = assess("Böen 110 km/h allgemein; Böen 140 km/h im gesamten Warngebiet mit Ausnahme der Tallagen.")
    assert result["hard_lock"] and result["gust_max_kmh"] == 110 and result["gust_scope_uncertain"]


@pytest.mark.parametrize("relation,compare", [("oberhalb", operator.gt), ("ab", operator.ge),
                                             ("unterhalb", operator.lt), ("bis", operator.le)])
@pytest.mark.parametrize("elevation", [60, 1199.99, 1200, 1200.01, 1500])
def test_numeric_exclusion_membership_uses_real_bounds_instead_of_disabling_every_exception(relation, compare, elevation):
    result = assess(f"Böen 110 km/h im gesamten Warngebiet mit Ausnahme von Höhen {relation} 1.200 m.", elevation=elevation)
    assert result["hard_lock"] is (not compare(elevation, 1200))


@pytest.mark.parametrize("height,locked", [(60, False), (1500, True)])
def test_a_window_outside_a_subregions_numeric_bound_does_not_need_invented_terrain_membership(height, locked):
    result = assess("Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Tallagen unterhalb 1.200 m.", elevation=height)
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("description", [
    "Böen 110 km/h im gesamten Warngebiet mit Ausnahme von Höhen oberhalb 1.200 m und unterhalb 500 m.",
    "Böen 110 km/h im gesamten Warngebiet mit Ausnahme von Neudorf oder Höhen oberhalb 1.200 m.",
    "Böen 110 km/h im gesamten Warngebiet mit Ausnahme der Höhen oberhalb 1.20.0 m.",
])
def test_unresolved_exception_alternatives_and_invalid_numbers_are_not_guessed(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


def test_an_exception_cannot_consume_the_gust_denial_that_follows_it():
    text = "Böen 110 km/h im gesamten Warngebiet mit Ausnahme von Höhen oberhalb 1.200 m sind nicht zu erwarten."
    for description in (text, text.upper()):
        result = assess(description)
        assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("description,locked", [
    ("Böen 110 km/h im gesamten Warngebiet sind nicht zu erwarten.", False),
    ("Böen 110 km/h im gesamten Warngebiet sind nicht ausgeschlossen.", True),
    ("Böen 110 km/h im gesamten Warngebiet mit Ausnahme von Höhen oberhalb 1.200 m, Schäden sind nicht zu erwarten.", True),
])
def test_verified_area_adjuncts_do_not_block_or_transfer_forecast_negation(description, locked):
    assert assess(description)["hard_lock"] is locked


def test_an_exception_time_is_not_silently_used_as_the_general_wind_onset():
    result = assess("Böen 110 km/h im gesamten Warngebiet mit Ausnahme von Höhen oberhalb 1.200 m ab 18 Uhr UTC.")
    assert not result["hard_lock"] and result["gust_time_uncertain"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h mit Schäden im gesamten Warngebiet mit Ausnahme der Tallagen.",
    "Böen 110 km/h und Regen im gesamten Warngebiet mit Ausnahme der Tallagen.",
    "Böen 110 km/h im gesamten Warngebiet außer bei Regen.",
])
def test_other_subject_or_weather_condition_exceptions_do_not_become_gust_regions(description):
    result = assess(description)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110


REFERENCES = ["über NN", "über NHN", "über Normalnull", "über Normalhöhennull", "über dem Meeresspiegel",
              "ü. NN", "ü. NHN", "ü. d. M", "NN", "NHN", "MSL", "AMSL", "above sea level", "above mean sea level"]


@pytest.mark.parametrize("reference", REFERENCES)
@pytest.mark.parametrize("relation,compare", [("oberhalb", operator.gt), ("unterhalb", operator.lt),
                                             ("ab", operator.ge), ("bis", operator.le)])
@pytest.mark.parametrize("elevation", [60, 1200, 1500])
def test_height_number_unit_and_reference_form_one_quantity(reference, relation, compare, elevation):
    result = assess(f"Böen 110 km/h {relation} 1.200 Metern {reference}.", elevation=elevation)
    assert result["hard_lock"] is compare(elevation, 1200)
    assert not result["gust_time_uncertain"]
    assert result["gust_evidence"][0]["height_references"]


@pytest.mark.parametrize("reference", ["über Grund", "über dem Boden", "AGL", "above ground level", "WGS84"])
@pytest.mark.parametrize("elevation", [60, 1500])
def test_a_relative_or_ellipsoidal_height_is_not_a_sea_level_window_height(reference, elevation):
    result = assess(f"Böen 110 km/h oberhalb 1.200 Metern {reference}.", elevation=elevation)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h oberhalb 1.200 Metern über NN im Harz.",
    "Böen 110 km/h oberhalb 1.200 Metern über Neudorf.",
    "Böen 110 km/h oberhalb 1.200 Metern ü. NN, nur auf Gipfeln.",
])
def test_height_references_do_not_consume_genuine_additional_place_restrictions(description):
    result = assess(description, elevation=1500)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("suffix", ["m ü. NN", "m ü. NN.", "mNHN", "Metern über NN"])
@pytest.mark.parametrize("offset,locked", [(-1801, False), (-1800, True), (0, True)])
def test_datum_abbreviations_do_not_break_the_following_clock_scope(suffix, offset, locked):
    start = NOW.replace(hour=18, minute=0, second=0)
    result = assess(f"Böen 110 km/h oberhalb 1.200 {suffix} ab 18.00 Uhr UTC.",
                    elevation=1500, now=start + timedelta(seconds=offset))
    assert result["hard_lock"] is locked and not result["gust_time_uncertain"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h oberhalb 1.200 m ü. NN. sind nicht zu erwarten.",
    "Böen 110 km/h oberhalb 1.200 m ü. NN. ab 18 Uhr UTC sind nicht zu erwarten.",
])
def test_a_terminal_datum_abbreviation_dot_does_not_hide_the_negative_forecast(description):
    result = assess(description, elevation=1500, now=NOW.replace(hour=19))
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("elevation", [None, True, math.inf, math.nan])
def test_height_reference_text_cannot_supply_a_missing_window_elevation(elevation):
    result = assess("Böen 110 km/h oberhalb 1.200 Metern über NN.", elevation=elevation)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("source", ["nach DWD-Angaben", "nach jüngsten DWD-Angaben", "nach aktuellen Meldungen des DWD",
                                    "nach Wetterdienst-Angaben", "nach MeteoSwiss-Angaben"])
@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h sind {source} nicht zu erwarten.", False),
    ("Böen 110 km/h sind, {source}, nicht zu erwarten.", False),
    ("Böen 110 km/h sind {source} nicht ausgeschlossen.", True),
    ("Böen 110 km/h, Schäden sind {source} nicht zu erwarten.", True),
])
def test_hyphenated_reporting_noun_groups_keep_their_own_forecast_polarity(source, frame, locked):
    assert assess(frame.format(source=source))["hard_lock"] is locked


@pytest.mark.parametrize("frame,locked", [("sind völlig ausgeschlossen", False), ("sind voellig ausgeschlossen", False),
                                         ("sind völlig unmöglich", False), ("werden völlig ausgeschlossen", False),
                                         ("sind nicht völlig ausgeschlossen", True), ("sind völlig nicht ausgeschlossen", True),
                                         ("werden nicht völlig erwartet", True), ("sind völlig möglich", True)])
def test_degree_modifiers_do_not_reverse_exclusion_or_certainty_polarity(frame, locked):
    result = assess(f"Böen 110 km/h {frame}.")
    assert result["hard_lock"] is locked
    json.dumps(result, allow_nan=False)
