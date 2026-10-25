"""Independent audit cases, predicate roles and bounded CAP-time failure handling.

The 616 warning decisions and 16 no-exception inputs are copied unchanged from
2026-10-25 05:59. Additional counterpairs cover source/subject boundaries and the
actual provider-to-persisted-safety handoff without starting Home Assistant.
"""
from datetime import datetime, timedelta, timezone
import json
import math
from types import SimpleNamespace

import pytest

from test_v0119_warning_scopes_pure import NOW, assess, policy, warning, _provider_case
from test_v0114_complete2_pure import _extract, _provider, _safety

AUDIT_NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)

AUDIT_CASES = [('weather', 'Böen 65 km/h bei Regen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei starkem Frost.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Schneegriesel.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Schneetreiben.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Wetterberuhigung.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Schneematsch.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Gewitter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei intensivem Starkregen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Trockenheit.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Schneefall.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei gefrierender Nässe.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Böigkeit.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Frühlingswetter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei einer Wetterbesserung.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei leichtem Tauwetter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Graupel.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei Schneegestöber.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei nächtlichem Schneefall.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei hoher Luftfeuchte.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 65 km/h bei klaren Sichtverhältnissen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Regen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei starkem Frost.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Schneegriesel.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Schneetreiben.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Wetterberuhigung.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Schneematsch.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Gewitter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei intensivem Starkregen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Trockenheit.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Schneefall.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei gefrierender Nässe.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Böigkeit.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Frühlingswetter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei einer Wetterbesserung.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei leichtem Tauwetter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Graupel.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei Schneegestöber.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei nächtlichem Schneefall.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei hoher Luftfeuchte.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 85 km/h bei klaren Sichtverhältnissen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Regen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei starkem Frost.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Schneegriesel.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Schneetreiben.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Wetterberuhigung.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Schneematsch.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Gewitter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei intensivem Starkregen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Trockenheit.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Schneefall.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei gefrierender Nässe.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Böigkeit.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Frühlingswetter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei einer Wetterbesserung.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei leichtem Tauwetter.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Graupel.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei Schneegestöber.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei nächtlichem Schneefall.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei hoher Luftfeuchte.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 89 km/h bei klaren Sichtverhältnissen.', False, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Regen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei starkem Frost.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Schneegriesel.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Schneetreiben.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Wetterberuhigung.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Schneematsch.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Gewitter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei intensivem Starkregen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Trockenheit.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Schneefall.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei gefrierender Nässe.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Böigkeit.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Frühlingswetter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei einer Wetterbesserung.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei leichtem Tauwetter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Graupel.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei Schneegestöber.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei nächtlichem Schneefall.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei hoher Luftfeuchte.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 90 km/h bei klaren Sichtverhältnissen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Regen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei starkem Frost.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Schneegriesel.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Schneetreiben.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Wetterberuhigung.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Schneematsch.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Gewitter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei intensivem Starkregen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Trockenheit.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Schneefall.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei gefrierender Nässe.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Böigkeit.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Frühlingswetter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei einer Wetterbesserung.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei leichtem Tauwetter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Graupel.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei Schneegestöber.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei nächtlichem Schneefall.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei hoher Luftfeuchte.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 95 km/h bei klaren Sichtverhältnissen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Regen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei starkem Frost.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Schneegriesel.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Schneetreiben.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Wetterberuhigung.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Schneematsch.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Gewitter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei intensivem Starkregen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Trockenheit.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Schneefall.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei gefrierender Nässe.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Böigkeit.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Frühlingswetter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei einer Wetterbesserung.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei leichtem Tauwetter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Graupel.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei Schneegestöber.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei nächtlichem Schneefall.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei hoher Luftfeuchte.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 110 km/h bei klaren Sichtverhältnissen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Regen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei starkem Frost.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Schneegriesel.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Schneetreiben.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Wetterberuhigung.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Schneematsch.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Gewitter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei intensivem Starkregen.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Trockenheit.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Schneefall.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei gefrierender Nässe.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Böigkeit.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Frühlingswetter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei einer Wetterbesserung.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei leichtem Tauwetter.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Graupel.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei Schneegestöber.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei nächtlichem Schneefall.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei hoher Luftfeuchte.', True, 'Windwarnung', 60, {}),
 ('weather', 'Böen 145 km/h bei klaren Sichtverhältnissen.', True, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h sind nicht zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h bleiben nach den neuesten Berechnungen aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h sind aller Voraussicht nach ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h gelten inzwischen als ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h treten laut amtlichen Prognosen nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h werden nach Angaben des DWD nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h wurden nicht vorhergesagt.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h sind keinesfalls zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h sind derzeit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h sind mit hoher Sicherheit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h bleiben garantiert aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h können laut dem Wetterdienst ausgeschlossen werden.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h sind nach Ansicht der Behörde ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h werden definitiv nicht eintreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h werden aller Voraussicht nach nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h treten auch heute nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation',
  'Böen 65 km/h sind mit an Sicherheit grenzender Wahrscheinlichkeit ausgeschlossen.',
  False,
  'Windwarnung',
  60,
  {}),
 ('negation', 'Böen 65 km/h werden weder heute noch morgen erwartet.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 65 km/h sind laut aktueller Lageeinschätzung ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h sind nicht zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h bleiben nach den neuesten Berechnungen aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h sind aller Voraussicht nach ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h gelten inzwischen als ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h treten laut amtlichen Prognosen nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h werden nach Angaben des DWD nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h wurden nicht vorhergesagt.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h sind keinesfalls zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h sind derzeit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h sind mit hoher Sicherheit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h bleiben garantiert aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h können laut dem Wetterdienst ausgeschlossen werden.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h sind nach Ansicht der Behörde ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h werden definitiv nicht eintreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h werden aller Voraussicht nach nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h treten auch heute nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation',
  'Böen 85 km/h sind mit an Sicherheit grenzender Wahrscheinlichkeit ausgeschlossen.',
  False,
  'Windwarnung',
  60,
  {}),
 ('negation', 'Böen 85 km/h werden weder heute noch morgen erwartet.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 85 km/h sind laut aktueller Lageeinschätzung ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h sind nicht zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h bleiben nach den neuesten Berechnungen aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h sind aller Voraussicht nach ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h gelten inzwischen als ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h treten laut amtlichen Prognosen nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h werden nach Angaben des DWD nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h wurden nicht vorhergesagt.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h sind keinesfalls zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h sind derzeit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h sind mit hoher Sicherheit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h bleiben garantiert aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h können laut dem Wetterdienst ausgeschlossen werden.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h sind nach Ansicht der Behörde ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h werden definitiv nicht eintreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h werden aller Voraussicht nach nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h treten auch heute nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation',
  'Böen 89 km/h sind mit an Sicherheit grenzender Wahrscheinlichkeit ausgeschlossen.',
  False,
  'Windwarnung',
  60,
  {}),
 ('negation', 'Böen 89 km/h werden weder heute noch morgen erwartet.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 89 km/h sind laut aktueller Lageeinschätzung ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h sind nicht zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h bleiben nach den neuesten Berechnungen aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h sind aller Voraussicht nach ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h gelten inzwischen als ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h treten laut amtlichen Prognosen nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h werden nach Angaben des DWD nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h wurden nicht vorhergesagt.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h sind keinesfalls zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h sind derzeit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h sind mit hoher Sicherheit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h bleiben garantiert aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h können laut dem Wetterdienst ausgeschlossen werden.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h sind nach Ansicht der Behörde ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h werden definitiv nicht eintreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h werden aller Voraussicht nach nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h treten auch heute nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation',
  'Böen 90 km/h sind mit an Sicherheit grenzender Wahrscheinlichkeit ausgeschlossen.',
  False,
  'Windwarnung',
  60,
  {}),
 ('negation', 'Böen 90 km/h werden weder heute noch morgen erwartet.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 90 km/h sind laut aktueller Lageeinschätzung ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h sind nicht zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h bleiben nach den neuesten Berechnungen aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h sind aller Voraussicht nach ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h gelten inzwischen als ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h treten laut amtlichen Prognosen nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h werden nach Angaben des DWD nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h wurden nicht vorhergesagt.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h sind keinesfalls zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h sind derzeit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h sind mit hoher Sicherheit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h bleiben garantiert aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h können laut dem Wetterdienst ausgeschlossen werden.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h sind nach Ansicht der Behörde ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h werden definitiv nicht eintreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h werden aller Voraussicht nach nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h treten auch heute nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation',
  'Böen 95 km/h sind mit an Sicherheit grenzender Wahrscheinlichkeit ausgeschlossen.',
  False,
  'Windwarnung',
  60,
  {}),
 ('negation', 'Böen 95 km/h werden weder heute noch morgen erwartet.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 95 km/h sind laut aktueller Lageeinschätzung ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h sind nicht zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h bleiben nach den neuesten Berechnungen aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h sind aller Voraussicht nach ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h gelten inzwischen als ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h treten laut amtlichen Prognosen nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h werden nach Angaben des DWD nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h wurden nicht vorhergesagt.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h sind keinesfalls zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h sind derzeit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h sind mit hoher Sicherheit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h bleiben garantiert aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h können laut dem Wetterdienst ausgeschlossen werden.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h sind nach Ansicht der Behörde ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h werden definitiv nicht eintreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h werden aller Voraussicht nach nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h treten auch heute nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation',
  'Böen 110 km/h sind mit an Sicherheit grenzender Wahrscheinlichkeit ausgeschlossen.',
  False,
  'Windwarnung',
  60,
  {}),
 ('negation', 'Böen 110 km/h werden weder heute noch morgen erwartet.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 110 km/h sind laut aktueller Lageeinschätzung ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h sind nicht zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h sind nach Ansicht der Meteorologen auszuschließen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h bleiben nach den neuesten Berechnungen aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h sind aller Voraussicht nach ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h gelten inzwischen als ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h treten laut amtlichen Prognosen nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h werden nach Angaben des DWD nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h wurden nicht vorhergesagt.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h sind keinesfalls zu erwarten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h sind derzeit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h sind mit hoher Sicherheit ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h bleiben garantiert aus.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h können laut dem Wetterdienst ausgeschlossen werden.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h sind nach Ansicht der Behörde ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h werden definitiv nicht eintreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h werden aller Voraussicht nach nicht auftreten.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h treten auch heute nicht auf.', False, 'Windwarnung', 60, {}),
 ('negation',
  'Böen 145 km/h sind mit an Sicherheit grenzender Wahrscheinlichkeit ausgeschlossen.',
  False,
  'Windwarnung',
  60,
  {}),
 ('negation', 'Böen 145 km/h werden weder heute noch morgen erwartet.', False, 'Windwarnung', 60, {}),
 ('negation', 'Böen 145 km/h sind laut aktueller Lageeinschätzung ausgeschlossen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h nur in der Eifel.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h nur im Harz.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h im Norden des Kreises.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h östlich von Bonn.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h auf der Zugspitze.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h über dem Bergland.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h zwischen Bonn und Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h entlang der Nordseeküste.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h im Umland von Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h am Rand der Stadt.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h in den Bergen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h auf dem offenen Meer.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h von Aachen bis Düren.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h in den Tälern.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 65 km/h ausschließlich in höheren Lagen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h nur in der Eifel.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h nur im Harz.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h im Norden des Kreises.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h östlich von Bonn.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h auf der Zugspitze.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h über dem Bergland.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h zwischen Bonn und Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h entlang der Nordseeküste.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h im Umland von Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h am Rand der Stadt.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h in den Bergen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h auf dem offenen Meer.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h von Aachen bis Düren.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h in den Tälern.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 85 km/h ausschließlich in höheren Lagen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h nur in der Eifel.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h nur im Harz.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h im Norden des Kreises.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h östlich von Bonn.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h auf der Zugspitze.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h über dem Bergland.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h zwischen Bonn und Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h entlang der Nordseeküste.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h im Umland von Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h am Rand der Stadt.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h in den Bergen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h auf dem offenen Meer.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h von Aachen bis Düren.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h in den Tälern.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 89 km/h ausschließlich in höheren Lagen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h nur in der Eifel.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h nur im Harz.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h im Norden des Kreises.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h östlich von Bonn.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h auf der Zugspitze.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h über dem Bergland.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h zwischen Bonn und Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h entlang der Nordseeküste.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h im Umland von Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h am Rand der Stadt.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h in den Bergen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h auf dem offenen Meer.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h von Aachen bis Düren.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h in den Tälern.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 90 km/h ausschließlich in höheren Lagen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h nur in der Eifel.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h nur im Harz.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h im Norden des Kreises.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h östlich von Bonn.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h auf der Zugspitze.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h über dem Bergland.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h zwischen Bonn und Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h entlang der Nordseeküste.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h im Umland von Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h am Rand der Stadt.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h in den Bergen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h auf dem offenen Meer.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h von Aachen bis Düren.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h in den Tälern.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 95 km/h ausschließlich in höheren Lagen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h nur in der Eifel.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h nur im Harz.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h im Norden des Kreises.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h östlich von Bonn.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h auf der Zugspitze.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h über dem Bergland.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h zwischen Bonn und Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h entlang der Nordseeküste.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h im Umland von Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h am Rand der Stadt.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h in den Bergen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h auf dem offenen Meer.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h von Aachen bis Düren.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h in den Tälern.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 110 km/h ausschließlich in höheren Lagen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h nur in der Eifel.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h nur im Harz.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h im Norden des Kreises.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h östlich von Bonn.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h auf der Zugspitze.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h über dem Bergland.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h zwischen Bonn und Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h entlang der Nordseeküste.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h im Umland von Köln.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h am Rand der Stadt.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h in den Bergen.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h auf dem offenen Meer.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h von Aachen bis Düren.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h in den Tälern.', False, 'Windwarnung', 60, {}),
 ('location', 'Böen 145 km/h ausschließlich in höheren Lagen.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h in allen Teilen des Warngebiets.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h überall im Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h flächendeckend im Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h im ganzen Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h innerhalb des gesamten Warngebiets.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h im gesamten ausgegebenen Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h in allen Regionen des Warngebietes.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 65 km/h über das gesamte Warngebiet verteilt.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h in allen Teilen des Warngebiets.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h überall im Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h flächendeckend im Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h im ganzen Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h innerhalb des gesamten Warngebiets.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h im gesamten ausgegebenen Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h in allen Regionen des Warngebietes.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 85 km/h über das gesamte Warngebiet verteilt.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h in allen Teilen des Warngebiets.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h überall im Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h flächendeckend im Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h im ganzen Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h innerhalb des gesamten Warngebiets.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h im gesamten ausgegebenen Warngebiet.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h in allen Regionen des Warngebietes.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 89 km/h über das gesamte Warngebiet verteilt.', False, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h in allen Teilen des Warngebiets.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h überall im Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h flächendeckend im Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h im ganzen Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h innerhalb des gesamten Warngebiets.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h im gesamten ausgegebenen Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h in allen Regionen des Warngebietes.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 90 km/h über das gesamte Warngebiet verteilt.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h in allen Teilen des Warngebiets.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h überall im Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h flächendeckend im Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h im ganzen Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h innerhalb des gesamten Warngebiets.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h im gesamten ausgegebenen Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h in allen Regionen des Warngebietes.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 95 km/h über das gesamte Warngebiet verteilt.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h in allen Teilen des Warngebiets.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h überall im Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h flächendeckend im Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h im ganzen Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h innerhalb des gesamten Warngebiets.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h im gesamten ausgegebenen Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h in allen Regionen des Warngebietes.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 110 km/h über das gesamte Warngebiet verteilt.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h in allen Teilen des Warngebiets.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h überall im Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h flächendeckend im Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h im ganzen Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h innerhalb des gesamten Warngebiets.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h im gesamten ausgegebenen Warngebiet.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h in allen Regionen des Warngebietes.', True, 'Windwarnung', 60, {}),
 ('whole_area', 'Böen 145 km/h über das gesamte Warngebiet verteilt.', True, 'Windwarnung', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Hagel nur auf Inseln', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Starkregen nur in der Eifel', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Schnee nur auf den Bergen', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Frost nur in Tälern', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Regen nur in Höhenlagen', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Nebel nur an der Küste', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Glatteis nur in Randlagen', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Hitzewarnung nur in der Innenstadt', 60, {}),
 ('other_event_header', 'Böen 65 km/h im gesamten Warngebiet.', False, 'Schneefall nur im Harz', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Hagel nur auf Inseln', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Starkregen nur in der Eifel', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Schnee nur auf den Bergen', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Frost nur in Tälern', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Regen nur in Höhenlagen', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Nebel nur an der Küste', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Glatteis nur in Randlagen', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Hitzewarnung nur in der Innenstadt', 60, {}),
 ('other_event_header', 'Böen 85 km/h im gesamten Warngebiet.', False, 'Schneefall nur im Harz', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Hagel nur auf Inseln', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Starkregen nur in der Eifel', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Schnee nur auf den Bergen', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Frost nur in Tälern', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Regen nur in Höhenlagen', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Nebel nur an der Küste', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Glatteis nur in Randlagen', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Hitzewarnung nur in der Innenstadt', 60, {}),
 ('other_event_header', 'Böen 89 km/h im gesamten Warngebiet.', False, 'Schneefall nur im Harz', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Hagel nur auf Inseln', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Starkregen nur in der Eifel', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Schnee nur auf den Bergen', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Frost nur in Tälern', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Regen nur in Höhenlagen', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Nebel nur an der Küste', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Glatteis nur in Randlagen', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Hitzewarnung nur in der Innenstadt', 60, {}),
 ('other_event_header', 'Böen 90 km/h im gesamten Warngebiet.', True, 'Schneefall nur im Harz', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Hagel nur auf Inseln', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Starkregen nur in der Eifel', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Schnee nur auf den Bergen', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Frost nur in Tälern', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Regen nur in Höhenlagen', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Nebel nur an der Küste', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Glatteis nur in Randlagen', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Hitzewarnung nur in der Innenstadt', 60, {}),
 ('other_event_header', 'Böen 95 km/h im gesamten Warngebiet.', True, 'Schneefall nur im Harz', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Hagel nur auf Inseln', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Starkregen nur in der Eifel', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Schnee nur auf den Bergen', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Frost nur in Tälern', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Regen nur in Höhenlagen', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Nebel nur an der Küste', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Glatteis nur in Randlagen', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Hitzewarnung nur in der Innenstadt', 60, {}),
 ('other_event_header', 'Böen 110 km/h im gesamten Warngebiet.', True, 'Schneefall nur im Harz', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Hagel nur auf Inseln', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Starkregen nur in der Eifel', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Schnee nur auf den Bergen', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Frost nur in Tälern', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Regen nur in Höhenlagen', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Nebel nur an der Küste', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Glatteis nur in Randlagen', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Hitzewarnung nur in der Innenstadt', 60, {}),
 ('other_event_header', 'Böen 145 km/h im gesamten Warngebiet.', True, 'Schneefall nur im Harz', 60, {}),
 ('height', 'Böen 65 km/h oberhalb 1200 m.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 65 km/h oberhalb 1200 m.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 65 km/h oberhalb 1200 m.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 65 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 65 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 65 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 65 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 65 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 65 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 65 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 65 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 65 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 65 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 65 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 65 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 85 km/h oberhalb 1200 m.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 85 km/h oberhalb 1200 m.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 85 km/h oberhalb 1200 m.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 85 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 85 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 85 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 85 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 85 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 85 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 85 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 85 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 85 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 85 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 85 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 85 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 89 km/h oberhalb 1200 m.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 89 km/h oberhalb 1200 m.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 89 km/h oberhalb 1200 m.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 89 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 89 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 89 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 89 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 89 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 89 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 89 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 89 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 89 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 89 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 89 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 89 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1500, {}),
 ('height', 'Böen 90 km/h oberhalb 1200 m.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 90 km/h oberhalb 1200 m.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 90 km/h oberhalb 1200 m.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 90 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 90 km/h ab einer Höhe von 1200 Metern.', True, 'Windwarnung', 1200, {}),
 ('height', 'Böen 90 km/h ab einer Höhe von 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 90 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 90 km/h ab einer Höhenlage von 1200 Metern.', True, 'Windwarnung', 1200, {}),
 ('height', 'Böen 90 km/h ab einer Höhenlage von 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 90 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 90 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 90 km/h auf Höhen über 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 90 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 90 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 90 km/h oberhalb von 1.200 Metern über NN.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 95 km/h oberhalb 1200 m.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 95 km/h oberhalb 1200 m.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 95 km/h oberhalb 1200 m.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 95 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 95 km/h ab einer Höhe von 1200 Metern.', True, 'Windwarnung', 1200, {}),
 ('height', 'Böen 95 km/h ab einer Höhe von 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 95 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 95 km/h ab einer Höhenlage von 1200 Metern.', True, 'Windwarnung', 1200, {}),
 ('height', 'Böen 95 km/h ab einer Höhenlage von 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 95 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 95 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 95 km/h auf Höhen über 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 95 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 95 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 95 km/h oberhalb von 1.200 Metern über NN.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 110 km/h oberhalb 1200 m.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 110 km/h oberhalb 1200 m.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 110 km/h oberhalb 1200 m.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 110 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 110 km/h ab einer Höhe von 1200 Metern.', True, 'Windwarnung', 1200, {}),
 ('height', 'Böen 110 km/h ab einer Höhe von 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 110 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 110 km/h ab einer Höhenlage von 1200 Metern.', True, 'Windwarnung', 1200, {}),
 ('height', 'Böen 110 km/h ab einer Höhenlage von 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 110 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 110 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 110 km/h auf Höhen über 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 110 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 110 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 110 km/h oberhalb von 1.200 Metern über NN.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 145 km/h oberhalb 1200 m.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 145 km/h oberhalb 1200 m.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 145 km/h oberhalb 1200 m.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 145 km/h ab einer Höhe von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 145 km/h ab einer Höhe von 1200 Metern.', True, 'Windwarnung', 1200, {}),
 ('height', 'Böen 145 km/h ab einer Höhe von 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 145 km/h ab einer Höhenlage von 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 145 km/h ab einer Höhenlage von 1200 Metern.', True, 'Windwarnung', 1200, {}),
 ('height', 'Böen 145 km/h ab einer Höhenlage von 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 145 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 145 km/h auf Höhen über 1200 Metern.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 145 km/h auf Höhen über 1200 Metern.', True, 'Windwarnung', 1500, {}),
 ('height', 'Böen 145 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 60, {}),
 ('height', 'Böen 145 km/h oberhalb von 1.200 Metern über NN.', False, 'Windwarnung', 1200, {}),
 ('height', 'Böen 145 km/h oberhalb von 1.200 Metern über NN.', True, 'Windwarnung', 1500, {})]

AUDIT_TIMES = [('effective', '9999-12-31T23:59:59-12:00'),
 ('effective', '0001-01-01T00:00:00+14:00'),
 ('effective', '0001-01-01T00:00:00Z'),
 ('effective', '9999-12-31T23:59:59+14:00'),
 ('onset', '9999-12-31T23:59:59-12:00'),
 ('onset', '0001-01-01T00:00:00+14:00'),
 ('onset', '0001-01-01T00:00:00Z'),
 ('onset', '9999-12-31T23:59:59+14:00'),
 ('expires', '9999-12-31T23:59:59-12:00'),
 ('expires', '0001-01-01T00:00:00+14:00'),
 ('expires', '0001-01-01T00:00:00Z'),
 ('expires', '9999-12-31T23:59:59+14:00'),
 ('event_end', '9999-12-31T23:59:59-12:00'),
 ('event_end', '0001-01-01T00:00:00+14:00'),
 ('event_end', '0001-01-01T00:00:00Z'),
 ('event_end', '9999-12-31T23:59:59+14:00')]


def _audit_run(description, *, title="Windwarnung", elevation=60, **changes):
    record = warning(description=description, headline=title, event="", parameters={},
                     effective=AUDIT_NOW - timedelta(days=1), onset=AUDIT_NOW - timedelta(hours=1),
                     expires=AUDIT_NOW + timedelta(days=1), event_end=None,
                     issued_at=AUDIT_NOW - timedelta(days=1), evidence_at=AUDIT_NOW)
    for key, value in changes.items():
        setattr(record, key, value)
    return policy.assess_official_warning(record, AUDIT_NOW, elevation=elevation)


@pytest.mark.parametrize("group,description,locked,title,elevation,changes", AUDIT_CASES)
def test_unchanged_external_warning_decisions(group, description, locked, title, elevation, changes):
    notice = _audit_run(description, title=title, elevation=elevation, **changes)
    assert notice is not None and notice["hard_lock"] is locked, (group, notice)
    json.dumps(notice, allow_nan=False)


@pytest.mark.parametrize("field,stamp", AUDIT_TIMES)
def test_unchanged_external_provider_dates_do_not_crash(field, stamp):
    notice = _audit_run("Böen 110 km/h.", **{field: stamp})
    json.dumps(notice, allow_nan=False)


WEATHER_ADJUNCTS = [
    "bei Schneegriesel", "bei Schneetreiben", "bei heftigem Schneegestöber",
    "bei gefrierender Nässe", "bei einer Wetterbesserung", "bei Wetterberuhigung",
    "bei starker Böigkeit", "bei Frühlingswetter", "bei Sommerwetter",
    "bei klaren Sichtverhältnissen", "unter einer Wetterverschlechterung",
    "bei Schneegriesel und gefrierender Nässe",
]


def _field_notice(statement, source, **changes):
    if source == "parameter":
        return assess(parameters={"gusts": statement}, headline="Windwarnung", **changes)
    return policy.assess_official_warning(warning(**{"headline": "Windwarnung", source: statement, **changes}),
                                          NOW, elevation=60)


@pytest.mark.parametrize("source", ["description", "headline", "event", "parameter"])
@pytest.mark.parametrize("condition", WEATHER_ADJUNCTS)
@pytest.mark.parametrize("speed", [89, 90, 110])
def test_meteorological_constituents_across_warning_fields(source, condition, speed):
    notice = _field_notice(f"Böen {speed} km/h {condition}.", source)
    assert notice["hard_lock"] is (speed >= 90)
    assert notice["gust_max_kmh"] == speed and not notice["gust_scope_uncertain"]


@pytest.mark.parametrize("place", [
    "bei Schneegrieselhausen", "bei Schneetreibenbach", "bei Winterberg",
    "beim Wetterkreuz", "bei einer Wetterstation", "bei Bonn", "im Ort Wetter",
    "bei Schneegriesel in der Eifel", "bei gefrierender Nässe an der Küste",
    "bei einer Wetterbesserung zwischen Köln und Bonn",
])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_weather_words_do_not_verify_unknown_places(place, parameters):
    notice = assess(f"Böen 110 km/h {place}.", parameters)
    assert not notice["hard_lock"] and notice["gust_scope_uncertain"]


@pytest.mark.parametrize("condition", WEATHER_ADJUNCTS[:6])
@pytest.mark.parametrize("height,locked", [(60, False), (1200, False), (1500, True)])
def test_weather_adjunct_does_not_remove_numeric_height(condition, height, locked):
    notice = assess(f"Böen 110 km/h {condition} oberhalb 1.200 m.", elevation=height)
    assert notice["hard_lock"] is locked


PREDICATES = [
    ("gelten inzwischen als ausgeschlossen", False),
    ("gelten aller Voraussicht nach als ausgeschlossen", False),
    ("sind derzeit ausgeschlossen", False),
    ("sind aller Voraussicht nach ausgeschlossen", False),
    ("bleiben garantiert aus", False),
    ("werden aller Voraussicht nach nicht auftreten", False),
    ("werden nicht derzeit erwartet", False),
    ("sind momentan nicht zu erwarten", False),
    ("gelten inzwischen als nicht ausgeschlossen", True),
    ("sind derzeit nicht ausgeschlossen", True),
    ("bleiben garantiert nicht aus", True),
    ("sind nicht garantiert ausgeschlossen", True),
    ("werden nicht sicher erwartet", True),
    ("werden garantiert erwartet", True),
]


@pytest.mark.parametrize("predicate,locked", PREDICATES)
@pytest.mark.parametrize("source", ["description", "headline", "event", "parameter"])
def test_predicate_time_certainty_and_exclusion_keep_their_polarity(predicate, locked, source):
    notice = _field_notice(f"Böen 110 km/h {predicate}.", source)
    assert notice["hard_lock"] is locked


@pytest.mark.parametrize("subject", ["Schäden", "Hagel", "Schneefall", "Sichtbehinderungen"])
@pytest.mark.parametrize("predicate", [
    "gelten inzwischen als ausgeschlossen", "sind aller Voraussicht nach ausgeschlossen",
    "bleiben garantiert aus", "werden derzeit nicht erwartet", "sind nicht auszuschließen",
])
@pytest.mark.parametrize("separator", [", ", "; "])
def test_another_subjects_forecast_does_not_deny_gusts(subject, predicate, separator):
    if subject in {"Hagel", "Schneefall"}:
        for plural, singular in [("gelten", "gilt"), ("sind", "ist"), ("bleiben", "bleibt"), ("werden", "wird")]:
            predicate = predicate.replace(plural, singular)
    notice = assess(f"Böen 110 km/h bei gefrierender Nässe{separator}{subject} {predicate}.")
    assert notice["hard_lock"] and notice["gust_max_kmh"] == 110


@pytest.mark.parametrize("predicate,locked", [
    ("werden derzeit nicht erwartet", False), ("gelten inzwischen als ausgeschlossen", False),
    ("bleiben garantiert aus", False), ("sind derzeit nicht ausgeschlossen", True),
])
def test_coordinated_weather_adjunct_keeps_the_gust_predicate(predicate, locked):
    notice = assess(f"Böen 110 km/h bei gefrierender Nässe und Hagel {predicate}.")
    assert notice["hard_lock"] is locked


@pytest.mark.parametrize("predicate", [
    "gelten inzwischen als ausgeschlossen", "sind aller Voraussicht nach ausgeschlossen",
    "bleiben garantiert aus", "werden aller Voraussicht nach nicht auftreten",
])
def test_new_denial_stays_visible_in_a_source_conflict(predicate):
    notice = assess("Böen 110 km/h werden erwartet.", headline=f"Böen 110 km/h {predicate}.")
    assert notice["gust_conflict"] and notice["gust_polarity_conflict"]
    assert not notice["hard_lock"]
    assert {item["denied"] for item in notice["gust_evidence"]} == {False, True}


@pytest.mark.parametrize("stamp,expected", [
    ("0001-01-01T00:00:00Z", "0001-01-01T00:00:00+00:00"),
    ("0001-01-01T00:00:00-14:00", "0001-01-01T14:00:00+00:00"),
    ("9999-12-31T23:59:59+14:00", "9999-12-31T09:59:59+00:00"),
    ("9999-12-31T23:59:59.999999Z", "9999-12-31T23:59:59.999999+00:00"),
    ("0001-01-01T00:00:00+14:00", None),
    ("9999-12-31T23:59:59-12:00", None),
    ("0000-01-01T00:00:00Z", None), ("10000-01-01T00:00:00Z", None),
    ("2026-10-25T12:00:00+25:00", None), ("2026-10-25T12:00:00", None),
    (None, None), (False, None), ([], None), ({}, None),
])
def test_utc_normalization_has_explicit_representable_limits(stamp, expected):
    normalized = policy.aware(stamp)
    assert (normalized.isoformat() if normalized else None) == expected


@pytest.mark.parametrize("field", ["effective", "onset", "expires", "event_end"])
@pytest.mark.parametrize("stamp", [
    "0001-01-01T00:00:00+14:00", "9999-12-31T23:59:59-12:00",
    "0000-01-01T00:00:00Z", "10000-01-01T00:00:00Z", "bad-time",
    datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=14))),
    datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone(-timedelta(hours=12))),
])
def test_invalid_cap_times_remain_an_uncertain_notice(field, stamp):
    notice = assess("Böen 110 km/h.", **{field: stamp})
    assert notice is not None and notice["phase"] == "time_uncertain"
    assert notice["timing_uncertain"] and not notice["hard_lock"]
    json.dumps(notice, allow_nan=False)


