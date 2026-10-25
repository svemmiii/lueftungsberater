"""Wind assertions keep their noun group, polarity, conditions and scope."""
from datetime import timedelta
import math
import operator

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


# The independent COMPLETE (1)(7) audit's 82 inputs and original expectations.
# Result metadata and audit reports are intentionally not shipped with tests.
AUDIT_CASES = [
    ('Böen 110 km/h bei Eisregen.', 1500, True),
    ('Böen 110 km/h bei Schneeregen.', 1500, True),
    ('Böen 110 km/h bei Graupel.', 1500, True),
    ('Böen 110 km/h bei Glatteis.', 1500, True),
    ('Böen 110 km/h bei Gewitterschauern.', 1500, True),
    ('Böen 110 km/h bei Starkregen.', 1500, True),
    ('Böen 110 km/h bei Nebel.', 1500, True),
    ('Böen 110 km/h bei Schneefall.', 1500, True),
    ('Böen 110 km/h bei dichtem Nebel.', 1500, True),
    ('Böen 110 km/h bei Eisglätte.', 1500, True),
    ('Böen 110 km/h in Verbindung mit Eisregen.', 1500, True),
    ('Böen 110 km/h bei orkanartigen Böen.', 1500, True),
    ('Böen 110 km/h unter Gewitterschauern.', 1500, True),
    ('Böen 110 km/h sind mit Sicherheit nicht zu erwarten.', 1500, False),
    ('Böen 110 km/h sind ganz sicher nicht zu erwarten.', 1500, False),
    ('Böen 110 km/h werden unter keinen Umständen auftreten.', 1500, False),
    ('Böen 110 km/h sind zweifellos ausgeschlossen.', 1500, False),
    ('Böen 110 km/h sind nicht zu befürchten.', 1500, False),
    ('Böen 110 km/h werden nicht eintreten.', 1500, False),
    ('Böen 110 km/h werden keineswegs auftreten.', 1500, False),
    ('Böen 110 km/h treten auf keinen Fall auf.', 1500, False),
    ('Böen 110 km/h lassen sich sicher ausschließen.', 1500, False),
    ('Böen 110 km/h werden zu keiner Zeit auftreten.', 1500, False),
    ('Böen 110 km/h wurden offiziell ausgeschlossen.', 1500, False),
    ('Böen 110 km/h bleiben definitiv aus.', 1500, False),
    ('Böen 110 km/h sind ausgeschlossen.', 1500, False),
    ('Böen 110 km/h sind unmöglich.', 1500, False),
    ('Böen 110 km/h zwischen Bonn und Köln.', 60, False),
    ('Böen 110 km/h von Bonn bis Köln.', 60, False),
    ('Böen 110 km/h entlang der A4.', 60, False),
    ('Böen 110 km/h im Raum Eifel.', 60, False),
    ('Böen 110 km/h im Gebiet zwischen Köln und Bonn.', 60, False),
    ('Böen 110 km/h an der Ostseeküste.', 60, False),
    ('Böen 110 km/h nur entlang der Küste.', 60, False),
    ('Böen 110 km/h rund um den Harz.', 60, False),
    ('Böen 110 km/h südlich von Bonn.', 60, False),
    ('Böen 110 km/h auf den Gipfeln.', 60, False),
    ('Böen 110 km/h überall im Warngebiet.', 60, True),
    ('Böen 110 km/h im gesamten Warngebiet.', 60, True),
    ('Böen 110 km/h in allen Teilen des Warngebiets.', 60, True),
    ('Böen 110 km/h flächendeckend im Warngebiet.', 60, True),
    ('Böen 110 km/h überall innerhalb des Warngebiets.', 60, True),
    ('Böen 110 km/h in allen Regionen des Warngebietes.', 60, True),
    ('Böen 110 km/h im kompletten Warnbereich.', 60, True),
    ('Böen 110 km/h ab 1200 Metern.', 1500, True),
    ('Böen 110 km/h ab 1200 Metern.', 60, False),
    ('Böen 110 km/h ab einer Höhe von 1200 Metern.', 1500, True),
    ('Böen 110 km/h ab einer Höhe von 1200 Metern.', 60, False),
    ('Böen 110 km/h oberhalb 1200 m.', 1500, True),
    ('Böen 110 km/h oberhalb 1200 m.', 60, False),
    ('Böen 110 km/h oberhalb einer Höhe von 1200 m.', 1500, True),
    ('Böen 110 km/h oberhalb einer Höhe von 1200 m.', 60, False),
    ('Böen 110 km/h in Höhen über 1200 Metern.', 1500, True),
    ('Böen 110 km/h in Höhen über 1200 Metern.', 60, False),
    ('Böen 110 km/h in Höhenlagen oberhalb von 1200 m.', 1500, True),
    ('Böen 110 km/h in Höhenlagen oberhalb von 1200 m.', 60, False),
    ('Böen 110 km/h werden erwartet.', 1500, True),
    ('Böen 110 km/h sind möglich.', 1500, True),
    ('Böen 110 km/h sind keinesfalls ausgeschlossen.', 1500, True),
    ('Böen 110 km/h bei Starkregen.', 1500, True),
    ('Böen 110 km/h oberhalb von 1200 m.', 1500, True),
    ('Böen 110 km/h sind ausgeschlossen.', 60, False),
    ('Böen 110 km/h treten nicht auf.', 60, False),
    ('Böen 110 km/h sind unmöglich.', 60, False),
    ('Böen 110 km/h nur im Harz.', 60, False),
    ('Böen 110 km/h in höheren Lagen.', 60, False),
    ('Rafales jusqu’à 110 km/h.', 60, True),
    ('Rafales de vent jusqu’à 110 km/h.', 60, True),
    ('Vent avec rafales de 110 km/h.', 60, True),
    ('Rafales atteignant 110 km/h.', 60, True),
    ('Rachas de viento de 110 km/h.', 60, True),
    ('Rachas de hasta 110 km/h.', 60, True),
    ('Viento con rachas de 110 km/h.', 60, True),
    ('Se esperan rachas de viento de 110 km/h.', 60, True),
    ('Raffiche di 110 km/h.', 60, True),
    ('Raffiche di vento fino a 110 km/h.', 60, True),
    ('Vento con raffiche fino a 110 km/h.', 60, True),
    ('Windstoten van 110 km/h.', 60, True),
    ('Windstoten tot 110 km/h.', 60, True),
    ('Wind gusts of 110 km/h are expected.', 60, True),
    ('Gusts of wind up to 110 km/h.', 60, True),
    ('Severe wind gusts reaching 110 km/h.', 60, True),

]