@pytest.mark.parametrize("minutes,microseconds,locked", [(0, 0, False), (30, -1, False), (30, 0, True)])
def test_thirty_minute_lead_at_datetime_minimum_is_not_wrapped_or_guessed(minutes, microseconds, locked):
    minimum = datetime.min.replace(tzinfo=timezone.utc)
    onset = minimum + timedelta(minutes=minutes, microseconds=microseconds)
    notice = assess("Böen 110 km/h.", now=minimum + timedelta(minutes=15),
                    effective=None, onset=onset, expires=minimum + timedelta(days=1))
    assert notice["hard_lock"] is locked
    assert notice["timing_uncertain"] is (not locked)
    if locked:
        assert notice["lock_from"] == minimum.isoformat() and notice["phase"] == "prelock"
    else:
        assert notice["phase"] == "time_uncertain" and notice["lock_from"] is None


def test_valid_maximum_date_uses_datetime_ordering_and_keeps_normal_lead():
    onset = datetime(9999, 12, 31, 23, 0, tzinfo=timezone.utc)
    notice = assess("Böen 110 km/h.", effective=None, onset=onset,
                    expires=datetime.max.replace(tzinfo=timezone.utc), now=onset - timedelta(minutes=30))
    assert notice["hard_lock"] and notice["phase"] == "prelock"
    assert notice["lock_from"] == "9999-12-31T22:30:00+00:00"


@pytest.mark.parametrize("description,onset,expires", [
    ("Böen 110 km/h ab 00 Uhr CET.", "0001-01-01T00:30:00Z", "0001-01-01T01:00:00Z"),
    ("Böen 110 km/h ab 23 Uhr CET.", "9999-12-31T22:30:00Z", "9999-12-31T23:30:00Z"),
    ("Böen 110 km/h ab 0001-01-01T00:00:00+14:00.", None, None),
    ("Böen 110 km/h ab 9999-12-31T23:59:59-12:00.", None, None),
])
def test_textual_clock_and_offset_overflows_remain_unresolved(description, onset, expires):
    changes = {key: value for key, value in {"onset": onset, "expires": expires}.items() if value}
    now = policy.aware(onset) if onset else NOW
    notice = assess(description, effective=None, now=now, **changes)
    assert not notice["hard_lock"] and notice["gust_time_uncertain"]
    assert notice["phase"] == "time_uncertain" and notice["lock_from"] is None


@pytest.mark.parametrize("field,stamp", [
    ("effective", "9999-12-31T23:59:59-12:00"),
    ("onset", "0001-01-01T00:00:00+14:00"),
    ("onset", "0001-01-01T00:00:00Z"),
    ("expires", "9999-12-31T23:59:59-12:00"),
    ("event_end", "0001-01-01T00:00:00+14:00"),
])
def test_actual_cap_normalization_and_provider_keep_old_lock_status_unknown(field, stamp):
    cap = _extract("auto_providers.py", {"_warning_times"}, {"_cap_time": policy.aware})
    times = dict(effective=NOW - timedelta(hours=1), onset=NOW - timedelta(minutes=30),
                 expires=NOW + timedelta(hours=2), event_end=None)
    times[field] = stamp
    normalized = cap["_warning_times"](**times)
    scope, entry = _provider_case(warning(description="Böen 110 km/h.", **normalized))
    current = scope["_automatic_warning_assessment"](SimpleNamespace(), entry)
    assert not current.weather_hard_lock and current.warning_ambiguous_clear
    assert current.warning_notices[0]["phase"] == "time_uncertain"
    assert current.warning_notice_kind != "all_clear" and current.warning_observations == []
    previous = {"source_key": current.safety_source_key, "warning_ids": ["scoped"]}
    safety = _safety()["_warning_provider_availability"]
    assert safety(SimpleNamespace(), entry, current, previous)[0] == "unknown"
    # A later, valid lower-wind forecast is still authoritative clearance.
    valid_scope, valid_entry = _provider_case(warning(description="Böen 70 km/h."))
    valid = valid_scope["_automatic_warning_assessment"](SimpleNamespace(), valid_entry)
    assert not valid.warning_ambiguous_clear
    assert safety(SimpleNamespace(), valid_entry, valid, previous)[0] == "clear"