@pytest.mark.parametrize("description,elevation,locked", AUDIT_CASES)
def test_independent_117_audit_cases(description, elevation, locked):
    result = assess(description, elevation=elevation)
    assert result["hard_lock"] is locked


WEATHER = ["Eisregen", "Schneeregen", "Graupelschauern", "Glatteis", "dichtem Nebel",
           "Eisglätte", "orkanartigen Böen", "starkem Schneeregen", "anhaltendem Eisregen"]


@pytest.mark.parametrize("condition", WEATHER)
@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h bei {condition}.", True),
    ("Bei {condition} sind Böen 110 km/h möglich.", True),
    ("Böen 110 km/h sind bei {condition} nicht ausgeschlossen.", True),
    ("Böen 110 km/h sind bei {condition} nicht zu erwarten.", False),
])
def test_weather_adjuncts_preserve_their_gust_predicate(condition, frame, locked):
    result = assess(frame.format(condition=condition))
    assert result["hard_lock"] is locked
    assert not result["gust_scope_uncertain"] and not result["gust_time_uncertain"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h bei Eisregenhausen.", "Böen 110 km/h bei Schneeregenstadt.",
    "Böen 110 km/h bei Graupelberg.", "Böen 110 km/h bei Glatteisheim.",
    "Böen 110 km/h bei Eisglättetal.", "Böen 110 km/h bei dichtem Nebelheim.",
    "Böen 110 km/h bei orkanartigen Böenhausen.",
    "Böen 110 km/h bei Eisregen im Harz.", "Bei Eisregen im Harz Böen 110 km/h.",
    "Böen 110 km/h bei orkanartigen Böen nördlich von Bonn.",
])
def test_weather_grammar_does_not_consume_named_or_additional_places(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


DENIALS = [
    "Böen 110 km/h werden unter keinen Umständen auftreten.",
    "Böen 110 km/h sind nicht zu befürchten.",
    "Böen 110 km/h lassen sich sicher ausschließen.",
    "Böen 110 km/h werden zu keiner Zeit auftreten.",
    "Böen 110 km/h wurden offiziell ausgeschlossen.",
]


@pytest.mark.parametrize("description", DENIALS)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_grammatical_denial_and_flat_parameters_keep_the_absent_wind(description, parameters):
    result = assess(description, parameters)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("description", [
    "Böen 110 km/h sind unter keinen Umständen auszuschließen.",
    "Böen 110 km/h lassen sich nicht ausschließen.",
    "Böen 110 km/h lassen sich nicht sicher ausschließen.",
    "Böen 110 km/h sind zu befürchten.",
    "Böen 110 km/h werden offiziell erwartet.",
    "Böen 110 km/h, Schäden werden unter keinen Umständen auftreten.",
    "Böen 110 km/h, Schäden sind nicht zu befürchten.",
    "Böen 110 km/h, Schäden lassen sich sicher ausschließen.",
    "Böen 110 km/h, Graupel wird zu keiner Zeit auftreten.",
    "Keine Eisglätte bei Böen 110 km/h zu erwarten.",
    "Wind gusts 110 km/h with hail not expected.",
    "Böen 110 km/h mit Graupel nicht zu erwarten.",
])
def test_negated_exclusions_or_other_subjects_do_not_deny_the_gusts(description):
    result = assess(description)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110


CORRIDORS = ["von Bonn bis Köln", "von Bad Godesberg bis Köln", "from Bonn to Cologne",
             "von Neudorf bis Altstadt", "von der Eifel bis an den Rhein"]


@pytest.mark.parametrize("corridor", CORRIDORS)
@pytest.mark.parametrize("frame", ["Böen 110 km/h {corridor}.", "{corridor} Böen 110 km/h.",
                                   "Böen 110 km/h, {corridor}."])
def test_correlated_place_prepositions_need_a_verified_window(corridor, frame):
    result = assess(frame.format(corridor=corridor))
    assert not result["hard_lock"] and result["gust_scope_uncertain"]
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("text,changes", [
    ("Böen von 90 bis 110 km/h.", {}),
    ("Böen 110 km/h von 18:00 UTC bis 20:00 UTC.",
     {"now": NOW.replace(hour=18, minute=0)}),
    ("Böen 110 km/h von 2026-10-24T18:00:00Z bis 2026-10-24T20:00:00Z.",
     {"now": NOW.replace(hour=18, minute=0)}),
])
def test_numeric_speed_and_time_ranges_are_not_geographic_corridors(text, changes):
    result = assess(text, **changes)
    assert result["hard_lock"] and not result["gust_scope_uncertain"]
    assert not result["gust_time_uncertain"]


def test_a_calendar_range_without_a_unique_date_stays_temporally_unresolved():
    result = assess("Böen 110 km/h von Montag bis Dienstag.")
    assert not result["hard_lock"] and result["gust_time_uncertain"]
    assert not result["gust_scope_uncertain"]


WHOLE_AREAS = ["überall im Warngebiet", "flächendeckend im Warngebiet",
               "überall innerhalb des Warngebiets", "everywhere in the warning area",
               "überall in der Warnregion", "flaechendeckend im Warnbereich",
               "nur im gesamten Warngebiet", "only in the entire warning area"]


@pytest.mark.parametrize("area", WHOLE_AREAS)
@pytest.mark.parametrize("cap_unknown", [False, True])
def test_universal_distribution_uses_only_the_matched_cap_area(area, cap_unknown):
    result = assess(f"Böen 110 km/h {area}.", area_restriction_unknown=cap_unknown)
    assert result["hard_lock"] is (not cap_unknown)
    assert result["area_verified"] is (not cap_unknown)


@pytest.mark.parametrize("area", [
    "nicht überall im Warngebiet", "fast überall im Warngebiet",
    "nahezu flächendeckend im Warngebiet", "überall im Harz",
    "überall im Warngebiet im Harz", "überall im Warngebiet des Harzes",
    "nicht im gesamten Warngebiet", "almost in the entire warning area",
])
def test_qualified_distribution_and_named_regions_are_not_universal_cap_coverage(area):
    result = assess(f"Böen 110 km/h {area}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


HEIGHTS = [
    ("ab einer Höhe von", operator.ge), ("oberhalb einer Höhe von", operator.gt),
    ("unterhalb einer Höhe von", operator.lt), ("bis zu einer Höhe von", operator.le),
    ("in Höhen über", operator.gt), ("in Höhen unter", operator.lt),
    ("in Höhenlagen oberhalb von", operator.gt), ("in Höhenlagen unterhalb von", operator.lt),
    ("in einer Höhe ab", operator.ge), ("oberhalb von einer Höhe von", operator.gt),
]


@pytest.mark.parametrize("phrase,compare", HEIGHTS)
@pytest.mark.parametrize("elevation", [60, 1199.99, 1200, 1200.01, 1500])
@pytest.mark.parametrize("unit", ["m", "Metern"])
def test_complete_height_noun_groups_preserve_exact_relations(phrase, compare, elevation, unit):
    result = assess(f"Böen 110 km/h {phrase} 1200 {unit}.", elevation=elevation)
    assert result["hard_lock"] is compare(elevation, 1200)
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("elevation", [None, True, math.nan, math.inf])
def test_a_height_noun_group_cannot_verify_missing_or_invalid_elevation(elevation):
    result = assess("Böen 110 km/h ab einer Höhe von 1200 Metern.", elevation=elevation)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("offset,locked", [(-1801, False), (-1800, True), (0, True),
                                          (7199, True), (7200, False)])
def test_height_and_zoned_clock_adjuncts_have_independent_units_and_boundaries(offset, locked):
    start = NOW.replace(hour=18, minute=0, second=0)
    result = assess("Böen 110 km/h ab einer Höhe von 1200 Metern von 18.00 UTC bis 20.00 UTC.",
                    elevation=1500, now=start + timedelta(seconds=offset))
    assert result["hard_lock"] is locked
    assert not result["gust_time_uncertain"] and not result["gust_scope_uncertain"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h ab einer Höhe von 1200 Metern ab 18 Uhr.",
    "Böen 110 km/h ab einer Höhe von 1200 Metern ab Montag.",
])
def test_recognized_height_does_not_supply_an_unknown_clock_or_calendar_date(description):
    result = assess(description, elevation=1500)
    assert not result["hard_lock"] and result["gust_time_uncertain"]


GUST_GROUPS = ["Gusts of wind", "Rachas de viento", "Raffiche di vento", "Rafales de vent"]


@pytest.mark.parametrize("group", GUST_GROUPS)
@pytest.mark.parametrize("speed,locked", [(70, False), (89.99, False), (90, True), (110, True)])
def test_international_gust_noun_groups_bind_their_own_value(group, speed, locked):
    result = assess(f"{group} {speed} km/h.")
    assert result["hard_lock"] is locked and result["gust_max_kmh"] == speed


@pytest.mark.parametrize("description", [
    "No rachas de viento de 110 km/h.",
    "No se esperan rachas de viento de 110 km/h.",
    "Non sono previste raffiche di vento fino a 110 km/h.",
    "Gusts of wind up to 110 km/h are not expected.",
    "Rafales de vent de 110 km/h sont exclues.",
])
def test_negation_stays_on_the_international_gust_noun_group(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("description", [
    "Gusts of wind 70 km/h, wind 110 km/h.",
    "Rachas de viento de 70 km/h y viento de 110 km/h.",
    "Raffiche di vento di 70 km/h e vento di 110 km/h.",
    "Rafales de vent de 70 km/h et vent de 110 km/h.",
])
def test_an_independent_mean_wind_does_not_inherit_the_gust_subject(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_max_kmh"] == 70


@pytest.mark.parametrize("description", ["Gusts, wind 110 km/h.", "Gusts with wind 110 km/h.",
                                          "Rachas con viento de 110 km/h."])
def test_only_a_direct_nominal_complement_can_extend_the_gust_group(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("field", ["headline", "event", "parameter", "description"])
@pytest.mark.parametrize("text,locked,elevation", [
    ("Böen 110 km/h bei Eisregen.", True, 60),
    ("Böen 110 km/h werden unter keinen Umständen auftreten.", False, 60),
    ("Böen 110 km/h von Bonn bis Köln.", False, 60),
    ("Böen 110 km/h überall im Warngebiet.", True, 60),
    ("Böen 110 km/h ab einer Höhe von 1200 Metern.", True, 1500),
    ("Rachas de viento de 110 km/h.", True, 60),
])
def test_each_warning_source_uses_the_same_assertion_grammar(field, text, locked, elevation):
    changes = {field: text} if field in {"headline", "event"} else {}
    parameters = {"gusts": text} if field == "parameter" else {}
    result = assess(text if field == "description" else "", parameters,
                    elevation=elevation, **changes)
    assert result["hard_lock"] is locked