def test_manual_invalid_time_does_not_clear_a_stored_dwd_lock():
    scope = _provider()
    scope["dt_util"] = SimpleNamespace(utcnow=lambda: NOW)
    current = scope["WarningAssessment"](safety_source_key="dwd-entry")
    record = warning(description="Böen 110 km/h.", onset="0001-01-01T00:00:00Z")
    notice = scope["_apply_manual_official_notice"](current, record, entity_id="sensor.dwd")
    assert notice["timing_uncertain"] and current.warning_ambiguous_clear
    hass = SimpleNamespace(config_entries=SimpleNamespace(async_get_entry=lambda key:
                           SimpleNamespace(domain="dwd_weather_warnings", entry_id=key)))
    entry = SimpleNamespace(data={"warning_source": "dwd-entry"})
    previous = {"source_key": "dwd-entry", "source_entity": "sensor.dwd", "warning_ids": ["scoped"]}
    safety = _safety()["_warning_provider_availability"]
    assert safety(hass, entry, current, previous)[0] == "unknown"
    # A separate, confirmed current hazard still wins over ambiguous data.
    current.weather_hard_lock = True
    assert safety(hass, entry, current, previous)[0] == "active"


@pytest.mark.parametrize("stamp", ["0001-01-01T00:00:00+14:00", "9999-12-31T23:59:59-12:00", "bad-time"])
@pytest.mark.parametrize("adapter", ["dwd", "nina"])
def test_actual_manual_adapter_preserves_failed_normalization(stamp, adapter):
    scope = _provider()
    scope["dt_util"] = SimpleNamespace(utcnow=lambda: NOW)
    scope["AutoWarningRecord"] = _extract("auto_providers.py", {"AutoWarningRecord"})["AutoWarningRecord"]
    if adapter == "dwd":
        entity = "sensor.dwd"
        state = SimpleNamespace(state="2", attributes={
            "warning_count": 1, "warning_1_identifier": "scoped", "warning_1_headline": "Windwarnung",
            "warning_1_description": "Böen 110 km/h.", "warning_1_start": stamp,
            "warning_1_end": (NOW + timedelta(hours=2)).isoformat()})
        env = _extract("providers.py", {"_evaluate_dwd_warning_entities", "_dwd_warning_key",
            "_float", "_state_float", "_weather_warning_kind", "_weather_reason_key", "WEATHER_WARNING_WORDS"},
            {**scope, "math": math})
        evaluate = env["_evaluate_dwd_warning_entities"]
    else:
        entity = "binary_sensor.nina"
        state = SimpleNamespace(state="on", attributes={
            "id": "scoped", "headline": "Windwarnung", "description": "Böen 110 km/h.",
            "onset": stamp, "expires": (NOW + timedelta(hours=2)).isoformat()})
        env = _extract("providers.py", {"_text"}, scope)
        scope.update(_text=env["_text"], _nina_slot_sensor_values=lambda *args: {})
        evaluate = scope["_evaluate_nina_like_entities"]
    current = evaluate(SimpleNamespace(states=SimpleNamespace(get=lambda key: state)), [entity])
    assert not current.weather_hard_lock and current.warning_ambiguous_clear
    assert current.warning_notices[0]["phase"] == "time_uncertain"
    assert current.warning_notice_kind != "all_clear"


def test_uncertain_time_does_not_renew_or_extend_the_existing_fallback_ttl():
    validity = _extract("safety_state.py", {"_record_is_valid"}, {
        "_parse_datetime": policy.aware, "timedelta": timedelta,
        "SAFETY_FALLBACK_MAX_AGE": timedelta(hours=1)})["_record_is_valid"]
    stored = {"source_key": "auto_warning:50.7:7.1", "last_confirmed_at": NOW.isoformat(),
              "valid_until": (NOW + timedelta(hours=1)).isoformat()}
    assert validity(stored, stored["source_key"], NOW + timedelta(minutes=59))
    assert not validity(stored, stored["source_key"], NOW + timedelta(hours=1))


# CAP language/normalization regressions retained in the existing test file.
import json as _cap_language_json
import pytest as _cap_language_pytest
from test_v0119_warning_scopes_pure import assess as _cap_language_assess, policy as _cap_language_policy, warning as _cap_language_warning

@_cap_language_pytest.mark.parametrize('speed', [90, 110, 145])
@_cap_language_pytest.mark.parametrize('text,locked', [('Böen {speed} km/h bei guter Sicht.', True), ('Böen {speed} km/h bei Nebel.', True), ('Böen {speed} km/h bei guter Sicht im Harz.', False), ('Gusts of {speed} km/h are now ruled out.', False), ('Gusts of {speed} km/h have been ruled out.', False), ('Gusts of {speed} km/h are expected.', True), ('Rüzgâr hamleleri {speed} km/h sadece dağlarda.', False), ('Wind gusts of {speed} km/h only in mountainous areas.', False), ('Rüzgâr hamleleri {speed} km/h ihtimali ortadan kalktı.', False), ('Rüzgâr hamleleri {speed} km/h beklenmiyor.', False), ('Rüzgâr hamleleri {speed} km/h bekleniyor.', True), ('Rüzgâr hamleleri {speed} km/sa hıza ulaşması bekleniyor.', True)])
def test_reported_language_matrix(speed, text, locked):
    notice = _cap_language_assess(text.format(speed=speed))
    assert notice['hard_lock'] is locked, notice
    _cap_language_json.dumps(notice, allow_nan=False)

@_cap_language_pytest.mark.parametrize('language', ['de', 'en', 'tr'])
@_cap_language_pytest.mark.parametrize('description', ['Böen 110 km/h bei guter Sicht.', 'Wind gusts 110 km/h expected.', 'Rüzgâr hamleleri 110 km/sa bekleniyor.'])
def test_interface_language_never_selects_warning_parser(language, description):
    result = _cap_language_assess(description, ui_language=language)
    assert result['hard_lock']
    analysis = _cap_language_policy._warnings.analyze(_cap_language_warning(description=description), elevation=60)
    assert analysis.assertions[0].event == 'wind_gust'
    assert analysis.assertions[0].quantity.unit == 'km/h'
    assert analysis.assertions[0].quantity.maximum == 110
    assert analysis.assertions[0].polarity == 'affirmative'

@_cap_language_pytest.mark.parametrize('description,locked', [('Gusts 110 km/h are currently ruled out.', False), ('Gusts 110 km/h are now not ruled out.', True), ('Gusts 110 km/h are now expected; damage is ruled out.', True), ('Rüzgâr hamleleri 110 km/h ihtimali ortadan kalkmadı.', True), ('Rüzgâr hamleleri 110 km/h, hasar ihtimali ortadan kalktı.', True), ('Böen 110 km/h bei guter Sicht über 1000 m.', False), ('Rüzgâr hamleleri 110 km/h dağlık bölgelerde.', False)])
def test_language_scope_and_polarity_counterpairs(description, locked):
    assert _cap_language_assess(description)['hard_lock'] is locked

def test_unknown_language_is_not_a_clear_or_an_invented_numeric_warning():
    result = _cap_language_assess('風速110 km/h', language='ja-JP', headline='暴風')
    assert not result['hard_lock']
    assert result['interpretation_uncertain']
    assert 'unsupported_language' in result['language_issues']

def test_cap_language_mismatch_keeps_recognizable_official_subject():
    result = _cap_language_assess('Böen 110 km/h erwartet.', language='en-US')
    assert result['hard_lock']
    assert 'language_mismatch' in result['language_issues']

def test_language_capabilities_are_separate_from_interface_registration():
    languages = _cap_language_policy._warnings.capabilities.__globals__
    assert languages['UI_LANGUAGES'] == ('de', 'en', 'tr')
    capabilities = languages['capabilities']()
    assert capabilities['tr']['ui']
    assert not capabilities['fr']['ui']
    assert all((item['warning_text'] == 'bounded_rules' for item in capabilities.values()))

def test_nws_profile_requires_explicit_unit_and_never_infers_from_severity():
    good = _cap_language_assess(parameters={'maxWindGust': '60 MPH'}, provider_domain='nws_auto', headline='Wind')
    assert good['hard_lock'] and good['gust_max_kmh'] == _cap_language_pytest.approx(96.56064)
    assert good['gust_evidence'][0]['provider_profile'] == 'nws-cap-v1'
    bare = _cap_language_assess(parameters={'maxWindGust': '110'}, provider_domain='nws_auto', severity='Extreme')
    unknown = _cap_language_assess(parameters={'maxWindGust': '110 km/h'}, provider_domain='unknown_provider')
    assert not bare['hard_lock'] and (not unknown['hard_lock'])


def _profiled_cap_notice(infos, *, provider="nws_auto", now=NOW, elevation=60, actions=False):
    record = warning(headline="", description="", provider_domain=provider)
    defaults = {"effective": (NOW - timedelta(hours=1)).isoformat(),
                "onset": (NOW - timedelta(minutes=10)).isoformat(),
                "expires": (NOW + timedelta(hours=2)).isoformat()}
    cap = policy._warnings
    cap.attach_infos(record, tuple(cap.info_block({**defaults, **item}, index)
                                    for index, item in enumerate(infos)), now=now)
    close = False
    if actions:
        _, close, _ = cap.action_context(record, _provider()["_evaluate_air_warning"], now, elevation=elevation)
    return policy.assess_official_warning(record, now, explicit_close=close, elevation=elevation)


@pytest.mark.parametrize("language", ["de-DE", "en-US", "tr-TR", "ja-JP", "zh-CN", "ko-KR"])
def test_reported_profiled_quantity_is_independent_of_warning_language(language):
    result = _profiled_cap_notice([{"language": language,
        "description": "風が強まります" if language == "ja-JP" else "Starker Wind",
        "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}])
    assert result["hard_lock"] and result["gust_max_kmh"] == 110
    evidence = next(item for item in result["gust_evidence"] if item["evidence_kind"] == "structured_cap")
    assert evidence["parameter"] == "maxWindGust"
    assert evidence["provenance"][0]["language"] == language
    assert evidence["provenance"][0]["field"] == "parameter:maxWindGust"
    json.dumps(result, allow_nan=False)


def test_reported_high_profiled_quantity_in_unknown_translation_is_retained():
    result = _profiled_cap_notice([
        {"language": "de-DE", "description": "Böen 70 km/h."},
        {"language": "ja-JP", "description": "風が強まります",
         "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]},
    ])
    assert result["hard_lock"] and result["gust_max_kmh"] == 110
    assert result["gust_value_conflict"]
    assert {item["max"] for item in result["gust_evidence"]} == {70, 110}


@pytest.mark.parametrize("language", ["de-DE", "en-US", "tr-TR", "ja-JP"])
def test_reported_recognized_close_command_survives_incorrect_language_metadata(language):
    result = _profiled_cap_notice([{"language": language, "headline": "Rauch",
        "description": "Giftiger Rauch zieht auf.", "instruction": "Fenster und Türen schließen."}],
        provider="nina_auto_mowas", actions=True)
    assert result["hard_lock"] and result["explicit_close"]
    source = result["close_evidence"][0]["provenance"]
    assert source["language"] == language and source["detected_language"] == "de"
    if language != "de-DE":
        assert "language_mismatch" in result["language_issues"]
        assert source["language_mismatch"]


def test_structured_extractor_does_not_call_language_selection(monkeypatch):
    cap = policy._warnings
    def forbidden(*args, **kwargs):
        raise AssertionError("structured CAP quantities must not use text parsing")
    monkeypatch.setattr(cap, "select", forbidden)
    record = warning(provider_domain="nws_auto", language="ja-JP", headline="暴風",
                     parameters={"maxWindGust": "110 km/h"})
    findings = cap.extract_structured_cap(record, elevation=60)
    assert len(findings.assertions) == 1
    assert isinstance(findings.assertions[0], cap.WarningAssertion)
    assert findings.assertions[0].quantity.maximum == 110


@pytest.mark.parametrize("value,expected,locked", [
    ("89.999 km/h", 89.999, False), ("90 km/h", 90, True),
    ("110 km/h", 110, True), ("25 m/s", 90, True),
    ("60 MPH", 96.56064, True), ("50 mph", 80.4672, False),
    ("50 knots", 92.6, True), ("110 [km/h]", 110, True),
])
def test_profiled_quantity_uses_explicit_units_before_the_single_policy(value, expected, locked):
    result = _profiled_cap_notice([{"language": "ja-JP", "description": "強風",
                                   "parameter": [{"valueName": "maxWindGust", "value": value}]}])
    assert result["hard_lock"] is locked
    assert result["gust_max_kmh"] == pytest.approx(expected)


@pytest.mark.parametrize("value", ["110", 110, True, None, {"value": "110 km/h"},
                                    "110 furlongs/h", "110 km/h only in the mountains", "gusts 110 km/h",
                                    "NaN km/h", "Infinity km/h", "501 km/h", "300 m/s",
                                    "110 [km/h", "110 km/h]"])
def test_malformed_profiled_value_cannot_fall_back_into_a_text_number(value):
    result = _profiled_cap_notice([{"language": "en-US", "headline": "Wind",
                                   "parameter": [{"valueName": "maxWindGust", "value": value}]}])
    assert not result["hard_lock"] and result["gust_max_kmh"] is None
    assert result["interpretation_uncertain"]
    assert "invalid_structured_gust" in result["language_issues"]


@pytest.mark.parametrize("provider,key", [("unrecognized_provider", "maxWindGust"),
                                          ("nws_auto", "someNumber"), ("meteoalarm_auto", "maxWindGust")])
def test_unprofiled_unknown_language_numbers_do_not_become_authoritative(provider, key):
    result = _profiled_cap_notice([{"language": "ja-JP", "description": "強風",
                                   "parameter": [{"valueName": key, "value": "110 km/h"}]}], provider=provider)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


def test_profiled_and_textual_claims_remain_separate_in_a_real_polarity_conflict():
    result = _profiled_cap_notice([{"language": "en-US", "description": "Gusts 110 km/h are now ruled out.",
                                   "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}])
    assert result["gust_polarity_conflict"] and result["interpretation_uncertain"]
    assert not result["hard_lock"]
    assert any(item["evidence_kind"] == "structured_cap" and not item["denied"] for item in result["gust_evidence"])


@pytest.mark.parametrize("minutes,microseconds,locked", [(30, 0, True), (30, 1, False), (31, 0, False)])
def test_profiled_quantities_keep_the_exact_common_lead_time(minutes, microseconds, locked):
    result = _profiled_cap_notice([{"language": "ja-JP", "description": "強風",
        "onset": (NOW + timedelta(minutes=minutes, microseconds=microseconds)).isoformat(),
        "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}])
    assert result["hard_lock"] is locked


def test_unverified_cap_area_still_blocks_a_profiled_quantity():
    cap = policy._warnings
    record = warning(provider_domain="nws_auto", headline="", description="", language="ja-JP",
                     parameters={"maxWindGust": "110 km/h"}, area_restriction_unknown=True)
    result = policy.assess_official_warning(record, NOW, elevation=60)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]
    assert cap.extract_structured_cap(record, elevation=60).assertions[0].area.verified is False


def test_each_text_pack_has_an_isolated_subject_vocabulary():
    cap = policy._warnings
    english = warning(headline="", event="", description="Gusts 110 km/h expected.", parameters={})
    german = warning(headline="", event="", description="Böen 110 km/h erwartet.", parameters={})
    assert cap.EnglishWarningLanguage.extract(english, elevation=60).descriptions[0]["max"] == 110
    assert not cap.GermanWarningLanguage.extract(english, elevation=60).descriptions
    assert cap.GermanWarningLanguage.extract(german, elevation=60).descriptions[0]["max"] == 110
    assert not cap.EnglishWarningLanguage.extract(german, elevation=60).descriptions


def test_profiled_numbers_work_with_every_text_pack_disabled():
    cap = policy._warnings
    codes = [pack.CODE for pack in cap.installed()]
    try:
        for code in codes:
            cap.set_warning_language_enabled("fr" if code == "compat" else code, False)
        assert not cap.installed()
        for language in ("de-DE", "en-US", "tr-TR", "ja-JP", ""):
            result = _profiled_cap_notice([{"language": language, "description": "強風",
                "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}])
            assert result["hard_lock"] and result["gust_max_kmh"] == 110
    finally:
        for code in codes:
            cap.set_warning_language_enabled("fr" if code == "compat" else code, True)


def test_mixed_language_parsers_are_reentrant():
    from concurrent.futures import ThreadPoolExecutor
    inputs = [("Böen 110 km/h nicht erwartet.", False),
              ("Gusts 110 km/h expected.", True),
              ("Rüzgâr hamleleri 110 km/sa sadece dağlarda.", False)] * 4
    with ThreadPoolExecutor(max_workers=3) as workers:
        results = list(workers.map(lambda item: assess(item[0])["hard_lock"], inputs))
    assert results == [locked for _, locked in inputs]

# COMPLETE(8) findings: CAP numeric independence, local regional maxima,
# separately switchable FR/ES/IT/NL warning-text packs.
@pytest.mark.parametrize("language,field,value", [
    ("ja-JP", "gusts", "~110 [km/h]"),
    ("zh-CN", "gusts", "110 km/h"),
    ("ko-KR", "Gusts", "~110 [km/h]"),
    ("es-ES", "gusts", "110 [km/h]"),
])
def test_dwd_profiled_gusts_are_text_language_independent(language, field, value):
    notice = _profiled_cap_notice([{
        "language": language, "description": "風が強まります",
        "parameter": [{"valueName": field, "value": value}],
    }], provider="nina_auto_dwd")
    assert notice["hard_lock"] and notice["gust_max_kmh"] == 110
    # The numeric extractor is independent even if a known-language legacy
    # parameter parser additionally supplies local/time context to the notice.
    cap = policy._warnings
    record = warning(provider_domain="nina_auto_dwd", language=language, headline="",
                     description="風が強まります", parameters={field: value})
    structured = cap.extract_structured_cap(record, elevation=60)
    assert structured.assertions[0].quantity.maximum == 110
    item = structured.assertions[0].to_evidence()
    assert item["provider_profile"] == "dwd-cap-v2.1.14"
    assert item["parameter_original_value"] == value
    assert item["provenance"][0]["field"] == f"parameter:{field}"


@pytest.mark.parametrize("value,lock,lower,upper,qualifier", [
    (">120 [km/h]", True, 120.0, None, "greater_than"),
    ("<50 [km/h]", False, None, 50.0, "less_than"),
    ("~110 [km/h]", True, 110.0, 110.0, "approximately"),
])
def test_dwd_inequalities_preserve_real_numeric_bounds(value, lock, lower, upper, qualifier):
    notice = _profiled_cap_notice([{
        "language": "ja-JP", "description": "風が強まります",
        "parameter": [{"valueName": "gusts", "value": value}],
    }], provider="nina_auto_dwd")
    assert notice["hard_lock"] is lock
    assert notice["gust_min_kmh"] == lower and notice["gust_max_kmh"] == upper
    assert notice["gust_evidence"][0]["quantity_qualifier"] == qualifier


@pytest.mark.parametrize("value", ["110 mph", "110", "110 [knots]", "501 [km/h]"])
def test_dwd_unknown_units_never_create_structured_cap_gusts(value):
    notice = _profiled_cap_notice([{
        "language": "ja-JP", "description": "風が強まります",
        "parameter": [{"valueName": "gusts", "value": value}],
    }], provider="nina_auto_dwd")
    assert not notice["hard_lock"]
    assert not any(i["evidence_kind"] == "structured_cap" for i in notice["gust_evidence"])


@pytest.mark.parametrize("language,description", [
    ("en-US", "Gusts 110 km/h only above 1200 m."),
    ("de-DE", "Böen 110 km/h nur oberhalb 1200 m."),
    ("en-US", "Gusts 110 km/h only on mountain summits."),
    ("de-DE", "Böen 110 km/h nur in den Bergen."),
])
def test_nws_structured_regional_maximum_inherits_explicit_same_info_scope(language, description):
    info = {"language": language, "description": description,
            "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}
    low = _profiled_cap_notice([info], elevation=60)
    assert not low["hard_lock"] and low["gust_max_kmh"] is None
    structured = next(i for i in low["gust_evidence"] if i["evidence_kind"] == "structured_cap")
    assert structured["location_explicit"] and not structured["location_verified"]
    assert structured["scope_from_description"] == description
    if "1200 m" in description:
        high = _profiled_cap_notice([info], elevation=1400)
        assert high["hard_lock"] and high["gust_max_kmh"] == 110


def test_regional_scope_only_binds_the_same_quantity_and_block():
    limited = {"language": "en-US", "description": "Gusts 110 km/h only above 1200 m.",
               "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}
    separate = {"language": "en-US", "description": "風が強まります",
                "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}
    assert _profiled_cap_notice([limited, separate], elevation=60)["hard_lock"]
    different_value = {"language": "en-US", "description": "Gusts 70 km/h only above 1200 m.",
                       "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}
    assert _profiled_cap_notice([different_value], elevation=60)["hard_lock"]
    independent = {"language": "en-US", "description":
                   "Gusts 110 km/h only above 1200 m. Gusts 110 km/h are expected.",
                   "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]}
    assert _profiled_cap_notice([independent], elevation=60)["hard_lock"]


def test_compatible_language_packs_toggle_one_at_a_time():
    cap = policy._warnings
    initial = {code: pack.ENABLED for code, pack in cap._WARNING_LANGUAGE_PACKS.items()}
    try:
        for language, text in (("fr", "Rafales 110 km/h."),
                               ("es", "Rachas 110 km/h."),
                               ("it", "Raffiche 110 km/h."),
                               ("nl", "Windstoten 110 km/h.")):
            assert cap.select(f"{language}-{language.upper()}", text)[0].CODE == language
        for language in ("fr", "es", "it", "nl"):
            cap.set_warning_language_enabled(language, False)
            assert language not in cap.capabilities()
            assert all(other in cap.capabilities() for other in
                       (set(("fr", "es", "it", "nl")) - {language}))
            cap.set_warning_language_enabled(language, True)
    finally:
        for language, enabled in initial.items():
            cap.set_warning_language_enabled(language, enabled)

# CAP audit, 2026-10-25: strict upper speeds and same-info event start.
@pytest.mark.parametrize("language", ["ja-JP", "zh-CN", "ko-KR", "de-DE", "en-US", "tr-TR"])
@pytest.mark.parametrize("limit", ["<90 [km/h]", "<90 km/h"])
def test_dwd_cap_strict_ceiling_at_90_never_locks(language, limit):
    notice = _profiled_cap_notice([{
        "language": language, "description": "風が強まります",
        "parameter": [{"valueName": "gusts", "value": limit}],
    }], provider="nina_auto_dwd")
    assert not notice["hard_lock"]
    assert notice["lock_from"] is None
    assert notice["gust_max_kmh"] is not None and notice["gust_max_kmh"] <= 90.0
    # Supported languages may additionally preserve the legacy parameter-text
    # interpretation; the central structured parser still records the exact bound.
    record = warning(provider_domain="nina_auto_dwd", headline="", language=language,
                     parameters={"gusts": limit})
    gust = policy._warnings.extract_structured_cap(record, elevation=60).assertions[0].to_evidence()
    assert gust["speed_interval"]["upper_inclusive"] is False
    assert gust["speed_interval"]["upper_kmh"] == 90.0
    json.dumps(notice, allow_nan=False)


@pytest.mark.parametrize("value,locked", [
    ("<89 [km/h]", False), ("<90 [km/h]", False),
    ("<90.0 [km/h]", False), ("<90,0 [km/h]", False),
    ("<91 [km/h]", True), ("90 [km/h]", True),
    ("~90 [km/h]", True), (">89 [km/h]", False),
    (">90 [km/h]", True), (">120 [km/h]", True),
])
def test_dwd_strict_bound_reaches_threshold_exactly_when_supported(value, locked):
    notice = _profiled_cap_notice([{"language": "ja-JP",
        "parameter": [{"valueName": "gusts", "value": value}]}], provider="nina_auto_dwd")
    assert notice["hard_lock"] is locked, value
    json.dumps(notice, allow_nan=False)


@pytest.mark.parametrize("language,description", [
    ("en-US", "Gusts 110 km/h from 18:00 UTC."),
    ("de-DE", "Böen 110 km/h ab 18 Uhr UTC."),
])
def test_nws_regional_maximum_inherits_proven_same_info_gust_onset(language, description):
    # Match a future 18:00 onset on the day of the original CAP event.
    record = warning(provider_domain="nws_auto", headline="Wind gusts", description=description,
                     language=language, parameters={"maxWindGust": "110 km/h"})
    for hour, minute, locked in [(12, 30, False), (17, 29, False), (17, 30, True)]:
        notice = policy.assess_official_warning(record, NOW.replace(hour=hour, minute=minute), elevation=60)
        assert notice["hard_lock"] is locked, (description, hour, minute)
        assert notice["lock_from"] == "2026-10-24T17:30:00+00:00"
        assert notice["gust_onset"] == "2026-10-24T18:00:00+00:00"
        structured = next(e for e in notice["gust_evidence"] if e["evidence_kind"] == "structured_cap")
        assert structured["time_explicit"]
        assert structured["time_reconciliation"] == "same_info_matching_quantity"
    assert policy.assess_official_warning(record, NOW.replace(hour=18, minute=0))["phase"] == "active"


def test_nws_other_wind_speed_or_other_hazard_does_not_narrow_the_cap_peak():
    for description in ("Gusts 70 km/h from 18:00 UTC.",
                        "Gusts 110 km/h. Lightning from 18:00 UTC.",
                        "Gusts 110 km/h. Gusts 110 km/h from 18:00 UTC."):
        notice = policy.assess_official_warning(warning(provider_domain="nws_auto",
             headline="Wind gusts", description=description, language="en-US",
             parameters={"maxWindGust": "110 km/h"}), NOW, elevation=60)
        assert notice["hard_lock"] and notice["gust_onset"] == warning().onset.isoformat(), description


def test_nws_one_cap_info_does_not_donate_its_later_time_to_another_info():
    notice = _profiled_cap_notice([
        {"language": "en-US", "description": "Gusts 110 km/h from 18:00 UTC.",
         "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]},
        {"language": "ja-JP", "description": "風が強まります",
         "parameter": [{"valueName": "maxWindGust", "value": "110 km/h"}]},
    ])
    assert notice["hard_lock"]
    assert any(item["evidence_kind"] == "structured_cap" and not item["time_explicit"]
               for item in notice["gust_evidence"])


def test_nws_unrecognized_time_and_language_preserve_original_cap_timing():
    for description, language in [("Gusts 110 km/h much later.", "en-US"),
                                  ("風が強まります", "ja-JP")]:
        notice = policy.assess_official_warning(warning(provider_domain="nws_auto",
            headline="Wind gusts", description=description, language=language,
            parameters={"maxWindGust": "110 km/h"}), NOW, elevation=60)
        assert notice["hard_lock"] and notice["gust_onset"] == warning().onset.isoformat()
